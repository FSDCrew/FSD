from __future__ import annotations

import uuid
from typing import Any, Dict, Optional, Tuple, Type, cast

from pydantic import BaseModel, Field, create_model

from app.models.models import FlowDependencyGraph
from app.services.flow.flow_utils import type_resolver


def build_flow_state_model(graph: FlowDependencyGraph) -> Type[BaseModel]:
    """Build the Pydantic FlowState model from the dependency graph's field specs."""

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
        python_type = type_resolver.resolve(field_type_str)

        default_value: Any = [] if type_resolver.is_list_type(field_type_str) else None

        field_definitions[field_name] = (Optional[python_type], default_value)

    FlowStateModel = create_model(
        "FlowState",
        __base__=BaseModel,
        **cast(Dict[str, Any], field_definitions),
    )
    return FlowStateModel


def extract_inner_type_from_list(field_type_str: str) -> str:
    """Extract the inner type from a list type definition."""

    if field_type_str.startswith("list[") or field_type_str.startswith("List["):
        return field_type_str[5:-1].strip()
    if field_type_str.endswith("[]"):
        return field_type_str[:-2].strip()
    return field_type_str

