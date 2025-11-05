"""
Base generator class for creating documentation pages from database content.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Optional

from src.utils.core.config import GAME_TITLE
from src.utils.core.logger import get_logger
from src.utils.formatters.table_formatter import create_table
from src.utils.formatters.yaml_formatter import update_pokedex_subsection
from src.utils.text.text_util import format_display_name


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
        # Initialize instance variables
        self.category = ""
        self.subcategory_order = []
        self.subcategory_names = {}
        self.name_special_cases = {}
        self.index_table_headers = []
        self.index_table_alignments = []

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

    @abstractmethod
    def load_all_data(self) -> list[Any]:
        """
        Load all data items from the database.

        This method should be implemented by subclasses to load
        the relevant data items for generation.

        Returns:
            list[Any]: List of data items
        """
        raise NotImplementedError("Subclasses must implement load_all_data()")

    @abstractmethod
    def categorize_data(self, data: list[Any]) -> dict[str, list[Any]]:
        """
        Categorize data items into subcategories.

        This method should be implemented by subclasses to categorize
        the data items for index generation and navigation.

        Args:
            data (list[Any]): List of data items to categorize
        Returns:
            dict[str, list[Any]]: Mapping of subcategory IDs to lists of items
        """
        raise NotImplementedError("Subclasses must implement categorize_data()")

    def cleanup_output_dir(self, pattern: str = "*.md") -> int:
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
            self.logger.info(
                f"Cleaned up {deleted_count} old files from {self.output_dir}"
            )

        return deleted_count

    def update_mkdocs_nav(
        self,
        categorized_items: dict[str, list],
    ) -> bool:
        """
        Update the mkdocs navigation structure.

        Args:
            categorized_items (dict[str, list]): Mapping of subcategory IDs to lists of items

        Returns:
            bool: True if update succeeded, False otherwise
        """
        try:
            self.logger.info(f"Updating mkdocs.yml navigation for {self.category}...")
            mkdocs_path = self.project_root / "mkdocs.yml"

            # Create navigation structure with generation subsections
            nav_items = [{"Overview": f"pokedex/{self.category}.md"}]

            # Add subsections for each subcategory
            for subcategory in self.subcategory_order:
                if subcategory in categorized_items:
                    subcategory_items = categorized_items[subcategory]
                    display_name = self.subcategory_names.get(subcategory, subcategory)

                    subcategory_nav = [
                        {
                            format_display_name(
                                item.name, self.name_special_cases
                            ): f"pokedex/{self.category}/{item.name}.md"
                        }
                        for item in subcategory_items
                    ]
                    # Using type: ignore because mkdocs nav allows mixed dict value types
                    nav_items.append({display_name: subcategory_nav})  # type: ignore

            # Add unknown subcategory items if any exist
            if "unknown" in categorized_items:
                unknown_items = categorized_items["unknown"]
                unknown_nav = [
                    {
                        format_display_name(
                            item.name, self.name_special_cases
                        ): f"pokedex/{self.category}/{item.name}.md"
                    }
                    for item in unknown_items
                ]
                nav_items.append({"Unknown": unknown_nav})  # type: ignore

            # Use shared utility to update mkdocs navigation (capitalize category name)
            category_title = self.category.capitalize()
            success = update_pokedex_subsection(
                mkdocs_path, category_title, nav_items, self.logger
            )

            if success:
                self.logger.info(
                    f"Updated mkdocs.yml with {sum(len(items) for items in categorized_items.values())} {self.category} organized into {len(categorized_items)} subcategory sections"
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False

    @abstractmethod
    def generate_page(self, item: Any, cache: Optional[dict[str, Any]] = None) -> Path:
        """
        Generate a markdown page for a single data item.

        This method should be implemented by subclasses to generate
        the markdown file for an individual data item.

        Args:
            item: The data item to generate a page for
        Returns:
            Path: The path to the generated markdown file
        """
        raise NotImplementedError("Subclasses must implement generate_page()")

    def generate_all_pages(
        self, data: list[Any], cache: Optional[dict[str, Any]] = None
    ) -> list[Path]:
        """
        Generate markdown pages for all data items.

        Args:
            data (list[Any]): List of data items to generate pages for
            cache (Optional[dict[str, Any]], optional): Cache for previously generated pages. Defaults to None.

        Returns:
            list[Path]: List of paths to the generated markdown files
        """
        self.logger.info(f"Starting generation of {len(data)} ability pages")

        generated_files = []

        for ability in data:
            try:
                output_path = self.generate_page(ability, cache)
                generated_files.append(output_path)

            except Exception as e:
                self.logger.error(
                    f"Error generating page for {ability.name}: {e}",
                    exc_info=True,
                )

        self.logger.info(f"Generated {len(generated_files)} ability pages")
        return generated_files

    def generate_index(
        self,
        data: list[Any],
        categorized_items: dict[str, list],
    ) -> Path:
        """
        Generate an index markdown page for the category.

        Args:
            data (list[Any]): List of all data items
            categorized_items (dict[str, list]): Mapping of subcategory IDs to lists of items

        Returns:
            Path: Path to the generated index markdown file
        """
        self.logger.info(
            f"Generating {self.category} index page for {len(data)} {self.category}"
        )

        # Generate markdown header
        title = self.category.capitalize()
        md = f"# {title}\n\n"
        md += f"Complete list of all {self.category} in **{GAME_TITLE}**.\n\n"
        md += f"> Click on any of the {title} to see its full description.\n\n"

        # Generate sections for each subcategory
        for subcategory in self.subcategory_order:
            if subcategory not in categorized_items:
                continue

            subcategory_items = categorized_items[subcategory]
            display_name = self.subcategory_names.get(subcategory, subcategory)

            # Add subcategory header
            md += f"## {display_name}\n\n"

            # Build table rows
            rows = []
            for item in subcategory_items:
                rows.append(self.format_index_row(item))

            # Use subclass-specific table formatter
            md += create_table(
                self.index_table_headers,
                rows,
                self.index_table_alignments,
            )
            md += "\n\n"

        # Add unknown subcategory items if any
        if "unknown" in categorized_items:
            md += "## Unknown\n\n"
            rows = []
            for item in categorized_items["unknown"]:
                rows.append(self.format_index_row(item))

            md += create_table(
                self.index_table_headers,
                rows,
                self.index_table_alignments,
            )
            md += "\n\n"

        # Write to file
        output_file = self.output_dir.parent / f"{self.category}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated {self.category} index: {output_file}")
        return output_file

    @abstractmethod
    def format_index_row(self, item: Any) -> list[str]:
        """
        Format a single row for the index table.

        This method should be implemented by subclasses to format
        individual items into table rows.

        Args:
            item: The item to format
        Returns:
            str: Formatted table row
        """
        raise NotImplementedError("Subclasses must implement format_row()")

    def generate(self) -> bool:
        """
        Execute the full generation process.

        This is the main entry point for generators. It orchestrates:
        1. Cleanup of old files
        2. Loading data
        3. Generating individual pages
        4. Generating index
        5. Updating navigation

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        self.logger.info(f"Starting {self.category} generation...")

        try:
            # Clean up old markdown files
            self.cleanup_output_dir()

            # Load all data once (optimization to avoid multiple glob + parse operations)
            self.logger.info(f"Loading all {self.category} from database...")
            data = self.load_all_data()

            if not data:
                self.logger.error(f"No {self.category} were loaded")
                return False

            # Generate all data pages
            self.logger.info(f"Generating individual {self.category} pages...")
            data_files = self.generate_all_pages(data)

            if not data_files:
                self.logger.error(f"No {self.category} pages were generated")
                return False

            # Categorize data for index and navigation
            categorized_data = self.categorize_data(data)

            # Generate the index
            self.logger.info(f"Generating {self.category} index...")
            index_path = self.generate_index(data, categorized_data)

            # Update mkdocs.yml navigation
            self.logger.info("Updating mkdocs.yml navigation...")
            nav_success = self.update_mkdocs_nav(categorized_data)

            if not nav_success:
                self.logger.warning(
                    "Failed to update mkdocs.yml navigation, but pages were generated successfully"
                )

            self.logger.info(
                f"Successfully generated {len(data_files)} {self.category} pages and index"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate {self.category}: {e}", exc_info=True)
            return False

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
