from fastapi import Path
from pydantic_settings import BaseSettings

current_dir = Path(__file__).parent
env_path = ".env"

class Settings(BaseSettings):
    """
    Settings for CrewService.
    """
    CRUD_SERVICE_URL: str
        
    QUEUE_POLL_INTERVAL_SECONDS: int
    JOB_VISIBILITY_TIMEOUT_SECONDS: int
    HEARTBEAT_INTERVAL_SECONDS: int
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings() # type: ignore
