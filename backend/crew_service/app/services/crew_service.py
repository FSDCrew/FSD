from uuid import UUID
from typing import Dict
import httpx

from app.api.crud_client import AuthenticatedClient, errors
from app.api.crud_client.api.internal import (
    create_crew_run_internal_internal_crew_run_create_post as create_crew_run_func,
    get_crew_by_id_internal_crew_crew_id_get as get_crew_by_id_func,
)
from app.api.crud_client.models.body_create_crew_run_internal_internal_crew_run_create_post import (
    BodyCreateCrewRunInternalInternalCrewRunCreatePost as CrewRunCreateBody,
)
from app.api.crud_client.models.crew_run_create import CrewRunCreate
from app.api.crud_client.models.crew_run_metadata import CrewRunMetadata
from app.api.crud_client.models.crew_run_metadata_inputs import CrewRunMetadataInputs
from app.api.crud_client.models.http_validation_error import HTTPValidationError
from app.models.models import CrewRun, CrewRunCreateRequest
from app.services.flow.flow_service import FlowService
from config import settings


class CrewService:
    """Application service for crew operations."""

    def __init__(
        self,
        flow_service: FlowService,
    ) -> None:
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token=settings.INTERNAL_CREW_API_KEY,
            timeout=httpx.Timeout(30.0),
        )
        self.flow_service = flow_service

    async def get_required_inputs(self, crew_id: UUID, user_token: str) -> Dict[str, str]:
        """Get required inputs for a crew based on its tasks and flow dependencies."""
        try:
            crew_result = await get_crew_by_id_func.asyncio(
                crew_id=crew_id,
                client=self.crud_client,
            )
            if not crew_result:
                raise ValueError(f"Crew {crew_id} not found")
            
            if isinstance(crew_result, HTTPValidationError):
                raise ValueError(f"Validation error retrieving crew {crew_id}: {crew_result}")
        except errors.UnexpectedStatus as e:
            if e.status_code == 404:
                raise ValueError(f"Crew {crew_id} not found") from e
            raise
        
        tasks = crew_result.tasks
        if len(tasks) == 0:
            raise ValueError(f"Crew {crew_id} has no tasks")
        
        return self.flow_service.get_required_inputs(tasks)

    async def kickoff_crew_run(self, crew_run_data: CrewRunCreateRequest, user_token: str):
        """Queue a crew run in CRUD service."""
        metadata = None
        if crew_run_data.inputs:
            metadata_inputs = CrewRunMetadataInputs()
            metadata_inputs.additional_properties = crew_run_data.inputs
            metadata = CrewRunMetadata(inputs=metadata_inputs)
        
        crew_run_create = CrewRunCreate(
            crew_id=crew_run_data.crew_id,
            run_metadata=metadata,
        )
        
        response = await create_crew_run_func.asyncio_detailed(
            body=CrewRunCreateBody(crew_run_data=crew_run_create, user_token=user_token),
            client=self.crud_client,
        )

        if response.status_code != 201:
            error_msg = f"Failed to create crew run: status {response.status_code}"
            try:
                error_content = response.content.decode() if response.content else "No error details"
                error_msg += f" - {error_content}"
            except:
                pass
            raise ValueError(error_msg)

        if isinstance(response.parsed, HTTPValidationError):
            raise ValueError(f"Validation error creating crew run: {response.parsed}")

        if response.parsed is None:
            raise ValueError("Failed to create crew run: received None response")

        return CrewRun.model_validate(response.parsed.to_dict())
