import sys

from loguru import logger

from config import settings

# Calculate the minimum level based on settings.debug
log_level = "DEBUG" if settings.debug else "INFO"

# Replace the default logger configuration
logger.configure(
    handlers=[
        {
            "sink": sys.stderr,
            "level": log_level,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        }
    ]
)