from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    CrewRunCreate,
    CrewRunRead,
    QueueStatus,
    TaskStateSnapshot,
    TaskStatus,
    UpdateTaskStatusRequest,
)
from app.repositories.crew_run_repository import CrewRunRepository
from app.repositories.queue_repository import QueueRepository
from app.services.crew_service import CrewService


class CrewRunService:
    def __init__(
        self,
        crew_service: CrewService,
        repository: CrewRunRepository,
        queue_repository: QueueRepository,
        session: AsyncSession,
    ):
        self.crew_service = crew_service
        self.crew_run_repository = repository
        self.queue_repository = queue_repository
        self.session = session
        
    def _convert_db_to_read(self, db_crew_run) -> CrewRunRead:
        """Converts DB model to CrewRunRead."""
        crew_run_read = CrewRunRead.model_validate(db_crew_run)
        
        if db_crew_run.queue_entry:
            crew_run_read.queue_status = db_crew_run.queue_entry.status
            crew_run_read.retry_count = db_crew_run.queue_entry.retry_count
        
        return crew_run_read

    async def create_crew_run(
        self, crew_run_data: CrewRunCreate, user_id: UUID
    ) -> CrewRunRead:
        """Creates a crew run, enqueues it, and returns the Pydantic model."""
        crew = await self.crew_service.validate_crew(crew_run_data.crew_id, user_id)
        self.crew_service.is_crew_owner(crew.user_id, user_id)

        if len(crew_run_data.run_metadata.tasks_snapshot) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No tasks found in crew run metadata."
            )
        
        try:
            db_crew_run = await self.crew_run_repository.create_crew_run(crew_run_data)
            crew_run_id = UUID(str(db_crew_run.id))
            await self.queue_repository.enqueue_crew_run(crew_run_id)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create crew run: {e}"
            )
        await self.session.refresh(db_crew_run)
        full_crew_run = (
            await self.crew_run_repository.get_crew_run_by_id_with_artifacts(
                crew_run_id
            )
        )

        return self._convert_db_to_read(full_crew_run)
    
    async def cancel_crew_run(self, crew_run_id: UUID, user_id: UUID) -> None:
        """Cancels a crew run."""
        crew_run = await self.get_crew_run_by_id_with_artifacts(crew_run_id, user_id)
        crew = await self.crew_service.get_fully_loaded_crew_by_id_internal(crew_run.crew_id)
        if crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found."
            )
        if crew_run.queue_status in [QueueStatus.CANCELLED, QueueStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Crew Run with ID {crew_run_id} is already cancelled or completed."
            )
        
        self.crew_service.is_crew_owner(crew.user_id, user_id)
        
        if crew_run.queue_status in [QueueStatus.QUEUED, QueueStatus.FAILED]:
            await self.queue_repository.cancel_queued_job(crew_run_id, QueueStatus.CANCELLED)
            await self.session.commit()
        elif crew_run.queue_status == QueueStatus.CLAIMED:
            await self.queue_repository.cancel_claimed_job(crew_run_id)
            await self.session.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Crew Run with ID {crew_run_id} is not queued, claimed or failed."
            )
        return

    async def get_crew_run_by_id_with_artifacts(
        self, crew_run_id: UUID, user_id: UUID
    ) -> CrewRunRead:
        """Retrieves a crew run and its artifacts, performing access validation."""
        db_crew_run = await self.crew_run_repository.get_crew_run_by_id_with_artifacts(
            crew_run_id
        )

        if db_crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found."
            )

        return self._convert_db_to_read(db_crew_run)
    
    async def get_crew_run_by_id_internal(self, crew_run_id: UUID) -> CrewRunRead:
        """Retrieves a crew run by ID for internal use without user validation."""
        db_crew_run = await self.crew_run_repository.get_crew_run_by_id_internal(
            crew_run_id
        )

        if db_crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found.",
            )

        return self._convert_db_to_read(db_crew_run)

    async def update_crew_run_output(
        self, crew_run_id: UUID, output: dict
    ) -> CrewRunRead:
        """Updates the output of a crew run."""
        # TODO: Should output be an array of objects rather than just a dictionary?
        db_crew_run = await self.crew_run_repository.update_crew_run_output(
            crew_run_id, output
        )

        if db_crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found.",
            )

        full_crew_run = (
            await self.crew_run_repository.get_crew_run_by_id_with_artifacts(
                crew_run_id
            )
        )
        return self._convert_db_to_read(full_crew_run)

    async def update_task_status(
        self,
        crew_run_id: UUID,
        task_key: str,
        update_task_status_request: UpdateTaskStatusRequest,
    ) -> CrewRunRead:
        """Updates the status of a specific task in a crew run."""
        crew_run = await self.get_crew_run_by_id_internal(crew_run_id)
        if crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found.",
            )
        
        task_states_dict = crew_run.output.task_states
        current_task_state = task_states_dict.get(task_key)
        if current_task_state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with key {task_key} not found in crew run output.",
            )
        
        updated_task_state = TaskStateSnapshot(
            state={
                "reads": update_task_status_request.task_inputs,
                "writes": update_task_status_request.task_outputs,
            },
            completed_at=update_task_status_request.completed_at,
            status=update_task_status_request.status,
            order=current_task_state.order,
        )
        
        updated_output = crew_run.output.model_dump(mode='json')
        updated_output['task_states'][task_key] = updated_task_state.model_dump(mode='json')
        
        db_crew_run = await self.crew_run_repository.update_crew_run_output(
            crew_run_id, updated_output
        )
        
        if db_crew_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew Run with ID {crew_run_id} not found.",
            )
        
        # Refresh to get the full crew run with relationships
        full_crew_run = (
            await self.crew_run_repository.get_crew_run_by_id_with_artifacts(
                crew_run_id
            )
        )
        
        return self._convert_db_to_read(full_crew_run)
