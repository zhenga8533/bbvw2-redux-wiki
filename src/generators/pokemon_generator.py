"""
Generator for individual Pokemon markdown pages.

This generator creates comprehensive Pokemon documentation pages with data
from the configured version group (see config.VERSION_GROUP).

This generator:
1. Reads Pokemon data from data/pokedb/parsed/pokemon/
2. Generates individual markdown files for each Pokemon to docs/pokedex/pokemon/
3. Handles Pokemon forms and variations
4. Uses version group data configured in config.py

Note: Styles are applied inline when they depend on dynamic data:
- Hero gradient colors (based on Pokemon types)
- Type badges use format_type_badge() from markdown_util
- Name formatting uses format_display_name() from text_util
"""

from collections import defaultdict
from pathlib import Path
from typing import Any, Optional, cast

from src.utils.core.config import (
    GENERATOR_DEX_RELATIVE_PATH,
    GENERATOR_INDEX_RELATIVE_PATH,
    POKEDB_GAME_VERSIONS,
    POKEDB_SPRITE_VERSION,
    VERSION_GROUP,
)
from src.utils.core.loader import PokeDBLoader
from src.utils.data.constants import (
    POKEMON_FORM_SUBFOLDERS,
    TYPE_COLORS,
)
from src.utils.data.models import (
    EvolutionChain,
    EvolutionDetails,
    EvolutionNode,
    Pokemon,
)
from src.utils.data.type_effectiveness import calculate_type_effectiveness
from src.utils.formatters.markdown_formatter import (
    format_ability,
    format_category_badge,
    format_item,
    format_move,
    format_pokemon,
    format_pokemon_card_grid,
    format_stat_bar,
    format_type_badge,
)
from src.utils.formatters.table_formatter import create_table
from src.utils.formatters.yaml_formatter import load_mkdocs_config, save_mkdocs_config
from src.utils.text.text_util import extract_form_suffix, format_display_name

from .base_generator import BaseGenerator


