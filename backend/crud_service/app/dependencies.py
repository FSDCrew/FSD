from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional

from app.db.connection import get_session
from app.repositories.crew_repository import CrewRepository
from app.services.crew_service import CrewService
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
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
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