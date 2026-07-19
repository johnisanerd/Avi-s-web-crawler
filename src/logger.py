import logging
import sys
from pathlib import Path
from src.constants import LOGS_DIR


def get_logger(name: str = "lead_gen") -> logging.Logger:
    """
    Retrieves or configures a centralized logger instance.
    Configures console and file logging. Automatically creates the logs directory
    if it does not exist, uses UTF-8 encoding for file logging, and remains
    idempotent by avoiding duplicate handlers if requested multiple times.

    Args:
        name: Name of the logger to retrieve.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Idempotent check: prevent adding duplicate handlers if logger is already configured
    if logger.handlers:
        return logger

    # Format: Timestamp [Log Level] Logger Name: Message
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Console Handler (writes to stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (writes to logs/ directory with UTF-8 encoding)
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file_path = LOGS_DIR / f"{name}.log"
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to prevent startup crashes if directory creation or file writing fails
        logger.warning(f"Could not initialize file logging handler: {e}")

    # Disable logger propagation to prevent duplicate logs in root logger
    logger.propagate = False

    return logger
