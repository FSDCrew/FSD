from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.connection import get_session
from app.repositories.crew_repository import CrewRepository
from app.services.crew_service import CrewService
from app.services.task_service import TaskService


async def get_crew_repository(session: AsyncSession = Depends(get_session)) -> CrewRepository:
    """Dependency to get CrewRepository instance with database session."""
    return CrewRepository(session)


async def get_crew_service(repository: CrewRepository = Depends(get_crew_repository)) -> CrewService:
    """Dependency to get CrewService instance with repository injected."""
    return CrewService(repository)
