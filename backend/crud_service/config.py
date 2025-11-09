from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional
from pydantic import model_validator
from pathlib import Path
import os

current_dir = Path(__file__).parent
env_path = ".env"

class Settings(BaseSettings):
    """
    Pydantic settings class to manage application configuration.
    It automatically validates and loads settings from environment variables or a .env file.
    """
    crud_database_url: Optional[str] = None
    db_host: str
    db_port: str
    db_name: str
    db_user: str
    db_password: str

    # S3 settings
    s3_bucket_name: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str

    class Config:
        env_file = str(env_path) if env_path else None
        env_file_encoding = 'utf-8'

    @model_validator(mode='after')
    def construct_database_url(self):
        self.crud_database_url = f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return self

settings = Settings() # type: ignore