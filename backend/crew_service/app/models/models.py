from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Any


class CrewRun(BaseModel):
    id: UUID
    crew_id: UUID
    
    model_config = ConfigDict(extra="ignore")


class CrewRunCreateRequest(BaseModel):
    crew_id: UUID
    
    model_config = ConfigDict(extra="ignore")