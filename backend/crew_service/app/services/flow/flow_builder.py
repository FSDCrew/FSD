import uuid
from datetime import datetime, timezone
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type, cast

from crewai import LLM, Crew, Process, TaskOutput
from crewai import Agent as CrewAIAgent
from crewai import Task as CrewAITask
from crewai.flow.flow import Flow, listen, start
from crewai.tasks.output_format import OutputFormat
from opentelemetry import baggage
from pydantic import BaseModel, Field, ValidationError, create_model

from app.api.crud_client.models.task_read import TaskRead
from app.models.models import FlowDependencyGraph
from app.services.flow.flow_utils import (
    interpolate_task_description,
    resolve_python_type,
    resolve_tools_for_agent,
)
from config import agents_config, logger, settings, state_fields_config, tasks_config

GuardrailCallable = Callable[[TaskOutput], Tuple[bool, Any]]

# ============================================================================
# LLMs
# ============================================================================

general_llm = LLM(
    model="openai/gpt-4.1-mini",
    # model="openai/gpt-4o-mini",
    temperature=0.7,
    # model="openai/gpt-5-mini",
    # model="openai/gpt-5-nano",
    # reasoning_effort="none",
    stop=None,
    seed=42,
)

function_calling_llm = LLM(
    model="openai/gpt-4o-mini",
)


# ============================================================================
# Guardrail definitions
# ============================================================================


class GuardrailResponseFormat(BaseModel):
    """Structured response format used by the judge LLM."""

    valid: bool
    reason: str


judge_llm = LLM(
    model="openai/gpt-4.1-mini",
    temperature=0.7,
    response_format=GuardrailResponseFormat,
    seed=42,
)


def structured_output_guardrail(
    result: TaskOutput, expected_model: Type[BaseModel]
) -> Tuple[bool, Any]:
    """Ensure the structured output aligns with the expected Pydantic model."""   
    if result.output_format != OutputFormat.PYDANTIC:
        reason = (
            f"Task expected structured output '{expected_model.__name__}' "
            f"but produced '{result.output_format.value}'."
        )
        logger.error(reason)
        return False, reason

    pydantic_value = result.pydantic
    
    # WORKAROUND: If output_format is PYDANTIC but pydantic is None,
    # try to parse result.raw as JSON and validate it
    if pydantic_value is None and result.output_format == OutputFormat.PYDANTIC:
        try:
            import json
            # Try to parse raw as JSON string
            if isinstance(result.raw, str):
                parsed_json = json.loads(result.raw)
                # Validate against expected model
                pydantic_value = expected_model.model_validate(parsed_json)
                # Set it on the result object so it's available downstream
                result.pydantic = pydantic_value
            else:
                # If raw is already a dict, try to validate directly
                if isinstance(result.raw, dict):
                    pydantic_value = expected_model.model_validate(result.raw)
                    result.pydantic = pydantic_value
                else:
                    reason = (
                        f"Task expected structured output '{expected_model.__name__}' "
                        f"but raw output is neither JSON string nor dict (type: {type(result.raw)})."
                    )
                    return False, reason
        except json.JSONDecodeError as e:
            reason = (
                f"Task expected structured output '{expected_model.__name__}' "
                f"but failed to parse raw output as JSON: {e}"
            )
            return False, reason
        except ValidationError as e:
            reason = (
                f"Task expected structured output '{expected_model.__name__}' "
                f"but parsed JSON failed validation: {e}"
            )
            return False, reason
        except Exception as e:
            reason = (
                f"Task expected structured output '{expected_model.__name__}' "
                f"but failed to parse/validate raw output: {e}"
            )
            return False, reason
    
    if pydantic_value is None:
        reason = (
            f"Task expected structured output '{expected_model.__name__}' "
            "but no Pydantic payload was returned."
        )
        logger.error(reason) 
        return False, reason

    if not isinstance(pydantic_value, BaseModel):
        reason = (
            f"Structured output for '{expected_model.__name__}' "
            "was not a Pydantic model."
        )
        logger.error(reason)
        logger.error(f"Pydantic value type: {type(pydantic_value)}")
        logger.error(f"Pydantic value: {pydantic_value}")
        return False, reason

    try:
        validated_payload = expected_model.model_validate(pydantic_value.model_dump())
        result.pydantic = validated_payload
    except ValidationError as exc:
        reason = f"Structured output failed {expected_model.__name__} validation: {exc}"
        logger.error(reason)
        return False, reason

    return True, result


