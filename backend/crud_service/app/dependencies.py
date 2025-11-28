from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Header, Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional, cast
from uuid import UUID

from app.db.connection import get_session
from app.repositories.crew_repository import CrewRepository
from app.services.crew_service import CrewService
from app.services.internal_service import InternalService
from app.services.task_service import TaskService
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.artifact_repository import ArtifactRepository
from app.services.artifact_service import ArtifactService
from app.repositories.crew_run_repository import CrewRunRepository
from app.repositories.queue_repository import QueueRepository
from app.services.crew_run_service import CrewRunService
from app.services.queue_service import QueueService
from app.services.auth_service import AuthService
from app.models.models import User

import boto3
from config import settings

auth_scheme = HTTPBearer(auto_error=False)

async def get_token_from_request(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(auth_scheme)
) -> str:
    """Get token from Authorization header or cookies."""
    if creds and creds.credentials:
        return creds.credentials
    
    # Fallback to cookies - look for Cognito ID token
    cookies = request.cookies
    for cookie_name, cookie_value in cookies.items():
        if cookie_name.endswith('.idToken') or 'idToken' in cookie_name:
            return cookie_value
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication token. Provide Authorization header or cookie."
    )


async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """Dependency to get UserRepository instance with database session."""
    return UserRepository(session)


async def get_auth_service(repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Dependency to get AuthService instance with repository injected."""
    return AuthService(repository)


async def get_current_user(
    token: str = Depends(get_token_from_request),
    service: AuthService = Depends(get_auth_service)
) -> User:
    """Dependency to get current authenticated user."""
    return await service.get_user(token)


async def get_crew_repository(session: AsyncSession = Depends(get_session)) -> CrewRepository:
    """Dependency to get CrewRepository instance with database session."""
    return CrewRepository(session)


async def get_crew_service(repository: CrewRepository = Depends(get_crew_repository)) -> CrewService:
    """Dependency to get CrewService instance with repository injected."""
    return CrewService(repository)


async def get_task_repository(session: AsyncSession = Depends(get_session)) -> TaskRepository:
    """Dependency to get TaskRepository instance with database session."""
    return TaskRepository(session)


async def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    """Dependency to get TaskService instance with repositories sharing the same session."""
    task_repository = TaskRepository(session)
    crew_repository = CrewRepository(session)
    crew_service = CrewService(crew_repository)
    return TaskService(task_repository, crew_service)


async def get_artifact_repository(session: AsyncSession = Depends(get_session)) -> ArtifactRepository:
    """Dependency to get ArtifactRepository instance with database session."""
    return ArtifactRepository(session)


async def get_artifact_service(repository: ArtifactRepository = Depends(get_artifact_repository)) -> ArtifactService:
    """Dependency to get ArtifactService instance with repository injected."""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION
    )
    return ArtifactService(repository, s3_client)


async def get_crew_run_repository(session: AsyncSession = Depends(get_session)) -> CrewRunRepository:
    """Dependency to get CrewRunRepository instance with database session."""
    return CrewRunRepository(session)


async def get_queue_repository(session: AsyncSession = Depends(get_session)) -> QueueRepository:
    """Dependency to get QueueRepository instance with database session."""
    return QueueRepository(session)


async def get_crew_run_service(
    session: AsyncSession = Depends(get_session),
    crew_service: CrewService = Depends(get_crew_service)
) -> CrewRunService:
    """Dependency to get CrewRunService instance with repositories sharing the same session."""
    crew_run_repository = CrewRunRepository(session)
    queue_repository = QueueRepository(session)
    return CrewRunService(crew_service, crew_run_repository, queue_repository, session)


async def get_queue_service(
    repository: QueueRepository = Depends(get_queue_repository)
) -> QueueService:
    """Dependency to get QueueService instance with repository injected."""
    return QueueService(repository)


async def get_internal_service(
    crew_service: CrewService = Depends(get_crew_service),
    crew_run_service: CrewRunService = Depends(get_crew_run_service)
) -> InternalService:
    """Dependency to get InternalService instance."""
    return InternalService(crew_service, crew_run_service)


async def require_internal_api_key(
    api_key_header: Optional[str] = Header(None, alias="X-Internal-Api-Key"),
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(auth_scheme),
    internal_service: InternalService = Depends(get_internal_service),
) -> None:
    """
    Ensure the caller is another internal service by validating either the
    legacy `X-Internal-Api-Key` header or an `Authorization: Bearer <token>`
    header (used by openapi-python-client's AuthenticatedClient).
    """
    api_key = api_key_header

    if not api_key and auth_creds and auth_creds.scheme.lower() == "bearer":
        api_key = auth_creds.credentials

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing internal API key",
        )

    internal_service.validate_api_key(api_key)

async def get_crew_run_owner_id(
    crew_run_id: UUID,
    _auth: None = Depends(require_internal_api_key),
    crew_run_repo: CrewRunRepository = Depends(get_crew_run_repository),
    crew_repo: CrewRepository = Depends(get_crew_repository)
) -> UUID:
    """
    Acts like 'get_current_user' but for System-to-System calls.
    """
    crew_run = await crew_run_repo.get_crew_run_by_id_internal(crew_run_id)
    if not crew_run:
        raise HTTPException(status_code=404, detail=f"Crew Run {crew_run_id} not found")
        
    # --- FIX HERE: Cast the column to a UUID to satisfy Pylance ---
    crew_id_value = cast(UUID, crew_run.crew_id)
    
    crew = await crew_repo.get_fully_loaded_crew_by_id_internal(crew_id_value)
    if not crew:
        raise HTTPException(status_code=404, detail=f"Crew {crew_id_value} not found")
    
    # Same cast here if Pylance complains about user_id
    return cast(UUID, crew.user_id)