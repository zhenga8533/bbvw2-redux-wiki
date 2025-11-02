"""
Generator for ability markdown pages.

This generator is specifically designed for Blaze Black 2 & Volt White 2 Redux,
with content prioritizing Black 2 & White 2 data.

This generator:
1. Reads ability data from data/pokedb/parsed/ability/
2. Generates individual markdown files for each ability to docs/pokedex/abilities/
3. Lists Pokemon that have each ability (standard and hidden)
4. Prioritizes Black 2 & White 2 content (flavor text, etc.)
"""

from pathlib import Path
from typing import Optional, List, Dict
from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Ability, Pokemon
from src.utils.yaml_util import load_mkdocs_config, save_mkdocs_config
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

    def _format_name(self, name: str) -> str:
        """Format an ability name for display (capitalize and handle special cases)."""
        # Handle special characters and formatting
        name = name.replace("-", " ")

        # Special cases for proper capitalization
        special_cases = {
            "rks system": "RKS System",
        }

        lower_name = name.lower()
        if lower_name in special_cases:
            return special_cases[lower_name]

        # Default: title case
        return name.title()

    def _build_pokemon_ability_cache(self) -> Dict[str, Dict[str, List[Pokemon]]]:
        """
        Build a cache mapping ability names to Pokemon that have them.

        This loads all Pokemon once and builds the mapping, which is much more
        efficient than loading Pokemon separately for each ability.

        Returns:
            Dict with ability names as keys, values are dicts with 'normal' and 'hidden' lists
        """
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"
        subfolders = ["default", "transformation", "variant"]

        # Map: ability_name -> {"normal": [...], "hidden": [...]}
        ability_cache = {}
        seen_pokemon = set()

        for subfolder in subfolders:
            pokemon_dir = pokemon_base_dir / subfolder
            if not pokemon_dir.exists():
                continue

            pokemon_files = sorted(pokemon_dir.glob("*.json"))

            for pokemon_file in pokemon_files:
                try:
                    pokemon = PokeDBLoader.load_pokemon(
                        pokemon_file.stem, subfolder=subfolder
                    )

                    if not pokemon or not pokemon.is_default:
                        continue

                    # Create unique key to prevent duplicates
                    pokemon_key = (
                        pokemon.name,
                        pokemon.pokedex_numbers.get("national"),
                    )

                    if pokemon_key in seen_pokemon:
                        continue

                    seen_pokemon.add(pokemon_key)

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

                except Exception as e:
                    self.logger.warning(
                        f"Error loading Pokemon {pokemon_file.stem}: {e}"
                    )

        # Sort all lists by national dex number
        for ability_data in ability_cache.values():
            ability_data["normal"].sort(
                key=lambda p: p.pokedex_numbers.get("national", 9999)
            )
            ability_data["hidden"].sort(
                key=lambda p: p.pokedex_numbers.get("national", 9999)
            )

        return ability_cache

    def _get_pokemon_with_ability(
        self,
        ability_name: str,
        cache: Optional[Dict[str, Dict[str, List[Pokemon]]]] = None,
    ) -> Dict[str, List[Pokemon]]:
        """
        Get all Pokemon that have this ability.

        Args:
            ability_name: The ability name to search for
            cache: Optional pre-built cache of ability->Pokemon mappings for performance

        Returns:
            Dictionary with 'normal' and 'hidden' keys containing lists of Pokemon
        """
        # If cache is provided, use it (much faster)
        if cache is not None:
            return cache.get(ability_name, {"normal": [], "hidden": []})

        # Fallback to old method if no cache (for backwards compatibility)
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"
        subfolders = ["default", "transformation", "variant"]

        normal_pokemon = []
        hidden_pokemon = []
        seen_pokemon = set()  # Track (name, dex_number) to prevent duplicates

        for subfolder in subfolders:
            pokemon_dir = pokemon_base_dir / subfolder
            if not pokemon_dir.exists():
                continue

            pokemon_files = sorted(pokemon_dir.glob("*.json"))

            for pokemon_file in pokemon_files:
                try:
                    pokemon = PokeDBLoader.load_pokemon(
                        pokemon_file.stem, subfolder=subfolder
                    )

                    if not pokemon or not pokemon.is_default:
                        continue

                    # Create unique key to prevent duplicates
                    pokemon_key = (
                        pokemon.name,
                        pokemon.pokedex_numbers.get("national"),
                    )

                    if pokemon_key in seen_pokemon:
                        continue

                    # Check if this Pokemon has the ability
                    for poke_ability in pokemon.abilities:
                        if poke_ability.name == ability_name:
                            seen_pokemon.add(pokemon_key)
                            if poke_ability.is_hidden:
                                hidden_pokemon.append(pokemon)
                            else:
                                normal_pokemon.append(pokemon)
                            break  # Don't add the same Pokemon twice

                except Exception as e:
                    self.logger.warning(
                        f"Error loading Pokemon {pokemon_file.stem}: {e}"
                    )

        # Sort by national dex number
        normal_pokemon.sort(key=lambda p: p.pokedex_numbers.get("national", 9999))
        hidden_pokemon.sort(key=lambda p: p.pokedex_numbers.get("national", 9999))

        return {"normal": normal_pokemon, "hidden": hidden_pokemon}

    def _generate_pokemon_list_section(
        self, pokemon_with_ability: Dict[str, List[Pokemon]]
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
            md += '<div class="grid cards ability-pokemon-cards" markdown>\n\n'

            for pokemon in normal:
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = self._format_name(pokemon.name)
                link = f"../pokemon/{pokemon.name}.md"

                # Get sprite URL
                sprite_url = None
                if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
                    bw = pokemon.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Card structure: sprite first, then separator, then info
                md += "- "
                if sprite_url:
                    md += f"[![{name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})\n\n"
                else:
                    md += f"[{name}]({link})\n\n"

                md += "\t---\n\n"
                md += f"\t**#{dex_num:03d} [{name}]({link})**\n\n"

            md += "</div>\n\n"

        # Hidden ability section
        if hidden:
            md += "### :material-eye-off: Hidden Ability\n\n"
            md += '<div class="grid cards ability-pokemon-cards" markdown>\n\n'

            for pokemon in hidden:
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = self._format_name(pokemon.name)
                link = f"../pokemon/{pokemon.name}.md"

                # Get sprite URL
                sprite_url = None
                if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
                    bw = pokemon.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Card structure: sprite first, then separator, then info
                md += "- "
                if sprite_url:
                    md += f"[![{name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})\n\n"
                else:
                    md += f"[{name}]({link})\n\n"

                md += "\t---\n\n"
                md += f"\t**#{dex_num:03d} [{name}]({link})**\n\n"

            md += "</div>\n\n"

        return md

    def _generate_effect_section(self, ability: Ability) -> str:
        """Generate the effect description section."""
        md = "## :material-information: Effect\n\n"

        # Full effect
        if ability.effect:
            # Try to get version-specific effect, fallback to first available
            effect_text = getattr(ability.effect, "black_2_white_2", None) or getattr(
                ability.effect, "black_white", None
            )

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

        flavor_text = ability.flavor_text.black_2_white_2
        version = "Black 2 & White 2"

        if flavor_text:
            md += f'!!! quote "{version}"\n\n'
            md += f"    {flavor_text}\n\n"
        else:
            md += "*No in-game description available.*\n\n"

        return md

    def generate_ability_page(
        self,
        ability: Ability,
        cache: Optional[Dict[str, Dict[str, List[Pokemon]]]] = None,
    ) -> Path:
        """
        Generate a markdown page for a single ability.

        Args:
            ability: The Ability data to generate a page for
            cache: Optional pre-built cache of ability->Pokemon mappings for performance

        Returns:
            Path to the generated markdown file
        """
        display_name = self._format_name(ability.name)

        # Start building the markdown
        md = f"# {display_name}\n\n"

        # Add sections
        md += self._generate_effect_section(ability)
        md += self._generate_flavor_text_section(ability)

        # Get Pokemon with this ability (using cache if available)
        pokemon_with_ability = self._get_pokemon_with_ability(ability.name, cache=cache)
        md += self._generate_pokemon_list_section(pokemon_with_ability)

        # Write to file
        output_file = self.output_dir / f"{ability.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_ability_pages(self) -> List[Path]:
        """
        Generate markdown pages for all abilities in the database.

        Returns:
            List of paths to generated markdown files
        """
        self.logger.info("Starting generation of all ability pages")

        # Build Pokemon ability cache once (massive performance improvement)
        self.logger.info("Building Pokemon ability cache...")
        pokemon_cache = self._build_pokemon_ability_cache()
        self.logger.info(f"Cached {len(pokemon_cache)} abilities across all Pokemon")

        # Get ability directory
        ability_dir = self.project_root / "data" / "pokedb" / "parsed" / "ability"

        if not ability_dir.exists():
            self.logger.error(f"Ability directory not found: {ability_dir}")
            return []

        ability_files = sorted(ability_dir.glob("*.json"))
        self.logger.info(f"Found {len(ability_files)} abilities")

        generated_files = []

        for ability_file in ability_files:
            try:
                ability_name = ability_file.stem
                ability = PokeDBLoader.load_ability(ability_name)

                if ability and ability.is_main_series:
                    output_path = self.generate_ability_page(
                        ability, cache=pokemon_cache
                    )
                    generated_files.append(output_path)
                elif ability:
                    self.logger.debug(
                        f"Skipping non-main-series ability: {ability_name}"
                    )
                else:
                    self.logger.warning(f"Could not load ability: {ability_name}")

            except Exception as e:
                self.logger.error(
                    f"Error generating page for {ability_file.stem}: {e}",
                    exc_info=True,
                )

        self.logger.info(f"Generated {len(generated_files)} ability pages")
        return generated_files

    def generate_abilities_index(self) -> Path:
        """
        Generate the main abilities index page with links to all abilities.

        Returns:
            Path to the generated index file
        """
        self.logger.info("Generating abilities index page")

        # Get all abilities
        ability_dir = self.project_root / "data" / "pokedb" / "parsed" / "ability"
        ability_files = sorted(ability_dir.glob("*.json"))

        # Load ability data for the index
        abilities = []
        for ability_file in ability_files:
            try:
                ability = PokeDBLoader.load_ability(ability_file.stem)
                if ability and ability.is_main_series:
                    abilities.append(ability)
            except Exception as e:
                self.logger.error(f"Error loading {ability_file.stem}: {e}")

        # Sort alphabetically by name
        abilities.sort(key=lambda a: a.name)

        # Generate markdown
        md = "# Abilities\n\n"
        md += "Complete list of all Pokémon abilities in **Blaze Black 2 & Volt White 2 Redux**.\n\n"
        md += "> Click on any ability to see its full description and which Pokémon can learn it.\n\n"

        # Generate table
        md += "| Ability | Effect |\n"
        md += "|---------|--------|\n"

        for ability in abilities:
            name = self._format_name(ability.name)
            link = f"[{name}](abilities/{ability.name}.md)"
            short_effect = (
                ability.short_effect if ability.short_effect else "*No description*"
            )

            md += f"| {link} | {short_effect} |\n"

        md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "abilities.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated abilities index: {output_file}")
        return output_file

    def update_mkdocs_navigation(self) -> bool:
        """
        Update mkdocs.yml with navigation links to all ability pages.
        Organizes abilities alphabetically into subsections.

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

            # Get all abilities
            ability_dir = self.project_root / "data" / "pokedb" / "parsed" / "ability"
            ability_files = sorted(ability_dir.glob("*.json"))

            # Load abilities
            abilities = []
            for ability_file in ability_files:
                try:
                    ability = PokeDBLoader.load_ability(ability_file.stem)
                    if ability and ability.is_main_series:
                        abilities.append(ability)
                except Exception as e:
                    self.logger.warning(f"Could not load {ability_file.stem}: {e}")

            # Sort alphabetically
            abilities.sort(key=lambda a: a.name)

            # Group abilities by generation
            from collections import defaultdict

            abilities_by_generation = defaultdict(list)

            # Generation display name mapping
            generation_display_names = {
                "generation-iii": "Gen III",
                "generation-iv": "Gen IV",
                "generation-v": "Gen V",
            }

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
                    display_name = generation_display_names.get(gen_key, gen_key)
                    gen_nav = [
                        {self._format_name(a.name): f"pokedex/abilities/{a.name}.md"}
                        for a in gen_abilities
                    ]
                    # Using type: ignore because mkdocs nav allows mixed dict value types
                    abilities_nav_items.append({display_name: gen_nav})  # type: ignore

            # Add unknown generation abilities if any exist
            if "unknown" in abilities_by_generation:
                unknown_abilities = abilities_by_generation["unknown"]
                unknown_nav = [
                    {self._format_name(a.name): f"pokedex/abilities/{a.name}.md"}
                    for a in unknown_abilities
                ]
                abilities_nav_items.append({"Unknown": unknown_nav})  # type: ignore

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

            # Find or create Abilities subsection within Pokédex
            abilities_subsection_index = None
            for i, item in enumerate(pokedex_nav):
                if isinstance(item, dict) and "Abilities" in item:
                    abilities_subsection_index = i
                    break

            # Update or append Abilities subsection
            abilities_subsection = {"Abilities": abilities_nav_items}
            if abilities_subsection_index is not None:
                pokedex_nav[abilities_subsection_index] = abilities_subsection
            else:
                pokedex_nav.append(abilities_subsection)

            # Update the config
            nav_list[pokedex_index] = {"Pokédex": pokedex_nav}
            config["nav"] = nav_list

            # Write updated mkdocs.yml
            save_mkdocs_config(mkdocs_path, config)

            self.logger.info(
                f"Updated mkdocs.yml with {len(abilities)} abilities organized into {len(abilities_by_generation)} generation sections"
            )
            return True

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

            # Generate all ability pages
            self.logger.info("Generating individual ability pages...")
            ability_files = self.generate_all_ability_pages()

            if not ability_files:
                self.logger.error("No ability pages were generated")
                return False

            # Generate the abilities index
            self.logger.info("Generating abilities index...")
            index_path = self.generate_abilities_index()

            # Update mkdocs.yml navigation
            self.logger.info("Updating mkdocs.yml navigation...")
            nav_success = self.update_mkdocs_navigation()

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
