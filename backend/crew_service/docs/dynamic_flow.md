# Dynamic Flow Building

This document explains how Crew Service turns declarative YAML (`app/config/tasks.yaml`, `app/config/agents.yaml`, and tool specs) into executable CrewAI flows at runtime. The dynamic builder lives under `app/services/flow/` and is consumed by `FlowService` whenever the API or worker needs to launch a crew run.

## Key Modules

| Module | Purpose |
| --- | --- |
| `app/services/flow/flow_builder.py` | Creates CrewAI agents, derives dependency graphs, builds the Flow state model, and synthesizes a sequential `Flow` subclass tailored to the requested tasks. |
| `app/services/flow/flow_service.py` | Thin façade used by endpoints/workers to fetch required inputs, build flows, execute them, and validate user-supplied values. |
| `app/services/flow/flow_utils.py` | Shared helpers for resolving agent tools, mapping YAML types to Python/Pydantic types, interpolating prompt templates, and validating input payloads. |

## Configuration Inputs

All of the builder logic is data-driven:

- `config.tasks_config` and `config.state_fields_config` come from `app/config/tasks.yaml`. Tasks declare which fields they read/write, which agent should execute them, prompts, and output handling metadata. State fields are typed, labeled as `context` or `data`, and list cardinality restrictions.
- `config.agents_config` comes from `app/config/agents.yaml` and declares each agent's role, goal, backstory, and the tools they may access.
- `config.tools_spec_config` (from `app/lib/tools/tools_spec.yaml`) documents tool parameters; `flow_utils.TOOL_MAP` provides the actual callables that CrewAI agents can invoke.

## 1. Building the FlowDependencyGraph

`flow_builder.build_flow_dependency_graph` collects the state schema plus the read/write edges for the subset of tasks that will compose the flow (`TaskRead` models from the CRUD service). The resulting `FlowDependencyGraph` (`app/models/models.py`) tracks:

- `state_field_specs`: every field declared in the YAML state schema.
- `task_read_specs` / `task_write_specs`: per-task declarations of which fields are touched, including cardinality (`required`, `optional`, `at_least_one`) and write mode (`replace`, `append`).
- `field_readers` / `field_writers`: reverse lookups used for validation and dependency inference.

Graph creation immediately enforces invariants such as “context fields cannot be optional” so configuration issues fail before execution.

## 2. Inferring Required Inputs

`flow_builder.infer_initial_inputs` examines the dependency graph to figure out which state fields must be provided before the flow starts:

- **Context inputs** – All context fields read by any of the selected tasks.
- **Data inputs** – Data fields that at least one task requires but no selected task writes.

`FlowService.get_required_inputs` wraps this logic and returns `{field_name: type_str}` to callers so the UI can prompt the user before launching a run. `FlowService.validate_inputs` reuses the same graph to ensure required values are present, are non-null, and match their declared types via `flow_utils.validate_value_type`.

## 3. Flow State Model Generation

`flow_builder.build_flow_state_model` turns the dependency graph into a concrete Pydantic model that reflects only the fields touched by the requested tasks:

1. It seeds metadata fields (`flow_id`, `run_id`, `crew_run_id`).
2. It scans all read/write specs to determine which user-defined fields are actually needed.
3. For each field, it maps YAML type strings to Python/Pydantic types using `flow_utils.resolve_python_type`. List fields default to empty lists; scalars default to `None`.
4. It uses `pydantic.create_model` to synthesize the `FlowState` class, which becomes the generic parameter for the dynamic CrewAI `Flow` subclass.

This means each run has a minimal state surface and enjoys precise type validation during execution.

## 4. Agent and Tool Wiring

`flow_builder.build_crewai_agents` instantiates CrewAI `Agent` objects for every entry in `agents_config`. Tool names listed in `agents.yaml` are resolved to callables through `flow_utils.resolve_tools_for_agent`, which looks up each name in `TOOL_MAP`. Unknown tools are ignored so YAML typos cannot crash the service.

