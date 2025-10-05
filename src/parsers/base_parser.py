"""
Base parser class for processing documentation files and generating markdown output.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional
from ..utils.logger import setup_logger
import json


class BaseParser(ABC):
    """
    Abstract base class for all documentation parsers.

    All parsers should:
    - Read files from data/documentation/
    - Generate markdown files to docs/ (or subdirectories)
    - Optionally update data files in data/documentation/parsed/
    """

    def __init__(
        self,
        input_file: str,
        output_dir: str = "docs",
        log_file: Optional[str] = None,
    ):
        """
        Initialize the parser.

        Args:
            input_file: Path to the input file (relative to data/documentation/)
            output_dir: Directory where markdown files will be generated (default: docs)
            log_file: Optional path to use for logging (defaults to child class file)
        """
        # Use the provided log_file or derive from child class location
        log_file = log_file if log_file is not None else self._get_child_file()
        self.logger = setup_logger(self.__class__.__name__, log_file)

        # Set up paths
        self.project_root = Path(__file__).parent.parent.parent
        self.input_path = self.project_root / "data" / "documentation" / input_file
        self.output_file = input_file.replace(" ", "_").lower().split(".")[0]

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

    def _get_child_file(self) -> str:
        """
        Get the file path of the child class for logging purposes.

        Returns:
            str: Path to the child class file
        """
        import inspect

        return inspect.getfile(self.__class__)

    @abstractmethod
    def parse(self) -> Dict:
        """
        Parse the input file and extract structured data.

        Returns:
            Dict: Parsed data structure (format depends on parser implementation)
        """
        pass

    @abstractmethod
    def generate_markdown(self, parsed_data: Dict) -> str:
        """
        Generate markdown content from parsed data.

        Args:
            parsed_data: The data structure returned by parse()

        Returns:
            str: Markdown-formatted content
        """
        pass

    def save_markdown(self, content: str) -> Path:
        """
        Save markdown content to the output directory.

        Args:
            content: Markdown content to save
            filename: Output filename (should end in .md)

        Returns:
            Path: Path to the saved file
        """
        if not content:
            self.logger.warning("No content to save for markdown.")
            return self.output_path
        self.output_path.write_text(content, encoding="utf-8")
        self.logger.info(f"Saved markdown to {self.output_path}")
        return self.output_path

    def save_change_log(self, data: Dict) -> Optional[Path]:
        """
        Save parsed data to a file (JSON, YAML, etc.).

        Args:
            data: Data to save
            filename: Output filename

        Returns:
            Path: Path to the saved file, or None if no change_log_dir is set
        """
        if not data:
            self.logger.warning("No data to save for change log.")
            return None
        self.change_log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.logger.info(f"Saved parsed data to {self.change_log_path}")
        return self.change_log_path

    def run(self) -> tuple[Path, Optional[Path]]:
        """
        Execute the full parsing pipeline.

        Returns:
            tuple: (markdown_path, parsed_data_path)
        """
        self.logger.info(f"Starting parse of {self.input_path}")

        # Parse input file
        parsed_data = self.parse()

        # Generate markdown
        markdown_content = self.generate_markdown(parsed_data)

        # Save markdown
        markdown_path = self.save_markdown(markdown_content)

        # Optionally save parsed data
        data_path = self.save_change_log(parsed_data)

        self.logger.info("Parsing complete")
        return markdown_path, data_path
