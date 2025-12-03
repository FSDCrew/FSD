# Worker Architecture and Lifecycle

This document explains how the Crew Service worker processes queue jobs from the CRUD service, executing CrewAI flows in isolated child processes. The worker uses a **process-per-job** model where each job runs in its own OS process, handling its complete lifecycle including heartbeats, cancellation detection, and status updates.

## Introduction

The worker (`app/services/worker.py`) is a long-running service that polls the CRUD service queue for available jobs and executes them by spawning dedicated child processes. Each child process (`run_entire_job` in `app/services/job_executor.py`) is self-contained and handles:

- Fetching crew run data from the CRUD service
- Preparing execution data (tasks, inputs, retry information)
- Running a heartbeat loop to extend the queue lease
- Building and executing the CrewAI flow
- Detecting and handling cancellation requests
- Updating queue status (COMPLETED, FAILED, or CANCELLED)

This architecture simplifies the worker by removing the need for per-job asyncio task orchestration, making the system more maintainable and easier to reason about.

## High-Level Flow

The worker operates in a simple polling loop:

1. **Poll for Jobs**: The worker periodically calls `POST /internal/queue/claim` to claim the next available job from the CRUD service queue.

2. **Check Concurrency**: Before claiming a job, the worker checks if it has reached `MAX_CONCURRENT_JOBS` (default: 3). If at capacity, it skips claiming and waits for the next poll cycle.

3. **Spawn Process**: When a job is claimed, the worker immediately spawns a new OS process using `multiprocessing.Process`, passing job metadata (crew_run_id, queue_id, lease_token) to `run_entire_job`.

4. **Track Process**: The spawned process is registered in `running_processes` dictionary, keyed by `queue_id`. The worker tracks process lifecycle but does not orchestrate execution.

5. **Cleanup**: On each poll cycle, the worker removes completed processes from the registry by checking `process.is_alive()`.

6. **Repeat**: The loop continues, polling at intervals defined by `QUEUE_POLL_INTERVAL_SECONDS`.

The worker itself is stateless regarding job execution—it only manages process spawning and cleanup. All job-specific logic lives in the child processes.

## Architecture Overview

### Process-Per-Job Model

The current architecture uses a **single-layer concurrency model** based entirely on OS processes:

```
Worker Process (Main Loop)
├── Polls CRUD Service Queue
├── Spawns Child Process per Job
└── Tracks Process Registry
    │
    └── Child Process (run_entire_job)
        ├── Heartbeat Thread (background)
        ├── Fetches Crew Run Data
        ├── Builds Flow
        ├── Executes Flow
        └── Updates Queue Status
```

**Key Characteristics:**
- **One OS process per job** handles the complete lifecycle
- **No asyncio tasks** are created per job in the worker
- **Child processes are self-contained** and independent
- **Heartbeat logic runs in a background thread** within each child process
- **Worker is simplified** to polling, spawning, and cleanup only

### Comparison with Previous Architecture

The previous architecture used a **two-layer concurrency model**:

**Old Model (Async Orchestrator):**
- Worker created asyncio tasks per job
- Each task orchestrated heartbeat loops and cancellation
- Tasks spawned separate child processes for flow execution
- Two layers: async tasks + OS processes

**New Model (Process-Per-Job):**
- Worker spawns OS processes directly
- Each process handles its own heartbeat, cancellation, and execution
- Single layer: OS processes only

This migration simplifies the codebase by removing async orchestration complexity and making each job process fully independent.

### Key Components

**Worker (`app/services/worker.py`)**
- `Worker` class: Main worker that polls and spawns processes
- `_poll_and_process()`: Polls queue and spawns processes when jobs are available
- `_cleanup_completed_processes()`: Removes dead processes from registry
- `stop()`: Gracefully terminates all running processes on shutdown

**Job Executor (`app/services/job_executor.py`)**
- `run_entire_job()`: Top-level function executed in each child process
- `HeartbeatThread`: Background thread that sends periodic heartbeats
- `ResultBuilder`: Utility for serializing flow execution results (kept for compatibility)