class PokemonGenerator(BaseGenerator):
    """
    Generator for individual Pokemon markdown pages.

    Creates detailed pages for each Pokemon including:
    - Basic information (types, abilities, stats)
    - Evolution chain
    - Move learnset
    - Forms and variations
    - Sprites and images

    Args:
        BaseGenerator (_type_): Abstract base generator class
    """

    def __init__(
        self, output_dir: str = "docs/pokedex", project_root: Optional[Path] = None
    ):
        """Initialize the Pokemon page generator.

        Args:
            output_dir (str, optional): Directory where markdown files will be generated. Defaults to "docs/pokedex".
            project_root (Optional[Path], optional): The root directory of the project. If None, it's inferred.
        """
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        # Create pokemon subdirectory
        self.output_dir = self.output_dir / "pokemon"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configure category and subcategories for BaseGenerator
        self.category = "pokemon"
        self.subcategory_order = [
            "generation-i",
            "generation-ii",
            "generation-iii",
            "generation-iv",
            "generation-v",
        ]
        self.subcategory_names = {
            "generation-i": "Generation I",
            "generation-ii": "Generation II",
            "generation-iii": "Generation III",
            "generation-iv": "Generation IV",
            "generation-v": "Generation V",
        }
        self.index_table_headers = ["#", "Sprite", "Name", "Types", "Abilities"]
        self.index_table_alignments = ["right", "center", "left", "left", "left"]

    def load_all_data(self) -> list[Pokemon]:
        """Load all Pokemon from all form subfolders once.

        Returns:
            list[Pokemon]: List of all Pokemon objects across all form subfolders
        """
        self.logger.info("Loading all Pokemon from all form subfolders")

        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"
        all_pokemon = []
        total_files = 0

        for folder in POKEMON_FORM_SUBFOLDERS:
            pokemon_dir = pokemon_base_dir / folder

            if not pokemon_dir.exists():
                self.logger.debug(f"Subfolder not found, skipping: {folder}")
                continue

            pokemon_files = sorted(pokemon_dir.glob("*.json"))
            self.logger.info(
                f"Found {len(pokemon_files)} Pokemon in subfolder: {folder}"
            )
            total_files += len(pokemon_files)

            for pokemon_file in pokemon_files:
                try:
                    pokemon_name = pokemon_file.stem
                    pokemon = PokeDBLoader.load_pokemon(pokemon_name, subfolder=folder)

                    if pokemon:
                        all_pokemon.append(pokemon)
                    else:
                        self.logger.warning(
                            f"Could not load Pokemon: {pokemon_name} from {folder}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error loading {pokemon_file.stem} from {folder}: {e}",
                        exc_info=True,
                    )

        self.logger.info(
            f"Loaded {len(all_pokemon)} Pokemon from {total_files} files across all subfolders"
        )
        return all_pokemon

    def categorize_data(self, data: list[Pokemon]) -> dict[str, list[Pokemon]]:
        """Categorize Pokemon by generation.

        Args:
            data (list[Pokemon]): List of Pokemon objects to categorize

        Returns:
            dict[str, list[Pokemon]]: Mapping of generation IDs to lists of Pokemon (all forms, deduplicated)
        """
        categorized: dict[str, list[Pokemon]] = defaultdict(list)

        # Deduplicate by (dex_number, name) to prevent duplicate entries
        seen_pokemon = set()

        for pokemon in data:
            # Create unique key to prevent duplicates
            pokemon_key = (pokemon.pokedex_numbers.get("national"), pokemon.name)

            if pokemon_key in seen_pokemon:
                continue

            seen_pokemon.add(pokemon_key)

            gen = pokemon.generation if pokemon.generation else "unknown"
            categorized[gen].append(pokemon)

        # Sort Pokemon within each generation by national dex number, then by name
        for gen in categorized:
            categorized[gen].sort(
                key=lambda p: (p.pokedex_numbers.get("national", 9999), p.name)
            )

        return dict(categorized)

    def format_index_row(self, entry: Pokemon) -> list[str]:
        """Format a single Pokemon into a table row for the index page.

        Args:
            entry (Pokemon): The Pokemon object to format

        Returns:
            list[str]: List of table cell strings: [dex_num, sprite, name_link, types, abilities]
        """
        # Dex number
        dex_num = entry.pokedex_numbers.get("national", "???")
        dex_str = f"**{dex_num:03d}**" if isinstance(dex_num, int) else f"**{dex_num}**"

        # Sprite
        sprite_cell = format_pokemon(entry, is_linked=False)

        # Name link
        name = format_display_name(entry.name)
        name_link = f"[{name}](pokemon/{entry.name}.md)"

        # Types (stacked vertically)
        type_badges = " ".join([format_type_badge(t) for t in entry.types])
        types_cell = f'<div class="badges-vstack">{type_badges}</div>'

        # Abilities (non-hidden only, max 2)
        abilities = [a.name for a in entry.abilities if not a.is_hidden]
        abilities_str = ", ".join(
            [
                format_ability(a, relative_path=GENERATOR_INDEX_RELATIVE_PATH)
                for a in abilities[:2]
            ]
        )

        return [dex_str, sprite_cell, name_link, types_cell, abilities_str]

    def _format_ability(self, ability_name: str, is_hidden: bool = False) -> str:
        """Format an ability name with link and hidden indicator.

        Args:
            ability_name (str): The ability name
            is_hidden (bool, optional): Whether the ability is hidden. Defaults to False.

        Returns:
            str: Formatted ability name with link and hidden indicator.
        """
        formatted_name = format_display_name(ability_name)
        hidden_tag = " *(Hidden)*" if is_hidden else ""
        return f"{formatted_name}{hidden_tag}"

    def _generate_status_badges(self, pokemon: Pokemon) -> str:
        """Generate status badges for legendary/mythical/baby Pokemon.

        Args:
            pokemon (Pokemon): The Pokemon object to generate badges for.

        Returns:
            str: HTML string of status badges.
        """
        badges = []

        if pokemon.is_legendary:
            badges.append(
                "<span class='pokemon-hero-status-badge legendary-badge'>⭐ LEGENDARY</span>"
            )
        elif pokemon.is_mythical:
            badges.append(
                "<span class='pokemon-hero-status-badge mythical-badge'>✨ MYTHICAL</span>"
            )

        if pokemon.is_baby:
            badges.append(
                "<span class='pokemon-hero-status-badge baby-badge'>🍼 BABY</span>"
            )

        return " ".join(badges) if badges else ""

    def _get_gradient_colors(self, types: list[str]) -> tuple[str, str]:
        """Calculate gradient colors based on Pokemon types.

        Args:
            types (list[str]): List of Pokemon type names

        Returns:
            tuple[str, str]: Tuple of (primary_color, secondary_color) with opacity
        """
        default_color = "#667eea"

        if not types:
            return (f"{default_color}dd", f"{default_color}55")

        # Get primary type color
        color_1 = TYPE_COLORS.get(types[0].lower(), default_color)

        # Calculate secondary color based on type count
        if len(types) > 1:
            # Dual-type: use second type with higher opacity
            color_2_base = TYPE_COLORS.get(types[1].lower(), color_1)
            color_2 = f"{color_2_base}99"
        else:
            # Single-type: fade primary color
            color_2 = f"{color_1}55"

        # Add opacity to primary color
        color_1_with_opacity = f"{color_1}dd"

        return (color_1_with_opacity, color_2)

    def _create_dex_number_badge(self, region: str, number: int) -> str:
        """Create a regional Pokedex number badge.

        Args:
            region (str): The name of the region (e.g., "Kanto")
            number (int): The Pokedex number within the region

        Returns:
            str: HTML string of the regional Pokedex number badge
        """
        region_name = format_display_name(region)
        return f'<span class="regional-dex-badge">{region_name}: #{number:03d}</span>'

    def _generate_hero_section(self, pokemon: Pokemon) -> str:
        """Generate a hero section with sprite, types, and badges.

        Args:
            pokemon (Pokemon): The Pokemon object to generate the hero section for.

        Returns:
            str: HTML string of the hero section.
        """
        md = ""

        # Get gradient colors based on types
        color_1, color_2 = self._get_gradient_colors(pokemon.types)

        # Hero container with dynamic gradient based on type(s)
        md += f'<div class="pokemon-hero" style="background: linear-gradient(135deg, {color_1} 0%, {color_2} 100%);">\n'

        # Add subtle pattern overlay for depth
        md += '\t<div class="pokemon-hero-overlay"></div>\n'
        md += '\t<div class="pokemon-hero-content">\n'

        # Sprite with enhanced shadow and glow
        sprite_src = getattr(
            pokemon.sprites.versions, POKEDB_SPRITE_VERSION
        ).animated.front_default
        sprite = f'<img src="{sprite_src}" alt="{pokemon.name}" class="sprite" />'
        md += f'\t\t<div class="pokemon-hero-sprite">\n'
        md += f"\t\t\t{sprite}\n"
        md += "\t\t</div>\n"

        # Genus (species classification)
        if pokemon.genus:
            md += f'\t\t<div class="pokemon-hero-genus">{pokemon.genus}</div>\n'

        # National Pokedex number
        if "national" in pokemon.pokedex_numbers:
            dex_num = pokemon.pokedex_numbers["national"]
            md += f'\t\t<div class="pokemon-hero-dex-number">#{dex_num:03d}</div>\n'

        # Regional dex numbers
        regional_dex = {
            k: v
            for k, v in pokemon.pokedex_numbers.items()
            if k != "national" and v is not None
        }
        if regional_dex:
            dex_badges = [
                self._create_dex_number_badge(region, number)
                for region, number in sorted(regional_dex.items())
            ]
            md += f'\t\t<div class="pokemon-hero-regional-badge">{" ".join(dex_badges)}</div>\n'

        # Types
        types_str = " ".join([format_type_badge(t) for t in pokemon.types])
        md += f'\t\t<div class="badges-hstack">{types_str}</div>\n'

        # Status badges
        status_badges = self._generate_status_badges(pokemon)
        if status_badges:
            md += f"\t\t{status_badges}\n"

        md += "\t</div>\n"
        md += "</div>\n\n"

        return md

    def _generate_basic_info(self, pokemon: Pokemon) -> str:
        """Generate the basic information section.

        Args:
            pokemon (Pokemon): The Pokemon object to generate the basic information section for.

        Returns:
            str: HTML string of the basic information section.
        """
        md = "## :material-information: Basic Information\n\n"

        # Use grid layout for information cards
        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Abilities
        md += "- **:material-shield-star: Abilities**\n\n"
        md += "\t---\n\n"
        for ability in pokemon.abilities:
            ability_display = format_ability(
                ability.name, is_linked=True, relative_path=GENERATOR_DEX_RELATIVE_PATH
            )
            # Add hidden indicator if applicable
            if ability.is_hidden:
                ability_display += " :material-eye-off:"
            md += f"\t- {ability_display}\n"
        md += "\n"

        # Card 2: Physical Attributes
        height_m = pokemon.height / 10
        weight_kg = pokemon.weight / 10
        md += "- **:material-ruler: Physical Attributes**\n\n"
        md += "\t---\n\n"
        md += f"\t**Height:** {height_m:.1f} m\n\n"
        md += f"\t**Weight:** {weight_kg:.1f} kg\n\n"
        md += "\n"

        # Card 3: Training Info
        md += "- **:material-book-education: Training**\n\n"
        md += "\t---\n\n"
        md += f"\t**Base Experience:** {pokemon.base_experience}\n\n"
        md += f"\t**Base Happiness:** {pokemon.base_happiness}\n\n"
        md += f"\t**Capture Rate:** {pokemon.capture_rate}\n\n"
        md += f"\t**Growth Rate:** {format_display_name(pokemon.growth_rate)}\n\n"
        if pokemon.habitat:
            md += f"\t**Habitat:** {format_display_name(pokemon.habitat)}\n\n"
        # EV Yield
        if pokemon.ev_yield:
            md += "\t**EV Yield:** "
            ev_parts = []
            for ev in pokemon.ev_yield:
                stat_name = format_display_name(ev.stat)
                ev_parts.append(f"+{ev.effort} {stat_name}")
            md += ", ".join(ev_parts) + "\n\n"
        md += "\n"

        # Card 4: Breeding Info
        md += "- **:material-egg: Breeding**\n\n"
        md += "\t---\n\n"
        if pokemon.gender_rate == -1:
            md += "\t**Gender:** Genderless\n\n"
        else:
            female_pct = (pokemon.gender_rate / 8) * 100
            male_pct = 100 - female_pct
            md += f"\t**Gender Ratio:** {male_pct:.1f}% ♂ / {female_pct:.1f}% ♀\n\n"
            if pokemon.has_gender_differences:
                md += "\t**Gender Differences:** Yes\n\n"
        md += f"\t**Egg Groups:** {', '.join([format_display_name(eg) for eg in pokemon.egg_groups])}\n\n"
        md += f"\t**Hatch Counter:** {pokemon.hatch_counter} cycles\n\n"

        # Card 5: Classification
        md += "- **:material-star-four-points: Classification**\n\n"
        md += "\t---\n\n"
        md += f"\t**Generation:** {format_display_name(pokemon.generation)}\n\n"
        md += f"\t**Color:** {format_display_name(pokemon.color)}\n\n"
        md += f"\t**Shape:** {format_display_name(pokemon.shape)}\n\n"
        md += "\n"

        md += "</div>\n\n"

        return md

    def _generate_held_items_section(self, pokemon: Pokemon) -> str:
        """Generate the held items section showing what items this Pokemon can hold in the wild.

        Args:
            pokemon (Pokemon): The Pokemon object to generate the held items section for.

        Returns:
            str: HTML string of the held items section.
        """
        if not pokemon.held_items:
            return ""

        md = "## :material-treasure-chest: Wild Held Items\n\n"
        md += "These items can be found when catching or defeating this Pokémon in the wild:\n\n"

        # Build table rows with dynamic game version columns
        rows = []
        for item_name, rates in pokemon.held_items.items():
            # Convert underscores to hyphens for item identifier
            item_id = item_name.replace("_", "-")
            item_display = format_item(
                item_id, relative_path=GENERATOR_DEX_RELATIVE_PATH
            )

            # Build row with all game version rates
            row = [item_display]
            for version in POKEDB_GAME_VERSIONS:
                rate = rates.get(version, 0)
                rate_str = f"{rate}%" if rate else "—"
                row.append(rate_str)

            rows.append(row)

        # Build headers for game versions
        version_headers = [format_display_name(v) for v in POKEDB_GAME_VERSIONS]

        # Use standardized table utility with dynamic headers
        headers = ["Item"] + version_headers
        alignements = ["left"] + ["center"] * len(version_headers)
        md += create_table(headers, rows, alignements)
        md += "\n\n"
        return md

    def _generate_type_effectiveness(self, pokemon: Pokemon) -> str:
        """Generate the type effectiveness section with enhanced visuals.

        Args:
            pokemon (Pokemon): The Pokemon object to generate the type effectiveness section for.

        Returns:
            str: HTML string of the type effectiveness section.
        """
        md = "## :material-shield-half-full: Type Effectiveness\n\n"

        effectiveness = calculate_type_effectiveness(pokemon.types)

        # Create a visual display of type effectiveness
        has_any = any(effectiveness.values())
        if not has_any:
            md += "*No notable type advantages or disadvantages.*\n\n"
            return md

        # Use grid layout for better organization
        md += '<div class="grid cards" markdown>\n\n'

        # Weaknesses card
        if effectiveness["4x_weak"] or effectiveness["2x_weak"]:
            md += "- **:material-alert: Weak To**\n\n"
            md += "\t---\n\n"
            if effectiveness["4x_weak"]:
                md += "\t**4× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [format_type_badge(t) for t in sorted(effectiveness["4x_weak"])]
                )
                md += "\n\t{: .badges-hstack }\n\n"
            if effectiveness["2x_weak"]:
                md += "\t**2× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [format_type_badge(t) for t in sorted(effectiveness["2x_weak"])]
                )
                md += "\n\t{: .badges-hstack }\n\n"

        # Resistances card
        if effectiveness["0.25x_resist"] or effectiveness["0.5x_resist"]:
            md += "- **:material-shield-check: Resists**\n\n"
            md += "\t---\n\n"
            if effectiveness["0.25x_resist"]:
                md += "\t**¼× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [
                        format_type_badge(t)
                        for t in sorted(effectiveness["0.25x_resist"])
                    ]
                )
                md += "\n\t{: .badges-hstack }\n\n"
            if effectiveness["0.5x_resist"]:
                md += "\t**½× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [format_type_badge(t) for t in sorted(effectiveness["0.5x_resist"])]
                )
                md += "\n\t{: .badges-hstack }\n\n"

        # Immunities card
        if effectiveness["immune"]:
            md += "- **:material-shield: Immune To**\n\n"
            md += "\t---\n\n"
            md += "\t**No Damage**\n\n"
            md += "\t"
            md += " ".join(
                [format_type_badge(t) for t in sorted(effectiveness["immune"])]
            )
            md += '\n\t{ style="display: flex; flex-wrap: wrap; gap: 0.5rem;" }\n\n'

        md += "</div>\n\n"

        return md

    def _calculate_stat_range(self, base_stat: int, is_hp: bool = False) -> tuple:
        """Calculate min and max stat values at level 100 using official Pokemon formulas:
        https://bulbapedia.bulbagarden.net/wiki/Stat#Generation_III_onward

        Args:
            base_stat (int): The base stat value
            is_hp (bool, optional): Whether this is the HP stat (uses different formula). Defaults to False.

        Returns:
            tuple: (min_stat, max_stat) at level 100
        """
        if is_hp:
            # HP formula at level 100:
            # HP = floor(((2 * Base + IV + floor(EV / 4)) * Level) / 100) + Level + 10
            #
            # At Level 100:
            # Min (0 IV, 0 EV): floor(((2 * Base + 0 + 0) * 100) / 100) + 100 + 10 = 2 * Base + 110
            # Max (31 IV, 252 EV): floor(((2 * Base + 31 + 63) * 100) / 100) + 100 + 10 = 2 * Base + 204
            #
            # Note: Shedinja is a special case with HP always = 1 (handled separately)
            min_hp = (2 * base_stat) + 110
            max_hp = (2 * base_stat) + 204
            return (min_hp, max_hp)
        else:
            # Other stats formula at level 100:
            # Stat = floor((floor(((2 * Base + IV + floor(EV / 4)) * Level) / 100) + 5) * Nature)
            #
            # At Level 100:
            # Min (0 IV, 0 EV, hindering nature 0.9): floor((floor(((2 * Base) * 100) / 100) + 5) * 0.9)
            #                                        = floor((2 * Base + 5) * 0.9)
            # Max (31 IV, 252 EV, beneficial nature 1.1): floor((floor(((2 * Base + 31 + 63) * 100) / 100) + 5) * 1.1)
            #                                             = floor((2 * Base + 94 + 5) * 1.1)
            #                                             = floor((2 * Base + 99) * 1.1)
            min_stat = int(((2 * base_stat) + 5) * 0.9)
            max_stat = int(((2 * base_stat) + 99) * 1.1)
            return (min_stat, max_stat)

    def _generate_stats_table(self, pokemon: Pokemon) -> str:
        """Generate the stats table section with modern visual bars and level 100 ranges.

        Args:
            pokemon (Pokemon): The Pokemon object to generate the stats table for.

        Returns:
            str: HTML string of the stats table section.
        """
        md = "## :material-chart-bar: Base Stats\n\n"

        stats_display = [
            ("HP", pokemon.stats.hp, True),
            ("Attack", pokemon.stats.attack, False),
            ("Defense", pokemon.stats.defense, False),
            ("Sp. Atk", pokemon.stats.special_attack, False),
            ("Sp. Def", pokemon.stats.special_defense, False),
            ("Speed", pokemon.stats.speed, False),
        ]

        total = sum([s[1] for s in stats_display])

        # Create a table with stat bars and level 100 ranges
        md += "| Stat | Base | Min | Max | Distribution |\n"
        md += "|------|-----:|----:|----:|:-------------|\n"

        for stat_name, value, is_hp in stats_display:
            bar = format_stat_bar(value, max_value=255)
            min_stat, max_stat = self._calculate_stat_range(value, is_hp)
            md += (
                f"| **{stat_name}** | **{value}** | {min_stat} | {max_stat} | {bar} |\n"
            )

        # Total row
        md += f"| **Base Stat Total** | **{total}** | | | |\n\n"

        # Add legend explaining the min/max values
        md += "> **Min/Max Stats:** Calculated at Level 100.\n"
        md += ">\n"
        md += "> - **Min**: 0 IVs, 0 EVs, hindering nature (0.9×) for non-HP stats\n"
        md += ">\n"
        md += "> - **Max**: 31 IVs, 252 EVs, beneficial nature (1.1×) for non-HP stats\n\n"

        return md

    def _format_evo_method(self, evo_details: EvolutionDetails) -> str:
        """Format evolution method details into readable text.

        Args:
            evo_details (EvolutionDetails): Evolution details object

        Returns:
            Formatted evolution method string
        """
        if not evo_details:
            return ""

        details = []

        # Check trigger type first for special cases
        trigger = getattr(evo_details, "trigger", None)

        # Trade evolutions
        if trigger == "trade":
            if evo_details.held_item:
                details.append(
                    f"Trade holding {format_display_name(evo_details.held_item)}"
                )
            elif evo_details.trade_species:
                details.append(
                    f"Trade for {format_display_name(evo_details.trade_species)}"
                )
            else:
                details.append("Trade")

        # Level-up conditions
        if evo_details.min_level:
            details.append(f"Level {evo_details.min_level}")

        # Item-based evolutions
        if evo_details.item and trigger != "trade":
            details.append(f"Use {format_display_name(evo_details.item)}")

        # Party requirements
        if evo_details.party_species:
            details.append(
                f"With {format_display_name(evo_details.party_species)} in party"
            )
        if evo_details.party_type:
            details.append(
                f"With {format_display_name(evo_details.party_type)}-type in party"
            )

        # Move requirements
        if evo_details.known_move:
            details.append(f"Know {format_display_name(evo_details.known_move)}")
        if evo_details.known_move_type:
            details.append(
                f"Know {format_display_name(evo_details.known_move_type)}-type move"
            )

        # Happiness/Affection
        if evo_details.min_happiness:
            details.append(f"Happiness {evo_details.min_happiness}+")
        if evo_details.min_affection:
            details.append(f"Affection {evo_details.min_affection}+")

        # Beauty
        if evo_details.min_beauty:
            details.append(f"Beauty {evo_details.min_beauty}+")

        # Time of day
        if evo_details.time_of_day:
            details.append(f"During {evo_details.time_of_day}")

        # Location
        if evo_details.location:
            details.append(f"At {format_display_name(evo_details.location)}")

        # Gender requirement
        if evo_details.gender is not None:
            gender_text = "♀" if evo_details.gender == 1 else "♂"
            details.append(f"Gender: {gender_text}")

        # Physical stats comparison
        if evo_details.relative_physical_stats:
            if evo_details.relative_physical_stats == 1:
                details.append("Attack > Defense")
            elif evo_details.relative_physical_stats == -1:
                details.append("Attack < Defense")
            elif evo_details.relative_physical_stats == 0:
                details.append("Attack = Defense")

        # Weather/Special conditions
        if evo_details.needs_overworld_rain:
            details.append("During rain")
        if evo_details.turn_upside_down:
            details.append("Turn console upside down")

        return "<br>".join(details) if details else "Unknown"

    def _generate_evolution_chain(self, pokemon: Pokemon) -> str:
        """Generate the evolution chain section showing all stages.

        Args:
            pokemon (Pokemon): The Pokemon object with evolution chain data

        Returns:
            str: Markdown string with evolution chain organized by stages
        """
        if not pokemon.evolution_chain or not pokemon.evolution_chain.species_name:
            return ""

        md = "## :material-family-tree: Evolution Chain\n\n"

        # Check if this Pokemon doesn't evolve (single stage, no evolutions)
        if (
            not pokemon.evolution_chain.evolves_to
            and pokemon.evolution_chain.species_name.lower() == pokemon.species.lower()
        ):
            md += "> :material-information: This Pokémon does not evolve.\n\n"
            return md

        # Recursively collect all Pokemon in the evolution chain
        def collect_evolution_stages(
            node: EvolutionNode | EvolutionChain, stage: int = 1
        ) -> dict[int, list[tuple[str, Optional[EvolutionDetails]]]]:
            stages: dict[int, list[tuple[str, Optional[EvolutionDetails]]]] = {}

            # Handle the root chain (stage 1)
            if isinstance(node, EvolutionChain):
                stages[1] = [(node.species_name, None)]

                # Process all evolutions from the root
                for evolution in node.evolves_to:
                    child_stages = collect_evolution_stages(evolution, stage + 1)
                    for child_stage, pokemon_list in child_stages.items():
                        if child_stage not in stages:
                            stages[child_stage] = []
                        stages[child_stage].extend(pokemon_list)

            # Handle evolution nodes (stage 2+)
            elif isinstance(node, EvolutionNode):
                stages[stage] = [(node.species_name, node.evolution_details)]

                # Process child evolutions
                for evolution in node.evolves_to:
                    child_stages = collect_evolution_stages(evolution, stage + 1)
                    for child_stage, pokemon_list in child_stages.items():
                        if child_stage not in stages:
                            stages[child_stage] = []
                        stages[child_stage].extend(pokemon_list)

            return stages

        # Collect all stages
        evolution_stages = collect_evolution_stages(pokemon.evolution_chain)

        # Sort stages by stage number
        sorted_stages = sorted(evolution_stages.items())

        # Generate markdown for each stage
        for stage_num, pokemon_list in sorted_stages:
            md += f"### Stage {stage_num}\n\n"

            # Prepare extra_info for evolution methods
            extra_info = []
            pokemon_names = []

            for species_name, evo_details in pokemon_list:
                pokemon_names.append(species_name)

                # Format evolution method if available
                if evo_details:
                    method = self._format_evo_method(evo_details)
                    extra_info.append(f"*{method}*" if method else "")
                else:
                    extra_info.append("")

            # Use format_pokemon_card_grid to display Pokemon
            # Highlight the current Pokemon
            highlighted_pokemon = []
            highlighted_extra_info = []

            for idx, species_name in enumerate(pokemon_names):
                highlighted_pokemon.append(species_name)
                info = extra_info[idx]

                # Add indicator if this is the current Pokemon
                if species_name.lower() == pokemon.species.lower():
                    info += "\n\n\t***You are here***"

                highlighted_extra_info.append(info)

            md += format_pokemon_card_grid(
                highlighted_pokemon,
                relative_path=".",
                extra_info=highlighted_extra_info,
            )
            md += "\n\n"

        return md

    def _generate_forms_section(self, pokemon: Pokemon) -> str:
        """Generate section showing available forms for this Pokemon with Pokemon cards.

        Args:
            pokemon (Pokemon): The Pokemon object with form data

        Returns:
            str: Markdown string with available forms organized in a grid
        """
        # Don't show if only one form and not switchable
        if len(pokemon.forms) <= 1 and not pokemon.forms_switchable:
            return ""

        md = "## :material-shape: Available Forms\n\n"

        if pokemon.forms_switchable:
            md += "> :material-information: Forms are switchable during gameplay.\n\n"

        if len(pokemon.forms) > 1:
            forms = [f.name for f in pokemon.forms]
            categories = [format_display_name(f.category) for f in pokemon.forms]

            md += format_pokemon_card_grid(forms, extra_info=categories)  # type: ignore
            md += "\n\n"

        return md

    def _generate_move_table(
        self,
        moves: list,
        include_level: bool = False,
        sort_by_level: bool = False,
    ) -> str:
        """Generate a move table with formatted move data.

        Args:
            moves (list): List of move learn objects
            include_level (bool, optional): Whether to include the level column. Defaults to False.
            sort_by_level (bool, optional): Whether to sort by level learned (otherwise sort by name). Defaults to False.

        Returns:
            str: Formatted markdown table string
        """
        # Sort moves
        if sort_by_level:
            sorted_moves = sorted(moves, key=lambda m: m.level_learned_at)
        else:
            sorted_moves = sorted(moves, key=lambda m: m.name)

        # Build table rows
        rows = []
        for move_learn in sorted_moves:
            move_data = PokeDBLoader.load_move(move_learn.name)
            move_name_formatted = format_move(
                move_learn.name,
                is_linked=True,
                relative_path=GENERATOR_DEX_RELATIVE_PATH,
            )

            if move_data:
                # Get move details
                move_type = getattr(move_data.type, VERSION_GROUP, None) or "???"
                type_badge = format_type_badge(move_type)

                damage_class = move_data.damage_class
                category_icon = format_category_badge(damage_class)

                power = getattr(move_data.power, VERSION_GROUP, None)
                power_str = str(power) if power is not None else "—"

                accuracy = getattr(move_data.accuracy, VERSION_GROUP, None)
                accuracy_str = str(accuracy) if accuracy is not None else "—"

                pp = getattr(move_data.pp, VERSION_GROUP, None)
                pp_str = str(pp) if pp is not None else "—"

                if include_level:
                    level = str(move_learn.level_learned_at)
                    rows.append(
                        [
                            level,
                            move_name_formatted,
                            type_badge,
                            category_icon,
                            power_str,
                            accuracy_str,
                            pp_str,
                        ]
                    )
                else:
                    rows.append(
                        [
                            move_name_formatted,
                            type_badge,
                            category_icon,
                            power_str,
                            accuracy_str,
                            pp_str,
                        ]
                    )
            else:
                # Fallback if move data not available
                if include_level:
                    level = str(move_learn.level_learned_at)
                    rows.append(
                        [
                            level,
                            format_display_name(move_learn.name),
                            "—",
                            "—",
                            "—",
                            "—",
                            "—",
                        ]
                    )
                else:
                    rows.append(
                        [format_display_name(move_learn.name), "—", "—", "—", "—", "—"]
                    )

        # Use standardized table utility
        headers = ["Move", "Type", "Category", "Power", "Accuracy", "PP"]
        if include_level:
            headers = ["Level"] + headers
        alignments = ["left"] * len(headers)
        table_md = create_table(headers, rows, alignments)

        # Add tab indentation for nested table (in card grids)
        indented_table = "\n".join("\t" + line for line in table_md.split("\n"))

        return indented_table + "\n"

    def _generate_moves_section(self, pokemon: Pokemon) -> str:
        """Generate the moves section for a Pokémon.

        Args:
            pokemon (Pokemon): The Pokémon object with move data.

        Returns:
            str: Formatted markdown string with the moves section.
        """
        md = "## :material-sword-cross: Moves\n\n"

        # Use tabs for different move categories
        md += '=== ":material-arrow-up-bold: Level-Up"\n\n'
        if pokemon.moves.level_up:
            md += self._generate_move_table(
                pokemon.moves.level_up,
                include_level=True,
                sort_by_level=True,
            )
        else:
            md += "\t*No level-up moves available*\n\n"

        # TM/HM moves
        md += '=== ":material-disc: TM/HM"\n\n'
        if pokemon.moves.machine:
            md += self._generate_move_table(pokemon.moves.machine, include_level=False)
        else:
            md += "\t*No TM/HM moves available*\n\n"

        # Egg moves
        md += '=== ":material-egg-outline: Egg Moves"\n\n'
        if pokemon.moves.egg:
            md += self._generate_move_table(pokemon.moves.egg, include_level=False)
        else:
            md += "\t*No egg moves available*\n\n"

        # Tutor moves
        md += '=== ":material-school: Tutor"\n\n'
        if pokemon.moves.tutor:
            md += self._generate_move_table(pokemon.moves.tutor, include_level=False)
        else:
            md += "\t*No tutor moves available*\n\n"

        return md

    def _generate_flavor_text(self, pokemon: Pokemon) -> str:
        """Generate the Pokédex flavor text section.

        Args:
            pokemon (Pokemon): The Pokémon object with flavor text data.

        Returns:
            str: Formatted markdown string with the flavor text section.
        """
        md = "## :material-book-open: Pokédex Entries\n\n"

        # Check if any flavor text exists for configured game versions
        has_flavor_text = any(
            getattr(pokemon.flavor_text, version, None)
            for version in POKEDB_GAME_VERSIONS
        )

        if has_flavor_text:
            # Show flavor text for each configured game version
            for idx, version in enumerate(POKEDB_GAME_VERSIONS):
                version_display = format_display_name(version)
                # Use generic book icon for all tabs
                icon = ":material-book:"

                md += f'=== "{icon} {version_display}"\n\n'
                version_text = getattr(pokemon.flavor_text, version, None)
                if version_text:
                    md += f'\t!!! quote ""\n\n'
                    md += f"\t\t{version_text}\n\n"
                else:
                    md += "\t*No entry available*\n\n"
        else:
            md += "*No Pokédex entries available.*\n\n"

        return md

    def _generate_sprites_section(self, pokemon: Pokemon) -> str:
        """Generate the sprites section for a Pokémon.

        Args:
            pokemon (Pokemon): The Pokémon object with sprite data.

        Returns:
            str: Formatted markdown string with the sprites section.
        """
        md = "## :material-image-multiple: Sprites\n\n"

        sprites = pokemon.sprites
        has_female_sprites = False

        # Check if this is a cosmetic form (no animated GIFs available)
        is_cosmetic = any(form.category == "cosmetic" for form in pokemon.forms)

        # Check if this Pokemon has animated sprites
        has_animated = False
        if not is_cosmetic and hasattr(sprites, "versions") and sprites.versions:
            sprite_version = getattr(sprites.versions, POKEDB_SPRITE_VERSION, None)
            if (
                sprite_version
                and sprite_version.animated
                and sprite_version.animated.front_default
            ):
                has_animated = True
                if sprite_version.animated.front_female:
                    has_female_sprites = True

        # In-game Sprites Tab
        md += '=== "In-Game Sprites"\n\n'

        # Use animated sprites for default/variant/transformation, PNG for cosmetic
        if has_animated:
            sprite_version = getattr(sprites.versions, POKEDB_SPRITE_VERSION, None)
            if sprite_version is None:
                return md

            # Normal sprites
            md += "\t**Normal**\n\n"
            md += '\t<div class="grid cards" markdown>\n\n'

            if sprite_version.animated.front_default:
                md += f"\t- ![Front]({sprite_version.animated.front_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tFront\n\n"
            if sprite_version.animated.back_default:
                md += f"\t- ![Back]({sprite_version.animated.back_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tBack\n\n"

            # Female variants if available
            if has_female_sprites:
                if sprite_version.animated.front_female:
                    md += f"\t- ![Front ♀]({sprite_version.animated.front_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront ♀\n\n"
                if sprite_version.animated.back_female:
                    md += f"\t- ![Back ♀]({sprite_version.animated.back_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tBack ♀\n\n"

            md += "\t</div>\n\n"

            # Shiny sprites
            md += "\t**✨ Shiny**\n\n"
            md += '\t<div class="grid cards" markdown>\n\n'

            if sprite_version.animated.front_shiny:
                md += f"\t- ![Front Shiny]({sprite_version.animated.front_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tFront\n\n"
            if sprite_version.animated.back_shiny:
                md += f"\t- ![Back Shiny]({sprite_version.animated.back_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tBack\n\n"

            # Female shiny variants if available
            if has_female_sprites:
                if sprite_version.animated.front_shiny_female:
                    md += f"\t- ![Front Shiny ♀]({sprite_version.animated.front_shiny_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront ♀\n\n"
                if sprite_version.animated.back_shiny_female:
                    md += f"\t- ![Back Shiny ♀]({sprite_version.animated.back_shiny_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tBack ♀\n\n"

            md += "\t</div>\n\n"
        else:
            # Fall back to default PNG sprites for cosmetic forms
            # Check if female sprites are available
            has_png_female_sprites = sprites.front_female or sprites.back_female

            md += "\t**Normal**\n\n"
            md += '\t<div class="grid cards" markdown>\n\n'

            if sprites.front_default:
                md += f"\t- ![Front]({sprites.front_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tFront\n\n"
            if sprites.back_default:
                md += f"\t- ![Back]({sprites.back_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tBack\n\n"

            # Female variants if available
            if has_png_female_sprites:
                if sprites.front_female:
                    md += f"\t- ![Front ♀]({sprites.front_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront ♀\n\n"
                if sprites.back_female:
                    md += f"\t- ![Back ♀]({sprites.back_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tBack ♀\n\n"

            md += "\t</div>\n\n"

            # Shiny sprites
            md += "\t**✨ Shiny**\n\n"
            md += '\t<div class="grid cards" markdown>\n\n'

            if sprites.front_shiny:
                md += f"\t- ![Front Shiny]({sprites.front_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tFront\n\n"
            if sprites.back_shiny:
                md += f"\t- ![Back Shiny]({sprites.back_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tBack\n\n"

            # Female shiny variants if available
            if has_png_female_sprites:
                if sprites.front_shiny_female:
                    md += f"\t- ![Front Shiny ♀]({sprites.front_shiny_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront ♀\n\n"
                if sprites.back_shiny_female:
                    md += f"\t- ![Back Shiny ♀]({sprites.back_shiny_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tBack ♀\n\n"

            md += "\t</div>\n\n"

        # Official Artwork Tab
        md += '=== "Official Artwork"\n\n'

        if (
            hasattr(sprites, "other")
            and sprites.other
            and hasattr(sprites.other, "official_artwork")
        ):
            artwork = sprites.other.official_artwork

            md += '\t<div class="grid cards" markdown>\n\n'

            # Normal artwork
            if artwork.front_default:
                md += f"\t- ![Official Artwork]({artwork.front_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tNormal\n\n"

            # Shiny artwork
            if artwork.front_shiny:
                md += f"\t- ![Shiny Official Artwork]({artwork.front_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\t✨ Shiny\n\n"

            md += "\t</div>\n\n"

        return md

    def _generate_cries_section(self, pokemon: Pokemon) -> str:
        """Generate the cries section with audio players for both legacy and latest cries.

        Args:
            pokemon (Pokemon): The Pokémon object with cry data.

        Returns:
            str: Formatted markdown string with the cries section.
        """
        md = "## :material-volume-high: Cries\n\n"

        if hasattr(pokemon, "cries") and pokemon.cries:
            legacy_cry = getattr(pokemon.cries, "legacy", None)
            latest_cry = getattr(pokemon.cries, "latest", None)

            # Check if we have any cries
            if legacy_cry or latest_cry:
                md += '<div class="grid cards" markdown>\n\n'

                # Legacy cry (original)
                if legacy_cry:
                    md += "- **:material-history: Legacy Cry**\n\n"
                    md += "\t---\n\n"
                    md += f'\t<audio controls style="width: 100%;">\n'
                    md += f'\t\t<source src="{legacy_cry}" type="audio/ogg">\n'
                    md += "\t\tYour browser does not support the audio element.\n"
                    md += "\t</audio>\n\n"
                    md += "\t*Original legacy cry*\n\n"

                # Latest cry (modern)
                if latest_cry:
                    md += "- **:material-new-box: Latest Cry**\n\n"
                    md += "\t---\n\n"
                    md += f'\t<audio controls style="width: 100%;">\n'
                    md += f'\t\t<source src="{latest_cry}" type="audio/ogg">\n'
                    md += "\t\tYour browser does not support the audio element.\n"
                    md += "\t</audio>\n\n"
                    md += "\t*Updated cry from recent games*\n\n"

                md += "</div>\n\n"
            else:
                md += "*Cry audio is not currently available for this Pokémon.*\n\n"
        else:
            md += "*Cry audio is not currently available for this Pokémon.*\n\n"

        return md

    def generate_page(
        self, entry: Pokemon, cache: Optional[dict[str, Any]] = None
    ) -> Path:
        """Generate a markdown page for a single Pokemon.

        Args:
            entry (Pokemon): The Pokémon object to generate a page for.
            cache (Optional[dict[str, Any]], optional): Cache for previously generated pages. Defaults to None.

        Returns:
            Path: The path to the generated markdown file.
        """
        display_name = format_display_name(entry.name)

        # Start building the markdown
        md = f"# {display_name}\n\n"

        # Add sections
        md += self._generate_hero_section(entry)
        md += self._generate_basic_info(entry)
        md += self._generate_held_items_section(entry)
        md += self._generate_type_effectiveness(entry)
        md += self._generate_stats_table(entry)
        md += self._generate_evolution_chain(entry)
        md += self._generate_forms_section(entry)
        md += self._generate_flavor_text(entry)
        md += self._generate_moves_section(entry)
        md += self._generate_sprites_section(entry)
        md += self._generate_cries_section(entry)

        # Write to file
        output_file = self.output_dir / f"{entry.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def update_mkdocs_nav(self, categorized_entries: dict[str, list[Pokemon]]) -> bool:
        """Update mkdocs.yml with navigation links to all Pokemon pages.

        Args:
            categorized_entries (dict[str, list[Pokemon]]): Dictionary mapping generation IDs to lists of Pokemon.

        Raises:
            ValueError: If the mkdocs.yml file is not found or is invalid.
            ValueError: If the navigation structure is invalid.

        Returns:
            bool: True if the update succeeded, False if it failed.
        """
        # Flatten categorized entries back to a single list for Pokemon-specific processing
        all_pokemon = []
        for pokemon_list in categorized_entries.values():
            all_pokemon.extend(pokemon_list)
        try:
            mkdocs_path = self.project_root / "mkdocs.yml"

            if not mkdocs_path.exists():
                self.logger.error(f"mkdocs.yml not found at {mkdocs_path}")
                return False

            # Load current mkdocs.yml using utility
            config = load_mkdocs_config(mkdocs_path)

            # Deduplicate Pokemon by (dex_number, name) to prevent duplicates
            seen_pokemon = set()
            deduplicated_pokemon = []

            for pokemon in all_pokemon:
                pokemon_key = (
                    pokemon.pokedex_numbers.get("national"),
                    pokemon.name,
                )

                if pokemon_key not in seen_pokemon:
                    seen_pokemon.add(pokemon_key)
                    deduplicated_pokemon.append(pokemon)

            # Group Pokemon by national dex number first for form handling
            pokemon_by_dex: dict[int, list[Pokemon]] = defaultdict(list)

            for pokemon in deduplicated_pokemon:
                dex_num = pokemon.pokedex_numbers.get("national")
                if dex_num:
                    pokemon_by_dex[dex_num].append(pokemon)

            # Sort each group: default form first, then alternates
            for dex_num in pokemon_by_dex:
                pokemon_by_dex[dex_num].sort(key=lambda p: (not p.is_default, p.name))

            # Group Pokemon by generation attribute
            pokemon_by_generation: dict[str, dict[int, list[Pokemon]]] = defaultdict(
                lambda: defaultdict(list)
            )

            for dex_num, pokemon_forms in pokemon_by_dex.items():
                # Use the generation from the default form
                default_form = pokemon_forms[0]
                gen = default_form.generation if default_form.generation else "unknown"
                pokemon_by_generation[gen][dex_num] = pokemon_forms

            # Create navigation structure for Pokémon subsection
            pokemon_nav_items = [{"Overview": "pokedex/pokemon.md"}]

            # Build navigation for each generation
            for gen_key in self.subcategory_order:
                if gen_key not in pokemon_by_generation:
                    continue

                display_name = self.subcategory_names.get(gen_key, gen_key)
                gen_pokemon_by_dex = pokemon_by_generation[gen_key]
                sorted_dex_numbers = sorted(gen_pokemon_by_dex.keys())

                gen_nav = []
                for dex_num in sorted_dex_numbers:
                    pokemon_forms = gen_pokemon_by_dex[dex_num]

                    # Get the default form (should be first after sorting)
                    default_form = pokemon_forms[0]
                    base_name = default_form.species

                    # Check if default form has a suffix
                    default_form_suffix = extract_form_suffix(
                        default_form.name, base_name
                    )

                    # Create main entry for default form
                    main_entry = {
                        f"#{dex_num:03d} {format_display_name(default_form.name)}": f"pokedex/pokemon/{default_form.name}.md"
                    }

                    # If there are alternate forms, add them as nested entries
                    if len(pokemon_forms) > 1:
                        # If default form has a suffix, use base species name for main entry
                        # and show all forms (including default) with their suffixes
                        if default_form_suffix:
                            all_forms = []
                            for form in pokemon_forms:
                                form_display = format_display_name(
                                    extract_form_suffix(form.name, base_name)
                                    or "standard"
                                )
                                all_forms.append(
                                    {form_display: f"pokedex/pokemon/{form.name}.md"}
                                )

                            main_entry = {
                                f"#{dex_num:03d} {format_display_name(base_name)}": all_forms
                            }
                        else:
                            # Default has no suffix, keep current behavior
                            alternate_forms = []
                            for alt_form in pokemon_forms[1:]:
                                form_display = format_display_name(
                                    extract_form_suffix(alt_form.name, base_name)
                                    or "standard"
                                )
                                alternate_forms.append(
                                    {
                                        form_display: f"pokedex/pokemon/{alt_form.name}.md"
                                    }
                                )

                            main_entry = {
                                f"#{dex_num:03d} {format_display_name(default_form.name)}": [
                                    {
                                        "Default": f"pokedex/pokemon/{default_form.name}.md"
                                    }
                                ]
                                + alternate_forms
                            }

                    gen_nav.append(main_entry)

                # Using type: ignore because mkdocs nav allows mixed dict value types
                pokemon_nav_items.append({display_name: gen_nav})  # type: ignore

            # Add unknown generation Pokemon if any exist
            if "unknown" in pokemon_by_generation:
                unknown_pokemon_by_dex = pokemon_by_generation["unknown"]
                sorted_unknown_dex = sorted(unknown_pokemon_by_dex.keys())
                unknown_nav = []
                for dex_num in sorted_unknown_dex:
                    pokemon_forms = unknown_pokemon_by_dex[dex_num]
                    default_form = pokemon_forms[0]
                    unknown_nav.append(
                        {
                            f"#{dex_num:03d} {format_display_name(default_form.name)}": f"pokedex/pokemon/{default_form.name}.md"
                        }
                    )
                pokemon_nav_items.append({"Unknown": unknown_nav})  # type: ignore

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

            # Ensure typing is flexible for mixed nav entry value types
            pokedex_nav = cast(list[dict[str, Any]], pokedex_nav)

            # Find or create Pokémon subsection within Pokédex
            pokemon_subsection_index = None
            for i, item in enumerate(pokedex_nav):
                if isinstance(item, dict) and "Pokémon" in item:
                    pokemon_subsection_index = i
                    break

            # Update or append Pokémon subsection
            pokemon_subsection = {"Pokémon": pokemon_nav_items}
            if pokemon_subsection_index is not None:
                pokedex_nav[pokemon_subsection_index] = pokemon_subsection
            else:
                # Prepend Pokémon subsection as the first item
                pokedex_nav.insert(0, pokemon_subsection)

            # Update the config
            nav_list[pokedex_index] = {"Pokédex": pokedex_nav}
            config["nav"] = nav_list

            # Write updated mkdocs.yml using utility
            save_mkdocs_config(mkdocs_path, config)

            total_pokemon = len(pokemon_by_dex)
            total_forms = len(deduplicated_pokemon)
            total_generations = len(
                [g for g in self.subcategory_order if g in pokemon_by_generation]
            )
            self.logger.info(
                f"Updated mkdocs.yml with {total_pokemon} Pokemon ({total_forms} total forms including alternates) organized into {total_generations} generations"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False
