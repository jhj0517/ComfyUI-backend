import logging
import sys
from typing import Optional

def get_logger(name: str = "ComfyUI-fastapi.app") -> logging.Logger:
    """
    Set up logger.
    """
    logger = logging.getLogger(name)
    return logger

logger = get_logger("ComfyUI-fastapi.app") 