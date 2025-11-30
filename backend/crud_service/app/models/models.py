from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Agent(BaseModel):
    key: str
    role: str
    goal: str
    backstory: str


class TaskBase(BaseModel):
    key: str
    # description: str
    # expected_output: str
    order: int


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(TaskBase):
    id: UUID
    description: str | None = None
    expected_output: str | None = None


class ArtifactType(Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"


class QueueStatus(Enum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClaimJobResponse(BaseModel):
    id: UUID
    crew_run_id: UUID
    crew_id: UUID
    status: QueueStatus
    lease_token: str
    visible_at: str

    model_config = ConfigDict(from_attributes=True)


class UpdateStatusRequest(BaseModel):
    lease_token: str
    status: QueueStatus


class HeartbeatRequest(BaseModel):
    lease_token: str


class ArtifactBase(BaseModel):
    type: ArtifactType
    file_name: str | None


class ArtifactCreate(ArtifactBase):
    object_key: str | None = None


class ArtifactRead(ArtifactBase):
    id: UUID
    crew_run_id: UUID

    model_config = ConfigDict(from_attributes=True)


class ArtifactServerCreate(ArtifactBase):
    file_content_base64: str


class TaskFieldRead(BaseModel):
    """Describes a state field that a task consumes."""

    field: str
    cardinality: str


class TaskFieldWrite(BaseModel):
    """Describes a state field that a task produces."""

    field: str
    mode: str


class TaskInfo(BaseModel):
    key: str
    name: str
    task_description: str
    description: str
    expected_output: str
    agent: str
    output_file: str
    reads: list[TaskFieldRead]
    writes: list[TaskFieldWrite]

    model_config = ConfigDict(extra="allow")


class CrewRunMetadataBase(BaseModel):
    inputs: dict[str, Any]


class CrewRunMetadataCreate(CrewRunMetadataBase):
    pass

class CrewRunMetadataRead(CrewRunMetadataBase):
    tasks_snapshot: list[TaskInfo]

class CrewRunBase(BaseModel):
    output: dict[str, Any] | None = None


class CrewRunCreate(CrewRunBase):
    crew_id: UUID
    run_metadata: CrewRunMetadataCreate | None = None


class CrewRunRead(CrewRunBase):
    id: UUID
    crew_id: UUID
    output: dict[str, Any] | None = None
    artifacts: list[ArtifactRead] | None = None
    queue_status: QueueStatus | None = None
    retry_count: int | None = None
    run_metadata: CrewRunMetadataRead

    model_config = ConfigDict(from_attributes=True)


class CrewBase(BaseModel):
    name: str | None = None


class CrewCreate(CrewBase):
    # user_id: UUID
    pass


class CrewRead(CrewBase):
    id: UUID
    user_id: UUID
    tasks: list[TaskRead]
    crew_runs: list[CrewRunRead] | None = None
    model_config = ConfigDict(from_attributes=True)


class CrewUpdate(CrewBase):
    id: UUID
    name: str | None = None


class User(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    given_name: str
    family_name: str
    picture: str | None
