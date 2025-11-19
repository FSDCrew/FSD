from fastapi import APIRouter, Depends

from app.models.models import User
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user, get_token_from_request

user_router = APIRouter(
    prefix="/user",
    tags=["user"],
)

@user_router.post(
    "/sync",
    status_code=200,
    response_model=User,
)
async def sync_user(
    token: str = Depends(get_token_from_request),
    service: AuthService = Depends(get_auth_service),
):
    """Sync/create user in database from JWT token."""
    return await service.sync_user(token)

@user_router.get(
    "/",
    status_code=200,
    response_model=User,
)
async def get_user_by_id(
    current_user: User = Depends(get_current_user),
):
    """Get user by ID. Users can only access their own profile."""
    return current_user
