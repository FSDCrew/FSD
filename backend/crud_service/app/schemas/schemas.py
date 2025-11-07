from sqlalchemy import Column, Integer, String, UUID, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.models.models import ArtifactType

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    given_name = Column(String, nullable=False)
    family_name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    
class Crew(Base):
    __tablename__ = "crews"
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="crews")
    tasks = relationship("Task", back_populates="crews")
    
class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID, primary_key=True)
    key = Column(String, nullable=False)
    agent_key = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    crew_id = Column(UUID, ForeignKey("crews.id"), nullable=False)
    crew = relationship("Crew", back_populates="tasks")

class CrewRun(Base):
    __tablename__ = "crew_runs"
    id = Column(UUID, primary_key=True)
    output = Column(JSONB, nullable=True)
    crew_id = Column(UUID, ForeignKey("crews.id"), nullable=False)
    crew = relationship("Crew", back_populates="crew_runs")
    
class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(UUID, primary_key=True)
    type = Column(Enum(ArtifactType), nullable=False)
    object_key = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    crew_run_id = Column(UUID, ForeignKey("crew_runs.id"), nullable=False)
    crew_run = relationship("CrewRun", back_populates="artifacts")
    