def llm_judge_guardrail(result: TaskOutput) -> Tuple[bool, Any]:
    """
    Use a separate LLM as a judge to validate a task's output.

    Returns:
        (is_valid, output_format) as a tuple where output_format is a TaskOutputFormat
        instance containing the standardized task output.

    Note: Return type annotation must be Tuple[bool, Any] to satisfy CrewAI's validation,
    but the actual return value is a TaskOutputFormat instance.
    """
    try:
        evaluation_prompt = (
            "<task_expected_output>\n"
            f"{result.expected_output}\n"
            "</task_expected_output>\n\n"
            "<task_actual_output>\n"
            f"{result.raw}\n"
            "</task_actual_output>\n\n"
            "<your_task>\n"
            "Evaluate if the actual output meets the task requirements.\n"
            "Respond ONLY with JSON format.\n"
            "{\n"
            '    "valid": boolean,\n'
            '    "reason": string\n'
            "}\n"
            "</your_task>\n"
        )

        response = judge_llm.call([{"role": "user", "content": evaluation_prompt}])

        if isinstance(response, str):
            parsed = GuardrailResponseFormat.model_validate_json(response)
        elif isinstance(response, dict):
            parsed = GuardrailResponseFormat.model_validate(response)
        else:
            parsed = response
        if not parsed.valid:
            logger.error(f"Guardrail validation failed: {parsed.reason}")
            return parsed.valid, parsed.reason
        return parsed.valid, result

    except Exception as e:
        raise Exception(f"Evaluation error: {str(e)}")


def compose_guardrails(guardrails: Sequence[GuardrailCallable]) -> GuardrailCallable:
    """Chain multiple guardrails so each validates before the next runs."""

    def runner(result: TaskOutput) -> Tuple[bool, Any]:
        if not guardrails:
            return True, result.raw

        current_output = result
        last_result: Any = result
        for guard in guardrails:
            success, guard_result = guard(current_output)
            if not success:
                return False, guard_result

            last_result = guard_result
            if isinstance(guard_result, TaskOutput):
                current_output = guard_result

        return True, last_result

    return runner


# ============================================================================
# Agent creation
# ============================================================================


def build_crewai_agents() -> Dict[str, CrewAIAgent]:
    """
    Build CrewAI Agent instances from agent config in config.py.

    Returns:
        Mapping of agent_key -> CrewAI Agent.
    """
    agents: Dict[str, CrewAIAgent] = {}

    for agent_key, agent_config in agents_config.items():
        tools = resolve_tools_for_agent(agent_config)

        agents[agent_key] = CrewAIAgent(
            role=agent_config.get("role", ""),
            goal=agent_config.get("goal", ""),
            backstory=agent_config.get("backstory", ""),
            tools=tools or None,
            verbose=True,
            llm=general_llm,
        )

    return agents


# ============================================================================
# Flow dependency graph
# ============================================================================


def build_flow_dependency_graph(
    flow_tasks: List[TaskRead],
) -> FlowDependencyGraph:
    """
    Build the FlowDependencyGraph from task definitions in config.py and TaskRead list.
    """
    graph = FlowDependencyGraph()

    # State fields defined in config.py
    for field_name, field_spec in state_fields_config.items():
        graph.add_state_field(field_name, field_spec)

    # Reads/writes for only the tasks that are actually in this flow
    for task_record in flow_tasks:
        task_key = task_record.key
        if task_key not in tasks_config:
            continue

        task_config = tasks_config[task_key]

        for read_spec in task_config.get("reads", []):
            graph.register_task_read(task_key, read_spec)

        for write_spec in task_config.get("writes", []):
            graph.register_task_write(task_key, write_spec)

    return graph


