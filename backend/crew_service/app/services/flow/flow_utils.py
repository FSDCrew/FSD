from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Type

from pydantic import BaseModel

from app.lib.tools.dates import calculate_num_weeks
from app.lib.tools.html_table_to_excel import html_table_to_excel_tool
from app.lib.tools.image_generator import generate_image_tool
from app.lib.tools.imagen_generator import generate_imagen_tool
from app.lib.tools.markdown_to_word import markdown_to_word_doc
from app.lib.tools.math import verify_sum_equals_expected
from app.lib.tools.open_instagram_posts import open_instagram_posts
from app.lib.tools.orshot_tool import orshot_render_tool
from app.lib.tools.search import open_pages, search_internet, search_instagram
from app.lib.tools.social_media_schedule import generate_social_media_schedule_tool
from app.lib.tools.generate_copywriting import generate_copywriting_tool
from app.models.models import CUSTOM_TYPE_REGISTRY


class FlowToolResolver:
    """Resolve tool names from config into callable implementations."""

    def __init__(self, tool_map: Dict[str, Any]):
        self._tool_map = tool_map

    def resolve(self, agent_config: Dict[str, Any]) -> List[Any]:
        configured_tools = agent_config.get("tools", [])
        if not isinstance(configured_tools, List):
            return []

        resolved_tools: List[Any] = []
        for tool_name in configured_tools:
            if isinstance(tool_name, str) and tool_name in self._tool_map:
                tool_obj = self._tool_map[tool_name]
                if tool_obj not in resolved_tools:
                    resolved_tools.append(tool_obj)
        return resolved_tools


class FlowTypeResolver:
    """Convert YAML field types into Python types."""

    def __init__(self, base_types: Dict[str, Type], custom_types: Dict[str, Type]):
        self._base_types = base_types
        self._custom_types = custom_types

    def resolve(self, field_type: str) -> Type:
        if self.is_generic_list(field_type):
            inner_type_str = field_type[5:-1].strip()
            inner_type = self.resolve(inner_type_str)
            return List[inner_type]

        if field_type.endswith("[]"):
            inner_type_str = field_type[:-2].strip()
            inner_type = self.resolve(inner_type_str)
            return List[inner_type]

        lower_type = field_type.lower()
        if lower_type in self._base_types:
            return self._base_types[lower_type]

        if field_type in self._custom_types:
            return self._custom_types[field_type]

        return Dict[str, Any]

    def is_list_type(self, field_type: str) -> bool:
        return self.is_generic_list(field_type) or field_type.endswith("[]")

    @staticmethod
    def is_generic_list(field_type: str) -> bool:
        return field_type.startswith("list[") or field_type.startswith("List[")


