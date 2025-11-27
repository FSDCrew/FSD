from uuid import UUID
from fastapi import HTTPException
from app.models.models import CrewRead, CrewRunRead
from app.services.crew_service import CrewService
from app.services.crew_run_service import CrewRunService
from config import settings


class InternalService:
    def __init__(self, crew_service: CrewService, crew_run_service: CrewRunService):
        self.crew_service = crew_service
        self.crew_run_service = crew_run_service

    def validate_api_key(self, api_key: str) -> bool:
        """Validate the API key."""
        if api_key == settings.INTERNAL_CREW_API_KEY:
            return True
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    async def get_fully_loaded_crew_by_id(self, crew_id: UUID) -> CrewRead:
        """Get a single crew by ID."""
        return await self.crew_service.get_fully_loaded_crew_by_id_internal(crew_id)
    
    async def get_crew_run_by_id(self, crew_run_id: UUID) -> CrewRunRead:
        """Get a single crew run by ID for internal use."""
        return await self.crew_run_service.get_crew_run_by_id_internal(crew_run_id)