from sqlalchemy import Column, Integer, String, ForeignKey, Enum, text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.models.models import ArtifactType, QueueStatus

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    email = Column(String, nullable=False)
    given_name = Column(String, nullable=False)
    family_name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    crews = relationship("Crew", back_populates="user", cascade="all, delete-orphan")
    
class Crew(Base):
    __tablename__ = "crews"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name = Column(String, nullable=False)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="crews")
    tasks = relationship("Task", back_populates="crew", order_by="Task.order", cascade="all, delete-orphan")
    crew_runs = relationship("CrewRun", back_populates="crew", cascade="all, delete-orphan")
    
class Task(Base):
    __tablename__ = "tasks"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    key = Column(String, nullable=False)
    agent_key = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    crew_id = Column(PostgresUUID(as_uuid=True), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False)
    crew = relationship("Crew", back_populates="tasks")

class CrewRun(Base):
    __tablename__ = "crew_runs"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    output = Column(JSONB, nullable=True)
    crew_id = Column(PostgresUUID(as_uuid=True), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False)
    crew = relationship("Crew", back_populates="crew_runs")
    artifacts = relationship("Artifact", back_populates="crew_run")
    queue_entry = relationship("CrewRunQueue", back_populates="crew_run", uselist=False, cascade="all, delete-orphan")
    
class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    type = Column(Enum(ArtifactType), nullable=False)
    object_key = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    crew_run_id = Column(PostgresUUID(as_uuid=True), ForeignKey("crew_runs.id", ondelete="CASCADE"), nullable=False)
    crew_run = relationship("CrewRun", back_populates="artifacts")

class CrewRunQueue(Base):
    __tablename__ = "crew_run_queue"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    crew_run_id = Column(PostgresUUID(as_uuid=True), ForeignKey("crew_runs.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(Enum(QueueStatus), nullable=False, default=QueueStatus.QUEUED)
    retry_count = Column(Integer, nullable=False, default=0)
    visible_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'))
    lease_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'))
    crew_run = relationship("CrewRun", back_populates="queue_entry")
    
    __table_args__ = (
        Index('idx_queue_status_visible_created', 'status', 'visible_at', 'created_at'),
    )