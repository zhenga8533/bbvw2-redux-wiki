"""
Base generator class for creating documentation pages from database content.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from ..utils.logger_util import get_logger


class BaseGenerator(ABC):
    """
    Abstract base class for all documentation generators.

    All generators should:
    - Read data from data/pokedb/parsed/
    - Generate markdown files to docs/ (or subdirectories)

    Each generator instance is independent and thread-safe.
    """

    def __init__(
        self,
        output_dir: str = "docs",
        project_root: Optional[Path] = None,
    ):
        """
        Initialize the generator.

        Args:
            output_dir: Directory where markdown files will be generated
            project_root: The root directory of the project. If None, it's inferred.
        """
        # Set up logger for this generator instance
        self.logger = get_logger(self.__class__.__module__)

        # Set up paths
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = project_root

        self.output_dir = self.project_root / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.debug(
            f"Initializing generator: {self.__class__.__name__}",
            extra={"output_dir": str(self.output_dir)},
        )

    def _cleanup_output_dir(self, pattern: str = "*.md") -> int:
        """
        Clean up old files in the output directory.

        Args:
            pattern: Glob pattern for files to delete (default: "*.md")

        Returns:
            int: Number of files deleted
        """
        deleted_count = 0
        if self.output_dir.exists():
            for old_file in self.output_dir.glob(pattern):
                old_file.unlink()
                self.logger.debug(f"Deleted old file: {old_file}")
                deleted_count += 1

        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old files from {self.output_dir}")

        return deleted_count

    @abstractmethod
    def generate(self) -> bool:
        """
        Generate documentation pages.

        This method should be implemented by subclasses to perform the actual
        generation logic.

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def run(self) -> bool:
        """
        Execute the full generation pipeline.

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        try:
            return self.generate()
        except Exception as e:
            self.logger.error(f"Generation failed: {e}", exc_info=True)
            return False