def infer_initial_inputs(
    graph: FlowDependencyGraph,
    flow_tasks: List[TaskRead],
) -> Dict[str, List[str]]:
    """
    Infer which state fields must be provided by the user before the flow starts.

    Returns:
        {
            "context": [...],  # context fields read by any task
            "data":    [...],  # required data fields not written by any task
            "all":     [...],  # combined list
        }
    """
    required_context_fields: List[str] = []
    required_data_fields: List[str] = []

    task_keys = {task.key for task in flow_tasks}

    # Context fields: used by at least one selected task.
    for field_name, field_spec in graph.state_field_specs.items():
        if field_spec.get("field_kind") != "context":
            continue

        readers = graph.field_readers.get(field_name, [])
        if any(
            reader in task_keys for reader in readers
        ):  # true if any task reads this field
            required_context_fields.append(field_name)

    # Data fields: required by some task, but no selected task writes them.
    for field_name, field_spec in graph.state_field_specs.items():
        if field_spec.get("field_kind") != "data":
            continue

        is_required_somewhere = False
        for task_key in task_keys:
            for read_spec in graph.task_read_specs.get(task_key, []):
                if read_spec["field"] != field_name:
                    continue
                cardinality = read_spec["cardinality"]
                if cardinality == "required" or cardinality == "at_least_one":
                    is_required_somewhere = True
                    break
            if is_required_somewhere:
                break

        if not is_required_somewhere:
            continue

        writers = graph.field_writers.get(field_name, [])
        if not any(writer in task_keys for writer in writers):
            required_data_fields.append(field_name)

    return {
        "context": required_context_fields,
        "data": required_data_fields,
        "all": required_context_fields + required_data_fields,
    }


# ============================================================================
# Flow state model generation
# ============================================================================


def build_flow_state_model(graph: FlowDependencyGraph) -> Type[BaseModel]:
    """
    Build the Pydantic FlowState model from the dependency graph's field specs.

    Only includes fields that are read or written by tasks in the current flow.

    The resulting model is used as the state type for the dynamic Flow class.
    """
    field_definitions: Dict[str, Tuple[Any, Any]] = {}

    field_definitions["flow_id"] = (
        Optional[str],
        Field(default_factory=lambda: uuid.uuid4().hex[:8]),
    )
    field_definitions["run_id"] = (Optional[str], None)
    field_definitions["crew_run_id"] = (Optional[str], None)

    used_fields: set[str] = set()

    for read_specs in graph.task_read_specs.values():
        for read_spec in read_specs:
            used_fields.add(read_spec["field"])

    for write_specs in graph.task_write_specs.values():
        for write_spec in write_specs:
            used_fields.add(write_spec["field"])
        field_definitions["crew_run_id"] = (Optional[str], None)

    for field_name, field_spec in graph.state_field_specs.items():
        if field_name not in used_fields:
            continue

        field_type_str = field_spec.get("type", "string")
        python_type = resolve_python_type(field_type_str)

        if field_type_str.startswith("list[") or field_type_str.startswith("List["):
            default_value: Any = []
        else:
            default_value = None

        field_definitions[field_name] = (Optional[python_type], default_value)

    FlowStateModel = create_model(
        "FlowState",
        __base__=BaseModel,
        **cast(Dict[str, Any], field_definitions),
    )
    return FlowStateModel


# ============================================================================
# Dynamic Flow class generation
# ============================================================================


def extract_inner_type_from_list(field_type_str: str) -> str:
    """
    Extract inner type from list field types.

    Examples:
        list[ContentStrategy] -> ContentStrategy
        List[string] -> string
        Type[] -> Type

    Args:
        field_type_str: Field type string from YAML config

    Returns:
        Inner type string, or original string if not a list type
    """
    if field_type_str.startswith("list[") or field_type_str.startswith("List["):
        return field_type_str[5:-1].strip()
    elif field_type_str.endswith("[]"):
        return field_type_str[:-2].strip()
    return field_type_str


