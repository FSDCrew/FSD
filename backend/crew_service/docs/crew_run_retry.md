# Crew Run Retry Modules

This document explains the retry flow through the logic implemented inside:

- `app/services/retry/retry_service.py` - Retry creation (API endpoint)
- `app/services/retry/retry_task_analyzer.py` - Task dependency analysis
- `app/services/retry/retry_validator.py` - Retry request validation
- `app/services/retry/retry_executor.py` - Retry execution preparation

## RetryService Overview

`RetryService` orchestrates the server-side retry process. It is constructed with an authenticated CRUD client and internally owns a `RetryValidator` plus a `RetryTaskAnalyzer`. Its responsibilities span fetching the original run, validating the request, preparing the payload for the new run, and coordinating CRUD API calls that create, copy, and cancel resources.

### `get_crew_run`

`get_crew_run` wraps the generated `get_crew_run_func` client call. It returns the parsed `CrewRunRead` or raises a `ValueError` when the run is missing or the CRUD service responds with a validation error/404. `errors.UnexpectedStatus` is propagated unless it is a 404, which is converted to a `ValueError` for the caller.

### `retry_crew_run`

The central entry point accepts a `CrewRunRetryRequest`, a `crew_run_id`, and a `user_token`. The method performs the following steps in order:

1. **Load the original run** via `get_crew_run`. A missing run aborts the request.
2. **Validate the retry task** by calling `RetryValidator.validate_retry_request`. Only tasks that exist in the saved task states and are `TaskStatus.COMPLETED` can be used as the retry point; failures are surfaced as HTTP 400 errors.
3. **Partition task states**:
   - `crew_run.output.task_states.additional_properties` are sorted by each snapshot’s `order`.
   - `tasks_snapshot` is converted to a `{task_key: TaskInfo}` dictionary for quick lookups.
   - `RetryTaskAnalyzer.find_upstream_tasks` returns all tasks before `retry_from_task_key`.
   - `RetryTaskAnalyzer.find_retry_and_downstream_tasks` returns `retry_from_task_key` plus everything after it.
4. **Seed output state for the new run** by constructing a `CrewRunOutputCreateTaskStates`:
   - Upstream tasks are copied directly into the new structure and forced to `TaskStatus.COMPLETED`.
   - The retry task and everything downstream are reset to new `TaskStateSnapshot` objects with empty `state`, a queued status, and preserved `order`.
5. **Reuse metadata** by cloning the original `run_metadata.inputs` into a `CrewRunMetadataCreateInputs` object and reusing the original `tasks_snapshot` inside a new `CrewRunMetadataCreate`. The new metadata also records a `RetryFeedback` payload (`retry_from_task_key` plus the user-provided `feedback`) so downstream components know which task triggered the retry and can surface the feedback to the agent that will re-run it.
6. **Create the retry run** by calling `_create_retry_crew_run`, which posts a `CrewRunCreateBody` (wrapping `CrewRunCreate`) to `create_crew_run_func`. The helper raises descriptive `ValueError`s when the CRUD service does not return HTTP 201, returns `HTTPValidationError`, or produces no parsed payload.
7. **Copy artifacts** with `_copy_artifacts`, which invokes `copy_artifacts_func.asyncio_detailed` and rejects non-200 responses.
8. **Cancel the original run** with `_cancel_original_crew_run`, unless its `queue_status` is already `CANCELLED` or `COMPLETED`. Cancellation errors are logged and re-raised so callers can decide how to handle failures.

The method returns the `CrewRunRead` for the newly created retry run.

### Error Handling Helpers

- `_create_retry_crew_run` logs and re-raises unexpected exceptions after enriching value errors with payload content when available.
- `_copy_artifacts` and `_cancel_original_crew_run` wrap errors in log statements so operators can trace failed cleanup work.

## RetryTaskAnalyzer Helpers

`RetryTaskAnalyzer` packages common routines for understanding task order and state-field relationships:

- `find_upstream_tasks(sorted_task_states, tasks_snapshot_dict, retry_from_task_key)` walks the sorted task states until it reaches the retry key and returns `(task_key, snapshot, task_info)` tuples for everything before it.
- `find_retry_and_downstream_tasks(...)` locates the index of `retry_from_task_key` in the sorted list and returns tuples for that task plus every item after it. Missing keys raise `ValueError`.
- `get_fields_written_by_tasks(graph, task_keys)` inspects `FlowDependencyGraph.task_write_specs` and returns the set of state fields any of the provided tasks can write.
- `filter_inputs_for_retry(original_inputs, graph, tasks_to_retry_keys)` removes stale fields from the input payload:
  - Context fields (identified via `graph.state_field_specs[field_name]["field_kind"] == "context"`) are always preserved.
  - Non-context fields are kept only if no retried task writes them.
  - The filtered dictionary can be fed into a new metadata payload so retried tasks recompute the fields they own.

