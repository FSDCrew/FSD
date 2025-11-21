from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.crew_run_repository import CrewRunRepository
from app.repositories.queue_repository import QueueRepository
from app.models.models import CrewRunCreate, CrewRunRead
from app.services.crew_service import CrewService

class CrewRunService:
    def __init__(self, crew_service: CrewService, repository: CrewRunRepository, queue_repository: QueueRepository, session: AsyncSession):
        self.crew_service = crew_service
        self.crew_run_repository = repository
        self.queue_repository = queue_repository
        self.session = session
    
    async def create_crew_run(self, crew_run_data: CrewRunCreate, user_id: UUID) -> CrewRunRead:
        """Creates a crew run, enqueues it, and returns the Pydantic model."""
        await self.crew_service.validate_crew(crew_run_data.crew_id, user_id)
        self.crew_service.is_crew_owner(crew_run_data.crew_id, user_id)
        async with self.session.begin():
            db_crew_run = await self.crew_run_repository.create_crew_run(crew_run_data)
            crew_run_id = db_crew_run.id.value
            await self.queue_repository.enqueue_crew_run(crew_run_id)
        
        await self.session.refresh(db_crew_run)
        full_crew_run = await self.crew_run_repository.get_crew_run_by_id_with_artifacts(crew_run_id)

        return CrewRunRead.model_validate(full_crew_run)

    async def get_crew_run_by_id_with_artifacts(self, crew_run_id: UUID, user_id: UUID) -> CrewRunRead:
        """Retrieves a crew run and its artifacts, performing access validation."""
        db_crew_run = await self.crew_run_repository.get_crew_run_by_id_with_artifacts(crew_run_id)

        if db_crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found."
            )

        return CrewRunRead.from_orm(db_crew_run)
    
    async def update_crew_run_output(self, crew_run_id: UUID, output: dict) -> CrewRunRead:
        """Updates the output of a crew run."""
        # TODO: Should output be an array of objects rather than just a dictionary?
        db_crew_run = await self.crew_run_repository.update_crew_run_output(crew_run_id, output)
        
        if db_crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found."
            )
        
        full_crew_run = await self.crew_run_repository.get_crew_run_by_id_with_artifacts(crew_run_id)
        return CrewRunRead.from_orm(full_crew_run)