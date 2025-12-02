from enum import Enum, IntEnum
from typing import Any, Dict, List, Literal, Optional, Type
import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from pydantic import BaseModel, ConfigDict, Field


class CrewRun(BaseModel):
    id: UUID
    crew_id: UUID

    model_config = ConfigDict(extra="ignore")


class CrewRunCreateRequest(BaseModel):
    crew_id: UUID
    inputs: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


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
    recommended_content_types: List[str] = Field(
        ...,
        description="Content formats recommended here (e.g., posts, reels, stories).",
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

    global_settings: Dict[str, Any] = Field(
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
                        "recommended_content_types": ["posts", "reels", "stories"],
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
    recommended_content_types: List[str]
    messaging_guidelines: Optional[List[str]] = None


class ScheduleItem(BaseModel):
    """
    Represents a single scheduled Instagram content unit (post, story, reel).
    This is derived from the HTML table but stored in a structured way
    for UI, analytics, or downstream processing.
    """
    phase_name: Optional[str] = Field(
        default=None,
        description="Name of the strategy phase this item belongs to, if available."
    )
    week: int = Field(..., description="Week number within the campaign (1-based).")
    date: datetime.date = Field(..., description="Calendar date for this content.")
    post_type: Literal["Post", "Story", "Reel"] = Field(
        ...,
        description="Type of content."
    )
    theme_concept: str = Field(..., description="Theme or concept for this content unit.")
    objective: str = Field(..., description="Objective for this content (e.g., awareness, engagement, CTA).")
    description: str = Field(..., description="Detailed description to guide copy and visual creation.")
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes such as tags, CTA, stickers, collaborators, or audio suggestions."
    )
    
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "additionalProperties": False
        }
    )


class SocialMediaSchedule(BaseModel):
    """
    Represents the final social media posting schedule.

    - `html_table`: The fully-formed HTML table that is compatible with the html_table_to_excel tool.
    - `items`: Structured representation of each scheduled post/story/reel.
    """
    items: List[ScheduleItem] = Field(
        ...,
        description="Flattened list of scheduled content items, one per row of the schedule (excluding header)."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "week": 1,
                        "phase_name": "Awareness",
                        "post_type": "Post",
                        "date": "2025-11-01",
                        "theme_concept": "Welcome to Semester & Campus Life",
                        "objective": "Kickstart engagement; introduce semester vibe",
                        "description": "Vibrant shots of campus, student groups & iconic spots.",
                        "notes": "Use Canva template; include hashtag #CampusLife"
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