def build_task_step_function(
    task_record: TaskRead,
    step_index: int,
    crew_agents: Dict[str, CrewAIAgent],
    graph: FlowDependencyGraph,
):
    """
    Build the method that will run a single step of the flow for one task.

    The returned function is later decorated with @listen and attached
    to the dynamic Flow subclass.
    """
    task_key = task_record.key

    # Get agent_key from tasks.yaml config using the task's key
    task_yaml = tasks_config.get(task_key, {})
    agent_key = task_yaml.get("agent")
    if not agent_key:
        raise ValueError(f"agent not found in tasks.yaml for task {task_key}")

    def step(self, previous_result: str):
        # tasks_config is already the tasks dict (not the full YAML structure)
        task_yaml = tasks_config.get(task_key, {})

        # Collect inputs from state according to the declared reads
        step_inputs: Dict[str, Any] = {}
        read_specs = graph.task_read_specs.get(task_key, [])

        for read_spec in read_specs:
            field_name = read_spec["field"]
            cardinality = read_spec["cardinality"]

            field_spec = graph.state_field_specs.get(field_name)
            if field_spec:
                field_kind = field_spec.get("field_kind")
                if (
                    field_kind == "context"
                    and cardinality.strip().lower() == "optional"
                ):
                    raise ValueError(
                        f"Context field '{field_name}' cannot be optional for task {task_key}. "
                        "Context fields must be required inputs."
                    )

            value = getattr(self.state, field_name, None)

            if cardinality == "required" and value is None:
                raise ValueError(
                    f"{field_name} is required for task {task_key} but is not available in state"
                )

            if cardinality == "at_least_one":
                if not isinstance(value, list) or len(value) == 0:
                    raise ValueError(
                        f"{field_name} must contain at least one item for task {task_key}"
                    )

            step_inputs[field_name] = value

        crew_run_id = getattr(self.state, "crew_run_id", None)
        if crew_run_id is not None:
            step_inputs["crew_run_id"] = crew_run_id

        description_template = task_yaml.get("description", "")
        formatted_description = interpolate_task_description(
            description_template, step_inputs
        )

        agent = crew_agents.get(agent_key)
        if not agent:
            raise ValueError(f"Agent {agent_key} not found")

        # Determine output_pydantic from write specs
        # Extract inner type if field is a list (task outputs single object, not list)
        output_pydantic_model = None
        write_specs = graph.task_write_specs.get(task_key, [])
        for write_spec in write_specs:
            field_name = write_spec["field"]
            field_spec = graph.state_field_specs.get(field_name)
            if field_spec:
                field_type_str = field_spec.get("type", "string")

                # Extract inner type if it's a list (e.g., list[ContentStrategy] -> ContentStrategy)
                inner_type_str = extract_inner_type_from_list(field_type_str)

                # Resolve the Python type for the inner type
                python_type = resolve_python_type(inner_type_str)

                # Check if it's a Pydantic BaseModel
                if isinstance(python_type, type) and issubclass(python_type, BaseModel):
                    output_pydantic_model = python_type
                    break  # Use the first Pydantic model found

        task_guardrails: List[GuardrailCallable] = []
        if output_pydantic_model:
            task_guardrails.append(
                partial(
                    structured_output_guardrail,
                    expected_model=output_pydantic_model,
                )
            )
        task_guardrails.append(llm_judge_guardrail)

        crew_task_kwargs = {
            "name": task_yaml.get("name", "Task"),
            "description": formatted_description,
            "expected_output": task_yaml.get("expected_output", ""),
            "agent": agent,
            "guardrail": compose_guardrails(task_guardrails),
            "guardrail_max_retries": 3,
        }

        if output_pydantic_model:
            crew_task_kwargs["output_pydantic"] = output_pydantic_model

        output_file = task_yaml.get("output_file")
        if output_file:
            crew_task_kwargs["output_file"] = output_file

        crew_task = CrewAITask(**crew_task_kwargs)

        crew = Crew(
            agents=[agent],
            tasks=[crew_task],
            process=Process.sequential,
            verbose=True,
            function_calling_llm=function_calling_llm,
            output_log_file="crew_logs.json"
        )

        result = crew.kickoff(inputs=step_inputs)

        # Write outputs back into state according to the declared writes
        write_specs = graph.task_write_specs.get(task_key, [])
        for write_spec in write_specs:
            field_name = write_spec["field"]
            mode = write_spec.get("mode", "replace")

            pydantic_value = getattr(result, "pydantic", None)
            if pydantic_value is not None:
                if isinstance(pydantic_value, BaseModel):
                    output_value = pydantic_value.model_dump()
                else:
                    output_value = pydantic_value
            else:
                output_value = getattr(result, "raw", result)

            if mode == "replace":
                setattr(self.state, field_name, output_value)
            elif mode == "append":
                current_value = getattr(self.state, field_name, [])
                if not isinstance(current_value, list):
                    current_value = []
                current_value.append(output_value)
                setattr(self.state, field_name, current_value)

        return f"{task_key} completed"

    return step


