from fastapi import HTTPException
from uuid import UUID

from app.models.models import CrewBase, CrewCreate, CrewUpdate, CrewRead, User
from app.repositories.crew_repository import CrewRepository

class CrewService:
    def __init__(self, repository: CrewRepository):
        self.repository = repository
    
    def is_crew_owner(self, crew_owner_id: UUID, current_user_id: UUID) -> bool:
        """Check if the current user is the owner of the crew."""
        if crew_owner_id == current_user_id:
            return True
        raise HTTPException(status_code=403, detail="You are not the owner of this crew")
        
    async def validate_crew(self, crew_id: UUID, user_id: UUID) -> CrewRead:
        """Validate the crew exists."""
        crew = await self.repository.get_crew_with_tasks(crew_id, user_id)
        if crew is None:
            raise HTTPException(status_code=404, detail="Crew not found")
        return crew
    
    async def get_crew_with_tasks(self, crew_id: UUID, user_id: UUID) -> CrewRead | None:
        """Get a crew by ID."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        return await self.repository.get_crew_with_tasks(crew_id, user_id)

    async def get_crews_with_tasks(self, user_id: UUID) -> list[CrewRead]:
        """Get crews, optionally filtered by crew_id."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        return await self.repository.get_crews_with_tasks(user_id)
    
    async def create_crew(self, crew: CrewBase, user_id: UUID) -> CrewRead:
        """Create a new crew."""
        return await self.repository.create_crew(CrewCreate(name=crew.name, user_id=user_id))
    
    async def update_crew(self, crew: CrewUpdate, current_user: User) -> CrewRead | None:
        """Update an existing crew."""
        existing_crew = await self.validate_crew(crew.id, current_user.id)
        self.is_crew_owner(existing_crew.user_id, current_user.id)
        return await self.repository.update_crew(crew)