## Full Lifecycle and Process Handling

### Job Execution Lifecycle

When a job is claimed, the following sequence occurs:

#### 1. Process Spawning

```python
# Worker._poll_and_process()
job_metadata = {
    'crew_run_id': str(job.crew_run_id),
    'crew_id': str(job.crew_id),
    'queue_id': str(job.id),
    'lease_token': job.lease_token
}

process = multiprocessing.Process(
    target=run_entire_job,
    args=(job_metadata,)
)
process.start()
self.running_processes[job.id] = process
```

The worker spawns a new process using Python's `multiprocessing` module with the 'spawn' context. The process immediately starts executing `run_entire_job()`.

#### 2. Child Process Initialization

Inside `run_entire_job()`:

1. **Parse Job Metadata**: Extracts `crew_run_id`, `queue_id`, `lease_token` from the metadata dictionary.

2. **Initialize HTTP Client**: Creates a synchronous `AuthenticatedClient` for CRUD service communication.

3. **Create Cancellation Event**: Instantiates a `threading.Event` that the heartbeat thread will set when cancellation is detected.

4. **Start Heartbeat Thread**: Launches `HeartbeatThread` in a background daemon thread before any other work begins.

#### 3. Heartbeat Mechanism

The `HeartbeatThread` runs independently in the background:

- **Interval**: Sends heartbeats every `HEARTBEAT_INTERVAL_SECONDS` (configurable)
- **Purpose**: Extends the queue lease to prevent the job from being reclaimed
- **Cancellation Detection**: Checks `cancel_requested` flag in heartbeat response
- **Retry Logic**: Implements exponential backoff (up to 3 retries) for network failures
- **Signaling**: Sets `cancellation_event` when cancellation is detected

```python
# HeartbeatThread._heartbeat_loop()
while not self._stop_event.is_set():
    time.sleep(settings.HEARTBEAT_INTERVAL_SECONDS)
    success, cancel_requested = self._send_heartbeat_with_retry()
    
    if cancel_requested:
        self.cancellation_event.set()
        break
```

The heartbeat thread continues running until:
- Cancellation is detected (`cancel_requested=True`)
- The process is shutting down (`_stop_event` is set)
- An unrecoverable error occurs

#### 4. Fetching Crew Run Data

The child process fetches the crew run from the CRUD service:

```python
crew_run_response = get_crew_run_func.sync(
    crew_run_id=crew_run_id,
    client=crud_client
)
```

This includes:
- Task snapshots (ordered list of tasks to execute)
- Input values (user-provided inputs for the flow)
- Retry feedback (if this is a retry run)
- Task states (current status of each task)

#### 5. Preparing Execution Data

The process prepares data for flow execution:

- **Extracts Inputs**: Converts `crew_run.run_metadata.inputs` to a dictionary
- **Parses Tasks**: Validates task snapshots into `TaskInfo` objects
- **Handles Retry Logic**: If `retry_feedback` is present:
  - Finds the retry point (first `QUEUED` task)
  - Collects outputs from upstream `COMPLETED` tasks
  - Adds `_retry_info` to inputs dictionary

#### 6. Cancellation Check (Pre-Execution)

Before building the flow, the process checks if cancellation was detected:

```python
if cancellation_event.is_set():
    update_queue_status_func.sync(
        queue_id=queue_id,
        client=crud_client,
        body=UpdateStatusRequest(
            lease_token=lease_token,
            status=QueueStatus.CANCELLED
        )
    )
    return
```

If cancellation occurred during initialization, the process exits early and updates the queue status.

#### 7. Flow Building and Execution

The process builds and executes the CrewAI flow:

