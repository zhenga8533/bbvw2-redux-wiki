"""
Generator for item markdown pages.

This generator is specifically designed for Blaze Black 2 & Volt White 2 Redux,
with content prioritizing Black 2 & White 2 data.

This generator:
1. Reads item data from data/pokedb/parsed/item/
2. Generates individual markdown files for each item to docs/pokedex/items/
3. Lists Pokemon that can hold each item in the wild
4. Prioritizes Black 2 & White 2 content (flavor text, etc.)
"""

from pathlib import Path
from typing import Dict, List, Optional

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Item, Pokemon
from src.utils.pokemon.constants import (
    ITEM_NAME_SPECIAL_CASES,
    POKEMON_FORM_SUBFOLDERS_STANDARD,
)
from src.utils.pokemon.pokemon_util import iterate_pokemon
from src.utils.formatters.table_util import (
    create_item_index_table,
    create_pokemon_with_item_table,
)
from src.utils.text.text_util import format_display_name
from src.utils.formatters.yaml_util import (
    load_mkdocs_config,
    save_mkdocs_config,
    update_pokedex_subsection,
)

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

        # Create items subdirectory
        self.output_dir = self.output_dir / "items"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_pokemon_item_cache(self) -> Dict[str, List[Dict]]:
        """
        Build a cache mapping item names to Pokemon that can hold them in the wild.

        Returns:
            Dict with item names as keys, values are lists of dicts with pokemon and rates
        """
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"

        # Map: item_name -> [{"pokemon": Pokemon, "black_2": rate, "white_2": rate}, ...]
        item_cache = {}

        # Use shared Pokemon iteration utility (handles deduplication and filtering)
        for pokemon in iterate_pokemon(
            pokemon_base_dir,
            subfolders=POKEMON_FORM_SUBFOLDERS_STANDARD,
            include_non_default=False,
            deduplicate=True,
        ):
            # Add this Pokemon to each item it can hold
            if pokemon.held_items:
                for item_name, rates in pokemon.held_items.items():
                    if item_name not in item_cache:
                        item_cache[item_name] = []

                    item_cache[item_name].append(
                        {
                            "pokemon": pokemon,
                            "black_2": rates.get("black_2", 0),
                            "white_2": rates.get("white_2", 0),
                        }
                    )

        # Sort all lists by national dex number
        for item_data in item_cache.values():
            item_data.sort(
                key=lambda p: p["pokemon"].pokedex_numbers.get("national", 9999)
            )

        return item_cache

    def _generate_pokemon_with_item_section(
        self, item_name: str, cache: Optional[Dict[str, List[Dict]]] = None
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

        # Build table rows
        rows = []
        for entry in pokemon_list:
            pokemon = entry["pokemon"]
            dex_num = pokemon.pokedex_numbers.get("national", "???")
            name = format_display_name(pokemon.name, ITEM_NAME_SPECIAL_CASES)
            link = f"[**#{dex_num:03d} {name}**](../pokemon/{pokemon.name}.md)"

            black_2_rate = f"{entry['black_2']}%" if entry["black_2"] else "—"
            white_2_rate = f"{entry['white_2']}%" if entry["white_2"] else "—"

            rows.append([link, black_2_rate, white_2_rate])

        # Use standardized table utility
        md += create_pokemon_with_item_table(rows)
        md += "\n"
        return md

    def _generate_effect_section(self, item: Item) -> str:
        """Generate the effect description section."""
        md = "## :material-information: Effect\n\n"

        # Full effect
        if item.effect:
            # Try to get version-specific effect, fallback to first available
            effect_text = getattr(item.effect, "black_2_white_2", None) or getattr(
                item.effect, "black_white", None
            )

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

    def _generate_flavor_text_section(self, item: Item) -> str:
        """Generate the flavor text section."""
        md = "## :material-book-open: In-Game Description\n\n"

        flavor_text = item.flavor_text.black_2_white_2
        version = "Black 2 & White 2"

        if flavor_text:
            md += f'!!! quote "{version}"\n\n'
            md += f"    {flavor_text}\n\n"
        else:
            md += "*No in-game description available.*\n\n"

        return md

    def _generate_attributes_section(self, item: Item) -> str:
        """Generate the item attributes section."""
        md = "## :material-tag: Attributes\n\n"

        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Category
        md += "- **:material-shape: Category**\n\n"
        md += "\t---\n\n"
        md += f"\t{format_display_name(item.category, ITEM_NAME_SPECIAL_CASES)}\n\n"

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
        """
        Generate an item header section with sprite and basic info.
        """
        md = ""

        display_name = format_display_name(item.name, ITEM_NAME_SPECIAL_CASES)
        category = format_display_name(item.category, ITEM_NAME_SPECIAL_CASES)

        md += '<div style="display: flex; align-items: center; gap: 1.5rem; background: var(--md-code-bg-color); padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">\n'

        # Sprite section
        if hasattr(item, "sprite") and item.sprite:
            md += '\t<div style="flex-shrink: 0;">\n'
            md += f'\t\t<img src="{item.sprite}" alt="{display_name}" style="width: 64px; height: 64px; image-rendering: pixelated;" />\n'
            md += "\t</div>\n"

        # Content section
        md += '\t<div style="display: flex; flex-direction: column; gap: 0.25rem;">\n'
        md += f'\t\t<div style="font-size: 1.25rem; font-weight: 600;">{display_name}</div>\n'
        md += f'\t\t<div style="font-size: 0.875rem; opacity: 0.7;">{category}</div>\n'
        md += "\t</div>\n"

        md += "</div>\n\n"

        return md

    def generate_item_page(
        self, item: Item, cache: Optional[Dict[str, List[Dict]]] = None
    ) -> Path:
        """
        Generate a markdown page for a single item.

        Args:
            item: The Item data to generate a page for
            cache: Optional pre-built cache of item->Pokemon mappings for performance

        Returns:
            Path to the generated markdown file
        """
        display_name = format_display_name(item.name, ITEM_NAME_SPECIAL_CASES)

        # Start building the markdown with title
        md = f"# {display_name}\n\n"

        # Add item header with sprite and category
        md += self._generate_item_header(item)

        # Add sections
        md += self._generate_effect_section(item)
        md += self._generate_flavor_text_section(item)
        md += self._generate_attributes_section(item)

        # Get Pokemon that hold this item (using cache if available)
        md += self._generate_pokemon_with_item_section(item.name, cache=cache)

        # Write to file
        output_file = self.output_dir / f"{item.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_item_pages(self) -> List[Path]:
        """
        Generate markdown pages for all items in the database.

        Returns:
            List of paths to generated markdown files
        """
        self.logger.info("Starting generation of all item pages")

        # Build Pokemon item cache once (massive performance improvement)
        self.logger.info("Building Pokemon item cache...")
        pokemon_cache = self._build_pokemon_item_cache()
        self.logger.info(f"Cached {len(pokemon_cache)} items found on wild Pokemon")

        # Get item directory
        item_dir = self.project_root / "data" / "pokedb" / "parsed" / "item"

        if not item_dir.exists():
            self.logger.error(f"Item directory not found: {item_dir}")
            return []

        item_files = sorted(item_dir.glob("*.json"))
        self.logger.info(f"Found {len(item_files)} items")

        generated_files = []

        for item_file in item_files:
            try:
                item_name = item_file.stem
                item = PokeDBLoader.load_item(item_name)

                if item:
                    # Skip miracle-shooter category items
                    if item.category == "miracle-shooter":
                        self.logger.debug(f"Skipping miracle-shooter item: {item_name}")
                        continue

                    output_path = self.generate_item_page(item, cache=pokemon_cache)
                    generated_files.append(output_path)
                else:
                    self.logger.warning(f"Could not load item: {item_name}")

            except Exception as e:
                self.logger.error(
                    f"Error generating page for {item_file.stem}: {e}",
                    exc_info=True,
                )

        self.logger.info(f"Generated {len(generated_files)} item pages")
        return generated_files

    def generate_items_index(self) -> Path:
        """
        Generate the main items index page with links to all items.

        Returns:
            Path to the generated index file
        """
        self.logger.info("Generating items index page")

        # Get all items
        item_dir = self.project_root / "data" / "pokedb" / "parsed" / "item"
        item_files = sorted(item_dir.glob("*.json"))

        # Load item data for the index
        items = []
        for item_file in item_files:
            try:
                item = PokeDBLoader.load_item(item_file.stem)
                if item:
                    # Skip miracle-shooter category items
                    if item.category == "miracle-shooter":
                        continue
                    items.append(item)
            except Exception as e:
                self.logger.error(f"Error loading {item_file.stem}: {e}")

        # Sort alphabetically by name
        items.sort(key=lambda i: i.name)

        # Generate markdown
        md = "# Items\n\n"
        md += (
            "Complete list of all items in **Blaze Black 2 & Volt White 2 Redux**.\n\n"
        )
        md += (
            "> Click on any item to see its full description and where to find it.\n\n"
        )

        # Group items by usage context
        from collections import defaultdict
        items_by_context = defaultdict(list)

        for item in items:
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

        # Usage context display names and order
        context_display = {
            "consumable": "Consumable Items",
            "holdable": "Holdable Items",
            "key-items": "Key Items",
            "machines": "Machines (TMs/HMs)",
            "evolution-items": "Evolution Items",
            "miscellaneous": "Miscellaneous",
        }
        context_order = [
            "consumable",
            "holdable",
            "key-items",
            "machines",
            "evolution-items",
            "miscellaneous",
        ]

        # Generate sections for each usage context
        for context_key in context_order:
            if context_key not in items_by_context:
                continue

            context_items = items_by_context[context_key]
            display_name = context_display.get(context_key, context_key.title())

            # Add usage context header
            md += f"## {display_name}\n\n"

            # Build table rows for this usage context
            rows = []
            for item in context_items:
                name = format_display_name(item.name, ITEM_NAME_SPECIAL_CASES)
                link = f"[{name}](items/{item.name}.md)"
                category = format_display_name(item.category, ITEM_NAME_SPECIAL_CASES)
                short_effect = (
                    item.short_effect if item.short_effect else "*No description*"
                )

                # Get sprite URL
                sprite_cell = "—"
                if hasattr(item, "sprite") and item.sprite:
                    sprite_cell = f'<img src="{item.sprite}" alt="{name}" />'

                rows.append([sprite_cell, link, category, short_effect])

            # Use standardized table utility
            md += create_item_index_table(rows)
            md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "items.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated items index: {output_file}")
        return output_file

    def update_mkdocs_navigation(self) -> bool:
        """
        Update mkdocs.yml with navigation links to all item pages.
        Organizes items alphabetically into subsections.

        Returns:
            bool: True if update succeeded, False if it failed
        """
        try:
            mkdocs_path = self.project_root / "mkdocs.yml"

            if not mkdocs_path.exists():
                self.logger.error(f"mkdocs.yml not found at {mkdocs_path}")
                return False

            # Load current mkdocs.yml
            config = load_mkdocs_config(mkdocs_path)

            # Get all items
            item_dir = self.project_root / "data" / "pokedb" / "parsed" / "item"
            item_files = sorted(item_dir.glob("*.json"))

            # Load items
            items = []
            for item_file in item_files:
                try:
                    item = PokeDBLoader.load_item(item_file.stem)
                    if item:
                        # Skip miracle-shooter category items
                        if item.category == "miracle-shooter":
                            continue
                        items.append(item)
                except Exception as e:
                    self.logger.warning(f"Could not load {item_file.stem}: {e}")

            # Sort alphabetically within each group
            items.sort(key=lambda i: i.name)

            # Group items by usage context
            from collections import defaultdict

            items_by_context = defaultdict(list)

            for item in items:
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

            # Create navigation structure with usage context subsections
            items_nav_items = [{"Overview": "pokedex/items.md"}]

            # Usage context display names and order
            context_display = {
                "consumable": "Consumable",
                "holdable": "Holdable",
                "key-items": "Key Items",
                "machines": "Machines",
                "miscellaneous": "Miscellaneous",
                "evolution-items": "Evolution Items",
            }
            context_order = [
                "consumable",
                "holdable",
                "key-items",
                "machines",
                "miscellaneous",
                "evolution-items",
            ]

            # Add subsections for each usage context
            for context_key in context_order:
                if context_key in items_by_context:
                    context_items = items_by_context[context_key]
                    display_name = context_display.get(context_key, context_key.title())
                    context_nav = [
                        {
                            format_display_name(
                                i.name, ITEM_NAME_SPECIAL_CASES
                            ): f"pokedex/items/{i.name}.md"
                        }
                        for i in context_items
                    ]
                    # Using type: ignore because mkdocs nav allows mixed dict value types
                    items_nav_items.append({display_name: context_nav})  # type: ignore

            # Find and update Pokédex section in nav
            if "nav" not in config:
                raise ValueError("mkdocs.yml does not contain a 'nav' section")

            nav_list = config["nav"]
            pokedex_index = None

            # Find the Pokédex section
            for i, item in enumerate(nav_list):
                if isinstance(item, dict) and "Pokédex" in item:
                    pokedex_index = i
                    break

            if pokedex_index is None:
                raise ValueError(
                    "mkdocs.yml nav section does not contain 'Pokédex'. "
                    "Please add a 'Pokédex' section to the navigation first."
                )

            # Get the Pokédex navigation items
            pokedex_nav = nav_list[pokedex_index]["Pokédex"]
            if not isinstance(pokedex_nav, list):
                pokedex_nav = []

            # Find or create Items subsection within Pokédex
            items_subsection_index = None
            for i, item in enumerate(pokedex_nav):
                if isinstance(item, dict) and "Items" in item:
                    items_subsection_index = i
                    break

            # Update or append Items subsection
            items_subsection = {"Items": items_nav_items}
            if items_subsection_index is not None:
                pokedex_nav[items_subsection_index] = items_subsection
            else:
                pokedex_nav.append(items_subsection)

            # Update the config
            nav_list[pokedex_index] = {"Pokédex": pokedex_nav}
            config["nav"] = nav_list

            # Write updated mkdocs.yml
            save_mkdocs_config(mkdocs_path, config)

            self.logger.info(
                f"Updated mkdocs.yml with {len(items)} items organized into {len(items_by_context)} usage context sections"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False

    def generate(self) -> bool:
        """
        Generate item pages and items index.

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        self.logger.info("Starting items generation...")
        try:
            # Clean up old item markdown files
            self._cleanup_output_dir()

            # Generate all item pages
            self.logger.info("Generating individual item pages...")
            item_files = self.generate_all_item_pages()

            if not item_files:
                self.logger.error("No item pages were generated")
                return False

            # Generate the items index
            self.logger.info("Generating items index...")
            index_path = self.generate_items_index()

            # Update mkdocs.yml navigation
            self.logger.info("Updating mkdocs.yml navigation...")
            nav_success = self.update_mkdocs_navigation()

            if not nav_success:
                self.logger.warning(
                    "Failed to update mkdocs.yml navigation, but pages were generated successfully"
                )

            self.logger.info(
                f"Successfully generated {len(item_files)} item pages and index"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate items: {e}", exc_info=True)
            return False
