from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import model_validator
from pathlib import Path

current_dir = Path(__file__).parent
env_path = ".env"

class Settings(BaseSettings):
    """
    Pydantic settings class to manage application configuration.
    It automatically validates and loads settings from environment variables or a .env file.
    """
    CREW_SERVICE_URL: str
    
    INTERNAL_CREW_API_KEY: str
    
    CRUD_DATABASE_URL: Optional[str] = None
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    # Cognito Settings
    JWKS_URL: Optional[str] = None
    COGNITO_REGION: str
    COGNITO_USER_POOL_ID: str
    COGNITO_APP_CLIENT_ID: str

    # S3 settings
    S3_BUCKET_NAME: str
    S3_REGION: str
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # CORS Origins
    FRONTEND_ORIGIN: str

    class Config:
        env_file = str(env_path) if env_path else None
        env_file_encoding = 'utf-8'

    @model_validator(mode='after')
    def construct_database_url(self):
        self.CRUD_DATABASE_URL = f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        self.JWKS_URL = f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        return self

settings = Settings() # type: ignore
