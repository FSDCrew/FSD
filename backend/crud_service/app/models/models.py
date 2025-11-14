from enum import Enum
from typing import Any
from uuid import UUID
from pydantic import BaseModel

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
    user_id: UUID
    tasks: list[TaskRead] 
    agents: list[Agent]

class CrewUpdate(CrewBase):
    id: UUID
    name: str | None = None

class CrewRunBase(BaseModel):
    output: dict[str, Any] | None = None

class CrewRunCreate(CrewRunBase):
    crew_id: UUID
    
class CrewRunRead(CrewRunBase):
    id: UUID
    output: dict[str, Any] | None = None

class CrewRunUpdate(CrewRunBase):
    id: UUID
    output: dict[str, Any] | None = None
    
class ArtifactType(Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"
    
class ArtifactBase(BaseModel):
    type: ArtifactType
    object_key: str | None
    file_name: str | None

class ArtifactCreate(ArtifactBase):
    pass

class ArtifactRead(ArtifactBase):
    id: UUID
    crew_run_id: UUID
    
class User(BaseModel):
    id: UUID
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str | None