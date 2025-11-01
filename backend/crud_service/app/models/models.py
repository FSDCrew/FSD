from sqlalchemy import Column, String
from sqlalchemy.sql import func
from db.dbconfig import Base # Assuming you have a database.py with Base = declarative_base()

class User(Base):
  __tablename__ = "users"
  
  id = Column(String, primary_key=True, index=True)
  
  email = Column(String, unique=True, index=True, nullable=False)

class CrewRun(Base):
  __tablename__ = "crew_runs"
  
  id = Column(String, primary_key=True, index=True)
  
  email = Column(String, unique=True, index=True, nullable=False)

class Crew(Base):
  __tablename__ = "crews"
  
  id = Column(String, primary_key=True, index=True)
  
  email = Column(String, unique=True, index=True, nullable=False)
