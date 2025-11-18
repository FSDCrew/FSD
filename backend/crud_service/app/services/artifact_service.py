from app.models.models import ArtifactRead, ArtifactCreate, ArtifactType
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.schemas import Artifact as ArtifactDB
from fastapi import HTTPException, status
from uuid import UUID
import uuid
from typing import Any
from config import settings
import os

PRESIGNED_URL_EXPIRATION = 3600  


class ArtifactService:
    def __init__(self, repository: ArtifactRepository, s3_client: Any):
        self.repository = repository
        self.s3_client = s3_client
        

    async def create_artifact(
        self, 
        uploaded_file: Any,
        artifact_type: ArtifactType,
        crew_run_id: UUID, 
        user_id: UUID
    ) -> ArtifactRead:
        """
        1. Validate access.
        2. Upload to S3 to get object_key and file_name.
        3. Create the database record.
        """

        object_key, file_name = self._upload_content_to_s3(
            uploaded_file=uploaded_file, 
            crew_run_id=crew_run_id, 
            user_id=user_id, 
            artifact_type=artifact_type
        )

        artifact_create = ArtifactCreate(
            type=artifact_type,
            object_key=object_key,
            file_name=file_name
        )

        return await self.repository.create_artifact(artifact_create, crew_run_id)
    
    async def get_artifact_presigned_url(self, artifact_id: UUID) -> str:
        """Retrieve an artifact by its ID and return a presigned S3 URL."""
        db_artifact = await self.repository.get_artifact(artifact_id)

        if db_artifact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact with ID {artifact_id} not found."
            )

        # Generate presigned URL
        presigned_url = self._get_presigned_url(db_artifact)
        return presigned_url

    def _upload_content_to_s3(self, uploaded_file: Any, crew_run_id: UUID, user_id: UUID, artifact_type: ArtifactType) -> tuple[str, str]:
        """
        Uploads a file stream to S3, dynamically setting the file extension 
        and content type based on the uploaded file metadata.
        
        Assumes 'uploaded_file' is a file-like object (e.g., FastAPI's UploadFile) 
        with attributes: .filename, .content_type, and .file (the content stream).
        """

        # May need come back to this. Currently allows for artifact upload via bytes and UploadFile
        if isinstance(uploaded_file, dict):
            original_filename = uploaded_file.get('filename', '')
            content_type = uploaded_file.get('content_type', 'application/octet-stream')
            file_stream = uploaded_file.get('file', uploaded_file)
        else:
            # Fallback to attribute access for the old UploadFile flow
            original_filename = getattr(uploaded_file, 'filename', '')
            content_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')
            file_stream = getattr(uploaded_file, 'file', uploaded_file)
        
        if not original_filename:
             raise HTTPException(status_code=400, detail="Uploaded file is missing a filename.")

        _, ext = os.path.splitext(original_filename)
        
        # Create a unique S3 key: artifacts/{user_id}/{crew_run_id}/file_uuid.<ext>
        file_uuid = uuid.uuid4()
        object_key = f"artifacts/{user_id}/{crew_run_id}/{file_uuid}{ext}"

        try:
            self.s3_client.upload_fileobj(
                Fileobj=file_stream,
                Bucket=settings.S3_BUCKET_NAME, 
                Key=object_key, 
                ExtraArgs={"ContentType": content_type}
            )
            return object_key, original_filename
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload failed: {e}"
            )
        
    def _get_presigned_url(self, db_artifact: ArtifactDB) -> str:
        """Generate a presigned URL for accessing the S3 object."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.S3_BUCKET_NAME, 
                    'Key': db_artifact.object_key,
                    'ResponseContentDisposition': f'inline; filename="{db_artifact.file_name}"'
                    },
                ExpiresIn=PRESIGNED_URL_EXPIRATION
            )
            return url
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {e}"
            )