```python
flow_service = get_flow_service()
task_status_service = TaskStatusService()
FlowStateModel, FlowClass, _ = flow_service.build_flow(tasks, task_status_service)
flow = FlowClass()

# Execute flow in a separate thread to allow cancellation monitoring
flow_result = []
flow_exception = [None]

def run_flow():
    try:
        result = flow.kickoff(inputs=stored_inputs)
        flow_result.append(result)
    except Exception as e:
        flow_exception[0] = e

flow_thread = threading.Thread(target=run_flow, daemon=False)
flow_thread.start()

# Monitor flow execution and check for cancellation periodically
while flow_thread.is_alive():
    flow_thread.join(timeout=1.0)  # Check every second
    
    if flow_thread.is_alive() and cancellation_event.is_set():
        # Cancellation detected - update status and exit process
        update_queue_status_func.sync(...)
        heartbeat_thread.stop()
        os._exit(0)  # Terminates all threads including flow execution

# Flow completed - check for exceptions and handle result
if flow_exception[0]:
    raise flow_exception[0]
result = flow_result[0] if flow_result else None
```

**Note**: `flow.kickoff()` runs in a separate thread to enable cancellation monitoring. The main thread checks `cancellation_event` every second. When cancellation is detected, the process immediately updates the queue status to `CANCELLED` and exits using `os._exit(0)`, which terminates all threads including the flow execution thread, providing immediate cancellation.

#### 8. Post-Execution Status Update

After flow execution completes:

**On Success:**
```python
update_queue_status_func.sync(
    queue_id=queue_id,
    client=crud_client,
    body=UpdateStatusRequest(
        lease_token=lease_token,
        status=QueueStatus.COMPLETED
    )
)
```

**On Cancellation Detected:**
```python
if cancellation_event.is_set():
    update_queue_status_func.sync(
        queue_id=queue_id,
        client=crud_client,
        body=UpdateStatusRequest(
            lease_token=lease_token,
            status=QueueStatus.CANCELLED
        )
    )
```

**On Exception:**
```python
except Exception as flow_error:
    status = QueueStatus.CANCELLED if cancellation_event.is_set() else QueueStatus.FAILED
    update_queue_status_func.sync(
        queue_id=queue_id,
        client=crud_client,
        body=UpdateStatusRequest(
            lease_token=lease_token,
            status=status
        )
    )
```

#### 9. Cleanup

Finally, the process cleans up resources:

```python
finally:
    if heartbeat_thread:
        heartbeat_thread.stop()  # Stops heartbeat thread
    
    sync_client = crud_client.get_httpx_client()
    sync_client.close()  # Closes HTTP client
```

The process then exits, and the worker detects it as completed in the next poll cycle.

### Process Management

**Process Registry**

The worker maintains a `running_processes` dictionary:

```python
self.running_processes: dict[UUID, Any] = {}  # queue_id -> Process
```

- **Key**: `queue_id` (UUID of the queue job)
- **Value**: `multiprocessing.Process` object
- **Purpose**: Track active processes for cleanup and concurrency limits

**Process Cleanup**

On each poll cycle, the worker removes completed processes:

```python
def _cleanup_completed_processes(self):
    completed = [
        queue_id for queue_id, process in self.running_processes.items()
        if not process.is_alive()
    ]
    for queue_id in completed:
        process = self.running_processes.pop(queue_id, None)
        if process:
            process.join(timeout=0.1)  # Wait for process to fully exit
```

**Concurrency Control**

The worker enforces `MAX_CONCURRENT_JOBS` (default: 3):

```python
if len(self.running_processes) >= self.MAX_CONCURRENT_JOBS:
    return  # Skip claiming until capacity available
```

This prevents resource exhaustion by limiting simultaneous job executions.

### Cancellation Handling

Cancellation is detected and handled entirely within the child process:

1. **Detection**: `HeartbeatThread` receives `cancel_requested=True` in heartbeat response
2. **Signaling**: Thread sets `cancellation_event` to notify main execution
3. **Response**: Process checks `cancellation_event`:
   - Before flow execution: Exits early, updates status to CANCELLED
   - During flow execution: `flow.kickoff()` runs in a separate thread, and the main thread checks `cancellation_event` every second. When cancellation is detected, the process immediately updates status to CANCELLED, stops the heartbeat thread, closes the HTTP client, and exits using `os._exit(0)`, which terminates all threads including the flow execution thread
   - After flow execution: Updates status to CANCELLED if cancellation was detected (e.g., cancellation was set right before completion)
   - During exception handling: Sets status to CANCELLED if event is set

