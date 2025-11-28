from fastapi import APIRouter, Depends, Path, HTTPException, status
from uuid import UUID
import io
import base64

from app.models.models import ArtifactRead, ArtifactServerCreate, User
from app.services.artifact_service import ArtifactService
from app.dependencies import get_artifact_service, get_current_user, get_crew_run_owner_id, require_internal_api_key

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
    artifact_upload: ArtifactServerCreate, 
    crew_run_id: UUID = Path(..., description="Crew Run ID to associate the artifact with", example="123e4567-e89b-12d3-a456-426614174000"),
    crew_run_owner_id: UUID = Depends(get_crew_run_owner_id),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Create a new artifact linked to a crew run (designed for server-to-server Base64 upload).
    """

    try:
        file_bytes = base64.b64decode(artifact_upload.file_content_base64)
        file_stream = io.BytesIO(file_bytes)
        
        uploaded_file = {
            'file': file_stream,
            'filename': artifact_upload.file_name, 
            'content_type': 'application/octet-stream'
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid Base64 content: {e}")

    return await artifact_service.create_artifact(
        uploaded_file=uploaded_file,
        artifact_type=artifact_upload.type,
        crew_run_id=crew_run_id,
        user_id=crew_run_owner_id
    )

@artifact_router.get(
    "/{artifact_id}",
    response_model=str
)
async def get_artifact(
    artifact_id: UUID = Path(..., description="Artifact ID to retrieve", example="123e4567-e89b-12d3-a456-426614174000"),
    # current_user: User = Depends(get_current_user),
    _auth: None = Depends(require_internal_api_key),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Retrieve an artifact by its ID."""
    return await artifact_service.get_artifact_presigned_url(artifact_id)

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
    # Optional: You could add logic here to check if 'current_user' 
    # actually owns the artifact (via crew_run -> crew -> user_id)
    # for extra security.
    
    return await artifact_service.get_artifact_presigned_url(artifact_id)