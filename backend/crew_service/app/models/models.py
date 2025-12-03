from enum import Enum, IntEnum
from typing import Any, Dict, List, Literal, Optional, Type
import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_serializer, field_validator


class CrewRun(BaseModel):
    id: UUID
    crew_id: UUID

    model_config = ConfigDict(extra="ignore")


class CrewRunCreateRequest(BaseModel):
    crew_id: UUID
    inputs: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


class CrewRunRetryRequest(BaseModel):
    feedback: str
    retry_from_task_key: str


class TaskFieldRead(BaseModel):
    """Describes a state field that a task consumes."""

    field: str
    cardinality: str


class TaskFieldWrite(BaseModel):
    """Describes a state field that a task produces."""

    field: str
    mode: str


class TaskInfo(BaseModel):
    """Full task definition surfaced via /tasks/pre-defined."""

    key: str
    name: str
    task_description: str
    description: str
    expected_output: str
    agent: str
    reads: List[TaskFieldRead]
    writes: List[TaskFieldWrite]

    model_config = ConfigDict(extra="allow")

# ============================================================================
# Flow Models and Types
# ============================================================================


class MarketingResearchReport(BaseModel):
    """
    Structured representation of the marketing‑research markdown report.

    The task’s `expected_output` asks for a markdown document that contains:

    • Executive summary
    • Competitive landscape
    • Emerging trends
    • Successful examples / references
    • Recommendations
    • References

    Each section is stored as a separate string so the workflow can either:
      – render the whole markdown (`report`) directly, or
      – access individual sections programmatically (e.g. for UI rendering, analytics, etc.).

    `metadata` can be used for generation timestamps, model version, or any other
    bookkeeping the system wants to keep.
    """

    executive_summary: str = Field(..., description="High‑level overview of findings.")
    competitive_landscape: str = Field(
        ..., description="Analysis of competitors identified."
    )
    emerging_trends: str = Field(
        ..., description="Key trends tied to the campaign theme."
    )
    successful_examples: str = Field(
        ..., description="Relevant Instagram examples with usernames & URLs."
    )
    recommendations: str = Field(
        ..., description="Actionable advice for the upcoming campaign."
    )
    references: str = Field(
        ..., description="Citations of web‑search & Instagram sources."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "executive_summary": "The market is shifting toward ...",
                "competitive_landscape": "Top 2‑3 competitors are ...",
                "emerging_trends": "Short‑form video, user‑generated content, ...",
                "successful_examples": "- @brand1 https://instagram.com/p/ABC123\\n- @brand2 https://instagram.com/p/DEF456",
                "recommendations": "Post 3‑4 reels per week, leverage carousel posts ...",
                "references": "1. https://example.com/competitor‑analysis\\n2. https://instagram.com/hashtag/…",
            }
        }


class PostType(str, Enum):
    """Enum for Instagram post types."""
    POST = "POST"
    STORY = "STORY"


class StrategyPhase(BaseModel):
    """
    Non-date-specific strategic phase definition.
    The scheduler will later map these phases to calendar weeks.
    """

    name: str = Field(
        ..., description="Phase name, e.g., 'Awareness', 'Engagement', etc."
    )
    duration_in_weeks: int = Field(
        ..., description="How long the phase should run, without calendar dates."
    )
    themes: List[str] = Field(..., description="Core themes emphasized in this phase.")
    objectives: List[str] = Field(
        ..., description="Strategic objectives for the phase."
    )
    recommended_content_types: List[PostType] = Field(
        ...,
        description="Content formats recommended here (e.g., POST, STORY).",
    )
    posting_cadence: Dict[str, int] = Field(
        ...,
        description="Cadence expressed as counts, e.g., {'posts_per_week': 3, 'stories_per_week': 2}",
    )
    messaging_guidelines: Optional[List[str]] = Field(
        default=None, description="Tone & message guidelines specific to this phase."
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "additionalProperties": False
        }
    )


class ContentStrategy(BaseModel):
    """
    Complete content strategy output.
    
    - `content`: Human-readable markdown summary
    - `global_settings`: Tone, voice, brand alignment, audience considerations
    - `phases`: Structured, agent-parsable strategy blocks (no dates!)
    - `metadata`: Version, timestamps, etc.
    """
    content: str = Field(
        ...,
        description="Full content strategy rendered as markdown"
    )

    global_settings: Optional[Dict[str, Any]] = Field(
        ...,
        description="High-level settings: tone, voice, brand alignment, messaging principles, content pillars"
    )

    phases: List[StrategyPhase] = Field(
        ...,
        description="List of strategic phases that define themes, cadence, and objectives without assigning dates"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Content Strategy\n\n## Executive Summary\nHigh-level strategy...",
                "global_settings": {
                    "tone": "Friendly, confident, aspirational",
                    "voice": "Conversational but informative",
                    "content_pillars": ["Education", "Brand Story", "Engagement"]
                },
                "phases": [
                    {
                        "name": "Awareness",
                        "duration_in_weeks": 2,
                        "themes": ["Brand Intro", "Problem Awareness"],
                        "objectives": ["Build recognition", "Warm up audience"],
                        "recommended_content_types": ["POST", "STORY"],
                        "posting_cadence": {"posts_per_week": 3, "stories_per_week": 2},
                        "messaging_guidelines": ["Highlight core value", "Use simple, clear language"]
                    }
                ]
            }
        }


