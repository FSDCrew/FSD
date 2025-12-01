from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_serializer
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Type


class CrewRun(BaseModel):
    id: UUID
    crew_id: UUID
    
    model_config = ConfigDict(extra="ignore")


class CrewRunCreateRequest(BaseModel):
    crew_id: UUID
    inputs: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="ignore")
    
    
class TaskInfo(BaseModel):
    """Task information exposed to the frontend."""
    key: str
    name: str
    task_description: str



# ============================================================================
# Flow Models and Types
# ============================================================================

class MarketingResearch(BaseModel):
    """
    Represents marketing research data, typically stored as markdown content.
    
    Contains structured research report with sections like:
    - Executive summary
    - Competitive landscape
    - Emerging trends
    - Successful examples/references
    - Recommendations
    - References
    """
    content: str = Field(..., description="Markdown content of the marketing research report")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata about the research")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Marketing Research Report\n\n## Executive Summary\n...",
                "metadata": {"source": "research_synthesis_report", "generated_at": "2024-01-01"}
            }
        }


class ContentStrategy(BaseModel):
    """
    Represents a content strategy plan, typically stored as markdown content.
    
    Contains structured content plan with:
    - Executive summary
    - Calendar overview with theme/concept, objective, and posting cadence
    - Phase-based strategy (per month, week, or day)
    """
    content: str = Field(..., description="Markdown content of the content strategy")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata about the strategy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Content Strategy\n\n## Executive Summary\n...",
                "metadata": {"phase": "monthly", "generated_at": "2024-01-01"}
            }
        }


class SocialMediaSchedule(BaseModel):
    """
    Represents a social media posting schedule, typically stored as markdown or structured data.
    
    Contains a detailed schedule with:
    - Post dates and times
    - Content descriptions
    - Content types (posts, stories, reels)
    - Objectives and key messages
    """
    content: str = Field(..., description="Markdown or structured content of the social media schedule")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata about the schedule")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Social Media Schedule\n\n## Week 1\n...",
                "metadata": {"format": "markdown", "generated_at": "2024-01-01"}
            }
        }

class AllowedTemplateId(IntEnum):
    """
    Registry of supported Orshot Templates.
    The frontend uses this to render a dropdown.
    """
    IG_POST = 1201
    BG_POST = 1909

class OrshotDataType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    BACKGROUND = "BACKGROUND"

class OrshotSchemaField(BaseModel):
    """
    Represents a single configurable field in an Orshot Template.
    User inputs a list of these objects to define the 'rules' for the template.
    """
    field: str = Field(..., description="The exact parameter key to modify in the Orshot template (e.g., 'headline', 'background_image')")
    dataType: OrshotDataType = Field(..., description="The data type of this field: 'TEXT', 'IMAGE' or 'BACKGROUND'")
    description: str = Field(..., description="Contextual description of the field (e.g., 'Main title, max 20 chars', 'Product shot in portrait mode')")

    model_config = ConfigDict(use_enum_values=True)

# Type registry for custom types
CUSTOM_TYPE_REGISTRY: Dict[str, Type[BaseModel] | Type[IntEnum] | Type[Enum]] = {
    "MarketingResearch": MarketingResearch,
    "ContentStrategy": ContentStrategy,
    "SocialMediaSchedule": SocialMediaSchedule,
    "OrshotSchemaField": OrshotSchemaField,
    "AllowedTemplateId": AllowedTemplateId,
    "OrshotDataType": OrshotDataType,
}


def get_custom_type_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Generate JSON schemas for all custom types in CUSTOM_TYPE_REGISTRY.
    
    Returns:
        Dictionary mapping type names to their JSON schemas
    """
    schemas = {}
    for type_name, type_class in CUSTOM_TYPE_REGISTRY.items():
        if issubclass(type_class, BaseModel):
            try:
                schemas[type_name] = type_class.model_json_schema()
            except Exception:
                schemas[type_name] = {}
        elif issubclass(type_class, (Enum, IntEnum)):
            schemas[type_name] = {
                "type": "enum",
                "values": [member.value for member in type_class]
            }
    return schemas


# ============================================================================
# Required Inputs Response Models
# ============================================================================

class FieldTypeInfo(BaseModel):
    """
    Represents type information for a field, enabling frontend form rendering.
    
    Handles:
    - Basic types (string, int, float, bool, date)
    - Custom models (MarketingResearch, ContentStrategy, etc.)
    - Enums (AllowedTemplateId, OrshotDataType)
    - Lists of any type (list[string], list[OrshotSchemaField], etc.)
    - Nested types (custom models containing enums)
    """
    type: str = Field(..., description="Type name (e.g., 'string', 'MarketingResearch', 'AllowedTemplateId')")
    is_list: bool = Field(default=False, description="Whether this is a list type")
    inner_type: Optional[str] = Field(default=None, description="Inner type for lists (e.g., 'string' for list[string])")
    is_enum: bool = Field(default=False, description="Whether this is an enum type")
    enum_values: Optional[List[Any]] = Field(default=None, description="List of enum values (for enums)")
    is_custom_model: bool = Field(default=False, description="Whether this is a custom Pydantic model")
    model_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON schema for custom models (for nested form rendering)")
    
    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Exclude None values for related fields, but always include boolean flags."""
        data: Dict[str, Any] = {
            "type": self.type,
            "is_list": self.is_list,
            "is_enum": self.is_enum,
            "is_custom_model": self.is_custom_model,
        }
        
        # Only include inner_type if is_list is True and it's not None
        if self.is_list and self.inner_type is not None:
            data["inner_type"] = self.inner_type
        
        # Only include enum_values if is_enum is True and it's not None
        if self.is_enum and self.enum_values is not None:
            data["enum_values"] = self.enum_values
        
        # Only include model_schema if is_custom_model is True and it's not None
        if self.is_custom_model and self.model_schema is not None:
            data["model_schema"] = self.model_schema
        
        return data


