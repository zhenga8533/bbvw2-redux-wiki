"""
Base parser class for processing documentation files and generating markdown output.
"""

import re
import unicodedata
from abc import ABC
from pathlib import Path
from typing import Optional

from src.utils.core.logger import get_logger


class BaseParser(ABC):
    """
    Abstract base class for all documentation parsers.

    All parsers should:
    - Read files from data/documentation/
    - Generate markdown files to docs/ (or subdirectories)
    - Optionally update data files in data/documentation/parsed/

    Each parser instance is independent and thread-safe.
    """

    def __init__(
        self,
        input_file: str,
        output_dir: str = "docs",
        project_root: Optional[Path] = None,
    ):
        """
        Initialize the parser.

        Args:
            input_file: Path to the input file (relative to data/documentation/)
            output_dir: Directory where markdown files will be generated (default: docs)
            project_root: The root directory of the project. If None, it's inferred.
        """
        # Initialize instance variables to avoid shared state
        self._markdown = ""
        self._sections = []
        self._current_section = ""
        self._lines = []
        self._line_index = 0
        self._last_line = ""

        # Set up logger for this parser instance
        self.logger = get_logger(self.__class__.__module__)

        # Set up paths
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = project_root

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

    def _section_to_method_name(self, section: str) -> str:
        """
        Convert a section name to a normalized handler method name.

        Examples:
          "Getting Started" -> "parse_getting_started"
          "Pokémon & Data"   -> "parse_pokemon_data"

        Falls back to "parse_default" if the section yields an empty name.
        """
        if not section:
            return "parse_default"

        # Normalize unicode (e.g., "Pokémon" -> "Pokemon") and lower-case
        s = (
            unicodedata.normalize("NFKD", section)
            .encode("ASCII", "ignore")
            .decode("ASCII")
            .lower()
        )

        # Replace any sequence of non-alphanumeric characters with a single underscore
        s = re.sub(r"[^a-z0-9]+", "_", s)

        # Trim leading/trailing underscores and collapse duplicates
        s = s.strip("_")

        return f"parse_{s}" if s else "parse_default"

    def get_title(self) -> str:
        """
        Get the title for the markdown document.

        Default implementation converts the input filename to title case.
        Subclasses can override to provide custom titles.

        Returns:
            str: The title for the markdown document
        """
        return self.output_file.replace("_", " ").title()

    def parse(self) -> None:
        """
        Default parse implementation for section-based parsers.

        This template method:
        1. Reads input lines
        2. Initializes markdown with a title
        3. Dispatches lines to section-specific handlers

        Subclasses should:
        - Define _sections class attribute with section names
        - Implement parse_<section_name>() methods for each section
        - Optionally override get_title() to customize the markdown title
        - Can override this method entirely for custom parsing logic
        """
        if not hasattr(self, "_sections"):
            raise NotImplementedError(
                "Subclasses must define _sections or override parse()"
            )

        self._lines = self.read_input_lines()
        self._line_index = 0
        self._markdown = f"# {self.get_title()}\n\n"

        while self._line_index < len(self._lines):
            line = self._lines[self._line_index]

            if line in self._sections:
                self.handle_section_change(line)
            elif self._current_section:
                method_name = self._section_to_method_name(self._current_section)
                method = getattr(self, method_name, None)

                if method is None:
                    self.logger.warning(
                        f"No handler for section '{self._current_section}', using parse_default"
                    )
                    self.parse_default(line)
                else:
                    method(line)

            self._last_line = line
            self._line_index += 1

    def parse_default(self, line: str) -> None:
        """
        Default line parser if no section-specific method is found.

        Simply appends the line to the markdown output.

        Args:
            line: The line to parse
        """

        if line == "" and self._last_line == "":
            return
        self._markdown += f"{line}\n"

    def peek_line(self, offset: int) -> Optional[str]:
        """
        Peek at a line at a specific offset from the current position.

        Args:
            offset: Number of lines ahead to peek (1 = next line, 2 = line after next, etc.)

        Returns:
            Optional[str]: The line at the specified offset, or None if out of bounds
        """
        index = self._line_index + offset
        if 0 <= index < len(self._lines):
            return self._lines[index]
        return None

    def handle_section_change(self, new_section: str) -> None:
        """
        Handle logic when changing sections.

        This is a template method that subclasses can override to add custom
        behavior when sections change (e.g., adding table headers, resetting state).

        The default implementation updates self._current_section.

        Args:
            new_section: Name of the new section being entered
        """
        self._markdown += f"## {new_section}\n\n"
        self._current_section = new_section

    def read_input_lines(self) -> list[str]:
        """Read and return the input file as lines, skipping empty lines and skip patterns."""
        skip_patterns = [r"^=+$"]

        self.logger.debug(f"Reading input file: {self.input_path}")
        try:
            # Read lines from the input file
            with self.input_path.open("r", encoding="utf-8") as f:
                lines = [line.rstrip() for line in f]
        except (OSError, IOError) as e:
            self.logger.error(
                f"Error reading input file {self.input_path}: {e}", exc_info=True
            )
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

    def save_markdown(self) -> Path:
        """
        Save markdown content to the output directory.

        Args:
            content: Markdown content to save

        Returns:
            Path: Path to the saved file
        """

        self.output_path.write_text(self._markdown, encoding="utf-8")
        self.logger.info(f"Saved markdown to {self.output_path}")
        return self.output_path

    def run(self) -> Optional[Path]:
        """
        Execute the full parsing pipeline.

        Returns:
            Path: Path to the saved markdown file
        """

        # Parse input file
        self.parse()

        # Save markdown
        markdown_path = self.save_markdown()

        return markdown_path