class CampaignWeekPlan(BaseModel):
    """
    Represents a single campaign week, mapped to a specific phase
    with its cadence and strategic context.
    """
    week_number: int
    phase_name: str
    week_start: datetime.date
    week_end: datetime.date

    phase_themes: List[str]
    phase_objectives: List[str]
    posting_cadence: Dict[str, int]
    recommended_content_types: List[PostType]
    messaging_guidelines: Optional[List[str]] = None


class ScheduleItem(BaseModel):
    """
    Represents a single scheduled Instagram content unit (post or story).
    This is derived from the HTML table but stored in a structured way
    for UI, analytics, or downstream processing.
    """
    id: int = Field(
        ..., 
        description="Unique identifier for this schedule item within the schedule."
    )
    phase_name: Optional[str] = Field(
        default=None,
        description="Name of the strategy phase this item belongs to, if available."
    )
    week: Optional[int] = Field(
        default=None, 
        description="Week number within the campaign."
    )
    date: datetime.date = Field(
        ..., 
        description="Calendar date for the post's content."
    )
    post_type: PostType = Field(
        ...,
        description="Type of content (POST or STORY)."
    )
    theme_concept: str = Field(
        ..., 
        description="Theme or concept for the post's content."
    )
    objective: str = Field(
        ..., 
        description="Objective for of the post's content (e.g., awareness, engagement, CTA)."
    )
    description: str = Field(
        ..., 
        description="Detailed description to of the post's content. Will be used to guide copy and visual creation if tasks are added."
    )
    
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "additionalProperties": False
        },
        use_enum_values=True
    )


class SocialMediaSchedule(BaseModel):
    """
    Represents the final social media posting schedule.

    - `html_table`: The fully-formed HTML table that is compatible with the html_table_to_excel tool.
    - `items`: Structured representation of each scheduled post/story.
    """
    items: List[ScheduleItem] = Field(
        ...,
        description="Flattened list of scheduled content items, one per row of the schedule (excluding header)."
    )

    @field_validator('items')
    @classmethod
    def validate_unique_ids(cls, v: List[ScheduleItem]) -> List[ScheduleItem]:
        """Ensure all schedule items have unique ids."""
        ids = [item.id for item in v]
        if len(ids) != len(set(ids)):
            duplicates = [id_val for id_val in ids if ids.count(id_val) > 1]
            raise ValueError(
                f"Duplicate ids found in schedule items: {set(duplicates)}. "
                "Each schedule item must have a unique id."
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "week": 1,
                        "phase_name": "Awareness",
                        "post_type": "POST",
                        "date": "2025-11-01",
                        "theme_concept": "Welcome to Semester & Campus Life",
                        "objective": "Kickstart engagement; introduce semester vibe",
                        "description": "Vibrant shots of campus, student groups & iconic spots."
                    }
                ]
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
    field: str = Field(
        ...,
        description="The exact parameter key to modify in the Orshot template (e.g., 'headline', 'background_image')",
    )
    dataType: OrshotDataType = Field(
        ..., description="The data type of this field: 'TEXT' or 'IMAGE'"
    )
    description: str = Field(
        ...,
        description="Contextual description of the field (e.g., 'Main title, max 20 chars', 'Product shot in portrait mode')",
    )

    model_config = ConfigDict(use_enum_values=True)

# Used for Flow Service to resolve custom types from YAML
CUSTOM_TYPE_REGISTRY: Dict[str, Type[BaseModel] | Type[IntEnum]] = {
    "MarketingResearchReport": MarketingResearchReport,
    
    # Content Strategy
    "ContentStrategy": ContentStrategy,
    "StrategyPhase": StrategyPhase,
    
    # Social Media
    "SocialMediaSchedule": SocialMediaSchedule,
    "ScheduleItem": ScheduleItem,
    
    # Orshot
    "AllowedTemplateId": AllowedTemplateId,
    "OrshotSchemaField": OrshotSchemaField,
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
    - Custom models (MarketingResearchReport, ContentStrategy, etc.)
    - Enums (AllowedTemplateId, OrshotDataType)
    - Lists of any type (list[string], list[OrshotSchemaField], etc.)
    - Nested types (custom models containing enums)
    """
    type: str = Field(..., description="Type name (e.g., 'string', 'MarketingResearchReport', 'AllowedTemplateId')")
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

# Used for Frontend to resolve custom types
class CustomTypesResponse(BaseModel):
    """
    Response model exposing all custom types for OpenAPI schema generation.
    
    This model is used solely to ensure custom types appear in the OpenAPI schema
    so that client generation tools (e.g., openapi-ts) can generate TypeScript types.
    All fields are optional and default to None since this is only for schema exposure.
    """
    marketing_research_report: Optional[MarketingResearchReport] = Field(
        default=None,
        description="MarketingResearchReport type schema reference"
    )
    
    # Content Strategy
    strategy_phase: Optional[StrategyPhase] = Field(
        default=None,
        description="StrategyPhase type schema reference"
    )
    content_strategy: Optional[ContentStrategy] = Field(
        default=None,
        description="ContentStrategy type schema reference"
    )
    
    # Social Media
    schedule_item: Optional[ScheduleItem] = Field(
        default=None,
        description="ScheduleItem type schema reference"
    )
    social_media_schedule: Optional[SocialMediaSchedule] = Field(
        default=None,
        description="SocialMediaSchedule type schema reference"
    )
    
    # Orshot
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
