import os
import logging
from logging.handlers import RotatingFileHandler

# Create logger
logger = logging.getLogger("elo_bot")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File Handler (Rotating)
file_handler = RotatingFileHandler("elo_bot.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
file_handler.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

__all__ = ["logger"]
