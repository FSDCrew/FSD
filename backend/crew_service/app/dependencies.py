from fastapi import Depends, Request
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.crew_service import CrewService
from app.services.flow.flow_service import FlowService

auth_scheme = HTTPBearer(auto_error=False)

async def get_user_token(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(auth_scheme)
) -> str:
    """Extract user token from Authorization header or cookies."""
    if creds and creds.credentials:
        return creds.credentials
    
    # Fallback to cookies - look for Cognito ID token
    cookies = request.cookies
    for cookie_name, cookie_value in cookies.items():
        if cookie_name.endswith('.idToken') or 'idToken' in cookie_name:
            return cookie_value
    
    raise HTTPException(
        status_code=401,
        detail="Missing authentication token. Provide Authorization header or cookie."
    )

def get_flow_service() -> FlowService:
    """Dependency to get FlowService instance."""
    return FlowService()

def get_crew_service(flow_service: FlowService = Depends(get_flow_service)) -> CrewService:
    """Dependency to get CrewService instance."""
    return CrewService(flow_service=flow_service)