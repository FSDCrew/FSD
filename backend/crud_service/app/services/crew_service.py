from fastapi import HTTPException
from uuid import UUID

from app.schemas.schemas import Crew as CrewDB, Task as TaskDB, CrewRun as CrewRunDB
from app.models.models import CrewCreate, CrewUpdate, CrewRead, User
from app.models.models import TaskRead, CrewRunRead
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
        crew = await self.repository.get_fully_loaded_crew_by_id(crew_id, user_id)
        if crew is None:
            raise HTTPException(status_code=404, detail="Crew not found")
        return self._convert_to_crew_read(crew)

    def _convert_to_crew_read(self, db_crew: CrewDB) -> CrewRead:
        """Helper to convert CrewDB object to CrewRead Pydantic model."""
        
        def convert_tasks(db_tasks: TaskDB) -> list[TaskRead]:
            if not db_tasks:
                return []
            return [TaskRead.model_validate(task) for task in db_tasks]

        def convert_crew_runs(db_runs: list[CrewRunDB]) -> list[CrewRunRead]:
            if not db_runs:
                return []
            return [CrewRunRead.model_validate(crew_run) for crew_run in db_runs]

        return CrewRead(
            id=UUID(str(db_crew.id)),
            name=str(db_crew.name),
            user_id=UUID(str(db_crew.user_id)),
            tasks=convert_tasks(db_crew.tasks),
            crew_runs=convert_crew_runs(db_crew.crew_runs)
        )
        
    async def get_fully_loaded_crew_by_id_internal(self, crew_id: UUID) -> CrewRead:
        """Get a fully loaded crew by ID for internal services without ownership validation."""
        db_crew = await self.repository.get_fully_loaded_crew_by_id_internal(crew_id)
        
        if not db_crew:
            raise HTTPException(
                status_code=404,
                detail=f"Crew with ID {crew_id} not found."
            )
        
        return self._convert_to_crew_read(db_crew)
    
    async def get_fully_loaded_crew_by_id(self, crew_id: UUID, user_id: UUID) -> CrewRead | None:
        """Get a crew by ID."""
        # TODO: Retrieve task descriptions and expected outputs
        db_crew = await self.repository.get_fully_loaded_crew_by_id(crew_id, user_id)
        
        if not db_crew:
            raise HTTPException(
                status_code=404,
                detail=f"Crew with ID {crew_id} not found."
            )

        return self._convert_to_crew_read(db_crew)

    async def get_all_fully_loaded_crews(self, user_id: UUID) -> list[CrewRead]:
        """Get crews, optionally filtered by crew_id."""
        # TODO: Retrieve task descriptions and expected outputs
        db_crews = await self.repository.get_all_fully_loaded_crews(user_id)
        if not db_crews:
            return []

        return [self._convert_to_crew_read(db_crew) for db_crew in db_crews]
    
    async def create_crew(self, crew: CrewCreate, user_id: UUID) -> CrewRead:
        """Create a new crew."""
        db_crew = await self.repository.create_crew(crew, user_id=user_id)
        return CrewRead(
            id=UUID(str(db_crew.id)),
            name=str(db_crew.name),
            user_id=UUID(str(db_crew.user_id)),
            tasks=[],
            crew_runs=[]
    )
    
    async def update_crew(self, crew: CrewUpdate, current_user: User) -> CrewRead | None:
        """Update an existing crew."""
        existing_crew = await self.validate_crew(crew.id, current_user.id)
        self.is_crew_owner(UUID(str(existing_crew.user_id)), current_user.id)

        db_crew = await self.repository.update_crew(crew)

        if db_crew is None:
            return None

        return self._convert_to_crew_read(db_crew)

    async def delete_crew(self, crew_id: UUID, user_id: UUID) -> CrewRead | None:
        """Delete an existing crew."""
        existing_crew = await self.validate_crew(crew_id, user_id)
        self.is_crew_owner(UUID(str(existing_crew.user_id)), user_id)
        deleted_crew = await self.repository.delete_crew(crew_id)

        if deleted_crew is None:
            raise HTTPException(
                status_code=404,
                detail=f"Crew with ID {crew_id} not found."
            )

        return self._convert_to_crew_read(deleted_crew)
    