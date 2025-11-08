from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.connection import get_session
from app.repositories.crew_repository import CrewRepository
from app.services.crew_service import CrewService
from app.services.task_service import TaskService
from app.repositories.task_repository import TaskRepository


async def get_crew_repository(session: AsyncSession = Depends(get_session)) -> CrewRepository:
    """Dependency to get CrewRepository instance with database session."""
    return CrewRepository(session)


async def get_crew_service(repository: CrewRepository = Depends(get_crew_repository)) -> CrewService:
    """Dependency to get CrewService instance with repository injected."""
    return CrewService(repository)


async def get_task_repository(session: AsyncSession = Depends(get_session)) -> TaskRepository:
    """Dependency to get TaskRepository instance with database session."""
    return TaskRepository(session)


async def get_task_service(repository: TaskRepository = Depends(get_task_repository), crew_service: CrewService = Depends(get_crew_service)) -> TaskService:
    """Dependency to get TaskService instance with repository injected."""
    return TaskService(repository, crew_service)
