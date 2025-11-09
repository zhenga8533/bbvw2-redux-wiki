"""
Base generator class for creating documentation pages from database content.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union

from src.utils.core.config import GAME_TITLE
from src.utils.core.logger import get_logger
from src.utils.formatters.table_formatter import create_table
from src.utils.formatters.yaml_formatter import update_pokedex_subsection
from src.utils.text.text_util import format_display_name

# Type aliases for navigation structures
NavItem = Union[dict[str, str], dict[str, list[dict[str, str]]]]
NavList = list[NavItem]


class BaseGenerator(ABC):
    """
    Abstract base class for all documentation generators.

    All generators should:
    - Read data from data/pokedb/parsed/
    - Generate markdown files to docs/ (or subdirectories)

    Each generator instance is independent and thread-safe.

    Args:
        ABC (_type_): Abstract base generator class
    """

    def __init__(
        self,
        output_dir: str = "docs",
        project_root: Optional[Path] = None,
    ):
        """Initialize the base generator.

        Args:
            output_dir (str, optional): Directory where markdown files will be generated. Defaults to "docs".
            project_root (Optional[Path], optional): The root directory of the project. If None, it's inferred.
        """
        # Initialize instance variables
        self.category = ""
        self.subcategory_order = []
        self.subcategory_names = {}
        self.name_special_cases = {}
        self.index_table_headers = []
        self.index_table_alignments = []

        self.logger = get_logger(self.__class__.__module__)
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
        """Load all data entries from the database.

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        Returns:
            list[Any]: List of data entries
        """
        raise NotImplementedError("Subclasses must implement load_all_data()")

    @abstractmethod
    def categorize_data(self, data: list[Any]) -> dict[str, list[Any]]:
        """Categorize data entries into subcategories.

        Args:
            data (list[Any]): List of data entries to categorize

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        Returns:
            dict[str, list[Any]]: Mapping of subcategory IDs to lists of entries
        """
        raise NotImplementedError("Subclasses must implement categorize_data()")

    def cleanup_output_dir(self, pattern: str = "*.md") -> int:
        """Clean up old files in the output directory.

        Args:
            pattern (str, optional): Glob pattern for files to delete (default: "*.md").

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

    def _build_pokemon_cache_by_attribute(
        self, attribute_extractor, cache_key_extractor, include_metadata=None
    ):
        """Build a cache mapping entity attributes to Pokemon that have them.

        This helper method reduces code duplication across generators that need
        to build reverse lookups from abilities/items/moves to Pokemon.

        Args:
            attribute_extractor: Function that takes a Pokemon and returns
                an iterable of attributes to cache (e.g., lambda p: p.abilities)
            cache_key_extractor: Function that takes an attribute and returns
                the cache key (e.g., lambda a: a.name)
            include_metadata: Function that takes an attribute and returns
                a dict of additional metadata to store (e.g., level, is_hidden)

        Returns:
            Mapping of cache keys to lists of Pokemon (or dicts with metadata)

        Example:
            ```python
            cache = self._build_pokemon_cache_by_attribute(
                attribute_extractor=lambda p: p.abilities,
                cache_key_extractor=lambda a: a.name,
                include_metadata=lambda a: {"is_hidden": a.is_hidden}
            )
            ```
        """
        from src.utils.core.loader import PokeDBLoader

        cache = {}

        for pokemon in PokeDBLoader.iterate_pokemon(
            include_non_default=False,
            deduplicate=True,
        ):
            attributes = attribute_extractor(pokemon)
            if not attributes:
                continue

            for attr in attributes:
                cache_key = cache_key_extractor(attr)

                if cache_key not in cache:
                    cache[cache_key] = []

                if include_metadata:
                    metadata = include_metadata(attr)
                    cache[cache_key].append({"pokemon": pokemon, **metadata})
                else:
                    cache[cache_key].append(pokemon)

        for cached_list in cache.values():
            if cached_list and isinstance(cached_list[0], dict):
                cached_list.sort(
                    key=lambda p: p["pokemon"].pokedex_numbers.get("national", 9999)
                )
            else:
                cached_list.sort(key=lambda p: p.pokedex_numbers.get("national", 9999))

        return cache

    def update_mkdocs_nav(
        self,
        categorized_entries: dict[str, list],
    ) -> bool:
        """Update the mkdocs navigation structure.

        Args:
            categorized_entries (dict[str, list]): Mapping of subcategory IDs to lists of entries

        Returns:
            bool: True if update succeeded, False otherwise
        """
        try:
            self.logger.info(f"Updating mkdocs.yml navigation for {self.category}...")
            mkdocs_path = self.project_root / "mkdocs.yml"

            nav_items: NavList = [{"Overview": f"pokedex/{self.category}.md"}]

            for subcategory in self.subcategory_order:
                if subcategory in categorized_entries:
                    subcategory_entries = categorized_entries[subcategory]
                    display_name = self.subcategory_names.get(subcategory, subcategory)

                    subcategory_nav: list[dict[str, str]] = [
                        {
                            format_display_name(
                                entry.name, self.name_special_cases
                            ): f"pokedex/{self.category}/{entry.name}.md"
                        }
                        for entry in subcategory_entries
                    ]
                    nav_items.append({display_name: subcategory_nav})

            if "unknown" in categorized_entries:
                unknown_entries = categorized_entries["unknown"]
                unknown_nav: list[dict[str, str]] = [
                    {
                        format_display_name(
                            entry.name, self.name_special_cases
                        ): f"pokedex/{self.category}/{entry.name}.md"
                    }
                    for entry in unknown_entries
                ]
                nav_items.append({"Unknown": unknown_nav})

            # Use shared utility to update mkdocs navigation (capitalize category name)
            category_title = self.category.capitalize()
            success = update_pokedex_subsection(
                mkdocs_path, category_title, nav_items, self.logger
            )

            if success:
                self.logger.info(
                    f"Updated mkdocs.yml with {sum(len(entries) for entries in categorized_entries.values())} {self.category} organized into {len(categorized_entries)} subcategory sections"
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False

    @abstractmethod
    def generate_page(self, entry: Any, cache: Optional[dict[str, Any]] = None) -> Path:
        """Generate a markdown page for a single data entry.

        Args:
            entry (Any): The data entry to generate a page for
            cache (Optional[dict[str, Any]], optional): Cache for previously generated pages. Defaults to None.

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        Returns:
            Path: Path to the generated markdown file
        """
        raise NotImplementedError("Subclasses must implement generate_page()")

    def generate_all_pages(
        self, data: list[Any], cache: Optional[dict[str, Any]] = None
    ) -> list[Path]:
        """Generate markdown pages for all data entries.

        Args:
            data (list[Any]): List of data entries to generate pages for
            cache (Optional[dict[str, Any]], optional): Cache for previously generated pages. Defaults to None.

        Returns:
            list[Path]: List of paths to the generated markdown files
        """
        self.logger.info(f"Starting generation of {len(data)} {self.category} pages")

        generated_files = []

        for entry in data:
            try:
                output_path = self.generate_page(entry, cache)
                generated_files.append(output_path)

            except Exception as e:
                self.logger.error(
                    f"Error generating page for {entry.name}: {e}",
                    exc_info=True,
                )

        self.logger.info(f"Generated {len(generated_files)} {self.category} pages")
        return generated_files

    def generate_index(
        self,
        data: list[Any],
        categorized_entries: dict[str, list],
    ) -> Path:
        """Generate an index markdown page for the category.

        Args:
            data (list[Any]): List of all data entries
            categorized_entries (dict[str, list]): Mapping of subcategory IDs to lists of entries

        Returns:
            Path: Path to the generated index markdown file
        """
        self.logger.info(
            f"Generating {self.category} index page for {len(data)} {self.category}"
        )

        title = self.category.capitalize()
        md = f"# {title}\n\n"
        md += f"Complete list of all {self.category} in **{GAME_TITLE}**.\n\n"
        md += f"> Click on any of the {title} to see its full description.\n\n"
        for subcategory in self.subcategory_order:
            if subcategory not in categorized_entries:
                continue

            subcategory_entries = categorized_entries[subcategory]
            display_name = self.subcategory_names.get(subcategory, subcategory)

            md += f"## {display_name}\n\n"

            rows = []
            for entry in subcategory_entries:
                rows.append(self.format_index_row(entry))

            # Use subclass-specific table formatter
            md += create_table(
                self.index_table_headers,
                rows,
                self.index_table_alignments,
            )
            md += "\n\n"
        if "unknown" in categorized_entries:
            md += "## Unknown\n\n"
            rows = []
            for entry in categorized_entries["unknown"]:
                rows.append(self.format_index_row(entry))

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
    def format_index_row(self, entry: Any) -> list[str]:
        """Format a single row for the index table.

        Args:
            entry (Any): The entry to format

        Raises:
            NotImplementedError: If not implemented by subclass

        Returns:
            list[str]: List of formatted row values
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
            self.cleanup_output_dir()

            self.logger.info(f"Loading all {self.category} from database...")
            data = self.load_all_data()

            if not data:
                self.logger.error(f"No {self.category} were loaded")
                return False

            self.logger.info(f"Generating individual {self.category} pages...")
            data_files = self.generate_all_pages(data)

            if not data_files:
                self.logger.error(f"No {self.category} pages were generated")
                return False

            categorized_data = self.categorize_data(data)

            self.logger.info(f"Generating {self.category} index...")
            index_path = self.generate_index(data, categorized_data)

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
