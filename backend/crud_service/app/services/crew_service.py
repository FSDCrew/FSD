from typing import Any
from fastapi import HTTPException
from uuid import UUID

from app.models.models import CrewBase, CrewCreate, CrewUpdate, CrewRead, User
from app.models.models import TaskRead, CrewRunRead, ArtifactRead
from app.repositories.crew_repository import CrewRepository

class CrewService:
    def __init__(self, repository: CrewRepository):
        self.repository = repository
    
    def _is_crew_owner(self, crew_owner_id: UUID, current_user_id: UUID) -> bool:
        if crew_owner_id == current_user_id:
            return True
        raise HTTPException(status_code=403, detail="You are not the owner of this crew")
        
    async def validate_crew(self, crew_id: UUID, user_id: UUID) -> CrewRead:
        """Validate the crew exists."""
        crew = await self.repository.get_crew_with_tasks(crew_id, user_id)
        if crew is None:
            raise HTTPException(status_code=404, detail="Crew not found")
        return self._convert_to_crew_read(crew)

    def _convert_to_crew_read(self, db_crew: Any) -> CrewRead:
        """Helper to convert CrewDB object to CrewRead Pydantic model."""
        
        def convert_tasks(db_tasks: Any) -> list[TaskRead]:
            if not db_tasks:
                return []
            
            return [
                TaskRead(
                    id=task.id,
                    key=str(task.key),
                    description=str(task.description) if hasattr(task, 'description') else "",
                    expected_output=str(task.expected_output) if hasattr(task, 'expected_output') else "",
                    agent_key=str(task.agent_key),
                    order=int(task.order)
                )
                for task in db_tasks
            ]

        # Helper to safely convert CrewRun ORM objects to CrewRunRead Pydantic models
        def convert_crew_runs(db_runs: Any) -> list[CrewRunRead]:
            if not db_runs:
                return []
            
            return [
                CrewRunRead(
                    id=crew_run.id,
                    output=crew_run.output if hasattr(crew_run, 'output') else None,
                )
                for crew_run in db_runs
            ]

        return CrewRead(
            id=UUID(str(db_crew.id)),
            name=str(db_crew.name),
            user_id=UUID(str(db_crew.user_id)),
            tasks=convert_tasks(db_crew.tasks),
            agents=[],
            crew_runs=convert_crew_runs(db_crew.crew_runs)
        )
    
    async def get_crew_with_tasks(self, crew_id: UUID, user_id: UUID) -> CrewRead | None:
        """Get a crew by ID."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        db_crew = await self.repository.get_crew_with_tasks(crew_id, user_id)
        
        if not db_crew:
            return None

        return self._convert_to_crew_read(db_crew)

    async def get_crews_with_tasks(self, user_id: UUID) -> list[CrewRead]:
        """Get crews, optionally filtered by crew_id."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        
        db_crews = await self.repository.get_crews_with_tasks(user_id)
        if not db_crews:
            return []

        return [self._convert_to_crew_read(db_crew) for db_crew in db_crews]
    
    async def create_crew(self, crew: CrewCreate, user_id: UUID) -> CrewRead:
        """Create a new crew."""
        db_crew = await self.repository.create_crew(CrewCreate(name=crew.name, user_id=user_id))
        return CrewRead(
            id=UUID(str(db_crew.id)),
            name=str(db_crew.name),
            user_id=UUID(str(db_crew.user_id)),
            tasks=[],
            agents=[],
            crew_runs=[]
    )
    
    async def update_crew(self, crew: CrewUpdate, current_user: User) -> CrewRead | None:
        """Update an existing crew."""
        existing_crew = await self.validate_crew(crew.id, current_user.id)
        self._is_crew_owner(UUID(str(existing_crew.user_id)), current_user.id)

        db_crew = await self.repository.update_crew(crew)

        if db_crew is None:
            return None

        return self._convert_to_crew_read(db_crew)

    async def delete_crew(self, crew_id: UUID, user_id: UUID) -> None:
        """Delete an existing crew."""
        existing_crew = await self.validate_crew(crew_id, user_id)
        self._is_crew_owner(UUID(str(existing_crew.user_id)), user_id)
        await self.repository.delete_crew(crew_id)
        return None
    