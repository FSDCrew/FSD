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
| Queue Status | Cancellation Action | Notes |
| --- | --- | --- |
| `QUEUED` / `FAILED` | Status set directly to `CANCELLED`. | Job is never handed to a worker again. |
| `CLAIMED` | `cancel_requested = True`; status remains `CLAIMED` until the worker acknowledges. | Keeps the claiming worker as the only process allowed to finalize the row because its lease token is still valid. |
| `CLAIMED` after worker ack | Worker updates queue via `UpdateStatusRequest(status=CANCELLED)`. | Happens inside the crew-service worker once it abandons execution. |

## Worker Handshake for Claimed Jobs
When a job is already running, the worker must cooperate with the CRUD service to avoid leaving an orphaned process:

1. `Worker._execute_job` spawns `JobExecutor.execute` for each claimed job and stores the asyncio task + lease token in `running_jobs` (`backend/crew_service/app/services/worker.py`).
2. `JobExecutor.execute` creates a dedicated heartbeat loop (`_heartbeat_loop`) that calls `POST /internal/queue/{queue_id}/heartbeat` via the generated CRUD client (`backend/crew_service/app/services/job_executor.py`).
3. If `QueueRepository.cancel_claimed_job` previously set `cancel_requested`, the next heartbeat response carries `cancel_requested=True` (`QueueService.heartbeat` in `backend/crud_service/app/services/queue_service.py`).
4. `_heartbeat_loop` logs the cancellation request, cancels the running `execute_task`, and raises `asyncio.CancelledError`.
5. The `asyncio.CancelledError` bubbles through `JobExecutor.execute`, which:
   - Terminates the spawned flow subprocess and removes it from `process_registry`.
   - Calls `update_queue_status_internal` with `QueueStatus.CANCELLED` so the CRUD service permanently marks the queue row as cancelled.
6. `Worker._execute_job` catches the cancellation, removes the task from `running_jobs`, and the queue entry no longer appears in future polls.

## Additional Notes
- Because the cancellation path reuses the same lease token that claimed the job, only the active worker can complete the transition to `CANCELLED`. This prevents a second worker from overriding the status mid-run.
- If the worker process itself shuts down (e.g., via `Worker.stop`), it explicitly cancels all running tasks and attempts to mark the associated queue entries as `FAILED` so they can be retried or cancelled later.
- No CRUD side effects occur after `QueueStatus.COMPLETED`; `cancel_crew_run` rejects such requests at the service layer to avoid rewriting historical runs.
