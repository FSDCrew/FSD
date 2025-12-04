from app.models.models import ArtifactRead, ArtifactCreate, ArtifactType
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.schemas import Artifact as ArtifactDB
from fastapi import HTTPException, status
from uuid import UUID
import uuid
from typing import Any
from config import settings
import os
import io
from botocore.client import BaseClient

PRESIGNED_URL_EXPIRATION = 3600  


class ArtifactService:
    def __init__(self, repository: ArtifactRepository, s3_client: BaseClient):
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

        db_artifact = await self.repository.create_artifact(artifact_create, crew_run_id)
        return ArtifactRead.model_validate(db_artifact)
    
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

    async def copy_artifacts_to_crew_run(
        self,
        original_crew_run_id: UUID,
        new_crew_run_id: UUID,
        user_id: UUID
    ) -> list[ArtifactRead]:
        """
        Copy all artifacts from the original crew run to the new crew run.
        
        This downloads each artifact from S3 and uploads it to a new location
        with the new crew_run_id in the path, then creates new artifact records.
        
        Args:
            original_crew_run_id: UUID of the original crew run
            new_crew_run_id: UUID of the new crew run
            user_id: UUID of the user (needed for S3 path construction)
            
        Returns:
            List of newly created ArtifactRead objects
            
        Raises:
            HTTPException: If artifacts cannot be retrieved or copied
        """
        # Get all artifacts from the original crew run
        original_artifacts = await self.repository.get_artifacts_by_crew_run_id(original_crew_run_id)
        
        if not original_artifacts:
            return []
        
        copied_artifacts = []
        
        for original_artifact in original_artifacts:
            try:
                # Download the original artifact from S3
                file_obj = io.BytesIO()
                self.s3_client.download_fileobj(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=original_artifact.object_key,
                    Fileobj=file_obj
                )
                file_obj.seek(0)
                
                # Determine file extension from original filename or object_key
                if original_artifact.file_name:
                    _, ext = os.path.splitext(original_artifact.file_name)
                else:
                    # Fallback: extract extension from object_key
                    _, ext = os.path.splitext(original_artifact.object_key)
                
                # Create new S3 key with new crew_run_id
                file_uuid = uuid.uuid4()
                new_object_key = f"artifacts/{user_id}/{new_crew_run_id}/{file_uuid}{ext}"
                
                # Determine content type based on artifact type
                content_type = "application/octet-stream"
                if original_artifact.type == ArtifactType.IMAGE:
                    content_type = "image/png"  # Default, could be improved
                elif original_artifact.type == ArtifactType.DOCUMENT:
                    content_type = "application/pdf"  # Default, could be improved
                
                # Upload to new S3 location
                self.s3_client.upload_fileobj(
                    Fileobj=file_obj,
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=new_object_key,
                    ExtraArgs={"ContentType": content_type}
                )
                
                # Create new artifact record
                artifact_create = ArtifactCreate(
                    type=original_artifact.type,
                    object_key=new_object_key,
                    file_name=original_artifact.file_name
                )
                
                db_artifact = await self.repository.create_artifact(artifact_create, new_crew_run_id)
                copied_artifacts.append(ArtifactRead.model_validate(db_artifact))
                
            except Exception as e:
                # Log error but continue with other artifacts
                # We'll let the caller handle partial failures
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to copy artifact {original_artifact.id}: {e}"
                )
        
        return copied_artifacts