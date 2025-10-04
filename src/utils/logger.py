"""
Logger utility for the wiki generator.
"""

import logging
from pathlib import Path


def setup_logger(name: str, file_path: str):
    """
    Set up a logger that logs to a file named after the calling script.

    Args:
        name: Logger name (typically __name__)
        file_path: Path to the calling script (typically __file__)

    Returns:
        Logger instance configured for both file and console output

    Note:
        Logs are reset on each run (file mode='w')
    """
    log_filename = f"{Path(file_path).stem}.log"
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / log_filename

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    # Console handler
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(console_formatter)
    logger.addHandler(c_handler)

    # File handler (overwrites the file on each run)
    f_handler = logging.FileHandler(log_file, mode="w")
    f_handler.setFormatter(file_formatter)
    logger.addHandler(f_handler)

    return logger
