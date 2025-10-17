from pydantic_settings import BaseSettings
from typing import Dict, Any
from pathlib import Path

current_dir = Path(__file__).parent

project_root = current_dir.parent.parent
env_path = project_root / ".env"

class Settings(BaseSettings):
    """
    Pydantic settings class to manage application configuration.
    It automatically validates and loads settings from environment variables or a .env file.
    """
    
    # Database settings
    # Pydantic will ensure this is a string. If the env var is missing, it will raise an error.
    crud_database_url: str
    
    # Static config values can be set directly with their types
    sqlalchemy_track_modifications: bool = False
    sqlalchemy_engine_options: Dict[str, Any] = {'pool_recycle': 299}

    # S3 settings
    s3_bucket_name: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str

    class Config:
        # This tells Pydantic to look for a .env file to load the settings from,
        # replacing the need for load_dotenv().
        env_file = env_path
        env_file_encoding = 'utf-8'

# Create a single instance of the Settings class that can be imported
# by other parts of your application.
settings = Settings()