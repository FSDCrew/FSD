import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

TEMP_DIR = Path(".temp")


def cleanup_temp_file(path: str) -> None:
    """Safely remove a temporary file created by this process.
    
    Args:
        path: The path to the file to remove. Must be within TEMP_DIR.
    
    Raises:
        ValueError: If the path is outside TEMP_DIR (safety check).
    """
    try:
        file_path = Path(path).resolve()
        temp_dir_abs = TEMP_DIR.resolve()
        
        file_path.relative_to(temp_dir_abs)
        
        if file_path.exists() and file_path.is_file():
            os.remove(file_path)
            logger.debug("Cleaned up temp file: %s", path)
        elif file_path.exists():
            logger.warning(
                "cleanup_temp_file: Path exists but is not a file: %s",
                path
            )
    except OSError as e:
        logger.debug("cleanup_temp_file: Could not remove %s: %s", path, e)
    except Exception as e:
        logger.warning("cleanup_temp_file: Unexpected error removing %s: %s", path, e)
