"""
Base parser class for processing documentation files and generating markdown output.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging
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
        parsed_data_dir: Optional[str] = None,
    ):
        """
        Initialize the parser.

        Args:
            input_file: Path to the input file (relative to data/documentation/)
            output_dir: Directory where markdown files will be generated (default: docs)
            parsed_data_dir: Optional directory for parsed data files
                           (relative to data/documentation/parsed/)
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Set up paths
        self.project_root = Path(__file__).parent.parent.parent
        self.input_path = self.project_root / "data" / "documentation" / input_file
        self.output_dir = self.project_root / output_dir

        if parsed_data_dir:
            self.parsed_data_dir = (
                self.project_root
                / "data"
                / "documentation"
                / "parsed"
                / parsed_data_dir
            )
        else:
            self.parsed_data_dir = None

        # Validate input file exists
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.parsed_data_dir:
            self.parsed_data_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def parse(self) -> dict:
        """
        Parse the input file and extract structured data.

        Returns:
            dict: Parsed data structure (format depends on parser implementation)
        """
        pass

    @abstractmethod
    def generate_markdown(self, parsed_data: dict) -> str:
        """
        Generate markdown content from parsed data.

        Args:
            parsed_data: The data structure returned by parse()

        Returns:
            str: Markdown-formatted content
        """
        pass

    def save_markdown(self, content: str, filename: str) -> Path:
        """
        Save markdown content to the output directory.

        Args:
            content: Markdown content to save
            filename: Output filename (should end in .md)

        Returns:
            Path: Path to the saved file
        """
        output_path = self.output_dir / filename
        output_path.write_text(content, encoding="utf-8")
        self.logger.info(f"Saved markdown to {output_path}")
        return output_path

    def save_parsed_data(self, data: dict, filename: str) -> Optional[Path]:
        """
        Save parsed data to a file (JSON, YAML, etc.).

        Args:
            data: Data to save
            filename: Output filename

        Returns:
            Path: Path to the saved file, or None if no parsed_data_dir is set
        """
        if not self.parsed_data_dir:
            self.logger.warning("No parsed_data_dir configured, skipping data save")
            return None

        output_path = self.parsed_data_dir / filename

        if filename.endswith(".json"):
            output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            # For other formats, subclasses should override this method
            raise NotImplementedError(f"Unsupported file format: {filename}")

        self.logger.info(f"Saved parsed data to {output_path}")
        return output_path

    def run(self, save_data: bool = False) -> tuple[Path, Optional[Path]]:
        """
        Execute the full parsing pipeline.

        Args:
            save_data: Whether to save parsed data to data/documentation/parsed/

        Returns:
            tuple: (markdown_path, parsed_data_path)
        """
        self.logger.info(f"Starting parse of {self.input_path}")

        # Parse input file
        parsed_data = self.parse()

        # Generate markdown
        markdown_content = self.generate_markdown(parsed_data)

        # Save markdown
        markdown_filename = self.get_output_filename()
        markdown_path = self.save_markdown(markdown_content, markdown_filename)

        # Optionally save parsed data
        data_path = None
        if save_data and self.parsed_data_dir:
            data_filename = self.get_data_filename()
            data_path = self.save_parsed_data(parsed_data, data_filename)

        self.logger.info("Parsing complete")
        return markdown_path, data_path

    def get_output_filename(self) -> str:
        """
        Get the output markdown filename.
        Override this method to customize output filenames.

        Returns:
            str: Output filename (e.g., "my_doc.md")
        """
        return self.input_path.stem + ".md"

    def get_data_filename(self) -> str:
        """
        Get the parsed data filename.
        Override this method to customize data filenames.

        Returns:
            str: Data filename (e.g., "my_doc.json")
        """
        return self.input_path.stem + ".json"
