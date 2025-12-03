# Crew Run Retry Flow

This guide documents how the Crew Service recreates a crew run that resumes from a specific task. The retry implementation lives in `app/api/crew_endpoints.py` (request surface) and `app/services/crew_service.py` (business logic near `retry_crew_run`). Use this when a user wants to re-run a portion of a flow without discarding upstream work.

## API Contract
- **Endpoint**: `POST /crew/crew-run/{crew_run_id}/retry`
- **Payload**: `CrewRunRetryRequest` with two required fields:
  - `retry_from_task_key`: task key from the original `tasks_snapshot` where the new run should restart.
  - `feedback`: free-form text explaining why the retry was requested; stored for auditing.
- **Response**: `CrewRun` for the newly created run (HTTP 201). Validation failures surface as HTTP 400 with the underlying error message.

## Validation and Task Selection
`CrewService.retry_crew_run` first fetches the existing run from the CRUD service to recover the immutable `tasks_snapshot`, run inputs, and recorded task states.

1. `_validate_retry_task_completed` ensures the run has task states and verifies that `retry_from_task_key` exists and is `TaskStatus.COMPLETED`. Retrying from any other status is rejected because downstream state would be undefined.
2. `_find_upstream_tasks` and `_find_downstream_tasks` walk the ordered `tasks_snapshot` to split the flow into three regions:
   - Upstream tasks keep their prior outputs.
   - `retry_from_task_key` plus all downstream tasks will be re-executed.
3. The service hydrates every snapshot entry into a `TaskInfo` and rebuilds the `FlowDependencyGraph`. This graph is essential for understanding which state fields were written by the tasks that are about to run again.

## Input Filtering and Metadata Preparation
The retry uses the original `run_metadata.inputs` as its starting point but filters out stale data to avoid leaking old outputs into the new run.

1. Build `fields_written_by_retry_tasks` by asking the dependency graph which state fields are written by the retry task itself or any downstream task.
2. Iterate over the original inputs:
   - Keep all context fields because they are user supplied and never overwritten at runtime.
   - Keep non-context fields only if no retried task writes them. This guarantees that regenerated data is recomputed instead of being pre-populated.
3. Construct a new `CrewRunMetadataCreate` using:
   - The unmodified `tasks_snapshot` (the retry must execute the same ordered tasks).
   - Fresh `inputs` containing only the filtered values.
   - `retry_feedback` populated with a single `RetryFeedback` entry `{retry_from_task_key, feedback}`. Each retry appends to this list so the CRUD service tracks the retry lineage.

## Seeding Task States
The new run's output payload is initialized via `_create_retry_task_states`:

1. The helper receives the upstream tasks, retry task key, downstream tasks, and the full snapshot for order lookups.
2. For every upstream task, it copies the entire original `TaskStateSnapshot` from the original run, preserving:
   - `state` (task outputs and execution state)
   - `status` (ensured to be `TaskStatus.COMPLETED`)
   - `order` (execution order)
   - `completed_at` (original completion timestamp)
   - All other fields and `additional_properties`
   
   If an upstream task's state doesn't exist in the original run, a new `TaskStateSnapshot` is created with `COMPLETED` status as a fallback.
3. For the retry task (`retry_from_task_key`) and all downstream tasks, new `TaskStateSnapshot` objects are created with `QUEUED` status, so they will be re-executed.
4. The resulting `CrewRunOutputCreateTaskStates` contains entries for all tasks: upstream tasks with preserved states, and retry/downstream tasks with `QUEUED` status.

Because upstream states are copied entirely from the original run (including their completion timestamps and outputs), UI surfaces (e.g., task history) immediately show which parts of the flow are being preserved, while the worker recomputes every task at and after `retry_from_task_key`.

## Creating the New Run and Cleaning Up
After preparing metadata and output scaffolding, the service:

1. Builds a `CrewRunCreate` (`crew_id`, new metadata, seeded output) and posts it to the CRUD service through `create_crew_run_func`.
2. Validates the response:
   - Non-201 status codes are turned into `ValueError` messages that include any response body text.
   - Parsed `HTTPValidationError` payloads or missing responses also raise `ValueError`.
3. Once the new run is created, the original run is cancelled via `cancel_crew_run` unless its queue status is already `CANCELLED` or `COMPLETED`. Cancellation failures are logged but do not fail the retry request—the newly created run remains valid.
