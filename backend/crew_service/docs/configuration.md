# Flow Configuration Files

This document explains how to work with the YAML files in `app/config/` and the validator script that keeps them consistent. These configuration files define the entire dynamic flow surface exposed by the crew service, so updating them correctly is critical.

## `app/config/tasks.yaml`

`tasks.yaml` is the single source of truth for both the flow state schema and the ordered task definitions consumed by the backend and frontend.

### `state.fields`

- Declares every piece of flow state. Each field entry includes:
  - `type` – primitive (`string`, `date`, etc.), lists (`list[string]`, `list[AllowedTemplateId]`), or custom models registered in `CUSTOM_TYPE_REGISTRY` (e.g., `MarketingResearch`).
  - `field_kind` – `context` fields are always user inputs; `data` fields may be produced by tasks.
  - Optional UX metadata (`required`, `placeholder`) that the frontend can use when rendering forms.
- Context fields drive `/crew/crews/{id}/required-inputs`: any context field referenced in a task read becomes a mandatory UI prompt. Data fields become required inputs when no task writes them (see `infer_initial_inputs`).
- Example (from `state.fields.theme`):

```yaml
theme:
  type: string
  field_kind: context
  required: true
  placeholder: "Enter your campaign theme"
```

### `tasks`

Each task entry mirrors a CrewAI step and must include:

- `key` (must match the task name) and `agent` (referencing `agents.yaml`).
- Narrative metadata (`name`, `task_description`, `description`, `expected_output`) used when generating prompts.
- `reads` and `writes` arrays that describe how the task interacts with state:
  - `reads[].field` names must exist under `state.fields` and declare a `cardinality` (`required`, `optional`, `at_least_one`). Context fields cannot be optional.
  - `writes[].field` must also exist in the schema and can optionally assert a `type` that is validated against the field definition. `mode` (`replace`/`append`) controls how flow state is mutated.
- Optional metadata: `output_file` (default artifact path), `crew_inputs` hints, sample HTML/JSON blocks, etc.

The backend converts these declarations into task-specific dependency graphs, FlowState models, and dynamic CrewAI steps (see `docs/dynamic_flow.md`).

## `app/config/agents.yaml`

Defines the agents referenced by tasks. Each top-level key is the agent identifier surfaced to `tasks.yaml` and must include:

- `key` – explicit agent key; when omitted, the YAML key itself is used.
- `role`, `goal`, and `backstory` – textual prompts that CrewAI uses to prime the agent persona. These fields support string interpolation (e.g., `{start_date}`) when interpolated inside tasks.
- Optional `tools` – list of tool names referenced in `app/services/flow/flow_utils.py::TOOL_MAP`. Any tool listed here becomes available to the agent when the flow builder instantiates CrewAI agents.

Agents can be lightweight (no tools) or specialized (e.g., `orshot_template_mapper` that mandates `orshot_render_tool`). When you add a new agent, make sure its `key` matches the value used in tasks.

## `app/config/validate_tasks_yaml.py`

This script enforces structural integrity across both YAML files. Run it whenever you touch `tasks.yaml` or `agents.yaml`:

```bash
uv run python app/config/validate_tasks_yaml.py app/config/tasks.yaml
```

### What it checks

1. **Duplicate keys** – Uses a `UniqueKeyLoader` so YAML parsing fails if a section redeclares the same key (prevents silent overwrites).
2. **State schema** – Ensures `state.fields` exists, every field lists a `type` and valid `field_kind`, and optional flags (`required`, `placeholder`) use the correct types.
3. **Task completeness** – Verifies every task declares `key`, `name`, `task_description`, `description`, and `expected_output`, and that `key` matches the task ID.
4. **Reads/Writes consistency** – Confirms each referenced field exists, `cardinality` sits in `{required, optional, at_least_one}`, context fields are never optional, and write overrides match the declared field type.
5. **Agent assignments** – Loads `agents.yaml`, extracts agent keys, and ensures each task references a known agent.

The script exits with a non-zero status on errors so CI or pre-commit hooks can block invalid config changes before they reach runtime.

## Workflow Tips

- **Schema-first changes** – Update `state.fields` before modifying tasks so the validator recognizes the new fields.
- **Agent lifecycle** – Add agents to `agents.yaml` first; then point tasks at them. Forgetting this order will trigger the agent validation error.
- **Iterative validation** – Run the validator early and often, especially before regenerating OpenAPI clients or kicking off the worker locally.
- **Frontend sync** – After changing `state.fields` or task reads/writes, confirm `/crew/crews/{id}/required-inputs` reflects the expected fields (see `docs/required_inputs.md`).

Keeping these files accurate ensures the dynamic flow builder can derive correct dependency graphs, required inputs, and agent wiring without additional backend changes.

