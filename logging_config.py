import logging
from logging.handlers import RotatingFileHandler
from .config import settings

# Create logger
logger = logging.getLogger("elo_bot")
logger.setLevel(settings.log_level.upper())

# Formatter with timestamp, level, module, line number
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler with rotation (5 MB per file, keep 5 backups)
file_handler = RotatingFileHandler(
    settings.log_file, maxBytes=5 * 1024 * 1024, backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Prevent log propagation to root logger
logger.propagate = False

__all__ = ["logger"]
