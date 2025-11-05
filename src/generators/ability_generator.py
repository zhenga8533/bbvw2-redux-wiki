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
from src.utils.core.config import GAME_TITLE, VERSION_GROUP, VERSION_GROUP_FRIENDLY
from src.utils.data.constants import (
    GENERATION_DISPLAY_NAMES,
    POKEMON_FORM_SUBFOLDERS_STANDARD,
)
from src.utils.data.pokemon_util import iterate_pokemon
from src.utils.formatters.table_formatter import create_ability_index_table
from src.utils.formatters.markdown_formatter import format_pokemon_card_grid
from src.utils.text.text_util import format_display_name
from src.utils.formatters.yaml_formatter import update_pokedex_subsection

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

    def _load_all_abilities(self) -> list[Ability]:
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

    def generate_ability_page(
        self, ability: Ability, cache: dict[str, dict[str, list[Pokemon]]]
    ) -> Path:
        """
        Generate a markdown page for a single ability.

        Args:
            ability: The Ability data to generate a page for
            cache: Optional pre-built cache of ability->Pokemon mappings for performance

        Returns:
            Path to the generated markdown file
        """
        display_name = format_display_name(ability.name)

        # Start building the markdown
        md = f"# {display_name}\n\n"

        # Add sections
        md += self._generate_effect_section(ability)
        md += self._generate_flavor_text_section(ability)

        # Get Pokemon with this ability
        pokemon_with_ability = cache.get(ability.name, {"normal": [], "hidden": []})
        md += self._generate_pokemon_section(pokemon_with_ability)

        # Write to file
        output_file = self.output_dir / f"{ability.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_ability_pages(self, abilities: list[Ability]) -> list[Path]:
        """
        Generate markdown pages for all abilities.

        Args:
            abilities: List of Ability objects to generate pages for

        Returns:
            List of paths to generated markdown files
        """
        self.logger.info(f"Starting generation of {len(abilities)} ability pages")

        # Build Pokemon ability cache once (massive performance improvement)
        self.logger.info("Building Pokemon ability cache...")
        pokemon_cache = self._build_pokemon_ability_cache()
        self.logger.info(f"Cached {len(pokemon_cache)} abilities across all Pokemon")

        generated_files = []

        for ability in abilities:
            try:
                output_path = self.generate_ability_page(
                    ability, cache=pokemon_cache
                )
                generated_files.append(output_path)

            except Exception as e:
                self.logger.error(
                    f"Error generating page for {ability.name}: {e}",
                    exc_info=True,
                )

        self.logger.info(f"Generated {len(generated_files)} ability pages")
        return generated_files

    def generate_abilities_index(self, abilities: list[Ability]) -> Path:
        """
        Generate the main abilities index page with links to all abilities.

        Args:
            abilities: List of Ability objects to include in the index

        Returns:
            Path to the generated index file
        """
        self.logger.info(f"Generating abilities index page for {len(abilities)} abilities")

        # Generate markdown
        md = "# Abilities\n\n"
        md += f"Complete list of all Pokémon abilities in **{GAME_TITLE}**.\n\n"
        md += "> Click on any ability to see its full description and which Pokémon can learn it.\n\n"

        # Group abilities by generation
        from collections import defaultdict

        abilities_by_generation = defaultdict(list)

        for ability in abilities:
            gen = ability.generation if ability.generation else "unknown"
            abilities_by_generation[gen].append(ability)

        # Generation order and display names
        generation_order = ["generation-iii", "generation-iv", "generation-v"]

        # Generate sections for each generation
        for gen_key in generation_order:
            if gen_key not in abilities_by_generation:
                continue

            gen_abilities = abilities_by_generation[gen_key]
            display_name = GENERATION_DISPLAY_NAMES.get(gen_key, gen_key)

            # Add generation header
            md += f"## {display_name}\n\n"

            # Build table rows for this generation
            rows = []
            for ability in gen_abilities:
                name = format_display_name(ability.name)
                link = f"[{name}](abilities/{ability.name}.md)"
                short_effect = (
                    ability.short_effect if ability.short_effect else "*No description*"
                )
                rows.append([link, short_effect])

            # Use standardized table utility
            md += create_ability_index_table(rows)
            md += "\n"

        # Add unknown generation abilities if any
        if "unknown" in abilities_by_generation:
            md += "## Unknown Generation\n\n"
            rows = []
            for ability in abilities_by_generation["unknown"]:
                name = format_display_name(ability.name)
                link = f"[{name}](abilities/{ability.name}.md)"
                short_effect = (
                    ability.short_effect if ability.short_effect else "*No description*"
                )
                rows.append([link, short_effect])

            md += create_ability_index_table(rows)
            md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "abilities.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated abilities index: {output_file}")
        return output_file

    def update_mkdocs_navigation(self, abilities: list[Ability]) -> bool:
        """
        Update mkdocs.yml with navigation links to all ability pages.
        Organizes abilities alphabetically into subsections.

        Args:
            abilities: List of Ability objects to include in navigation

        Returns:
            bool: True if update succeeded, False if it failed
        """
        try:
            mkdocs_path = self.project_root / "mkdocs.yml"

            # Group abilities by generation
            abilities_by_generation = defaultdict(list)

            for ability in abilities:
                gen = ability.generation if ability.generation else "unknown"
                abilities_by_generation[gen].append(ability)

            # Create navigation structure with generation subsections
            abilities_nav_items = [{"Overview": "pokedex/abilities.md"}]

            # Add subsections for each generation in order (III, IV, V)
            generation_order = ["generation-iii", "generation-iv", "generation-v"]
            for gen_key in generation_order:
                if gen_key in abilities_by_generation:
                    gen_abilities = abilities_by_generation[gen_key]
                    display_name = GENERATION_DISPLAY_NAMES.get(gen_key, gen_key)
                    gen_nav = [
                        {format_display_name(a.name): f"pokedex/abilities/{a.name}.md"}
                        for a in gen_abilities
                    ]
                    # Using type: ignore because mkdocs nav allows mixed dict value types
                    abilities_nav_items.append({display_name: gen_nav})  # type: ignore

            # Add unknown generation abilities if any exist
            if "unknown" in abilities_by_generation:
                unknown_abilities = abilities_by_generation["unknown"]
                unknown_nav = [
                    {format_display_name(a.name): f"pokedex/abilities/{a.name}.md"}
                    for a in unknown_abilities
                ]
                abilities_nav_items.append({"Unknown": unknown_nav})  # type: ignore

            # Use shared utility to update mkdocs navigation
            success = update_pokedex_subsection(
                mkdocs_path, "Abilities", abilities_nav_items, self.logger
            )

            if success:
                self.logger.info(
                    f"Updated mkdocs.yml with {len(abilities)} abilities organized into {len(abilities_by_generation)} generation sections"
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False

    def generate(self) -> bool:
        """
        Generate ability pages and abilities index.

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        self.logger.info("Starting abilities generation...")
        try:
            # Clean up old ability markdown files
            self._cleanup_output_dir()

            # Load all abilities once (optimization to avoid multiple glob + parse operations)
            self.logger.info("Loading all abilities from database...")
            abilities = self._load_all_abilities()

            if not abilities:
                self.logger.error("No abilities were loaded")
                return False

            # Generate all ability pages
            self.logger.info("Generating individual ability pages...")
            ability_files = self.generate_all_ability_pages(abilities)

            if not ability_files:
                self.logger.error("No ability pages were generated")
                return False

            # Generate the abilities index
            self.logger.info("Generating abilities index...")
            index_path = self.generate_abilities_index(abilities)

            # Update mkdocs.yml navigation
            self.logger.info("Updating mkdocs.yml navigation...")
            nav_success = self.update_mkdocs_navigation(abilities)

            if not nav_success:
                self.logger.warning(
                    "Failed to update mkdocs.yml navigation, but pages were generated successfully"
                )

            self.logger.info(
                f"Successfully generated {len(ability_files)} ability pages and index"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate abilities: {e}", exc_info=True)
            return False
