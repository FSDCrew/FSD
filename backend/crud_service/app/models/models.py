from enum import Enum
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class Agent(BaseModel):
    key: str
    role: str
    goal: str
    backstory: str
    
class TaskBase(BaseModel):
    key: str
    description: str
    expected_output: str
    order: int
    
class TaskCreate(TaskBase):
    agent_key: str | None = None

class TaskRead(TaskBase):
    id: UUID
    agent_key: str
    model_config = ConfigDict(from_attributes=True)
    
class TaskUpdate(TaskBase):
    id: UUID
    description: str | None = None
    expected_output: str | None = None
    
class CrewBase(BaseModel):
    name: str

class CrewCreate(CrewBase):
    user_id: UUID
    
class CrewRead(CrewBase):
    id: UUID
    tasks: list[TaskRead] 
    agents: list[Agent]
    
    model_config = ConfigDict(from_attributes=True)

class CrewUpdate(CrewBase):
    id: UUID
    name: str | None = None

class ArtifactType(Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"
    
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

class CrewRunBase(BaseModel):
    output: dict[str, Any] | None = None

class CrewRunCreate(CrewRunBase):
    crew_id: UUID
    
class CrewRunRead(CrewRunBase):
    id: UUID
    output: dict[str, Any] | None = None
    artifacts: list[ArtifactRead] | None = None

    model_config = ConfigDict(from_attributes=True)

class CrewRunUpdate(CrewRunBase):
    id: UUID
    output: dict[str, Any] | None = None
    
class User(BaseModel):
    id: UUID
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str | None