Inside each task step, prompt templates pulled from `tasks_config` are interpolated via `flow_utils.interpolate_task_description`. Any `{field_name}` placeholders are replaced with the current state value (or the placeholder `NOT PROVIDED BY USER` when a field is `None`). A helper named `build_tools_section` can embed structured tool docs inside a task description if the template opts into it.

## 5. Dynamic Flow Class Creation

For every requested `TaskRead`, `flow_builder.build_task_step_function` emits a Python function that will become one `@listen` step in the flow. Each step performs the same pattern:

1. **Read enforcement** – Pulls required fields from `self.state` based on the graph. Cardinality rules (`required`, `at_least_one`) are checked at runtime.
2. **CrewAI execution** – Builds a single-agent CrewAI `Task` with guardrails enabled. Each task uses the agent from YAML, the interpolated description, expected output text, and `llm_judge_guardrail` to validate the response via a second LLM.
3. **State writes** – Applies `replace` or `append` writes declared in YAML, storing the raw CrewAI output in the appropriate state fields.

`flow_builder.build_dynamic_flow_class` then:

- Defines an `initialize_flow` method marked with `@start`. It pulls incoming inputs out of OpenTelemetry baggage (CrewAI flows pass them in this way), copies them onto the state, generates a `run_id`, and validates that all context fields required by the selected tasks are populated.
- Wires every generated step with `@listen`, forming a sequential chain (`initialize_flow → step_task_a → step_task_b → …`).
- Subclasses `crewai.flow.Flow` with the generated state model so each run has typed access to `self.state`.

The final product is a tailor-made `Flow` subclass ready to run just the requested tasks in order.

## 6. FlowService Responsibilities

`FlowService` (`app/services/flow/flow_service.py`) is a small orchestration façade consumed by routes and the worker:

- `get_required_inputs(task_reads)` – returns the fields + types that callers must collect.
- `build_flow(task_reads)` – delegates to `flow_builder.create_flow_from_tasks`, which returns `(FlowStateModel, FlowClass, required_inputs)`.
- `execute_flow(flow_class, inputs)` – instantiates the generated flow and calls `flow.kickoff(inputs=inputs)`. The inputs dictionary becomes the baggage consumed by `initialize_flow`.
- `validate_inputs(inputs, tasks)` – ensures inputs are present and type-safe before `execute_flow` is allowed to run.

Because `FlowService` always routes through `build_flow_dependency_graph` and `infer_initial_inputs`, the API and background worker stay perfectly aligned with the YAML schema without duplicating logic.

## 7. Type and Value Validation Helpers

`flow_utils.validate_value_type` enforces that user-supplied data matches the schema:

- Supports nested list syntax (`list[MarketingResearch]`, `Type[]`).
- Validates ISO8601 date strings.
- Delegates to `CUSTOM_TYPE_REGISTRY` for rich Pydantic models such as `MarketingResearch` and `ContentStrategy`.
- Falls back to `Dict[str, Any]` for unknown custom types so new structs can be onboarded without code changes.

`resolve_python_type` mirrors this mapping logic for the FlowState model so reads/writes remain type-consistent.

## Execution Lifecycle Recap

1. **Task selection** – CRUD service (or the API client) sends an ordered list of `TaskRead` entries describing the logical flow.
2. **Flow construction** – `FlowService.build_flow` invokes `create_flow_from_tasks`, which builds the dependency graph, infers required inputs, creates CrewAI agents, generates the FlowState model, and emits the dynamic `Flow` subclass.
3. **Input validation** – Callers ask `FlowService.get_required_inputs` (for UI) and/or `FlowService.validate_inputs` (for backend safety) before execution.
4. **Runtime** – `FlowService.execute_flow` instantiates the Flow and runs `kickoff(inputs=...)`. CrewAI sequentially executes each generated step, storing outputs back into `self.state` as declared in YAML.
5. **Outputs** – Downstream services read the state (or files referenced in `output_file`) to persist or display results.
