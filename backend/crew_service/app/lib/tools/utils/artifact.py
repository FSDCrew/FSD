import logging
from dataclasses import dataclass
from typing import Optional, Union
from uuid import UUID

from app.api.crud_client import AuthenticatedClient
from app.api.crud_client.api.artifact import (
    get_artifact_artifact_artifact_id_get,
)
from app.api.crud_client.api.internal import create_artifact_internal_internal_artifact_crew_run_id_post as create_artifact_func
from app.api.crud_client.models.artifact_server_create import ArtifactServerCreate
from app.api.crud_client.models.artifact_type import ArtifactType
from app.api.crud_client.models.artifact_read import ArtifactRead
from config import settings

logger = logging.getLogger(__name__)


def _get_crud_client() -> AuthenticatedClient:
    """Factory for the default authenticated CRUD client.

    This keeps the wiring to settings in a single place so that the rest of the
    module can depend on the AuthenticatedClient abstraction instead.
    """
    return AuthenticatedClient(
        base_url=settings.CRUD_SERVICE_URL,
        token=settings.INTERNAL_CREW_API_KEY,
    )


@dataclass
class ArtifactSaveResult:
    """Result of attempting to save an artifact.

    Attributes:
        artifact: The created artifact on success, otherwise ``None``.
        error: A human-readable error message starting with ``"Error:"`` on
            failure, otherwise ``None``.
    """
    artifact: Optional[ArtifactRead] = None
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None


@dataclass
class ArtifactS3UrlResult:
    """Result of attempting to resolve an artifact's S3 URL.

    Attributes:
        url: The S3 URL on success, otherwise ``None``.
        error: A human-readable error message starting with ``"Error:"`` on
            failure, otherwise ``None``.
    """
    url: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None


class ArtifactService:
    """Service for CRUD artifact operations.

    This class encapsulates the dependency on :class:`AuthenticatedClient`
    so it can be injected (for example in tests) instead of being constructed
    implicitly inside every function.
    """

    def __init__(self, client: AuthenticatedClient) -> None:
        self._client = client

    def save_artifact(
        self,
        crew_run_id: str,
        file_name: str,
        file_content_base64: str,
        artifact_type: ArtifactType = ArtifactType.IMAGE,
    ) -> ArtifactSaveResult:
        """Save an artifact (image, document, etc.) to the CRUD service.

        This is the structured, Dependency-Inversion-friendly version of
        :func:`save_artifact_to_crud`.
        """
        try:
            artifact_body = ArtifactServerCreate(
                type_=artifact_type,
                file_name=file_name,
                file_content_base64=file_content_base64,
            )

            create_result = create_artifact_func.sync(
                crew_run_id=UUID(crew_run_id),
                client=self._client,
                body=artifact_body,
            )

            if not create_result:
                error_msg = (
                    "Error: Failed to save artifact to CRUD service "
                    "(no result returned)."
                )
                logger.error(error_msg)
                return ArtifactSaveResult(error=error_msg)

            if not isinstance(create_result, ArtifactRead):
                error_msg = (
                    "Error: Unexpected result type when saving artifact: "
                    f"{type(create_result)}"
                )
                logger.error(error_msg)
                return ArtifactSaveResult(error=error_msg)

            logger.info(
                "Successfully saved artifact %s for crew run %s",
                file_name,
                crew_run_id,
            )
            return ArtifactSaveResult(artifact=create_result)

        except ValueError as e:
            error_msg = "Error: Invalid UUID format for crew_run_id: {0}".format(e)
            logger.error(error_msg)
            return ArtifactSaveResult(error=error_msg)
        except Exception as e:  # pragma: no cover - defensive logging
            error_msg = "Error: Failed to save artifact to CRUD service: {0}".format(e)
            logger.error(error_msg, exc_info=True)
            return ArtifactSaveResult(error=error_msg)

    def get_artifact_s3_url(
        self,
        artifact_id: UUID,
        crew_run_id: Optional[str] = None,
    ) -> ArtifactS3UrlResult:
        """Get the S3 URL for an existing artifact.

        This is the structured, Dependency-Inversion-friendly version of
        :func:`get_artifact_s3_url`.
        """
        try:
            s3_url = get_artifact_artifact_artifact_id_get.sync(
                artifact_id=artifact_id,
                client=self._client,
            )

            if not s3_url:
                error_msg = "Error: Failed to obtain S3 URL from artifact."
                logger.error(error_msg)
                return ArtifactS3UrlResult(error=error_msg)

            log_context = " for crew run {0}".format(crew_run_id) if crew_run_id else ""
            logger.info(
                "Successfully retrieved S3 URL for artifact %s%s",
                artifact_id,
                log_context,
            )
            return ArtifactS3UrlResult(url=str(s3_url))

        except Exception as e:  # pragma: no cover - defensive logging
            error_msg = "Error: Failed to get artifact S3 URL: {0}".format(e)
            logger.error(error_msg, exc_info=True)
            return ArtifactS3UrlResult(error=error_msg)


def get_default_artifact_service(
    client: Optional[AuthenticatedClient] = None,
) -> ArtifactService:
    """Return an :class:`ArtifactService` using the given client or the default.

    High-level code can call this helper and still benefit from dependency
    inversion by passing a custom client (e.g. a test double).
    """
    return ArtifactService(client or _get_crud_client())
