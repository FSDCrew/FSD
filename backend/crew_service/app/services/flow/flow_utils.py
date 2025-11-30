from typing import Any, Dict, List, Type


from app.models.models import CUSTOM_TYPE_REGISTRY
from app.lib.tools.html_to_excel import html_to_excel_tool
from app.lib.tools.markdown_to_word import markdown_to_word_doc
from app.lib.tools.open_instagram_posts import open_instagram_posts
from app.lib.tools.search import open_pages, search_internet, search_instagram
from app.lib.tools.orshot_tool import orshot_render_tool
from app.lib.tools.image_generator import generate_image_tool
from app.lib.tools.imagen_generator import generate_imagen_tool


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
    "html_to_excel": html_to_excel_tool,
    "orshot_render_tool": orshot_render_tool,
    "generate_image_tool": generate_image_tool,
    "generate_imagen_tool": generate_imagen_tool,
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
            result = result.replace(placeholder, "NOT PROVIDED BY USER" if value is None else str(value))
    return result

