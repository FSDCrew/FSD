from fastapi import APIRouter, Depends, Path
from uuid import UUID

from app.models.models import User
from app.services.artifact_service import ArtifactService
from app.dependencies import get_artifact_service, get_current_user, require_internal_api_key

artifact_router = APIRouter(
    prefix="/artifact",
    tags=["artifact"],
)

@artifact_router.get(
    "/view/{artifact_id}",
    response_model=str
)
async def get_artifact_for_user(
    artifact_id: UUID = Path(..., description="Artifact ID to retrieve"),
    # AUTH: This uses the standard User JWT check
    current_user: User = Depends(get_current_user),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Retrieve an artifact by its ID for a Frontend User.
    Authenticated via JWT (Cognito/Auth0).
    """
    
    return await artifact_service.get_artifact_presigned_url(artifact_id)
