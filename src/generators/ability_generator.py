"""
Generator for ability markdown pages.

This generator creates comprehensive ability documentation pages with data
from the configured version group (see config.VERSION_GROUP).

This generator:
1. Reads ability data from data/pokedb/parsed/ability/
2. Generates individual markdown files for each ability to docs/pokedex/abilities/
3. Lists Pokemon that have each ability (standard and hidden)
4. Uses version group data configured in config.py
"""

from collections import defaultdict
from pathlib import Path
from typing import Optional

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Ability, Pokemon
from src.utils.core.config import VERSION_GROUP, VERSION_GROUP_FRIENDLY
from src.utils.data.constants import (
    POKEMON_FORM_SUBFOLDERS_STANDARD,
)
from src.utils.data.pokemon_util import iterate_pokemon
from src.utils.formatters.markdown_formatter import format_pokemon_card_grid
from src.utils.text.text_util import format_display_name

from .base_generator import BaseGenerator


class AbilityGenerator(BaseGenerator):
    """
    Generator for ability markdown pages.

    Creates detailed pages for each ability including:
    - Effect descriptions
    - Flavor text
    - Pokemon that have this ability
    """

    def __init__(
        self, output_dir: str = "docs/pokedex", project_root: Optional[Path] = None
    ):
        """
        Initialize the Ability page generator.

        Args:
            output_dir: Directory where markdown files will be generated
            project_root: The root directory of the project. If None, it's inferred.
        """
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        self.category = "abilities"
        self.subcategory_order = [
            "generation-iii",
            "generation-iv",
            "generation-v",
        ]
        self.subcategory_names = {
            "generation-iii": "Gen III",
            "generation-iv": "Gen IV",
            "generation-v": "Gen V",
        }
        self.index_table_headers = ["Ability", "Effect"]
        self.index_table_alignments = ["left", "left"]

        # Create abilities subdirectory
        self.output_dir = self.output_dir / "abilities"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_pokemon_ability_cache(self) -> dict[str, dict[str, list[Pokemon]]]:
        """
        Build a cache mapping ability names to Pokemon that have them.

        This loads all Pokemon once and builds the mapping, which is much more
        efficient than loading Pokemon separately for each ability.

        Returns:
            Dict with ability names as keys, values are dicts with 'normal' and 'hidden' lists
        """
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"

        # Map: ability_name -> {"normal": [...], "hidden": [...]}
        ability_cache = {}

        # Use shared Pokemon iteration utility (handles deduplication and filtering)
        for pokemon in iterate_pokemon(
            pokemon_base_dir,
            subfolders=POKEMON_FORM_SUBFOLDERS_STANDARD,
            include_non_default=False,
            deduplicate=True,
        ):
            # Add this Pokemon to each ability it has
            for poke_ability in pokemon.abilities:
                if poke_ability.name not in ability_cache:
                    ability_cache[poke_ability.name] = {
                        "normal": [],
                        "hidden": [],
                    }

                if poke_ability.is_hidden:
                    ability_cache[poke_ability.name]["hidden"].append(pokemon)
                else:
                    ability_cache[poke_ability.name]["normal"].append(pokemon)

        # Sort all lists by national dex number
        for ability_data in ability_cache.values():
            ability_data["normal"].sort(
                key=lambda p: p.pokedex_numbers.get("national", 9999)
            )
            ability_data["hidden"].sort(
                key=lambda p: p.pokedex_numbers.get("national", 9999)
            )

        return ability_cache

    def load_all_data(self) -> list[Ability]:
        """
        Load all main-series abilities from the database once.

        Returns:
            List of Ability objects, sorted alphabetically by name
        """
        ability_dir = self.project_root / "data" / "pokedb" / "parsed" / "ability"

        if not ability_dir.exists():
            self.logger.error(f"Ability directory not found: {ability_dir}")
            return []

        ability_files = sorted(ability_dir.glob("*.json"))
        self.logger.info(f"Found {len(ability_files)} ability files")

        abilities = []
        for ability_file in ability_files:
            try:
                ability = PokeDBLoader.load_ability(ability_file.stem)
                if ability and ability.is_main_series:
                    abilities.append(ability)
                elif ability:
                    self.logger.debug(
                        f"Skipping non-main-series ability: {ability_file.stem}"
                    )
                else:
                    self.logger.warning(f"Could not load ability: {ability_file.stem}")
            except Exception as e:
                self.logger.error(
                    f"Error loading {ability_file.stem}: {e}", exc_info=True
                )

        # Sort alphabetically by name
        abilities.sort(key=lambda a: a.name)
        self.logger.info(f"Loaded {len(abilities)} main-series abilities")

        return abilities

    def categorize_data(self, data: list[Ability]) -> dict[str, list[Ability]]:
        """
        Categorize abilities by generation for index and navigation.

        Args:
            data: List of Ability objects to categorize
        Returns:
            Dict mapping generation identifiers to lists of Ability objects
        """
        abilities_by_generation = defaultdict(list)
        for ability in data:
            gen = ability.generation if ability.generation else "unknown"
            abilities_by_generation[gen].append(ability)

        return abilities_by_generation

    def _generate_pokemon_section(
        self, pokemon_with_ability: dict[str, list[Pokemon]]
    ) -> str:
        """Generate the Pokemon list section showing which Pokemon have this ability."""
        md = "## :material-pokeball: Pokémon with this Ability\n\n"

        normal = pokemon_with_ability["normal"]
        hidden = pokemon_with_ability["hidden"]

        if not normal and not hidden:
            md += "*No Pokémon have this ability.*\n\n"
            return md

        # Normal ability section
        if normal:
            md += "### :material-star: Standard Ability\n\n"
            md += format_pokemon_card_grid(normal)  # type: ignore
            md += "\n\n"

        # Hidden ability section
        if hidden:
            md += "### :material-eye-off: Hidden Ability\n\n"
            md += format_pokemon_card_grid(hidden)  # type: ignore
            md += "\n\n"

        return md

    def _generate_effect_section(self, ability: Ability) -> str:
        """Generate the effect description section."""
        md = "## :material-information: Effect\n\n"

        # Full effect
        if ability.effect:
            # Try to get version-specific effect, fallback to first available
            effect_text = getattr(ability.effect, VERSION_GROUP, None)

            if effect_text:
                md += f'!!! info "Full Description"\n\n'
                md += f"    {effect_text}\n\n"

        # Short effect
        if ability.short_effect:
            md += f'!!! tip "Quick Summary"\n\n'
            md += f"    {ability.short_effect}\n\n"

        # If no effect information available
        if not ability.effect and not ability.short_effect:
            md += "*Effect description not available.*\n\n"

        return md

    def _generate_flavor_text_section(self, ability: Ability) -> str:
        """Generate the flavor text section."""
        md = "## :material-book-open: In-Game Description\n\n"

        flavor_text = getattr(ability.flavor_text, VERSION_GROUP, None)

        if flavor_text:
            md += f'!!! quote "{VERSION_GROUP_FRIENDLY}"\n\n'
            md += f"    {flavor_text}\n\n"
        else:
            md += "*No in-game description available.*\n\n"

        return md

    def generate_page(
        self, item: Ability, cache: Optional[dict[str, dict[str, list[Pokemon]]]] = None
    ) -> Path:
        """
        Generate a markdown page for a single ability.

        Args:
            ability: The Ability data to generate a page for
            cache: Optional pre-built cache of ability->Pokemon mappings for performance

        Returns:
            Path to the generated markdown file
        """
        display_name = format_display_name(item.name)

        # Start building the markdown
        md = f"# {display_name}\n\n"

        # Add sections
        md += self._generate_effect_section(item)
        md += self._generate_flavor_text_section(item)

        # Get Pokemon with this ability
        default = {"normal": [], "hidden": []}
        pokemon_with_ability = cache.get(item.name, default) if cache else default
        md += self._generate_pokemon_section(pokemon_with_ability)

        # Write to file
        output_file = self.output_dir / f"{item.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_pages(
        self,
        data: list[Ability],
        cache: Optional[dict[str, dict[str, list[Pokemon]]]] = None,
    ) -> list[Path]:
        cache = cache or self._build_pokemon_ability_cache()
        return super().generate_all_pages(data, cache=cache)

    def format_index_row(self, item: Ability) -> list[str]:
        """
        Format a single row for the index table.

        Args:
            item: The item to format
        Returns:
            str: Formatted table row
        """
        name = format_display_name(item.name)
        link = f"[{name}](abilities/{item.name}.md)"
        short_effect = item.short_effect if item.short_effect else "*No description*"
        return [link, short_effect]
