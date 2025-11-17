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
        return crew
    
    async def get_crew_with_tasks(self, crew_id: UUID, user_id: UUID) -> CrewRead | None:
        """Get a crew by ID."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        db_crew = await self.repository.get_crew_with_tasks(crew_id, user_id)
        
        if not db_crew:
            return None

        return CrewRead(
            id=db_crew.id,
            user_id=db_crew.user_id,
            name=db_crew.name,
            tasks=[
                TaskRead(
                    id=task.id,
                    key=task.key,
                    description=task.description if hasattr(task, 'description') else "",
                    expected_output=task.expected_output if hasattr(task, 'expected_output') else "",
                    agent_key=task.agent_key,
                    order=task.order
                )
                for task in db_crew.tasks
            ],
            agents=[],
            crew_runs=[
                CrewRunRead(
                    id=crew_run.id,
                    output=crew_run.output
                )
                for crew_run in (db_crew.crew_runs if db_crew.crew_runs else [])
            ]
        )

    async def get_crews_with_tasks(self, user_id: UUID) -> list[CrewRead]:
        """Get crews, optionally filtered by crew_id."""
        # TODO: Retrieve agents 
        # TODO: Retrieve task descriptions and expected outputs
        
        db_crews = await self.repository.get_crews_with_tasks(user_id)
        if not db_crews:
            return []

        return [CrewRead(
            id=db_crew.id,
            user_id=db_crew.user_id,
            name=db_crew.name,
            tasks=[
                TaskRead(
                    id=task.id,
                    key=task.key,
                    description=task.description if hasattr(task, 'description') else "",
                    expected_output=task.expected_output if hasattr(task, 'expected_output') else "",
                    agent_key=task.agent_key,
                    order=task.order
                )
                for task in (db_crew.tasks if db_crew.tasks else [])
            ],
            agents=[]
        ) for db_crew in db_crews
        ]
    
    async def create_crew(self, crew: CrewCreate, user_id: UUID) -> CrewRead:
        """Create a new crew."""
        db_crew = await self.repository.create_crew(CrewCreate(name=crew.name, user_id=user_id))
        return CrewRead(
            id=db_crew.id,
            user_id=db_crew.user_id,
            name=db_crew.name,
            tasks=[],
            agents=[]
    )
    
    async def update_crew(self, crew: CrewUpdate, current_user: User) -> CrewRead | None:
        """Update an existing crew."""
        existing_crew = await self.validate_crew(crew.id, current_user.id)
        self._is_crew_owner(existing_crew.user_id, current_user.id)

        db_crew = await self.repository.update_crew(crew)

        return CrewRead(
            id=db_crew.id,
            user_id=db_crew.user_id,
            name=db_crew.name,
            tasks=[
                TaskRead(
                    id=task.id,
                    key=task.key,
                    description=task.description if hasattr(task, 'description') else "",
                    expected_output=task.expected_output if hasattr(task, 'expected_output') else "",
                    agent_key=task.agent_key,
                    order=task.order
                )
                for task in db_crew.tasks
            ],
            agents=[]
        )

    async def delete_crew(self, crew_id: UUID, user_id: UUID) -> None:
        """Delete an existing crew."""
        existing_crew = await self.validate_crew(crew_id, user_id)
        self._is_crew_owner(existing_crew.user_id, user_id)
        await self.repository.delete_crew(crew_id)
        return None
    