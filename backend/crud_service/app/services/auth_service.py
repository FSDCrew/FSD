import httpx
import logging
import time
from uuid import UUID
from app.models.models import User
from config import settings
from jose import jwt, JWTError
from typing import Any
from app.repositories.user_repository import UserRepository

if settings.jwks_url is None:
    raise ValueError("JWKS_URL is not configured. Check your environment variables")

JWKS_URL: str = settings.jwks_url
JWKS_TTL_SECONDS = 60 * 60 

_jwks_cache: list[dict[str, Any]] = []
_jwks_expires_at: float = 0.0

async def get_jwks() -> list[dict[str, Any]]:
    global _jwks_cache, _jwks_expires_at

    now = time.time()
    if _jwks_cache and now < _jwks_expires_at:
        return _jwks_cache

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(JWKS_URL)
            resp.raise_for_status()
            keys = resp.json()["keys"]
    except httpx.HTTPError as e:
        if _jwks_cache:
            logging.warning("JWKS refresh failed, using cached keys: %s", e)
            return _jwks_cache
        raise RuntimeError(f"Could not fetch JWKS: {e}") from e

    _jwks_cache = keys
    _jwks_expires_at = now + JWKS_TTL_SECONDS
    return _jwks_cache


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def _validate_token(self, token: str) -> dict:
        """Validate JWT token asynchronously."""
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            if not kid:
                raise JWTError("Missing 'kid' in token header")

            jwks = await get_jwks()
            rsa_key = next(
                (
                    {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
                    for key in jwks
                    if key["kid"] == kid
                ),
                None,
            )

            if not rsa_key:
                raise JWTError("Unable to find matching 'kid' in JWKS")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.cognito_app_client_id,
                issuer=(
                    f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
                    f"{settings.cognito_user_pool_id}"
                ),
                options={"verify_at_hash": False},
            )
            return payload

        except JWTError as e:
            logging.error(f"JWT Validation Error: {e}")
            raise

    async def _user_from_token_payload(self, payload: dict) -> User:
        """Extract user information from validated JWT payload."""
        user_sub = payload.get("sub")
        if not user_sub:
            raise JWTError("Token missing 'sub' claim")

        try:
            user_id = UUID(user_sub)
        except (ValueError, TypeError) as e:
            raise JWTError(f"Invalid user ID format: {e}") from e
        email = payload.get("email") or ""
        given_name = payload.get("given_name") or ""
        family_name = payload.get("family_name") or ""
        picture = payload.get("picture")
        name = payload.get("name") or f"{given_name} {family_name}".strip() or email

        return User(
            id=user_id,
            email=email,
            name=name,
            given_name=given_name,
            family_name=family_name,
            picture=picture,
        )

    async def get_user(self, token: str) -> User:
        payload = await self._validate_token(token)

        user_sub = payload.get("sub")
        if not user_sub:
            raise JWTError("Token missing 'sub' claim")

        try:
            user_id = UUID(user_sub)
        except (ValueError, TypeError) as e:
            raise JWTError(f"Invalid user ID format: {e}") from e

        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise JWTError("User not found in local database")

        return user
    
    async def sync_user(self, token: str) -> User:
        """Validate token and sync/create user in database."""
        payload = await self._validate_token(token)
        user_from_token = await self._user_from_token_payload(payload)
        print("#########################") # !DEBUG
        print(user_from_token)
        print("#########################")
        
        existing_user = await self.repository.get_user_by_id(user_from_token.id)
        if existing_user:
            print("#########################") # !DEBUG
            print(existing_user)
            print("#########################")
            return existing_user

        return await self.repository.create_user(
            user_id=user_from_token.id,
            email=user_from_token.email,
            given_name=user_from_token.given_name,
            family_name=user_from_token.family_name,
            picture=user_from_token.picture
        )

