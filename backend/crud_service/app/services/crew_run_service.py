from uuid import UUID
from fastapi import HTTPException, status
from app.repositories.crew_run_repository import CrewRunRepository
from app.models.models import CrewRunCreate, CrewRunRead
# Assuming a CrewService exists for validation
# from app.services.crew_service import CrewService 

class CrewRunService:
    def __init__(self, repository: CrewRunRepository):
        self.repository = repository
        
    async def create_crew_run(self, crew_run_data: CrewRunCreate) -> CrewRunRead:
        """Creates a crew run and returns the Pydantic model."""
        db_crew_run = await self.repository.create_crew_run(crew_run_data)
        full_crew_run = await self.repository.get_crew_run_by_id_with_artifacts(db_crew_run.id)

        return CrewRunRead.from_orm(full_crew_run)

    async def get_crew_run_by_id_with_artifacts(self, crew_run_id: UUID, user_id: UUID) -> CrewRunRead:
        """Retrieves a crew run and its artifacts, performing access validation."""
        db_crew_run = await self.repository.get_crew_run_by_id_with_artifacts(crew_run_id)

        if db_crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found."
            )

        return CrewRunRead.from_orm(db_crew_run)