def build_dynamic_flow_class(
    FlowStateModel: Type[BaseModel],
    flow_tasks: List[TaskRead],
    crew_agents: Dict[str, CrewAIAgent],
    graph: FlowDependencyGraph,
) -> Type[Flow]:
    """
    Build a concrete Flow subclass with one step per TaskRead.

    The resulting class is parameterized with the generated FlowState Pydantic
    model and wired with @start / @listen decorators based on task order.
    """

    def initialize_flow(self) -> str:
        """
        Entry point of the flow (marked with @start).
        """
        # 1. Get inputs from baggage (Standard Logic)
        inputs = cast(dict[str, Any], baggage.get_baggage("flow_inputs") or {})
        filtered_inputs = {k: v for k, v in inputs.items() if k != "id"}

        if filtered_inputs:
            for field_name, value in filtered_inputs.items():
                if hasattr(self.state, field_name):
                    try:
                        setattr(self.state, field_name, value)
                    except Exception:
                        if hasattr(self.state, "model_copy"):
                            self.state = self.state.model_copy(
                                update={field_name: value}
                            )

        # 2. Generate Run ID (Standard Logic)
        run_id = getattr(self.state, "run_id", None)
        if not run_id:
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            setattr(self.state, "run_id", run_id)

        # 3. SMART VALIDATION (The Fix)
        # Only validate context fields that are READ by the active tasks
        active_task_keys = {t.key for t in flow_tasks}

        for field_name, field_spec in graph.state_field_specs.items():
            # Only care about context fields
            if field_spec.get("field_kind") != "context":
                continue

            # Check if this field is actually read by any task in this flow
            readers = graph.field_readers.get(field_name, [])
            is_used_by_active_tasks = any(
                reader in active_task_keys for reader in readers
            )

            if is_used_by_active_tasks:
                value = getattr(self.state, field_name, None)
                if not value:
                    raise ValueError(f"{field_name} is required for the current tasks")

        return "Flow initialized"

    # Mark as the starting node for CrewAI Flow
    initialize_flow = start()(initialize_flow)

    # Build all step functions first so we can wire their dependencies
    step_functions: Dict[str, Any] = {}
    for index, task_record in enumerate(flow_tasks):
        fn = build_task_step_function(
            task_record,
            index,
            crew_agents,
            graph,
        )
        fn.__name__ = f"step_{task_record.key}"
        step_functions[task_record.key] = fn

    def __init__(self):
        # Flow.__init__ sets up Flow.state with the generic model
        Flow.__init__(self, tracing=settings.CREWAI_TRACING_ENABLED)
        self.tasks_config = tasks_config
        self.agents_config = agents_config
        self.crew_agents = crew_agents
        self.dependency_graph = graph

    class_dict: Dict[str, Any] = {
        "__init__": __init__,
        "initialize_flow": initialize_flow,
    }

    # Wire each step with @listen so that steps trigger sequentially
    for index, task_record in enumerate(flow_tasks):
        base_step_fn = step_functions[task_record.key]

        if index == 0:
            decorated_step = listen("initialize_flow")(base_step_fn)
        else:
            previous_task_key = flow_tasks[index - 1].key
            previous_method_name = f"step_{previous_task_key}"
            decorated_step = listen(previous_method_name)(base_step_fn)

        method_name = f"step_{task_record.key}"
        class_dict[method_name] = decorated_step

    DynamicFlow = type(
        "DynamicFlow",
        (Flow[FlowStateModel],),
        class_dict,
    )

    return DynamicFlow


# ============================================================================
# Public factory: build FlowState + Flow from CrudTask list
# ============================================================================


def create_flow_from_tasks(
    incoming_tasks: List[TaskRead],
) -> Tuple[Type[BaseModel], Type[Flow], Dict[str, List[str]]]:
    """
    Build a dynamic FlowState model and Flow class from a list of TaskRead.

    Agent and task configs are retrieved from config.py.

    Args:
        incoming_tasks:
            Ordered list of logical tasks to include in this flow instance.

    Returns:
        (FlowStateModel, FlowClass, initial_input_spec)
    """
    dependency_graph = build_flow_dependency_graph(incoming_tasks)
    required_inputs = infer_initial_inputs(dependency_graph, incoming_tasks)
    crew_agents = build_crewai_agents()

    FlowStateModel = build_flow_state_model(dependency_graph)
    FlowClass = build_dynamic_flow_class(
        FlowStateModel,
        incoming_tasks,
        crew_agents,
        dependency_graph,
    )

    return FlowStateModel, FlowClass, required_inputs
