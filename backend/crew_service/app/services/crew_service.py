from uuid import UUID
import httpx

from app.api.crud_client import AuthenticatedClient
from app.api.crud_client.api.internal import (
    create_crew_run_internal_internal_crew_run_create_post as create_crew_run_func,
    get_crew_by_id_internal_crew_crew_id_get as get_crew_by_id_func,
)
from app.api.crud_client.models.body_create_crew_run_internal_internal_crew_run_create_post import (
    BodyCreateCrewRunInternalInternalCrewRunCreatePost as CrewRunCreateBody,
)
from app.api.crud_client.models.crew_run_create import CrewRunCreate
from app.api.crud_client.models.http_validation_error import HTTPValidationError
from app.models.models import CrewRun, CrewRunCreateRequest
from config import settings


class CrewService:
    """Application service for crew operations."""

    def __init__(
        self,
    ) -> None:
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token=settings.INTERNAL_CREW_API_KEY,
            timeout=httpx.Timeout(30.0),
        )

    async def kickoff_crew_run(self, crew_run_data: CrewRunCreateRequest, user_token: str):
        """Kick off a crew run via the CRUD service."""
        response = await create_crew_run_func.asyncio_detailed(
            body=CrewRunCreateBody(crew_run_data=CrewRunCreate(crew_id=crew_run_data.crew_id), user_token=user_token),
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