class RequiredInputField(BaseModel):
    """Represents a single required input field."""
    field_name: str = Field(..., description="Name of the field")
    type_info: FieldTypeInfo = Field(..., description="Type information for this field")
    field_kind: str = Field(..., description="Field kind: 'context' or 'data'")
    required: bool = Field(default=True, description="Whether this field is required (cannot be left blank)")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text for the input field")


class RequiredInputsResponse(BaseModel):
    """Response model for required inputs endpoint."""
    fields: List[RequiredInputField] = Field(..., description="List of required input fields")


class CustomTypesResponse(BaseModel):
    """
    Response model exposing all custom types for OpenAPI schema generation.
    
    This model is used solely to ensure custom types appear in the OpenAPI schema
    so that client generation tools (e.g., openapi-ts) can generate TypeScript types.
    All fields are optional and default to None since this is only for schema exposure.
    """
    marketing_research: Optional[MarketingResearch] = Field(
        default=None,
        description="MarketingResearch type schema reference"
    )
    content_strategy: Optional[ContentStrategy] = Field(
        default=None,
        description="ContentStrategy type schema reference"
    )
    social_media_schedule: Optional[SocialMediaSchedule] = Field(
        default=None,
        description="SocialMediaSchedule type schema reference"
    )
    orshot_schema_field: Optional[OrshotSchemaField] = Field(
        default=None,
        description="OrshotSchemaField type schema reference"
    )
    allowed_template_id: Optional[AllowedTemplateId] = Field(
        default=None,
        description="AllowedTemplateId enum schema reference"
    )
    orshot_data_type: Optional[OrshotDataType] = Field(
        default=None,
        description="OrshotDataType enum schema reference"
    )


class FlowDependencyGraph:
    """
    In-memory graph describing how tasks read and write flow state.

    Used to:
      * infer which input fields the user must provide
      * build the FlowState model
      * drive validation logic for each task step
    """

    def __init__(self):
        # field_name -> list of task keys that write to this field
        self.field_writers: Dict[str, List[str]] = {}

        # field_name -> list of task keys that read from this field
        self.field_readers: Dict[str, List[str]] = {}

        # task_key -> list of read specs from YAML (each spec is a small dict)
        self.task_read_specs: Dict[str, List[Dict[str, Any]]] = {}

        # task_key -> list of write specs from YAML (each spec is a small dict)
        self.task_write_specs: Dict[str, List[Dict[str, Any]]] = {}

        # field_name -> YAML field definition (type, field_kind, etc.)
        self.state_field_specs: Dict[str, Dict[str, Any]] = {}

    def add_state_field(self, field_name: str, field_spec: Dict[str, Any]) -> None:
        """Register a field from the state schema."""
        self.state_field_specs[field_name] = field_spec

        self.field_writers.setdefault(field_name, [])
        self.field_readers.setdefault(field_name, [])

    def register_task_read(self, task_key: str, read_spec: Dict[str, Any]) -> None:
        """Record that a task reads a particular field."""
        field_name = read_spec["field"]
        
        field_spec = self.state_field_specs.get(field_name)
        if field_spec:
            field_kind = field_spec.get("field_kind")
            cardinality = read_spec.get("cardinality", "").strip().lower()
            
            if field_kind == "context" and cardinality == "optional":
                raise ValueError(
                    f"Task '{task_key}' cannot mark context field '{field_name}' as optional. "
                    "Context fields must be required inputs."
                )

        self.task_read_specs.setdefault(task_key, []).append(read_spec)
        self.field_readers.setdefault(field_name, []).append(task_key)

    def register_task_write(self, task_key: str, write_spec: Dict[str, Any]) -> None:
        """Record that a task writes to a particular field."""
        field_name = write_spec["field"]

        self.task_write_specs.setdefault(task_key, []).append(write_spec)
        self.field_writers.setdefault(field_name, []).append(task_key)
