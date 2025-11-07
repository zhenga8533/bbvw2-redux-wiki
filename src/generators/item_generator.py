"""
Generator for item markdown pages.

This generator creates comprehensive item documentation pages with data
from the configured version group (see config.VERSION_GROUP).

This generator:
1. Reads item data from data/pokedb/parsed/item/
2. Generates individual markdown files for each item to docs/pokedex/items/
3. Lists Pokemon that can hold each item in the wild
4. Uses version group data configured in config.py
"""

from pathlib import Path
from typing import Any, Optional

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Item
from src.utils.core.config import POKEDB_GAME_VERSIONS, VERSION_GROUP
from src.utils.formatters.table_formatter import create_table
from src.utils.text.text_util import format_display_name

from .base_generator import BaseGenerator


class ItemGenerator(BaseGenerator):
    """
    Generator for item markdown pages.

    Creates detailed pages for each item including:
    - Effect descriptions
    - Flavor text
    - Pokemon that can hold this item in the wild
    """

    def __init__(
        self, output_dir: str = "docs/pokedex", project_root: Optional[Path] = None
    ):
        """
        Initialize the Item page generator.

        Args:
            output_dir: Directory where markdown files will be generated
            project_root: The root directory of the project. If None, it's inferred.
        """
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        self.category = "items"
        self.subcategory_order = [
            "consumable",
            "holdable",
            "key-items",
            "machines",
            "evolution-items",
            "miscellaneous",
        ]
        self.subcategory_names = {
            "consumable": "Consumable Items",
            "holdable": "Holdable Items",
            "key-items": "Key Items",
            "machines": "Machines (TMs/HMs)",
            "evolution-items": "Evolution Items",
            "miscellaneous": "Miscellaneous",
        }
        self.index_table_headers = ["Sprite", "Item", "Category", "Effect"]
        self.index_table_alignments = ["center", "left", "left", "left"]

        # Create items subdirectory
        self.output_dir = self.output_dir / "items"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_pokemon_item_cache(self) -> dict[str, list[dict]]:
        """
        Build a cache mapping item names to Pokemon that can hold them in the wild.

        Returns:
            Dict with item names as keys, values are lists of dicts with pokemon and rates
        """
        # Map: item_name -> [{"pokemon": Pokemon, <game_version>: rate, ...}, ...]
        item_cache = {}

        # Use shared Pokemon iteration utility (handles deduplication and filtering)
        for pokemon in PokeDBLoader.iterate_pokemon(
            include_non_default=False,
            deduplicate=True,
        ):
            # Add this Pokemon to each item it can hold
            if pokemon.held_items:
                for item_name, rates in pokemon.held_items.items():
                    if item_name not in item_cache:
                        item_cache[item_name] = []

                    # Build entry with rates for all configured game versions
                    entry: dict[str, Any] = {"pokemon": pokemon}
                    for version in POKEDB_GAME_VERSIONS:
                        entry[version] = rates.get(version, 0)

                    item_cache[item_name].append(entry)

        # Sort all lists by national dex number
        for item_data in item_cache.values():
            item_data.sort(
                key=lambda p: p["pokemon"].pokedex_numbers.get("national", 9999)
            )

        return item_cache

    def load_all_data(self) -> list[Item]:
        """
        Load all items from the database once.

        Returns:
            List of Item objects (excluding miracle-shooter items), sorted alphabetically by name
        """
        item_dir = self.project_root / "data" / "pokedb" / "parsed" / "item"

        if not item_dir.exists():
            self.logger.error(f"Item directory not found: {item_dir}")
            return []

        item_files = sorted(item_dir.glob("*.json"))
        self.logger.info(f"Found {len(item_files)} item files")

        items = []
        for item_file in item_files:
            try:
                item = PokeDBLoader.load_item(item_file.stem)
                if item:
                    # Skip miracle-shooter category items
                    if item.category == "miracle-shooter":
                        self.logger.debug(
                            f"Skipping miracle-shooter item: {item_file.stem}"
                        )
                        continue
                    items.append(item)
                else:
                    self.logger.warning(f"Could not load item: {item_file.stem}")
            except Exception as e:
                self.logger.error(f"Error loading {item_file.stem}: {e}", exc_info=True)

        # Sort alphabetically by name
        items.sort(key=lambda i: i.name)
        self.logger.info(f"Loaded {len(items)} items")

        return items

    def categorize_data(self, data: list[Item]) -> dict[str, list[Item]]:
        """
        Categorize items by usage context for index and navigation.

        Args:
            data: List of Item objects to categorize
        Returns:
            Dict mapping usage context identifiers to lists of Item objects
        """
        from collections import defaultdict

        items_by_context = defaultdict(list)

        for item in data:
            # Determine usage context based on attributes and category
            attributes = (
                item.attributes
                if hasattr(item, "attributes") and item.attributes
                else []
            )
            category = item.category if hasattr(item, "category") else None

            # Check consumable first (highest priority for items that can be used up)
            if "consumable" in attributes:
                context = "consumable"
            # Then check holdable (items that Pokemon can hold)
            elif (
                "holdable" in attributes
                or "holdable-active" in attributes
                or category == "held-items"
            ):
                context = "holdable"
            # Then check key items
            elif category == "gameplay":
                context = "key-items"
            # Then check for machines
            elif category == "all-machines":
                context = "machines"
            # Then check for evolution items
            elif category == "evolution":
                context = "evolution-items"
            # Default: miscellaneous
            else:
                context = "miscellaneous"

            items_by_context[context].append(item)

        return items_by_context

    def format_index_row(self, entry: Item) -> list[str]:
        """
        Format a single row for the index table.

        Args:
            entry: The entry to format
        Returns:
            List of strings for table columns: [sprite, link, category, short_effect]
        """
        name = format_display_name(entry.name)
        link = f"[{name}](items/{entry.name}.md)"
        category = format_display_name(entry.category)
        short_effect = entry.short_effect if entry.short_effect else "*No description*"

        # Get sprite URL
        sprite_cell = "—"
        if hasattr(entry, "sprite") and entry.sprite:
            sprite_cell = f'<img src="{entry.sprite}" alt="{name}" />'

        return [sprite_cell, link, category, short_effect]

    def _generate_pokemon_with_item_section(
        self, item_name: str, cache: Optional[dict[str, list[dict]]] = None
    ) -> str:
        """Generate the section showing which Pokemon can hold this item in the wild."""
        md = "## :material-pokeball: Wild Pokémon Encounters\n\n"

        # Get Pokemon that can hold this item
        pokemon_list = []
        if cache is not None:
            pokemon_list = cache.get(item_name, [])

        if not pokemon_list:
            md += "*This item is not found on wild Pokémon.*\n\n"
            return md

        md += (
            "The following Pokémon may hold this item when encountered in the wild:\n\n"
        )

        # Build table rows with dynamic game version columns
        rows = []
        for entry in pokemon_list:
            pokemon = entry["pokemon"]
            dex_num = pokemon.pokedex_numbers.get("national", "???")
            name = format_display_name(pokemon.name)
            link = f"[**#{dex_num:03d} {name}**](../pokemon/{pokemon.name}.md)"

            # Build row with all game version rates
            row = [link]
            for version in POKEDB_GAME_VERSIONS:
                rate = entry.get(version, 0)
                rate_str = f"{rate}%" if rate else "—"
                row.append(rate_str)

            rows.append(row)

        # Build headers for game versions
        version_headers = [format_display_name(v) for v in POKEDB_GAME_VERSIONS]

        # Use standardized table utility with dynamic headers
        headers = ["Pokémon"] + version_headers
        alignments = ["left"] + ["center"] * len(version_headers)
        md += create_table(headers, rows, alignments)
        md += "\n"
        return md

    def _generate_effect_section(self, item: Item) -> str:
        """Generate the effect description section."""
        md = "## :material-information: Effect\n\n"

        # Full effect
        if item.effect:
            # Try to get version-specific effect, fallback to first available
            effect_text = getattr(item.effect, VERSION_GROUP, None)

            if effect_text:
                md += f'!!! info "Description"\n\n'
                md += f"    {effect_text}\n\n"

        # Short effect
        if item.short_effect:
            md += f'!!! tip "Quick Summary"\n\n'
            md += f"    {item.short_effect}\n\n"

        # If no effect information available
        if not item.effect and not item.short_effect:
            md += "*Effect description not available.*\n\n"

        return md

    def _generate_attributes_section(self, item: Item) -> str:
        """Generate the item attributes section."""
        md = "## :material-tag: Attributes\n\n"

        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Category
        md += "- **:material-shape: Category**\n\n"
        md += "\t---\n\n"
        md += f"\t{format_display_name(item.category)}\n\n"

        # Card 2: Cost
        md += "- **:material-currency-usd: Cost**\n\n"
        md += "\t---\n\n"
        if item.cost and item.cost > 0:
            md += f"\t₽{item.cost:,}\n\n"
        else:
            md += "\t*Not for sale*\n\n"

        # Card 3: Fling Power (if applicable)
        if item.fling_power and item.fling_power > 0:
            md += "- **:material-fire: Fling Power**\n\n"
            md += "\t---\n\n"
            md += f"\t{item.fling_power}\n\n"

        md += "</div>\n\n"

        return md

    def _generate_item_header(self, item: Item) -> str:
        """Generate the item header section with sprite and category."""
        display_name = format_display_name(item.name)
        category_display_name = format_display_name(item.category)

        md = '!!! info "Item"\n\n'
        md += '\t<div style="display: flex; align-items: flex-start; gap: 15px;">\n'

        # Sprite
        img_style = "border: 1px solid; border-radius: 4px; padding: 4px; align-self: center; min-height: 60px; min-width: 60px;"
        md += f'\t\t<img src="{item.sprite}" alt="{display_name}" style="{img_style}" />\n'

        md += f"\t\t<div>\n"

        # Category
        md += f"\t\t\t<span markdown>**Category:** {category_display_name}</span>\n"

        md += f"\t\t\t<br/>\n"

        # Flavor Text
        flavor_text = getattr(
            item.flavor_text, VERSION_GROUP, "*No flavor text available.*"
        )
        md += f"\t\t\t<span markdown>**Flavor Text:** {flavor_text}</span>\n"

        md += f"\t\t</div>\n"
        md += "\t</div>\n\n"

        return md

    def generate_page(
        self, entry: Item, cache: Optional[dict[str, list[dict]]] = None
    ) -> Path:
        """
        Generate a markdown page for a single item.

        Args:
            entry: The Item data to generate a page for
            cache: Optional pre-built cache of item->Pokemon mappings for performance

        Returns:
            Path to the generated markdown file
        """
        display_name = format_display_name(entry.name)

        # Start building the markdown with title
        md = f"# {display_name}\n\n"

        # Add item header with sprite and category
        md += self._generate_item_header(entry)

        # Add sections
        md += self._generate_effect_section(entry)
        md += self._generate_attributes_section(entry)

        # Get Pokemon that hold this item (using cache if available)
        md += self._generate_pokemon_with_item_section(entry.name, cache=cache)

        # Write to file
        output_file = self.output_dir / f"{entry.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_pages(
        self,
        data: list[Item],
        cache: Optional[dict[str, list[dict]]] = None,
    ) -> list[Path]:
        cache = cache or self._build_pokemon_item_cache()
        return super().generate_all_pages(data, cache=cache)
