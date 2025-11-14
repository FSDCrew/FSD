from fastapi import APIRouter, Depends, Path, UploadFile, File, Form
from uuid import UUID

from app.models.models import ArtifactRead, ArtifactCreate, ArtifactType, User
from app.services.artifact_service import ArtifactService
from app.dependencies import get_artifact_service, get_current_user

artifact_router = APIRouter(
    prefix="/artifact",
    tags=["artifact"],
)

@artifact_router.post(
    "/{crew_run_id}",
    status_code=201,
    response_model=ArtifactRead
)
async def create_artifact(
    file: UploadFile = File(..., description="The artifact file content."),
    artifact_type: ArtifactType = Form(..., description="The type of artifact (e.g., TEXT, IMAGE)."),
    crew_run_id: UUID = Path(..., description="Crew Run ID to associate the artifact with", example="123e4567-e89b-12d3-a456-426614174000"),
    current_user: User = Depends(get_current_user),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Create a new artifact linked to a crew run."""
    # Call the service layer with the unpacked arguments
    return await artifact_service.create_artifact(
        uploaded_file=file,
        artifact_type=artifact_type,
        crew_run_id=crew_run_id,
        user_id=current_user.id 
    )

@artifact_router.get(
    "/{artifact_id}",
    response_model=ArtifactRead
)
async def get_artifact(
    artifact_id: UUID = Path(..., description="Artifact ID to retrieve", example="123e4567-e89b-12d3-a456-426614174000"),
    current_user: User = Depends(get_current_user),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Retrieve an artifact by its ID."""
    return await artifact_service.get_artifact(artifact_id)
