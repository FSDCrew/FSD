# Required Inputs - Backend Logic

This document explains how the backend determines which fields are required inputs for a crew run and how validation works.

## Overview

The backend uses a dependency graph built from task definitions in `tasks.yaml` to determine which state fields must be provided by the user before a crew run can start. This logic is implemented in `app/services/flow/flow_builder.py` via the `infer_initial_inputs` function.

## End-to-End Request Flow

When a frontend calls `GET /crew/{crew_id}/required-inputs`, the following happens:

1. **Authentication** – `get_user_token` (`app/dependencies.py`) extracts a bearer token or Cognito cookie. Missing tokens short-circuit with a 401.

2. **Crew lookup** – `CrewService.get_required_inputs` (`app/services/crew_service.py`) loads the crew from the CRUD service using `_get_crew_tasks`. The CRUD client returns the ordered `TaskRead` objects used to build the dynamic flow.

3. **Flow graph construction** – The `TaskRead` list is passed to `FlowService.get_required_inputs` (`app/services/flow/flow_service.py`). This constructs a `FlowDependencyGraph` via `build_flow_dependency_graph` (`app/services/flow/flow_builder.py`).

4. **Required inputs inference** – `infer_initial_inputs` (`app/services/flow/flow_builder.py`) analyzes the dependency graph to determine which state fields must be supplied up front.

5. **Response shaping** – `FlowService` enriches each required field with typed metadata (`FieldTypeInfo`) and frontend metadata (`required`, `placeholder`) from the YAML field definitions. The router returns `RequiredInputsResponse` to the client.

Because the API always sources the dependency graph from the YAML configs (`app/config/tasks.yaml` and `app/config/agents.yaml`), the UI automatically reflects schema changes without additional wiring.

## How Required Inputs Are Determined

`infer_initial_inputs` inspects every field defined under `state.fields` in `tasks.yaml` and applies two rules:

### Context Fields

**Rule**: Any context field read by at least one of the requested tasks is required.

Context fields are always user-provided entries (e.g., `theme`, `brand_description`, `templateId`). If any task in the crew reads a context field, it must be provided as an initial input.

### Data Fields

**Rule**: A data field is required if:
1. At least one task marks it as `cardinality: required` or `at_least_one` in its `reads` specification
2. AND no upstream task (one that executes earlier in the flow sequence) writes to that field

The function finds the earliest task that requires the field and checks if any task before it in execution order writes to it. If an upstream task writes the field, it will be available when the downstream task needs it, so it's not required as an initial input.

**Example**: 
- If Task A (position 0) requires field X and Task B (position 1) writes field X, then field X is **required** because Task A needs it before Task B runs.
- Conversely, if Task A writes field X and Task B requires it, field X is **not required** because Task A provides it before Task B executes.

`FlowService` merges both sets into the `required_inputs["all"]` list while preserving field order.

## Dependency Graph Structure

The `FlowDependencyGraph` tracks:

- **`field_writers`**: Maps field names to lists of task keys that write to that field
- **`field_readers`**: Maps field names to lists of task keys that read from that field
- **`task_read_specs`**: Maps task keys to their read specifications (including `cardinality`)
- **`task_write_specs`**: Maps task keys to their write specifications
- **`state_field_specs`**: Maps field names to their YAML field definitions (type, field_kind, required, placeholder, etc.)

## Input Validation

When a crew run is kicked off via `POST /crew/kickoff`, the backend validates inputs using `FlowService.validate_inputs()`:

1. **Required fields check**: Ensures all fields determined by `infer_initial_inputs` are provided
2. **Type validation**: Validates that each provided value matches the expected type from the state schema
3. **None check**: Ensures required fields are not `None`

**Important**: The validation logic uses `infer_initial_inputs` to determine required fields, **not** the `required` field in the YAML. The YAML `required` field is purely for frontend UI hints.

## Frontend Metadata Fields

The response includes two metadata fields that are **frontend-only** and do not affect backend logic:

- **`required`**: Boolean indicating if the field should be marked as required in the UI (defaults to `True` if not specified in YAML)
- **`placeholder`**: Optional placeholder text for form inputs (defaults to `None` if not specified in YAML)

These fields are extracted from the YAML field definitions (`state.fields.<field_name>.required` and `state.fields.<field_name>.placeholder`) but are **not used** by:
- `infer_initial_inputs()` - determines requirements based on task dependencies
- `validate_inputs()` - validates based on `infer_initial_inputs()` results
- Flow state creation - uses the dependency graph, not YAML metadata

**Note**: There may be cases where the YAML `required` field doesn't match what `infer_initial_inputs()` determines. In such cases, the backend validation will always enforce what `infer_initial_inputs()` returns, regardless of the YAML `required` value.

## Related Files

- `app/services/flow/flow_builder.py` - Contains `infer_initial_inputs()` and `build_flow_dependency_graph()`
- `app/services/flow/flow_service.py` - Contains `get_required_inputs()` and `validate_inputs()`
- `app/services/crew_service.py` - Contains `get_required_inputs()` endpoint handler
- `app/config/tasks.yaml` - Defines state fields and task dependencies
- `app/models/models.py` - Defines `RequiredInputsResponse`, `RequiredInputField`, and `FieldTypeInfo` models
