"""
Base parser class for processing documentation files and generating markdown output.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from ..utils.logger import get_logger
import json
import re

logger = get_logger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for all documentation parsers.

    All parsers should:
    - Read files from data/documentation/
    - Generate markdown files to docs/ (or subdirectories)
    - Optionally update data files in data/documentation/parsed/

    Configuration:
    - Use set_project_root() to override the default project root for testing

    Thread Safety:
    ⚠️  WARNING: This class is NOT thread-safe!
    - The class-level _project_root is shared across all parser instances
    - Concurrent access from multiple threads can lead to race conditions
    - DO NOT use parsers concurrently from multiple threads without external
      synchronization (e.g., threading.Lock)
    - If thread safety is required, implement proper locking around:
      * Project root changes (set_project_root())
      * File operations (parse(), save_markdown())
    """

    # Class-level project root (configurable for testing)
    _project_root: Optional[Path] = None

    @classmethod
    def set_project_root(cls, path: Path) -> None:
        """
        Set a custom project root path for all parsers.

        This is useful for testing or when running from a non-standard location.

        Args:
            path: The new project root path
        """
        old_root = cls._project_root
        cls._project_root = path
        logger.info(f"Project root changed from {old_root} to {path}")

    @classmethod
    def get_project_root(cls) -> Path:
        """
        Get the current project root path.

        Returns:
            Path: The project root path (either custom or default)
        """
        if cls._project_root is None:
            cls._project_root = Path(__file__).parent.parent.parent
        return cls._project_root

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """
        Initialize the parser.

        Args:
            input_file: Path to the input file (relative to data/documentation/)
            output_dir: Directory where markdown files will be generated (default: docs)
        """
        # Initialize instance variables to avoid shared state
        self._markdown = ""

        # Set up logger for this parser instance
        self.logger = get_logger(self.__class__.__module__)

        # Set up paths
        self.project_root = self.get_project_root()
        self.input_path = self.project_root / "data" / "documentation" / input_file
        self.output_file = Path(input_file).stem.replace(" ", "_").lower()

        self.output_dir = self.project_root / output_dir
        self.output_path = self.output_dir / (self.output_file + ".md")

        self.logger.debug(
            f"Initializing parser: {self.__class__.__name__}",
            extra={
                "input_file": str(self.input_path),
                "output_path": str(self.output_path),
            },
        )

        # Validate input file exists
        if not self.input_path.exists():
            self.logger.error(f"Input file not found: {self.input_path}")
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Output directory ready: {self.output_dir}")

    @abstractmethod
    def parse(self) -> None:
        """
        Parse the input file and extract data.

        This method should populate:
        - self._markdown: str containing the generated markdown

        Returns:
            None
        """
        pass

    def read_input_lines(self) -> list[str]:
        """Read and return the input file as lines, skipping empty lines and skip patterns."""
        skip_patterns = [r"^=+$"]

        self.logger.debug(f"Reading input file: {self.input_path}")
        try:
            # Read lines from the input file
            with self.input_path.open("r", encoding="utf-8") as f:
                lines = [line.strip() for line in f]
        except (OSError, IOError) as e:
            self.logger.error(f"Error reading input file {self.input_path}: {e}", exc_info=True)
            raise

        # Apply skip patterns
        filtered_lines = [
            line
            for line in lines
            if not any(re.fullmatch(pattern, line) for pattern in skip_patterns)
        ]

        self.logger.debug(
            f"Read {len(lines)} lines, filtered to {len(filtered_lines)} lines"
        )
        return filtered_lines

    def save_markdown(self, content: str) -> Optional[Path]:
        """
        Save markdown content to the output directory.

        Args:
            content: Markdown content to save

        Returns:
            Path: Path to the saved file
        """
        if not content:
            self.logger.warning("No content to save for markdown.")
            return None
        self.output_path.write_text(content, encoding="utf-8")
        self.logger.info(f"Saved markdown to {self.output_path}")
        return self.output_path

    def run(self) -> Optional[Path]:
        """
        Execute the full parsing pipeline.

        Returns:
            Path: Path to the saved markdown file
        """
        self.logger.info(f"Starting parse of {self.input_path}")

        # Parse input file
        self.parse()

        # Optionally save markdown
        markdown_path = self.save_markdown(self._markdown)

        self.logger.info("Parsing complete")
        return markdown_path
