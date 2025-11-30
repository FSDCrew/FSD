"""
Utility functions for saving artifacts to the CRUD service.
"""
import logging
from uuid import UUID
from typing import Union

from app.api.crud_client import AuthenticatedClient
from app.api.crud_client.api.artifact import (
    create_artifact_artifact_crew_run_id_post,
    get_artifact_artifact_artifact_id_get
)
from app.api.crud_client.models.artifact_server_create import ArtifactServerCreate
from app.api.crud_client.models.artifact_type import ArtifactType
from app.api.crud_client.models.artifact_read import ArtifactRead
from config import settings

logger = logging.getLogger(__name__)


def _get_crud_client() -> AuthenticatedClient:
    """Create and return an authenticated CRUD client."""
    return AuthenticatedClient(
        base_url=settings.CRUD_SERVICE_URL,
        token=settings.INTERNAL_CREW_API_KEY
    )


def save_artifact_to_crud(
    crew_run_id: str,
    file_name: str,
    file_content_base64: str,
    artifact_type: ArtifactType = ArtifactType.IMAGE
) -> Union[ArtifactRead, str]:
    """
    Save an artifact (image, document, etc.) to the CRUD service.
    
    Args:
        crew_run_id: The UUID of the current crew run (as string)
        file_name: Name of the file (e.g., "image.png", "document.docx")
        file_content_base64: Base64-encoded content of the file
        artifact_type: Type of artifact (default: ArtifactType.IMAGE)
    
    Returns:
        ArtifactRead: The created artifact object on success
        str: Error message string starting with "Error:" on failure
    
    Example:
        >>> artifact = save_artifact_to_crud(
        ...     crew_run_id="123e4567-e89b-12d3-a456-426614174000",
        ...     file_name="document.docx",
        ...     file_content_base64="UEsDBBQAAAAI..."
        ... )
        >>> if isinstance(artifact, ArtifactRead):
        ...     print(f"Artifact saved with ID: {artifact.id}")
    """
    try:
        crud_client = _get_crud_client()
        
        # Create artifact body
        artifact_body = ArtifactServerCreate(
            type_=artifact_type,
            file_name=file_name,
            file_content_base64=file_content_base64
        )
        
        # Create artifact in CRUD service
        create_result = create_artifact_artifact_crew_run_id_post.sync(
            crew_run_id=UUID(crew_run_id),
            client=crud_client,
            body=artifact_body
        )
        
        # Check if creation was successful
        if not create_result:
            error_msg = "Error: Failed to save artifact to CRUD service (no result returned)."
            logger.error(error_msg)
            return error_msg
        
        if not isinstance(create_result, ArtifactRead):
            error_msg = f"Error: Unexpected result type when saving artifact: {type(create_result)}"
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"Successfully saved artifact {file_name} for crew run {crew_run_id}")
        return create_result
        
    except ValueError as e:
        error_msg = f"Error: Invalid UUID format for crew_run_id: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error: Failed to save artifact to CRUD service: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def get_artifact_s3_url(artifact_id: UUID, crew_run_id: str = None) -> str:
    """
    Get the S3 URL for an existing artifact.
    
    Args:
        artifact_id: The UUID of the artifact
        crew_run_id: Optional crew run ID for logging purposes
    
    Returns:
        str: The S3 URL of the artifact, or an error message string starting with "Error:"
    
    Example:
        >>> s3_url = get_artifact_s3_url(
        ...     artifact_id=UUID("123e4567-e89b-12d3-a456-426614174000")
        ... )
        >>> print(s3_url)
        "https://s3.amazonaws.com/bucket/artifact-id.png"
    """
    try:
        crud_client = _get_crud_client()
        
        s3_url = get_artifact_artifact_artifact_id_get.sync(
            artifact_id=artifact_id,
            client=crud_client
        )
        
        if not s3_url:
            error_msg = "Error: Failed to obtain S3 URL from artifact."
            logger.error(error_msg)
            return error_msg
        
        log_context = f" for crew run {crew_run_id}" if crew_run_id else ""
        logger.info(f"Successfully retrieved S3 URL for artifact {artifact_id}{log_context}")
        return str(s3_url)
        
    except Exception as e:
        error_msg = f"Error: Failed to get artifact S3 URL: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

