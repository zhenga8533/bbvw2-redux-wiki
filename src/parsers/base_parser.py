"""
Base parser class for processing documentation files and generating markdown output.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from ..utils.logger import get_logger
import json
import re


class BaseParser(ABC):
    """
    Abstract base class for all documentation parsers.

    All parsers should:
    - Read files from data/documentation/
    - Generate markdown files to docs/ (or subdirectories)
    - Optionally update data files in data/documentation/parsed/
    """

    _markdown = ""
    _parsed_data: Dict[str, Any] = {}

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """
        Initialize the parser.

        Args:
            input_file: Path to the input file (relative to data/documentation/)
            output_dir: Directory where markdown files will be generated (default: docs)
        """
        # Set up logger for this parser instance
        self.logger = get_logger(self.__class__.__module__)

        # Set up paths
        self.project_root = Path(__file__).parent.parent.parent
        self.input_path = self.project_root / "data" / "documentation" / input_file
        self.output_file = Path(input_file).stem.replace(" ", "_").lower()

        self.output_dir = self.project_root / output_dir
        self.output_path = self.output_dir / (self.output_file + ".md")

        self.change_log_dir = self.project_root / "logs" / "changes"
        self.change_log_path = self.change_log_dir / (self.output_file + ".json")

        # Validate input file exists
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.change_log_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def parse(self) -> None:
        """
        Parse the input file and extract data.

        Returns:
            tuple: (markdown_content, parsed_data)
                - markdown_content: str containing the generated markdown
                - parsed_data: Dict containing structured data extracted from the input
        """
        pass

    def read_input_lines(self) -> list[str]:
        """Read and return the input file as lines, skipping empty lines and skip patterns."""
        skip_patterns = [r"^=+$"]

        # Read lines from the input file
        with self.input_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f]

        # Apply skip patterns
        filtered_lines = [
            line
            for line in lines
            if not any(re.fullmatch(pattern, line) for pattern in skip_patterns)
        ]

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

    def save_change_log(self, data: Dict[str, Any]) -> Optional[Path]:
        """
        Save parsed data to a file (JSON, YAML, etc.).

        Args:
            data: Data to save

        Returns:
            Path: Path to the saved file, or None if no change_log_dir is set
        """
        if not data:
            self.logger.warning("No data to save for change log.")
            return None
        self.change_log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.logger.info(f"Saved parsed data to {self.change_log_path}")
        return self.change_log_path

    def run(self) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Execute the full parsing pipeline.

        Returns:
            tuple: (markdown_path, data_path)
                - markdown_path: Path to the saved markdown file
                - data_path: Path to the saved data file (if any)
        """
        self.logger.info(f"Starting parse of {self.input_path}")

        # Parse input file
        self.parse()

        # Optionally save markdown
        markdown_path = self.save_markdown(self._markdown)

        # Optionally save parsed data
        data_path = self.save_change_log(self._parsed_data)

        self.logger.info("Parsing complete")
        return markdown_path, data_path
