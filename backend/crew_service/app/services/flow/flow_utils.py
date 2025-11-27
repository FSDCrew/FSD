from pathlib import Path
from typing import Any, Dict, List, Type
from datetime import datetime

import yaml

from app.models.models import CUSTOM_TYPE_REGISTRY
from app.lib.tools.html_table_to_excel import html_table_to_excel_tool
from app.lib.tools.dates import calculate_num_weeks
from app.lib.tools.markdown_to_word import markdown_to_word_doc
from app.lib.tools.open_instagram_posts import open_instagram_posts
from app.lib.tools.search import open_pages, search_internet, search_instagram


# ============================================================================
# Tool mapping
# ============================================================================

TOOL_MAP = {
    "search_internet": search_internet,
    "search_instagram": search_instagram,
    "open_pages": open_pages,
    "open_instagram_post_page": open_instagram_posts,
    "open_instagram_posts": open_instagram_posts,
    "markdown_to_word_doc": markdown_to_word_doc,
    "html_table_to_excel": html_table_to_excel_tool,
    "calculate_num_weeks": calculate_num_weeks,
}

# ============================================================================
# Tool resolution
# ============================================================================

def resolve_tools_for_agent(agent_config: Dict[str, Any]) -> List[Any]:
    """
    Convert the tool names in an agent config into actual tool callables.

    Unknown tool names are ignored.
    """
    resolved_tools: List[Any] = []
    configured_tools = agent_config.get("tools", [])

    if not isinstance(configured_tools, List):
        return resolved_tools

    for tool_name in configured_tools:
        if isinstance(tool_name, str) and tool_name in TOOL_MAP:
            tool_obj = TOOL_MAP[tool_name]
            if tool_obj not in resolved_tools:
                resolved_tools.append(tool_obj)

    return resolved_tools


# ============================================================================
# Type resolution
# ============================================================================

def resolve_python_type(field_type: str) -> Type:
    """
    Map a YAML type string into a Python type usable in a Pydantic model.
    
    Supports:
    - Simple types: "string", "int", "float", "bool", "date"
    - Lists: "list[str]", "list[int]", "list[MarketingResearch]", etc.
    - Custom types: "MarketingResearch", "ContentStrategy", "SocialMediaSchedule" (registered models)
    - Unknown custom types: "DiscoveryDataset", etc. (treated as Dict[str, Any])
    """
    base_type_mapping: Dict[str, Type] = {
        "string": str,
        "date": str,  # stored as ISO string
        "int": int,
        "float": float,
        "bool": bool,
    }

    if field_type.startswith("list[") or field_type.startswith("List["):
        # Extract inner type from list[InnerType] or List[InnerType]
        inner_type_str = field_type[5:-1].strip()
        inner_type = resolve_python_type(inner_type_str)
        
        return List[inner_type]
    
    # Handle array syntax: Type[] (e.g., "DiscoveryDataset[]")
    if field_type.endswith("[]"):
        inner_type_str = field_type[:-2].strip()
        inner_type = resolve_python_type(inner_type_str)
        return List[inner_type]

    if field_type.lower() in base_type_mapping:
        return base_type_mapping[field_type.lower()]
    
    if field_type in CUSTOM_TYPE_REGISTRY:
        return CUSTOM_TYPE_REGISTRY[field_type]
    
    # Unknown custom types (like DiscoveryDataset) are treated as Dict[str, Any]
    return Dict[str, Any]


# ============================================================================
# String interpolation
# ============================================================================

def interpolate_task_description(
    description_template: str,
    state_values: Dict[str, Any],
) -> str:
    """
    Fill {field_name} placeholders in the task description using state values.
    """
    result = description_template
    for field_name, value in state_values.items():
        placeholder = f"{{{field_name}}}"
        if placeholder in result:
            result = result.replace(placeholder, "" if value is None else str(value))
    return result


# ============================================================================
# Value type validation
# ============================================================================

def validate_value_type(value: Any, expected_type_str: str, field_name: str) -> None:
    """
    Validate that a value matches the expected type string.
    
    Args:
        value: The value to validate
        expected_type_str: Type string from YAML (e.g., "string", "list[DiscoveryDataset]")
        field_name: Name of the field (for error messages)
        
    Raises:
        ValueError: If the value doesn't match the expected type
    """
    if expected_type_str.startswith("list[") or expected_type_str.startswith("List["):
        if not isinstance(value, list):
            raise ValueError(
                f"Expected list type for field '{field_name}', but got {type(value).__name__}"
            )
        
        inner_type_str = expected_type_str[5:-1].strip()
        
        for i, item in enumerate(value):
            try:
                validate_value_type(item, inner_type_str, f"{field_name}[{i}]")
            except ValueError as e:
                raise ValueError(
                    f"Invalid item at index {i} in list field '{field_name}': {str(e)}"
                ) from e
        return
    
    if expected_type_str.endswith("[]"):
        if not isinstance(value, list):
            raise ValueError(
                f"Expected list type for field '{field_name}', but got {type(value).__name__}"
            )
        
        inner_type_str = expected_type_str[:-2].strip()
        for i, item in enumerate(value):
            try:
                validate_value_type(item, inner_type_str, f"{field_name}[{i}]")
            except ValueError as e:
                raise ValueError(
                    f"Invalid item at index {i} in list field '{field_name}': {str(e)}"
                ) from e
        return
    
    expected_python_type = resolve_python_type(expected_type_str)
    
    if expected_type_str.lower() == "date":
        if not isinstance(value, str):
            raise ValueError(
                f"Expected string (ISO date format) for field '{field_name}', "
                f"but got {type(value).__name__}"
            )
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid date format for field '{field_name}'. "
                f"Expected ISO format (e.g., '2024-01-01' or '2024-01-01T00:00:00Z')"
            )
        return
    
    if expected_type_str in CUSTOM_TYPE_REGISTRY:
        model_class = CUSTOM_TYPE_REGISTRY[expected_type_str]
        if isinstance(value, dict):
            try:
                model_class.model_validate(value)
            except Exception as e:
                raise ValueError(
                    f"Invalid {expected_type_str} for field '{field_name}': {str(e)}"
                ) from e
        elif isinstance(value, model_class):
            pass
        else:
            raise ValueError(
                f"Expected {expected_type_str} (dict or {expected_type_str} instance) "
                f"for field '{field_name}', but got {type(value).__name__}"
            )
        return
    
    # Handle Dict[str, Any] (for unknown custom types like DiscoveryDataset)
    if expected_python_type == dict:
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

