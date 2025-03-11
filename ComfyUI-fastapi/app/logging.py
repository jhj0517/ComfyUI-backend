import logging
import sys
from typing import Optional

def get_logger(name: str = "backend.app") -> logging.Logger:
    """
    Set up logger.
    """
    logger = logging.getLogger(name)
    return logger

logger = get_logger("backend.app") 