from __future__ import annotations

from typing import Dict, List

from app.models.models import FlowDependencyGraph, TaskInfo
from config import state_fields_config, tasks_config


def build_flow_dependency_graph(flow_tasks: List[TaskInfo]) -> FlowDependencyGraph:
    """Build the FlowDependencyGraph from task and state definitions."""

    graph = FlowDependencyGraph()

    for field_name, field_spec in state_fields_config.items():
        graph.add_state_field(field_name, field_spec)

    for task_record in flow_tasks:
        task_key = task_record.key
        
        for read_field in task_record.reads:
            read_spec = read_field.model_dump(mode='json')
            graph.register_task_read(task_key, read_spec)
        
        for write_field in task_record.writes:
            write_spec = write_field.model_dump(mode='json')
            graph.register_task_write(task_key, write_spec)

    return graph


def infer_initial_inputs(
    graph: FlowDependencyGraph,
    flow_tasks: List[TaskInfo],
) -> Dict[str, List[str]]:
    """Infer which state fields must be provided before the flow starts."""

    required_context_fields: List[str] = []
    required_data_fields: List[str] = []

    task_keys = {task.key for task in flow_tasks}

    for field_name, field_spec in graph.state_field_specs.items():
        if field_spec.get("field_kind") != "context":
            continue

        readers = graph.field_readers.get(field_name, [])
        if any(reader in task_keys for reader in readers):
            required_context_fields.append(field_name)

    for field_name, field_spec in graph.state_field_specs.items():
        if field_spec.get("field_kind") != "data":
            continue

        is_required_somewhere = False
        for task_key in task_keys:
            for read_spec in graph.task_read_specs.get(task_key, []):
                if read_spec["field"] != field_name:
                    continue
                cardinality = read_spec["cardinality"]
                if cardinality in {"required", "at_least_one"}:
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

