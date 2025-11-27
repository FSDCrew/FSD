from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
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


CUSTOM_TYPE_REGISTRY: Dict[str, Type[BaseModel]] = {
    "MarketingResearch": MarketingResearch,
    "ContentStrategy": ContentStrategy,
    "SocialMediaSchedule": SocialMediaSchedule,
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

        self.task_read_specs.setdefault(task_key, []).append(read_spec)
        self.field_readers.setdefault(field_name, []).append(task_key)

    def register_task_write(self, task_key: str, write_spec: Dict[str, Any]) -> None:
        """Record that a task writes to a particular field."""
        field_name = write_spec["field"]

        self.task_write_specs.setdefault(task_key, []).append(write_spec)
        self.field_writers.setdefault(field_name, []).append(task_key)
