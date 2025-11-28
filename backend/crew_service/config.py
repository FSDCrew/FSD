import logging
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

current_dir = Path(__file__).parent
env_path = ".env"

class Settings(BaseSettings):
    """
    Settings for CrewService.
    """
    INTERNAL_CREW_API_KEY: str
    CRUD_SERVICE_URL: str
        
    QUEUE_POLL_INTERVAL_SECONDS: int
    JOB_VISIBILITY_TIMEOUT_SECONDS: int
    HEARTBEAT_INTERVAL_SECONDS: int
    
    OPENAI_API_KEY: str
    
    HEADLESS: bool
    
    BRIGHT_DATA_API_KEY: str
    BRIGHT_DATA_ZONE: str

    ORSHOT_API_KEY: str
    ORSHOT_API_URL: str = "https://api.orshot.com/v1/studio/render"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings() # type: ignore


def load_agents_config() -> Dict[str, Dict[str, Any]]:
    """Load agents configuration from YAML file."""
    agents_config_path = Path(__file__).parent / "app" / "config" / "agents.yaml"
    try:
        if agents_config_path.exists():
            with open(agents_config_path, 'r') as f:
                agents_data = yaml.safe_load(f) or {}
                for key, agent_config in agents_data.items():
                    if isinstance(agent_config, dict):
                        agent_config['key'] = key
                return agents_data
        else:
            logger.warning(f"Agents config file not found: {agents_config_path}")
            return {}
    except Exception as e:
        logger.error(f"Error loading agents from YAML: {e}", exc_info=True)
        return {}


def load_tasks_and_state_fields_config() -> Dict[str, Dict[str, Any]]:
    """Load tasks configuration from YAML file."""
    tasks_config_path = Path(__file__).parent / "app" / "config" / "tasks.yaml"
    try:
        if tasks_config_path.exists():
            with open(tasks_config_path, 'r') as f:
                tasks_data = yaml.safe_load(f) or {}
                for key, task_config in tasks_data.items():
                    if isinstance(task_config, dict):
                        task_config['key'] = key
                return tasks_data
        else:
            logger.warning(f"Tasks config file not found: {tasks_config_path}")
            return {}
    except Exception as e:
        logger.error(f"Error loading tasks from YAML: {e}", exc_info=True)
        return {}


agents_config: Dict[str, Dict[str, Any]] = load_agents_config()
tasks_and_state_fields_config: Dict[str, Dict[str, Any]] = load_tasks_and_state_fields_config()

tasks_config: Dict[str, Dict[str, Any]] = tasks_and_state_fields_config.get("tasks", {})
state_fields_config: Dict[str, Dict[str, Any]] = tasks_and_state_fields_config.get("state", {}).get("fields", {})
