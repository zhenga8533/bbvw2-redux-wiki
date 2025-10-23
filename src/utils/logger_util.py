"""
Modern logging utilities for the wiki generator.

Provides structured logging with:
- Per-module loggers using standard Python logging
- Rich console output with colors and formatting
- Rotating file handlers to prevent unbounded growth
- JSON structured logging support
- Configuration via config.json or environment variables
- Context managers for operation tracking
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
import os


def _load_config():
    """Load configuration from config.json, with environment variable overrides."""
    config_path = Path(__file__).parent.parent / "config.json"
    defaults = {
        "level": "INFO",
        "format": "text",
        "log_dir": "logs",
        "max_log_size_mb": 10,
        "backup_count": 5,
        "console_colors": True,
        "clear_on_run": False,
    }

    # Try to load from config file
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                logging_config = config.get("logging", {})
                defaults.update(logging_config)
        except (json.JSONDecodeError, IOError):
            pass  # Fall back to defaults

    # Environment variables override config file
    clear_on_run_env = os.getenv("WIKI_CLEAR_ON_RUN")
    if clear_on_run_env is not None:
        clear_on_run = clear_on_run_env.lower() in ("true", "1", "yes")
    else:
        clear_on_run = defaults.get("clear_on_run", False)

    return {
        "log_dir": os.getenv("WIKI_LOG_DIR", defaults.get("log_dir", "logs")),
        "level": os.getenv("WIKI_LOG_LEVEL", defaults.get("level", "INFO")).upper(),
        "format": os.getenv("WIKI_LOG_FORMAT", defaults.get("format", "text")),
        "max_log_size_mb": int(os.getenv("WIKI_MAX_LOG_SIZE_MB", defaults.get("max_log_size_mb", 10))),
        "backup_count": int(os.getenv("WIKI_LOG_BACKUP_COUNT", defaults.get("backup_count", 5))),
        "console_colors": defaults.get("console_colors", True),
        "clear_on_run": clear_on_run,
    }


# Global configuration (loaded once)
_config = _load_config()
LOG_DIR = Path(_config["log_dir"])
LOG_LEVEL = _config["level"]
LOG_FORMAT_JSON = _config["format"] == "json"
MAX_LOG_SIZE = _config["max_log_size_mb"] * 1024 * 1024  # Convert MB to bytes
BACKUP_COUNT = _config["backup_count"]
CONSOLE_COLORS = _config["console_colors"]
CLEAR_ON_RUN = _config["clear_on_run"]

# Clear entire logs directory if configured (before any loggers are initialized)
if CLEAR_ON_RUN and LOG_DIR.exists():
    import shutil
    try:
        shutil.rmtree(LOG_DIR)
    except OSError:
        pass  # Ignore if directory is locked or can't be deleted

# Standard fields that are part of every LogRecord instance
# These fields are excluded when adding extra fields to JSON logs
# See: https://docs.python.org/3/library/logging.html#logrecord-attributes
_STANDARD_LOG_RECORD_FIELDS = frozenset([
    "name",
    "msg",
    "args",
    "created",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "thread",
    "threadName",
    "exc_info",
    "exc_text",
    "stack_info",
])


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the record (excluding standard LogRecord fields)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_LOG_RECORD_FIELDS:
                log_data[key] = value

        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output."""
        # Create a copy to avoid modifying the original record
        record_copy = logging.makeLogRecord(record.__dict__)

        log_color = self.COLORS.get(record_copy.levelname, self.RESET)

        # Color the level name on the copy
        record_copy.levelname = f"{log_color}{record_copy.levelname}{self.RESET}"

        # Format the message using the copy
        formatted = super().format(record_copy)

        return formatted


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.

    Args:
        name: Logger name (typically __name__ from calling module)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional specific log file name (without path)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.warning("Missing optional field", extra={"field": "description"})
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        return logger

    # Set log level
    log_level = getattr(logging, level or LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Console handler with optional colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if LOG_FORMAT_JSON:
        console_formatter = JSONFormatter()
    else:
        if CONSOLE_COLORS:
            console_formatter = ColoredConsoleFormatter(
                fmt="%(levelname)s - %(name)s - %(message)s",
                datefmt="%H:%M:%S",
            )
        else:
            console_formatter = logging.Formatter(
                fmt="%(levelname)s - %(name)s - %(message)s",
                datefmt="%H:%M:%S",
            )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    if log_file is None:
        # Use module-specific log file with directory structure
        # Remove 'src.' prefix if present and create subdirectories
        module_path = name
        if module_path.startswith('src.'):
            module_path = module_path[4:]  # Remove 'src.' prefix

        # Split into directory components and filename
        parts = module_path.split('.')
        if len(parts) > 1:
            # Create subdirectories for nested modules
            subdir = LOG_DIR / Path(*parts[:-1])
            subdir.mkdir(parents=True, exist_ok=True)
            log_file = str(Path(*parts[:-1]) / f"{parts[-1]}.log")
        else:
            log_file = f"{module_path}.log"

    file_path = LOG_DIR / log_file

    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)

    if LOG_FORMAT_JSON:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the given name.

    This is the recommended way to get a logger in your modules:

    Example:
        >>> from src.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process")

    Args:
        name: Logger name (use __name__ for automatic module naming)

    Returns:
        Logger instance
    """
    return setup_logger(name)


class LogContext:
    """
    Context manager for tracking operations with automatic success/failure logging.

    Example:
        >>> logger = get_logger(__name__)
        >>> with LogContext(logger, "parsing evolution data"):
        ...     # Your code here
        ...     process_data()
        # Automatically logs success or failure with timing
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        level: int = logging.INFO,
    ):
        """
        Initialize log context.

        Args:
            logger: Logger instance to use
            operation: Description of the operation
            level: Log level for success messages
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None

    def __enter__(self):
        """Enter the context."""
        self.start_time = datetime.now()
        self.logger.log(self.level, f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and log completion or failure."""
        if self.start_time is not None:
            duration = datetime.now() - self.start_time
            duration_ms = duration.total_seconds() * 1000
        else:
            duration_ms = None

        if exc_type is None:
            self.logger.log(
                self.level,
                f"Completed {self.operation}",
                extra={"duration_ms": duration_ms},
            )
        else:
            self.logger.error(
                f"Failed {self.operation}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={"duration_ms": duration_ms},
            )

        # Don't suppress exceptions
        return False


# Convenience function for quick setup
def configure_logging(level: Optional[str] = None):
    """
    Configure root logger with default settings.

    This is optional - individual modules can use get_logger() directly.

    Args:
        level: Override the default log level
    """
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers.clear()

    # Set up with new configuration
    setup_logger("root", level=level)
