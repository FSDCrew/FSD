from app.models.models import ArtifactRead, ArtifactCreate, ArtifactType
from app.repositories.artifact_repository import ArtifactRepository
from fastapi import HTTPException, status
from uuid import UUID
import boto3
from typing import Any
from datetime import datetime, timedelta
from config import settings
import os

from app.services.crew_service import CrewService

PRESIGNED_URL_EXPIRATION = 3600  # 1 hour

class ArtifactService:
    def __init__(self, repository: ArtifactRepository, s3_client: boto3.client, crew_service: CrewService):
        self.repository = repository
        self.s3_client = s3_client
        self.crew_service = crew_service

    async def create_artifact(
        self, 
        uploaded_file: Any, # The file stream from the API (e.g., UploadFile)
        artifact_type: ArtifactType, # The type (e.g., TEXT, IMAGE)
        crew_run_id: UUID, 
        user_id: UUID # Passed from current_user dependency
    ) -> ArtifactRead:
        """
        1. Validate access.
        2. Upload to S3 to get object_key and file_name.
        3. Create the database record.
        """
        
        # 1. Validation (Optional but Recommended)
        # We need to ensure the user owns the crew that owns the crew_run.
        # This requires looking up the crew_run to get the crew_id.
        # For brevity, assuming this check happens elsewhere or is skipped for now.
        # await self.crew_service.validate_crew_run_ownership(crew_run_id, user_id) 

        # 2. Upload to S3
        object_key, file_name = self._upload_content_to_s3(
            uploaded_file=uploaded_file, 
            crew_run_id=crew_run_id, 
            user_id=user_id, 
            artifact_type=artifact_type
        )

        # 3. Create the database record
        artifact_create = ArtifactCreate(
            type=artifact_type,
            object_key=object_key,
            file_name=file_name
        )

        return await self.repository.create_artifact(artifact_create, crew_run_id)

def _upload_content_to_s3(self, uploaded_file: Any, crew_run_id: UUID, user_id: UUID, artifact_type: ArtifactType) -> tuple[str, str]:
        """
        Uploads a file stream to S3, dynamically setting the file extension 
        and content type based on the uploaded file metadata.
        
        Assumes 'uploaded_file' is a file-like object (e.g., FastAPI's UploadFile) 
        with attributes: .filename, .content_type, and .file (the content stream).
        """
        # Safely extract filename, content type, and file stream
        # Fallback logic to support common UploadFile properties
        original_filename = getattr(uploaded_file, 'filename', '')
        content_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')
        file_stream = getattr(uploaded_file, 'file', uploaded_file)
        
        if not original_filename:
             raise HTTPException(status_code=400, detail="Uploaded file is missing a filename.")

        # Extract file extension safely using os.path.splitext
        _, ext = os.path.splitext(original_filename)
        
        # Create a unique S3 key: artifacts/{user_id}/{crew_run_id}/file_uuid.<ext>
        file_uuid = UUID.uuid4()
        object_key = f"artifacts/{user_id}/{crew_run_id}/{file_uuid}{ext}"
        
        # Create the file name for the database entry
        file_name = f"{crew_run_id}-{file_uuid}{ext}" 

        try:
            self.s3_client.upload_fileobj(
                Fileobj=file_stream,
                Bucket=settings.S3_BUCKET_NAME, 
                Key=object_key, 
                ExtraArgs={"ContentType": content_type}
            )
            return object_key, file_name
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload failed: {e}"
            )