**Important**: CrewAI's `flow.kickoff()` does not support cancellation signals directly. To enable cancellation during flow execution, the flow runs in a separate thread, and the main thread periodically checks for cancellation. When cancellation is detected, the process immediately exits using `os._exit(0)`, providing immediate termination of the flow execution.

See [Crew Run Cancellation Flow](crewrun_cancellation.md) for details on the cancellation API and queue status transitions.

### Error Handling

Errors can occur at multiple stages:

**During Initialization:**
- Failed to fetch crew_run → Raises `ValueError`, updates status to FAILED
- Invalid job metadata → Raises exception, updates status to FAILED

**During Flow Execution:**
- Flow build failure → Exception caught, updates status to FAILED
- Flow execution failure → Exception caught, updates status to FAILED
- Network errors → Retried with exponential backoff, eventually updates status to FAILED

**During Status Update:**
- If status update fails, error is logged but process still exits
- The queue entry may remain in CLAIMED state until lease expires

All exceptions are caught in `run_entire_job()`'s outer try/except block, ensuring the process always attempts to update queue status before exiting.

### Process Isolation

Each child process is completely isolated:

- **Separate Memory Space**: No shared state between processes
- **Independent HTTP Clients**: Each process creates its own CRUD client
- **Isolated Logging**: Process ID included in logs for traceability
- **Clean Exit**: Process exits when job completes, fails, or is cancelled

This isolation ensures that:
- One job failure cannot affect others
- Resource leaks are contained to individual processes
- Process crashes don't crash the worker

## Configuration

The worker behavior is controlled by environment variables (see `config.py`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `QUEUE_POLL_INTERVAL_SECONDS` | Sleep interval between worker poll cycles | Required |
| `JOB_VISIBILITY_TIMEOUT_SECONDS` | Lease duration handed out by the CRUD queue | Required |
| `HEARTBEAT_INTERVAL_SECONDS` | Interval for extending the lease while a job is running | Required |
| `CRUD_SERVICE_URL` | Base URL for CRUD service API | Required |
| `INTERNAL_CREW_API_KEY` | Authentication token for internal API calls | Required |

**Worker-Specific Constants:**

- `MAX_CONCURRENT_JOBS`: Hardcoded to `3` in `Worker` class. This limits the number of simultaneous job executions.

## Shutdown Behavior

When the worker receives a shutdown signal (SIGINT, SIGTERM, or KeyboardInterrupt):

1. **Stop Polling**: `_running` flag is set to `False`, stopping the polling loop
2. **Terminate Processes**: All processes in `running_processes` are forcefully terminated:
   ```python
   for queue_id, process in processes_to_stop:
       if process.is_alive():
           process.terminate()  # Send SIGTERM
           process.join(timeout=5.0)
           if process.is_alive():
               process.kill()  # Send SIGKILL if still alive
               process.join()
   ```
3. **Close HTTP Client**: Async HTTP client is closed cleanly

**Important Notes:**
- Processes are terminated immediately—they do not have time to update queue status
- Queue entries remain in `CLAIMED` state until lease expires
- The CRUD service will eventually reclaim these jobs and make them available again
- No attempt is made to mark jobs as FAILED during shutdown (unlike the old async model)

This behavior prioritizes fast shutdown over graceful job completion, which is acceptable for a worker service that can be restarted.

## Related Documentation

- [Dynamic Flow Building](dynamic_flow.md) - How flows are constructed and executed
- [Crew Run Cancellation Flow](crewrun_cancellation.md) - Detailed cancellation mechanism
- [Crew Run Retry Flow](crew_run_retry.md) - How retry runs are handled