These helpers are designed to ensure upstream work is preserved while retry tasks get a clean slate.

## RetryValidator Rules

`RetryValidator.validate_retry_request` enforces the invariants used by `RetryService`:

1. The provided `retry_from_task_key` must exist inside `crew_run.output.task_states`.
2. The referenced task must currently be marked `TaskStatus.COMPLETED`.

Any violation raises a `ValueError`, which `RetryService.retry_crew_run` wraps in an HTTP 400 response. This keeps retry execution limited to well-defined task boundaries.

## RetryExecutor Overview

`RetryExecutor` (`app/services/retry/retry_executor.py`) prepares crew run execution for retry scenarios. It is called by `run_entire_job` in `job_executor.py` when a crew run has `retry_feedback` set in its metadata.

### `prepare_retry_execution`

The `prepare_retry_execution()` static method orchestrates the preparation of a retry execution:

1. **Detects retry**: Checks that `crew_run.run_metadata.retry_feedback` is not null and is a `RetryFeedback` object.
2. **Extracts retry metadata**: Gets `retry_from_task_key` and `feedback` from the `retry_feedback` object.
3. **Partitions tasks**: Uses `RetryTaskAnalyzer.find_upstream_tasks()` and `find_retry_and_downstream_tasks()` to identify which tasks are upstream (completed) and which need to be retried.
4. **Filters tasks**: Creates a filtered list containing only `retry_from_task_key` and downstream tasks. This ensures the flow only executes tasks that need to be retried.
5. **Modifies retry task description**: Prepends a formatted retry prompt to the retry task's description, instructing the agent to ground their work on the feedback. The prompt includes the feedback text in a structured format.
6. **Extracts upstream outputs**: Collects outputs from all upstream tasks that have `TaskStatus.COMPLETED`. Outputs are extracted from `task_state.state.additional_properties` where field names are the keys.
7. **Combines inputs**: Merges `run_metadata.inputs` (context fields and initial inputs) with upstream task outputs (data fields) into a single inputs dictionary. This ensures downstream tasks have access to all necessary data.
8. **Returns prepared data**: Returns `(filtered_tasks, combined_inputs)` where:
   - `filtered_tasks`: List of `TaskInfo` objects starting from `retry_from_task_key`, with the retry task's description already modified to include the retry prompt
   - `combined_inputs`: Dictionary combining original inputs and upstream outputs

The method ensures that:

- Upstream work is preserved (outputs are extracted and merged into inputs)
- Only tasks that need retrying are included in the flow
- The retry task receives clear feedback instructions in its description
- Flow builder remains retry-agnostic (it just receives pre-prepared tasks and inputs)

### Helper Methods

- `_extract_upstream_outputs(upstream_tasks)`: Extracts outputs from completed upstream tasks, returning a dictionary of field_name -> output_value. Only tasks with `TaskStatus.COMPLETED` are processed.
- `_format_retry_prompt(original_description, feedback)`: Formats the retry prompt by prepending structured instructions and the feedback text to the original task description.

## Retry Execution Flow

When a retry crew run is executed:

1. **Creation** (`RetryService.retry_crew_run`): Creates a new crew run with `retry_feedback` set, upstream tasks marked as COMPLETED, and retry/downstream tasks marked as QUEUED.
2. **Queue Processing**: The worker picks up the retry crew run from the queue.
3. **Execution Preparation** (`RetryExecutor.prepare_retry_execution`): When `run_entire_job` detects `retry_feedback`, it calls `RetryExecutor` to:
   - Filter tasks to only include retry and downstream tasks
   - Extract upstream outputs and merge with original inputs
   - Modify retry task description with feedback prompt
4. **Flow Building**: Flow builder receives filtered tasks and combined inputs, building a flow that starts from the retry task.
5. **Flow Execution**: The flow executes normally, starting from the retry task (which now has feedback in its description) and continuing through downstream tasks. All necessary data from upstream tasks is available in the flow state.