class FlowValueValidator:
    """Validate runtime values against expected flow schema types."""

    def __init__(self, type_resolver: FlowTypeResolver):
        self._type_resolver = type_resolver

    def validate(self, value: Any, expected_type_str: str, field_name: str) -> None:
        if self._type_resolver.is_generic_list(expected_type_str):
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected list type for field '{field_name}', but got {type(value).__name__}"
                )
            inner_type_str = expected_type_str[5:-1].strip()
            for i, item in enumerate(value):
                self.validate(item, inner_type_str, f"{field_name}[{i}]")
            return

        if expected_type_str.endswith("[]"):
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected list type for field '{field_name}', but got {type(value).__name__}"
                )
            inner_type_str = expected_type_str[:-2].strip()
            for i, item in enumerate(value):
                self.validate(item, inner_type_str, f"{field_name}[{i}]")
            return

        expected_python_type = self._type_resolver.resolve(expected_type_str)

        if expected_type_str.lower() == "date":
            self._validate_date(value, field_name)
            return

        if expected_type_str in CUSTOM_TYPE_REGISTRY:
            self._validate_custom_type(value, expected_type_str, field_name)
            return

        if expected_python_type is dict:
            if not isinstance(value, dict):
                raise ValueError(
                    f"Expected dict type for field '{field_name}', but got {type(value).__name__}"
                )
            return

        if not isinstance(value, expected_python_type):
            raise ValueError(
                f"Expected {expected_type_str} ({expected_python_type.__name__}) "
                f"for field '{field_name}', but got {type(value).__name__}"
            )

    def _validate_date(self, value: Any, field_name: str) -> None:
        if not isinstance(value, str):
            raise ValueError(
                f"Expected string (ISO date format) for field '{field_name}', but got {type(value).__name__}"
            )
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid date format for field '{field_name}'. "
                "Expected ISO format (e.g., '2024-01-01' or '2024-01-01T00:00:00Z')"
            )

    def _validate_custom_type(
        self, value: Any, expected_type_str: str, field_name: str
    ) -> None:
        model_class = CUSTOM_TYPE_REGISTRY[expected_type_str]

        if isinstance(value, model_class):
            return

        if isinstance(value, dict):
            if issubclass(model_class, BaseModel):
                model_class.model_validate(value)
                return
            if issubclass(model_class, IntEnum):
                enum_value = value.get("value", value)
                model_class(enum_value)
                return
            raise ValueError(
                f"Unsupported custom type {expected_type_str} for field '{field_name}'"
            )

        if issubclass(model_class, IntEnum):
            if isinstance(value, int):
                model_class(value)
                return
            raise ValueError(
                f"Expected {expected_type_str} (int, dict, or {expected_type_str} instance) "
                f"for field '{field_name}', but got {type(value).__name__}"
            )

        if issubclass(model_class, BaseModel):
            raise ValueError(
                f"Expected {expected_type_str} (dict or {expected_type_str} instance) "
                f"for field '{field_name}', but got {type(value).__name__}"
            )

        raise ValueError(
            f"Unsupported custom type {expected_type_str} for field '{field_name}'"
        )


class TaskDescriptionInterpolator:
    """Formats task descriptions using flow state values."""

    @staticmethod
    def interpolate(description_template: str, state_values: Dict[str, Any]) -> str:
        result = description_template
        for field_name, value in state_values.items():
            placeholder = f"{{{field_name}}}"
            if placeholder in result:
                if value is None:
                    replacement = "NOT PROVIDED BY USER"
                elif isinstance(value, BaseModel):
                    replacement = value.model_dump_json(indent=2)
                else:
                    replacement = str(value)
                result = result.replace(placeholder, replacement)
        return result


TOOL_MAP = {
    "calculate_num_weeks": calculate_num_weeks,
    "generate_image": generate_image_tool,
    "generate_imagen": generate_imagen_tool,
    "generate_social_media_schedule": generate_social_media_schedule_tool,
    "generate_copywriting_for_item": generate_copywriting_tool,
    # "generate_copywriting_for_batch": generate_batch_copywriting_tool,
    "html_table_to_excel": html_table_to_excel_tool,
    "markdown_to_word_doc": markdown_to_word_doc,
    "open_instagram_posts": open_instagram_posts,
    "open_pages": open_pages,
    "orshot_render": orshot_render_tool,
    "search_instagram": search_instagram,
    "search_internet": search_internet,
    "verify_sum_equals_expected": verify_sum_equals_expected,
}

BASE_TYPE_MAPPING: Dict[str, Type] = {
    "string": str,
    "date": str,
    "int": int,
    "float": float,
    "bool": bool,
}


tool_resolver = FlowToolResolver(TOOL_MAP)
type_resolver = FlowTypeResolver(BASE_TYPE_MAPPING, CUSTOM_TYPE_REGISTRY)
value_validator = FlowValueValidator(type_resolver)
interpolator = TaskDescriptionInterpolator()


def resolve_tools_for_agent(agent_config: Dict[str, Any]) -> List[Any]:
    return tool_resolver.resolve(agent_config)


def resolve_python_type(field_type: str) -> Type:
    return type_resolver.resolve(field_type)


def validate_value_type(value: Any, expected_type_str: str, field_name: str) -> None:
    value_validator.validate(value, expected_type_str, field_name)


def interpolate_task_description(
    description_template: str,
    state_values: Dict[str, Any],
) -> str:
    return interpolator.interpolate(description_template, state_values)
