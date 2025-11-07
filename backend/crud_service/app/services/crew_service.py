from fastapi import HTTPException
from uuid import UUID

from app.models.models import CrewCreate, CrewUpdate, CrewRead
from app.repositories.crew_repository import CrewRepository


class CrewService:
    def __init__(self, repository: CrewRepository):
        self.repository = repository
        
    async def validate_crew(self, crew_id: UUID) -> CrewRead:
        """Validate the crew exists."""
        crew = await self.repository.get_crew_with_tasks(crew_id)
        if crew is None:
            raise HTTPException(status_code=404, detail="Crew not found")
        return crew
    
    async def get_crew_with_tasks(self, crew_id: UUID) -> CrewRead | None:
        """Get a crew by ID."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        return await self.validate_crew(crew_id)

    async def get_crews_with_tasks(self, crew_id: UUID | None = None) -> list[CrewRead]:
        """Get crews, optionally filtered by crew_id."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        if crew_id:
            crew = await self.validate_crew(crew_id)
            return [crew]
        return await self.repository.get_crews_with_tasks(crew_id)
    
    async def create_crew(self, crew: CrewCreate) -> CrewRead:
        """Create a new crew."""
        return await self.repository.create_crew(crew)
    
    async def update_crew(self, crew: CrewUpdate) -> CrewRead | None:
        """Update an existing crew."""
        await self.validate_crew(crew.id)
        return await self.repository.update_crew(crew)