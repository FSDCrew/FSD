# Crew Run Cancellation Flow

This guide explains how a crew run can be cancelled and how that request flows through the CRUD service queue, the worker, and the running flow execution.

## Entry Point (CRUD Service API)

1. **Endpoint:** `POST /internal/crew-run/{crew_run_id}/cancel` located in `backend/crud_service/app/api/internal_endpoints.py`.
2. **Auth & Validation:** `CrewRunService.cancel_crew_run` (`backend/crud_service/app/services/crew_run_service.py`) resolves the run plus its owning crew, ensures the caller owns the crew, and rejects requests when the queue status is already `CANCELLED` or `COMPLETED`.
3. **Status-Based Handling:**
   - `QUEUED` or `FAILED` → `QueueRepository.cancel_queued_job` immediately flips the row to `CANCELLED`.
   - `CLAIMED` → `QueueRepository.cancel_claimed_job` does **not** change `status`; it raises the `cancel_requested` flag so the worker that currently holds the lease can shut itself down cleanly.
   - Any other status → HTTP 400 because the run is not cancellable.

## Queue Status Lifecycle

| Queue Status               | Cancellation Action                                                                | Notes                                                                                                             |
| -------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `QUEUED` / `FAILED`        | Status set directly to `CANCELLED`.                                                | Job is never handed to a worker again.                                                                            |
| `CLAIMED`                  | `cancel_requested = True`; status remains `CLAIMED` until the worker acknowledges. | Keeps the claiming worker as the only process allowed to finalize the row because its lease token is still valid. |
| `CLAIMED` after worker ack | Worker updates queue via `UpdateStatusRequest(status=CANCELLED)`.                  | Happens inside the crew-service worker once it abandons execution.                                                |

## Worker Handshake for Claimed Jobs

When a job is already running, the worker and child process cooperate with the CRUD service to handle cancellation cleanly:

1. **Process Spawning**: `Worker._poll_and_process` spawns a new OS process (`run_entire_job`) for each claimed job and stores the process in `running_processes` dictionary, keyed by `queue_id` (`backend/crew_service/app/services/worker.py`). See [Worker Architecture and Lifecycle](worker.md) for details on the process-per-job model.

2. **Heartbeat Thread**: Inside the child process, `run_entire_job` creates a `HeartbeatThread` that runs in a background daemon thread. This thread periodically calls `POST /internal/queue/{queue_id}/heartbeat` using synchronous HTTP client (`backend/crew_service/app/services/job_executor.py`).

3. **Cancellation Detection**: If `QueueRepository.cancel_claimed_job` previously set `cancel_requested`, the next heartbeat response carries `cancel_requested=True` (`QueueService.heartbeat` in `backend/crud_service/app/services/queue_service.py`).

4. **Cancellation Signaling**: `HeartbeatThread._heartbeat_loop` detects `cancel_requested=True` in the response, logs the cancellation request, and sets a `threading.Event` (`cancellation_event`) to signal the main execution thread.

5. **Cancellation Handling**: The main execution thread in `run_entire_job` checks `cancellation_event` at multiple points:

   - **Before flow execution**: If cancellation is detected during initialization, the process exits early and updates queue status to `CANCELLED`.
   - **During flow execution**: `flow.kickoff()` runs in a separate thread, and the main thread periodically checks `cancellation_event` every second. When cancellation is detected, the process immediately updates queue status to `CANCELLED`, stops the heartbeat thread, closes the HTTP client, and exits the process using `os._exit(0)`, which terminates all threads including the flow execution thread.
   - **After flow execution**: If cancellation is detected after `flow.kickoff()` completes (e.g., cancellation was set right before completion), the process updates queue status to `CANCELLED`.
   - **During exception handling**: If an exception occurs and cancellation was detected, status is set to `CANCELLED` instead of `FAILED`.

6. **Status Update**: The child process calls `update_queue_status_internal` with `QueueStatus.CANCELLED` using the same lease token, ensuring only the process that claimed the job can finalize the status.

7. **Process Exit**: After updating status, the child process cleans up resources (stops heartbeat thread, closes HTTP client) and exits. The worker detects the completed process in the next poll cycle and removes it from `running_processes`.

## Additional Notes

- Because the cancellation path reuses the same lease token that claimed the job, only the child process that claimed the job can complete the transition to `CANCELLED`. This prevents a second worker from overriding the status mid-run.
- If the worker process itself shuts down (e.g., via `Worker.stop`), it forcefully terminates all running child processes. These processes do not have time to update queue status, so queue entries remain in `CLAIMED` state until the lease expires. The CRUD service will eventually reclaim these jobs and make them available again.
- **CrewAI Flow Cancellation**: CrewAI's `flow.kickoff()` does not support cancellation signals directly. To enable cancellation during flow execution, `flow.kickoff()` runs in a separate thread, and the main thread periodically checks for cancellation every second. When cancellation is detected, the process immediately updates the queue status to `CANCELLED` and exits using `os._exit(0)`, which terminates all threads including the flow execution thread, providing immediate cancellation.
- No CRUD side effects occur after `QueueStatus.COMPLETED`; `cancel_crew_run` rejects such requests at the service layer to avoid rewriting historical runs.

For detailed information on the worker architecture and process lifecycle, see [Worker Architecture and Lifecycle](worker.md).
