# Guardrail Pipeline for Dynamic Flows

Dynamic flows rely on guardrails to prevent malformed or off-spec agent outputs from polluting the shared state. Each CrewAI task that the flow builder emits carries a *chain* of guardrail functions defined in `app/services/flow/guardrails.py`. The chain is assembled inside `build_task_step_function` and always executes in the following order:

1. **Structured-output guardrail (`structured_output_guardrail`)** – Only attached when a task writes a custom Pydantic type. The guardrail checks that the task's `TaskOutput` reports `output_format == OutputFormat.PYDANTIC`, verifies a Pydantic payload is present, and re-validates it using the custom model from the state schema. The validated payload replaces `result.pydantic` so downstream writes can safely call `model_dump()`. Any schema violation short-circuits further guardrails and triggers a CrewAI retry.
2. **LLM judge (`llm_judge_guardrail`)** – Runs for every task. It sends the task's expected output and raw response to a dedicated judge LLM (configured in `llm_registry`), which responds using the `GuardrailResponseFormat` structured schema. The judge focuses on semantic alignment with the task's requirements and returns a descriptive reason if the answer is insufficient.

The helper `compose_guardrails` stitches the ordered list into a single callable compatible with CrewAI's `Task.guardrail` API while also exposing the list itself through `guardrails` for newer CrewAI releases. This allows us to add or remove guardrails per task simply by editing the list in `build_task_step_function` without touching CrewAI internals.

## Adding a New Guardrail

1. Implement a callable that accepts `TaskOutput` and returns `Tuple[bool, Any]`. Reuse the logging pattern in `structured_output_guardrail` to make failures actionable.
2. Append the callable to `task_guardrails` in `build_task_step_function`. Position matters—place guards that transform the `TaskOutput` (e.g., schema validation) before guards that depend on those transformations.
3. Update this doc with the new guardrail's intent so downstream consumers understand the validation pipeline.

## Why Two Separate LLMs?

- `llm_registry.general_llm` is used for agent reasoning and normal task execution.
- `guardrails.judge_llm` (a lightweight GPT-4.1-mini) stays isolated so judgment prompts and seeds do not interfere with task outputs. Because guardrail LLM calls are deterministic (seeded) and schema-bound, they provide stable feedback when tasks are retried.

This separation keeps guardrail logic deterministic and easier to audit while allowing the primary agent to run with its own configuration (temperature, tool usage, etc.).
