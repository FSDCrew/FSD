from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Type, cast
from uuid import UUID

from crewai import Agent as CrewAIAgent, Crew, Process, Task as CrewAITask
from crewai.flow.flow import Flow, listen, start
from opentelemetry import baggage
from pydantic import BaseModel

from app.api.crud_client.models import TaskStatus
from app.models.models import CUSTOM_TYPE_REGISTRY, FlowDependencyGraph, TaskInfo
from app.services.flow.flow_utils import TaskStatusService
from app.services.flow.agent_factory import build_crewai_agents
from app.services.flow.dependency_graph import (
    build_flow_dependency_graph,
    infer_initial_inputs,
)
from app.services.flow.flow_utils import (
    interpolate_task_description,
    resolve_python_type,
)
from app.services.flow.guardrails import (
    llm_judge_guardrail,
    structured_output_guardrail,
)
from app.services.flow.state_builder import (
    build_flow_state_model,
    extract_inner_type_from_list,
)
from config import logger, settings, tasks_config


def _serialize_task_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize task inputs/outputs for storage in CrewRun.
    Converts Pydantic models to dicts and handles other complex types.
    """
    serialized = {}
    for k, v in data.items():
        if k == "crew_run_id":
            continue
        if isinstance(v, BaseModel):
            serialized[k] = v.model_dump(mode='json')
        elif isinstance(v, (str, int, float, bool, dict, list, type(None))):
            serialized[k] = v
        else:
            # Convert other types to string representation
            serialized[k] = str(v)
    return serialized


def build_task_step_function(
    task_record: TaskInfo,
    step_index: int,
    crew_agents: Dict[str, CrewAIAgent],
    graph: FlowDependencyGraph,
    task_status_service: TaskStatusService | None = None,
):
    """Build the method that will run a single step of the flow for one task."""

    task_key = task_record.key

    task_yaml = tasks_config.get(task_key, {})
    agent_key = task_yaml.get("agent")
    if not agent_key:
        raise ValueError(f"agent not found in tasks.yaml for task {task_key}")

    def step(self, previous_result: str):
        task_yaml = tasks_config.get(task_key, {})

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

        output_pydantic_model = _resolve_task_output_model(task_key, graph)

        guardrails_to_use = []
        if output_pydantic_model:
            guardrails_to_use.append(structured_output_guardrail(output_pydantic_model))
        guardrails_to_use.append(llm_judge_guardrail)

        crew_task_kwargs = {
            "name": task_yaml.get("name", "Task"),
            "description": formatted_description,
            "expected_output": task_yaml.get("expected_output", ""),
            "agent": agent,
            "guardrails": guardrails_to_use,
            "guardrail_max_retries": 3,
        }

        if output_pydantic_model:
            crew_task_kwargs["output_pydantic"] = output_pydantic_model

        crew_task = CrewAITask(**crew_task_kwargs)

        crew = Crew(
            agents=[agent],
            tasks=[crew_task],
            process=Process.sequential,
            verbose=True,
        )
        
        # Update task status to RUNNING before kickoff
        crew_run_id = getattr(self.state, "crew_run_id", None)
        # Create service instance if not provided (for multiprocessing compatibility)
        # Note: task_status_service is captured in closure, but may be None in worker process
        status_service = task_status_service
        if crew_run_id and not status_service:
            status_service = TaskStatusService()
        
        if crew_run_id and status_service:
            try:
                # Convert crew_run_id to UUID if it's a string
                if isinstance(crew_run_id, str):
                    crew_run_id_uuid = UUID(crew_run_id)
                else:
                    crew_run_id_uuid = crew_run_id
                
                # Prepare inputs dict (exclude crew_run_id from inputs for cleaner state)
                task_inputs = _serialize_task_data(step_inputs)
                
                status_service.update_task_status_in_worker(
                    crew_run_id=crew_run_id_uuid,
                    task_key=task_key,
                    status=TaskStatus.RUNNING,
                    task_inputs=task_inputs,
                    task_outputs={},
                    completed_at=None,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to update task {task_key} status to RUNNING: {e}",
                    exc_info=True,
                )
        
        try:
            result = crew.kickoff()
        except Exception as e:
            # Update task status to FAILED if kickoff fails
            # Create service instance if not provided (for multiprocessing compatibility)
            if crew_run_id and not status_service:
                status_service = TaskStatusService()
            
            if crew_run_id and status_service:
                try:
                    if isinstance(crew_run_id, str):
                        crew_run_id_uuid = UUID(crew_run_id)
                    else:
                        crew_run_id_uuid = crew_run_id
                    
                    # Serialize inputs
                    task_inputs = _serialize_task_data(step_inputs)
                    
                    status_service.update_task_status_in_worker(
                        crew_run_id=crew_run_id_uuid,
                        task_key=task_key,
                        status=TaskStatus.FAILED,
                        task_inputs=task_inputs,
                        task_outputs={"error": str(e)},
                        completed_at=datetime.now(timezone.utc),
                    )
                except Exception as update_error:
                    logger.error(
                        f"Failed to update task {task_key} status to FAILED: {update_error}",
                        exc_info=True,
                    )
            raise

        # Process write specs to collect outputs
        task_outputs: Dict[str, Any] = {}
        write_specs = graph.task_write_specs.get(task_key, [])
        for write_spec in write_specs:
            field_name = write_spec["field"]
            mode = write_spec.get("mode", "replace")

            pydantic_value = getattr(result, "pydantic", None)
            if pydantic_value is not None:
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
            
            # Serialize Pydantic models to dict for storage
            if isinstance(output_value, BaseModel):
                task_outputs[field_name] = output_value.model_dump(mode='json')
            else:
                task_outputs[field_name] = output_value
        
        # Update task status to COMPLETED after successful execution
        # Use the service instance we created earlier (or create if needed)
        if crew_run_id and not status_service:
            status_service = TaskStatusService()
        
        if crew_run_id and status_service:
            try:
                if isinstance(crew_run_id, str):
                    crew_run_id_uuid = UUID(crew_run_id)
                else:
                    crew_run_id_uuid = crew_run_id
                
                task_inputs = _serialize_task_data(step_inputs)
                
                status_service.update_task_status_in_worker(
                    crew_run_id=crew_run_id_uuid,
                    task_key=task_key,
                    status=TaskStatus.COMPLETED,
                    task_inputs=task_inputs,
                    task_outputs=task_outputs,
                    completed_at=datetime.now(timezone.utc),
                )
            except Exception as e:
                logger.warning(
                    f"Failed to update task {task_key} status to COMPLETED: {e}",
                    exc_info=True,
                )
        
        return f"{task_key} completed"

    return step


def _resolve_task_output_model(
    task_key: str, graph: FlowDependencyGraph
) -> Type[BaseModel] | None:
    write_specs = graph.task_write_specs.get(task_key, [])
    for write_spec in write_specs:
        field_name = write_spec["field"]
        field_spec = graph.state_field_specs.get(field_name)
        if not field_spec:
            continue

        field_type_str = field_spec.get("type", "string")
        inner_type_str = extract_inner_type_from_list(field_type_str)
        python_type = resolve_python_type(inner_type_str)

        if isinstance(python_type, type) and issubclass(python_type, BaseModel):
            return python_type

    return None


def build_dynamic_flow_class(
    FlowStateModel: Type[BaseModel],
    flow_tasks: List[TaskInfo],
    crew_agents: Dict[str, CrewAIAgent],
    graph: FlowDependencyGraph,
    task_status_service: TaskStatusService,
) -> Type[Flow]:
    """Build a concrete Flow subclass with one step per TaskRead."""

    def initialize_flow(self) -> str:
        inputs = cast(dict[str, Any], baggage.get_baggage("flow_inputs") or {})
        filtered_inputs = {k: v for k, v in inputs.items() if k != "id"}

        if filtered_inputs:
            for field_name, value in filtered_inputs.items():
                if hasattr(self.state, field_name):
                    field_spec = graph.state_field_specs.get(field_name)
                    if field_spec and isinstance(value, dict):
                        field_type_str = field_spec.get("type", "")
                        if field_type_str in CUSTOM_TYPE_REGISTRY:
                            model_class = CUSTOM_TYPE_REGISTRY[field_type_str]
                            if issubclass(model_class, BaseModel):
                                value = model_class.model_validate(value)
                    
                    try:
                        setattr(self.state, field_name, value)
                    except Exception as e:
                        logger.warning(
                            "Failed to set state attribute %s via setattr (%s); falling back to model_copy",
                            field_name,
                            e,
                        )
                        if hasattr(self.state, "model_copy"):
                            self.state = self.state.model_copy(
                                update={field_name: value}
                            )

        run_id = getattr(self.state, "run_id", None)
        if not run_id:
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            setattr(self.state, "run_id", run_id)

        active_task_keys = {t.key for t in flow_tasks}

        for field_name, field_spec in graph.state_field_specs.items():
            if field_spec.get("field_kind") != "context":
                continue

            readers = graph.field_readers.get(field_name, [])
            is_used_by_active_tasks = any(
                reader in active_task_keys for reader in readers
            )

            if is_used_by_active_tasks:
                value = getattr(self.state, field_name, None)
                if not value:
                    raise ValueError(f"{field_name} is required for the current tasks")

        return "Flow initialized"

    initialize_flow = start()(initialize_flow)

    step_functions: Dict[str, Any] = {}
    for index, task_record in enumerate(flow_tasks):
        fn = build_task_step_function(
            task_record,
            index,
            crew_agents,
            graph,
            task_status_service,
        )
        fn.__name__ = f"step_{task_record.key}"
        step_functions[task_record.key] = fn

    def __init__(self):
        Flow.__init__(self, tracing=settings.CREWAI_TRACING_ENABLED)
        self.tasks_config = tasks_config
        self.crew_agents = crew_agents
        self.dependency_graph = graph

    class_dict: Dict[str, Any] = {
        "__init__": __init__,
        "initialize_flow": initialize_flow,
    }

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


def create_flow_from_tasks(
    incoming_tasks: List[TaskInfo],
    task_status_service: TaskStatusService,
) -> Tuple[Type[BaseModel], Type[Flow], Dict[str, List[str]]]:
    """Build a dynamic FlowState model and Flow class from a list of TaskRead."""

    dependency_graph = build_flow_dependency_graph(incoming_tasks)
    required_inputs = infer_initial_inputs(dependency_graph, incoming_tasks)
    crew_agents = build_crewai_agents()

    FlowStateModel = build_flow_state_model(dependency_graph)
    FlowClass = build_dynamic_flow_class(
        FlowStateModel,
        incoming_tasks,
        crew_agents,
        dependency_graph,
        task_status_service,
    )

    return FlowStateModel, FlowClass, required_inputs
