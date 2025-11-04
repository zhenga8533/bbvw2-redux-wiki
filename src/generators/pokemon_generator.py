"""
Generator for individual Pokemon markdown pages.

This generator is specifically designed for Blaze Black 2 & Volt White 2 Redux,
with content prioritizing Black 2 & White 2 data.

This generator:
1. Reads Pokemon data from data/pokedb/parsed/pokemon/
2. Generates individual markdown files for each Pokemon to docs/pokedex/pokemon/
3. Handles Pokemon forms and variations
4. Prioritizes Black 2 & White 2 content (flavor text, etc.)

Note: Styles are applied inline when they depend on dynamic data:
- Hero gradient colors (based on Pokemon types)
- Type badges use format_type_badge() from markdown_util
- Name formatting uses format_display_name() from text_util
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Move, Pokemon
from src.utils.formatters.markdown_formatter import (
    format_ability,
    format_item,
    format_move,
    format_pokemon_card_grid,
    format_type_badge,
)
from src.utils.data.constants import (
    DAMAGE_CLASS_ICONS,
    GENERATION_DISPLAY_NAMES,
    GENERATION_ORDER,
    POKEMON_FORM_SUBFOLDERS_ALL,
    TYPE_COLORS,
)
from src.utils.formatters.table_formatter import (
    create_held_items_table,
    create_move_learnset_table,
    create_pokemon_index_table,
)
from src.utils.text.text_util import extract_form_suffix, format_display_name
from src.utils.data.type_effectiveness import calculate_type_effectiveness
from src.utils.data.pokemon_util import get_pokemon_sprite_url
from src.utils.formatters.yaml_formatter import (
    load_mkdocs_config,
    save_mkdocs_config,
)

from .base_generator import BaseGenerator


# Constants for Pokemon page generation
MAX_STAT_VALUE = 255  # Maximum base stat value for progress bar scaling
MULTI_EVOLUTION_THRESHOLD = 4  # Threshold for special Eevee-style evolution layout
EVOLUTION_GRID_2_COLS_MAX = 6  # Maximum evolutions for 2-column grid
EVOLUTION_GRID_3_COLS_MAX = 9  # Maximum evolutions for 3-column grid


class PokemonGenerator(BaseGenerator):
    """
    Generator for individual Pokemon markdown pages.

    Creates detailed pages for each Pokemon including:
    - Basic information (types, abilities, stats)
    - Evolution chain
    - Move learnset
    - Forms and variations
    - Sprites and images
    """

    def __init__(
        self, output_dir: str = "docs/pokedex", project_root: Optional[Path] = None
    ):
        """
        Initialize the Pokemon page generator.

        Args:
            output_dir: Directory where markdown files will be generated
            project_root: The root directory of the project. If None, it's inferred.
        """
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        # Create pokemon subdirectory
        self.output_dir = self.output_dir / "pokemon"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _stat_bar(self, value: int, max_value: int = MAX_STAT_VALUE) -> str:
        """
        Create a visual progress bar for a stat.

        Args:
            value: The stat value to display
            max_value: Maximum value for scaling (default: 255)

        Returns:
            HTML string representing the progress bar
        """
        percentage = min(100, (value / max_value) * 100)

        # Create a proper progress bar with background and filled portion
        bar_html = f'<div style="background: var(--md-default-fg-color--lightest); border-radius: 4px; overflow: hidden; height: 20px; width: 100%;">'
        bar_html += f'<div style="background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%); height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>'
        bar_html += "</div>"
        return bar_html

    def _format_ability(self, ability_name: str, is_hidden: bool = False) -> str:
        """Format an ability name with link and hidden indicator."""
        formatted_name = format_display_name(ability_name)
        hidden_tag = " *(Hidden)*" if is_hidden else ""
        return f"{formatted_name}{hidden_tag}"

    def _generate_status_badges(self, pokemon: Pokemon) -> str:
        """
        Generate status badges for legendary/mythical/baby Pokemon.
        """
        badges = []
        badge_style = "background: rgba(255, 255, 255, 0.25); padding: 0.5rem 1rem; border-radius: 12px; font-size: 0.875rem; font-weight: 600; color: white; text-transform: uppercase;"

        if pokemon.is_legendary:
            badges.append(f'<span style="{badge_style}">⭐ LEGENDARY</span>')
        elif pokemon.is_mythical:
            badges.append(f'<span style="{badge_style}">✨ MYTHICAL</span>')

        if pokemon.is_baby:
            badges.append(f'<span style="{badge_style}">🍼 BABY</span>')

        return " ".join(badges) if badges else ""

    def _format_form_name(self, pokemon_name: str, base_name: str) -> str:
        """
        Extract and format the form name from a Pokemon's full name.

        Args:
            pokemon_name: Full Pokemon name (e.g., "darmanitan-zen")
            base_name: Base species name (e.g., "darmanitan")

        Returns:
            Formatted form name (e.g., "Zen")
        """
        # Remove base name and leading hyphen
        if pokemon_name.startswith(base_name):
            form_suffix = pokemon_name[len(base_name) :].lstrip("-")
        else:
            form_suffix = pokemon_name

        # If no form suffix, it's the default form
        if not form_suffix:
            return "Standard"

        # Format the form name: replace hyphens with spaces and title case
        formatted_form = form_suffix.replace("-", " ").title()

        return formatted_form

    def _get_type_color(self, type_name: str) -> str:
        """Get the color for a Pokemon type."""
        return TYPE_COLORS.get(type_name.lower(), "#777777")

    def _get_type_effectiveness(self, types: List[str]) -> Dict[str, List[str]]:
        """
        Calculate type effectiveness based on Pokemon's types.

        This method delegates to the type_effectiveness utility module,
        which contains the full type chart data for Generation 5.

        Args:
            types: List of Pokemon types (e.g., ["fire", "flying"])

        Returns:
            Dictionary with damage multipliers categorized by strength
        """
        return calculate_type_effectiveness(types)

    def _generate_hero_section(self, pokemon: Pokemon) -> str:
        """
        Generate a hero section with sprite, types, and badges.
        """
        md = ""

        # Get sprite URL using utility function
        sprite_url = get_pokemon_sprite_url(pokemon)

        # Get type colors for dynamic gradient
        color_1 = "#667eea"  # Default
        color_2 = "#667eea"  # Default

        if pokemon.types:
            color_1 = TYPE_COLORS.get(pokemon.types[0].lower(), "#667eea")
            # Default color 2 to a faded version of color 1
            color_2 = f"{color_1}55"

            if len(pokemon.types) > 1:
                # Get the second type color, but fade it slightly
                color_2 = f"{TYPE_COLORS.get(pokemon.types[1].lower(), color_1)}99"

        # Hero container with dynamic gradient based on type(s)
        md += f'<div style="background: linear-gradient(135deg, {color_1}dd 0%, {color_2} 100%); padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">\n'
        md += '\t<div style="display: flex; flex-direction: column; align-items: center; gap: 1rem;">\n'

        # Sprite
        if sprite_url:
            md += f'\t\t<div style="filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.5));">\n'
            md += f'\t\t\t<img src="{sprite_url}" alt="{pokemon.name}" style="max-width: 120px; image-rendering: pixelated;" />\n'
            md += "\t\t</div>\n"

        # Pokedex number
        if "national" in pokemon.pokedex_numbers:
            dex_num = pokemon.pokedex_numbers["national"]
            md += f'\t\t<div style="font-size: 1.5rem; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">#{dex_num:03d}</div>\n'

        # Regional dex numbers
        regional_dex = {
            k: v
            for k, v in pokemon.pokedex_numbers.items()
            if k != "national" and v is not None
        }
        if regional_dex:
            dex_badges = []
            for region, number in sorted(regional_dex.items()):
                region_name = format_display_name(region).replace("_", " ")
                dex_badges.append(
                    f'<span style="background: rgba(255, 255, 255, 0.2); padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.875rem; color: white;">{region_name}: #{number:03d}</span>'
                )
            md += f'\t\t<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;">{" ".join(dex_badges)}</div>\n'

        # Types
        types_str = " ".join([format_type_badge(t) for t in pokemon.types])
        md += f'\t\t<div class="badges-hstack">{types_str}</div>\n'

        # Status badges
        status_badges = self._generate_status_badges(pokemon)
        if status_badges:
            md += f'\t\t<div class="badges-hstack">{status_badges}</div>\n'

        md += "\t</div>\n"
        md += "</div>\n\n"

        return md

    def _generate_basic_info(self, pokemon: Pokemon) -> str:
        """Generate the basic information section."""
        md = ""

        # Use grid layout for information cards
        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Abilities
        md += "- **:material-shield-star: Abilities**\n\n"
        md += "\t---\n\n"
        for ability in pokemon.abilities:
            # Use format_ability() utility (relative_path="../.." to navigate to docs root, then to pokedex/abilities)
            ability_display = format_ability(
                ability.name, is_linked=True, relative_path="../.."
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
        """
        Generate the held items section showing what items this Pokemon can hold in the wild.

        Prioritizes Black 2 & White 2 data (the focus of this wiki).
        """
        if not pokemon.held_items:
            return ""

        md = "## :material-treasure-chest: Wild Held Items\n\n"
        md += "These items can be found when catching or defeating this Pokémon in the wild:\n\n"

        # Build table rows
        rows = []
        for item_name, rates in pokemon.held_items.items():
            # Convert underscores to hyphens for item identifier
            item_id = item_name.replace("_", "-")
            item_display = format_item(item_id)

            # Get rates for Black 2 & White 2
            black_2_rate = (
                f"{rates.get('black_2', 0)}%" if rates.get("black_2") else "—"
            )
            white_2_rate = (
                f"{rates.get('white_2', 0)}%" if rates.get("white_2") else "—"
            )

            rows.append([item_display, black_2_rate, white_2_rate])

        # Use standardized table utility
        md += create_held_items_table(rows)
        md += "\n"
        return md

    def _generate_type_effectiveness(self, pokemon: Pokemon) -> str:
        """Generate the type effectiveness section with enhanced visuals."""
        md = "## :material-shield-half-full: Type Effectiveness\n\n"

        effectiveness = self._get_type_effectiveness(pokemon.types)

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
        """
        Calculate min and max stat values at level 100 using official Pokemon formulas.

        These formulas are based on Generation 3+ stat calculation mechanics:
        https://bulbapedia.bulbagarden.net/wiki/Stat#Generation_III_onward

        Args:
            base_stat: The base stat value
            is_hp: Whether this is the HP stat (uses different formula)

        Returns:
            Tuple of (min_stat, max_stat) at level 100

        Note:
            Special case: Shedinja always has HP = 1 regardless of calculation
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
        """Generate the stats table section with modern visual bars and level 100 ranges."""
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
            bar = self._stat_bar(value)
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

    def _create_evo_card(self, species_name: str, actual_name: str) -> str:
        """
        Create an evolution card with sprite and name.

        Args:
            species_name: The species name for display
            actual_name: The actual Pokemon name for linking (handles forms)

        Returns:
            HTML string for the evolution card
        """
        display_name = format_display_name(species_name)
        link_name = actual_name or species_name

        # Load Pokemon and get sprite URL using utility function
        sprite_url = None
        try:
            # Try to load from different subfolders
            for subfolder in ["default", "transformation", "variant", "cosmetic"]:
                try:
                    poke = PokeDBLoader.load_pokemon(species_name, subfolder=subfolder)
                    if poke:
                        sprite_url = get_pokemon_sprite_url(poke)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        card_html = f'<a href="{link_name}/" style="display: flex; flex-direction: column; align-items: center; text-decoration: none; padding: 1rem; border-radius: 8px; background: var(--md-default-bg-color); border: 1px solid var(--md-default-fg-color--lightest);">\n'
        if sprite_url:
            card_html += f'\t<img src="{sprite_url}" alt="{display_name}" style="image-rendering: pixelated;" />\n'
        card_html += f'\t<div style="font-weight: 600; text-align: center; white-space: nowrap;">{display_name}</div>\n'
        card_html += "</a>"

        return card_html

    def _format_evo_method(self, evo_details) -> str:
        """
        Format evolution method details into readable text.

        Args:
            evo_details: Evolution details object

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
        """
        Generate the evolution chain section with branching structure.

        Handles various evolution patterns:
        - Simple linear chains (Charmander → Charmeleon → Charizard)
        - Multiple evolutions from one Pokemon (Eevee → 8 evolutions)
        - Branching chains (Wurmple → Silcoon/Cascoon → Beautifly/Dustox)
        """
        md = "## :material-swap-horizontal: Evolution Chain\n\n"

        # Check if this Pokemon doesn't evolve at all
        has_evolutions = bool(pokemon.evolution_chain.evolves_to)
        has_pre_evolution = bool(pokemon.evolves_from_species)

        if not has_evolutions and not has_pre_evolution:
            md += "> :material-information: This Pokémon does not evolve.\n\n"
            return md

        if pokemon.evolves_from_species:
            md += f"*Evolves from {format_display_name(pokemon.evolves_from_species)}*\n\n"

        def extract_all_paths(node, evolution_method=None) -> list:
            """
            Extract all evolution paths from root to leaves.
            evolution_method is the method used to get TO this node.
            """
            # Get actual Pokemon name
            actual_name = node.species_name
            try:
                for subfolder in ["default", "transformation", "variant"]:
                    try:
                        poke = PokeDBLoader.load_pokemon(
                            node.species_name, subfolder=subfolder
                        )
                        if poke:
                            actual_name = poke.name
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Create current Pokemon entry with method to GET TO it
            current_entry = {
                "species_name": node.species_name,
                "actual_name": actual_name,
                "evolution_method": evolution_method,
            }

            # If this is a leaf node (no evolutions), return a path with just this Pokemon
            if not node.evolves_to:
                return [[current_entry]]

            # If has evolutions, recurse for each branch
            all_paths = []
            for evo in node.evolves_to:
                # Get evolution method for this evolution
                method = self._format_evo_method(evo.evolution_details)

                # Get paths from this evolution (with method to get TO that Pokemon)
                branch_paths = extract_all_paths(evo, method)

                # Prepend current Pokemon to each path
                for path in branch_paths:
                    all_paths.append([current_entry] + path)

            return all_paths

        def find_common_prefix(paths):
            """Find the longest common prefix across all paths by species_name."""
            if not paths:
                return []

            prefix = []
            min_length = min(len(path) for path in paths)

            for i in range(min_length):
                # Check if all paths have the same Pokemon at position i
                first_species = paths[0][i]["species_name"]
                if all(path[i]["species_name"] == first_species for path in paths):
                    prefix.append(paths[0][i])
                else:
                    break

            return prefix

        # Extract all evolution paths
        paths = extract_all_paths(pokemon.evolution_chain)

        if not paths:
            return md

        # Calculate max depth (number of stages)
        max_depth = max(len(path) for path in paths)

        # Organize Pokemon by stage instead of by path
        # stages[i] = list of Pokemon at stage i
        stages = [[] for _ in range(max_depth)]

        for path in paths:
            for stage_idx, poke_data in enumerate(path):
                # Check if this Pokemon is already in this stage (avoid duplicates)
                if not any(
                    p["species_name"] == poke_data["species_name"]
                    for p in stages[stage_idx]
                ):
                    stages[stage_idx].append(poke_data)

        # Determine evolution pattern for better layout
        num_final_evolutions = len(stages[-1]) if max_depth > 0 else 0
        has_multiple_stage_2 = max_depth > 1 and len(stages[1]) > 1

        # Pattern detection:
        # - "multi_leaf": Many final evolutions (4+) with only 2 stages (like Eevee)
        # - "complex": Multiple stages or branching at stage 2 (like Wurmple)
        is_multi_leaf = (
            num_final_evolutions >= MULTI_EVOLUTION_THRESHOLD and max_depth == 2
        )

        # Generate HTML container
        md += '<div style="background: var(--md-code-bg-color); border-radius: 8px; padding: 2rem; margin: 1.5rem 0; overflow-x: auto;">\n'

        if is_multi_leaf:
            # Special layout for Eevee-like cases: base on left, evolutions in grid on right
            md += '\t<div style="display: flex; align-items: center; justify-content: center; gap: 2rem;">\n'

            # Left side: Base Pokemon (stage 0)
            if stages[0]:
                md += '\t\t<div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">\n'
                poke_data = stages[0][0]
                md += (
                    "\t\t\t"
                    + self._create_evo_card(
                        poke_data["species_name"], poke_data["actual_name"]
                    )
                    + "\n"
                )
                md += '\t\t\t<div style="font-size: 0.75rem; text-align: center; padding: 0.25rem; color: var(--md-default-fg-color--light);">Base</div>\n'
                md += "\t\t</div>\n"

                # Arrow pointing to evolutions
                md += '\t\t<div style="font-size: 3rem; color: var(--md-primary-fg-color); padding: 0 1rem;">→</div>\n'

            # Right side: Grid of evolutions (stage 1)
            # Adaptive grid: 2 columns for 4-6 evolutions, 3 columns for 7-9, 4 columns for 10+
            if num_final_evolutions <= EVOLUTION_GRID_2_COLS_MAX:
                grid_cols = 2
            elif num_final_evolutions <= EVOLUTION_GRID_3_COLS_MAX:
                grid_cols = 3
            else:
                grid_cols = 4
            md += f'\t\t<div style="display: grid; grid-template-columns: repeat({grid_cols}, 1fr); gap: 1.5rem; max-width: 800px;">\n'

            for poke_data in stages[1]:
                md += '\t\t\t<div style="display: flex; flex-direction: column; align-items: center;">\n'

                # Evolution method at top with fixed height to ensure alignment
                if poke_data["evolution_method"]:
                    md += f'\t\t\t\t<div style="font-size: 0.6rem; text-align: center; padding: 0.4rem; background: var(--md-default-bg-color); border-radius: 4px; max-width: 130px; line-height: 1.2; margin-bottom: 0.5rem; min-height: 3rem; display: flex; align-items: center; justify-content: center;">{poke_data["evolution_method"]}</div>\n'
                else:
                    md += '\t\t\t\t<div style="min-height: 3rem; margin-bottom: 0.5rem;"></div>\n'

                # Pokemon card
                md += (
                    "\t\t\t\t"
                    + self._create_evo_card(
                        poke_data["species_name"], poke_data["actual_name"]
                    )
                    + "\n"
                )

                md += "\t\t\t</div>\n"

            md += "\t\t</div>\n"
            md += "\t</div>\n"

        else:
            # Standard layout: organize by stages (columns)
            # Each column represents an evolution stage
            md += '\t<div style="display: flex; align-items: center; justify-content: center; gap: 1.5rem;">\n'

            # Render each stage as a column
            for stage_idx, stage_pokemon in enumerate(stages):
                if not stage_pokemon:
                    continue

                # Column for this stage
                md += '\t\t<div style="display: flex; flex-direction: column; align-items: stretch; gap: 1.5rem;">\n'

                # Add stage label for first Pokemon in stage
                if stage_idx == 0:
                    md += '\t\t\t<div style="font-size: 0.75rem; font-weight: 600; color: var(--md-default-fg-color--light); text-transform: uppercase; letter-spacing: 0.05em; text-align: center; margin-bottom: 0.5rem;">Stage 1</div>\n'
                else:
                    md += f'\t\t\t<div style="font-size: 0.75rem; font-weight: 600; color: var(--md-default-fg-color--light); text-transform: uppercase; letter-spacing: 0.05em; text-align: center; margin-bottom: 0.5rem;">Stage {stage_idx + 1}</div>\n'

                # Render all Pokemon in this stage
                for poke_idx, poke_data in enumerate(stage_pokemon):
                    md += '\t\t\t<div style="display: flex; flex-direction: column; align-items: center;">\n'

                    # Evolution method at top with fixed height to ensure alignment
                    if poke_data["evolution_method"]:
                        md += f'\t\t\t\t<div style="font-size: 0.6rem; text-align: center; padding: 0.4rem; background: var(--md-default-bg-color); border-radius: 4px; max-width: 130px; line-height: 1.2; margin-bottom: 0.5rem; min-height: 3rem; display: flex; align-items: center; justify-content: center;">{poke_data["evolution_method"]}</div>\n'
                    else:
                        md += '\t\t\t\t<div style="min-height: 3rem; margin-bottom: 0.5rem;"></div>\n'

                    # Pokemon card
                    md += (
                        "\t\t\t\t"
                        + self._create_evo_card(
                            poke_data["species_name"], poke_data["actual_name"]
                        )
                        + "\n"
                    )

                    md += "\t\t\t</div>\n"

                md += "\t\t</div>\n"

                # Add arrow between stages
                if stage_idx < len(stages) - 1 and stages[stage_idx + 1]:
                    current_stage_count = len(stage_pokemon)
                    next_stage_count = len(stages[stage_idx + 1])

                    # Calculate the height needed for proper alignment
                    # Each Pokemon card container has the same structure, so we match the gap
                    md += '\t\t<div style="display: flex; flex-direction: column; align-items: center; gap: 1.5rem;">\n'

                    # Add stage label spacer to align with Pokemon cards
                    md += '\t\t\t<div style="font-size: 0.75rem; font-weight: 600; color: transparent; text-transform: uppercase; letter-spacing: 0.05em; text-align: center; margin-bottom: 0.5rem;">.</div>\n'

                    # Add arrows matching the number of Pokemon in the next stage
                    for arrow_idx in range(max(current_stage_count, next_stage_count)):
                        md += '\t\t\t<div style="display: flex; flex-direction: column; align-items: center;">\n'
                        md += '\t\t\t\t<div style="min-height: 3rem; margin-bottom: 0.5rem; display: flex; align-items: center;"></div>\n'
                        md += '\t\t\t\t<div style="font-size: 2rem; color: var(--md-primary-fg-color); padding: 0 0.5rem;">→</div>\n'
                        md += "\t\t\t</div>\n"

                    md += "\t\t</div>\n"

            md += "\t</div>\n"

        md += "</div>\n\n"

        return md

    def _generate_forms_section(self, pokemon: Pokemon) -> str:
        """
        Generate section showing available forms for this Pokemon with Pokemon cards.

        Only displays if the Pokemon has multiple forms or if forms are switchable.
        """
        # Don't show if only one form and not switchable
        if len(pokemon.forms) <= 1 and not pokemon.forms_switchable:
            return ""

        md = "## :material-shape: Available Forms\n\n"

        if pokemon.forms_switchable:
            md += "> :material-information: Forms are switchable during gameplay.\n\n"

        if len(pokemon.forms) > 1:
            forms = [f.name for f in pokemon.forms]
            md += format_pokemon_card_grid(forms)  # type: ignore
            md += "\n\n"

        return md

    def _generate_move_table(
        self,
        moves: List,
        damage_class_icons: Dict[str, str],
        include_level: bool = False,
        sort_by_level: bool = False,
    ) -> str:
        """
        Generate a move table with formatted move data.

        Args:
            moves: List of move learn objects
            damage_class_icons: Dictionary mapping damage classes to icons
            include_level: Whether to include the level column
            sort_by_level: Whether to sort by level learned (otherwise sort by name)

        Returns:
            Formatted markdown table string
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
            # Use format_move() utility (relative_path="../.." to navigate to docs root, then to pokedex/moves)
            move_name_formatted = format_move(
                move_learn.name, is_linked=True, relative_path="../.."
            )

            if move_data:
                # Get move details
                move_type = move_data.type.black_2_white_2 or "???"
                type_badge = format_type_badge(move_type)

                damage_class = move_data.damage_class
                category_icon = damage_class_icons.get(damage_class, "")

                power = move_data.power.black_2_white_2
                power_str = str(power) if power is not None else "—"

                accuracy = move_data.accuracy.black_2_white_2
                accuracy_str = str(accuracy) if accuracy is not None else "—"

                pp = move_data.pp.black_2_white_2
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
        table_md = create_move_learnset_table(rows, include_level=include_level)

        # Add tab indentation for nested table (in card grids)
        indented_table = "\n".join("\t" + line for line in table_md.split("\n"))

        return indented_table + "\n"

    def _generate_moves_section(self, pokemon: Pokemon) -> str:
        """Generate the moves learnset section with detailed move information."""
        md = "## :material-sword-cross: Moves\n\n"

        # Use tabs for different move categories
        md += '=== ":material-arrow-up-bold: Level-Up"\n\n'
        if pokemon.moves.level_up:
            md += self._generate_move_table(
                pokemon.moves.level_up,
                DAMAGE_CLASS_ICONS,
                include_level=True,
                sort_by_level=True,
            )
        else:
            md += "\t*No level-up moves available*\n\n"

        # TM/HM moves
        md += '=== ":material-disc: TM/HM"\n\n'
        if pokemon.moves.machine:
            md += self._generate_move_table(
                pokemon.moves.machine, DAMAGE_CLASS_ICONS, include_level=False
            )
        else:
            md += "\t*No TM/HM moves available*\n\n"

        # Egg moves
        md += '=== ":material-egg-outline: Egg Moves"\n\n'
        if pokemon.moves.egg:
            md += self._generate_move_table(
                pokemon.moves.egg, DAMAGE_CLASS_ICONS, include_level=False
            )
        else:
            md += "\t*No egg moves available*\n\n"

        # Tutor moves
        md += '=== ":material-school: Tutor"\n\n'
        if pokemon.moves.tutor:
            md += self._generate_move_table(
                pokemon.moves.tutor, DAMAGE_CLASS_ICONS, include_level=False
            )
        else:
            md += "\t*No tutor moves available*\n\n"

        return md

    def _generate_flavor_text(self, pokemon: Pokemon) -> str:
        """
        Generate the Pokédex flavor text section.

        Focuses on Black 2 & White 2 (the main focus of this wiki).
        """
        md = "## :material-book-open: Pokédex Entries\n\n"

        # Pokemon flavor_text uses GameStringMap (individual game versions)
        # Prioritize Black 2 & White 2 since this is a B2W2 Redux wiki
        has_b2w2 = pokemon.flavor_text.black_2 or pokemon.flavor_text.white_2
        has_bw = pokemon.flavor_text.black or pokemon.flavor_text.white

        if has_b2w2:
            # Show Black 2 & White 2 (main focus)
            md += '=== ":material-numeric-2-circle-outline: Black 2"\n\n'
            if pokemon.flavor_text.black_2:
                md += f'\t!!! quote ""\n\n'
                md += f"\t\t{pokemon.flavor_text.black_2}\n\n"
            else:
                md += "\t*No entry available*\n\n"

            md += '=== ":material-numeric-2-circle: White 2"\n\n'
            if pokemon.flavor_text.white_2:
                md += f'\t!!! quote ""\n\n'
                md += f"\t\t{pokemon.flavor_text.white_2}\n\n"
            else:
                md += "\t*No entry available*\n\n"
        else:
            md += "*No Pokédex entries available.*\n\n"

        return md

    def _generate_sprites_section(self, pokemon: Pokemon) -> str:
        """Generate the sprites section with multiple sprite versions."""
        md = "## :material-image-multiple: Sprites\n\n"

        sprites = pokemon.sprites
        has_female_sprites = False

        # Check if this is a cosmetic form (no animated GIFs available)
        is_cosmetic = any(form.category == "cosmetic" for form in pokemon.forms)

        # Check if this Pokemon has animated sprites
        has_animated = False
        if not is_cosmetic and hasattr(sprites, "versions") and sprites.versions:
            bw = sprites.versions.black_white
            if bw.animated and bw.animated.front_default:
                has_animated = True
                if bw.animated.front_female:
                    has_female_sprites = True

        # In-game Sprites Tab
        md += '=== "In-Game Sprites"\n\n'

        # Use animated sprites for default/variant/transformation, PNG for cosmetic
        if has_animated:
            bw = sprites.versions.black_white
            # Normal sprites
            md += "\t**Normal**\n\n"
            md += '\t<div class="grid cards" markdown>\n\n'

            if bw.animated.front_default:
                md += f"\t- ![Front]({bw.animated.front_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tFront\n\n"
            if bw.animated.back_default:
                md += f"\t- ![Back]({bw.animated.back_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tBack\n\n"

            # Female variants if available
            if has_female_sprites:
                if bw.animated.front_female:
                    md += f"\t- ![Front ♀]({bw.animated.front_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront ♀\n\n"
                if bw.animated.back_female:
                    md += f"\t- ![Back ♀]({bw.animated.back_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tBack ♀\n\n"

            md += "\t</div>\n\n"

            # Shiny sprites
            md += "\t**✨ Shiny**\n\n"
            md += '\t<div class="grid cards" markdown>\n\n'

            if bw.animated.front_shiny:
                md += f"\t- ![Front Shiny]({bw.animated.front_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tFront\n\n"
            if bw.animated.back_shiny:
                md += f"\t- ![Back Shiny]({bw.animated.back_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tBack\n\n"

            # Female shiny variants if available
            if has_female_sprites:
                if bw.animated.front_shiny_female:
                    md += f"\t- ![Front Shiny ♀]({bw.animated.front_shiny_female})\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront ♀\n\n"
                if bw.animated.back_shiny_female:
                    md += f"\t- ![Back Shiny ♀]({bw.animated.back_shiny_female})\n\n"
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
        """Generate the cries section with audio players for both legacy and latest cries."""
        md = "## :material-volume-high: Cries\n\n"

        if hasattr(pokemon, "cries") and pokemon.cries:
            legacy_cry = getattr(pokemon.cries, "legacy", None)
            latest_cry = getattr(pokemon.cries, "latest", None)

            # Check if we have any cries
            if legacy_cry or latest_cry:
                md += '<div class="grid cards" markdown>\n\n'

                # Legacy cry (Gen 5 era)
                if legacy_cry:
                    md += "- **:material-history: Legacy Cry**\n\n"
                    md += "\t---\n\n"
                    md += f'\t<audio controls style="width: 100%;">\n'
                    md += f'\t\t<source src="{legacy_cry}" type="audio/ogg">\n'
                    md += "\t\tYour browser does not support the audio element.\n"
                    md += "\t</audio>\n\n"
                    md += "\t*Original cry from Gen 5*\n\n"

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

    def generate_pokemon_page(self, pokemon: Pokemon) -> Path:
        """
        Generate a markdown page for a single Pokemon.

        Args:
            pokemon: The Pokemon data to generate a page for

        Returns:
            Path to the generated markdown file
        """
        display_name = format_display_name(pokemon.name)

        # Start building the markdown
        md = f"# {display_name}\n\n"

        # Genus (species classification)
        md += f"*{pokemon.genus}*\n\n"

        # Hero section with sprite, types, and badges
        md += self._generate_hero_section(pokemon)

        # Add sections
        md += self._generate_basic_info(pokemon)
        md += self._generate_held_items_section(pokemon)
        md += self._generate_type_effectiveness(pokemon)
        md += self._generate_stats_table(pokemon)
        md += self._generate_evolution_chain(pokemon)
        md += self._generate_forms_section(pokemon)
        md += self._generate_flavor_text(pokemon)
        md += self._generate_moves_section(pokemon)
        md += self._generate_sprites_section(pokemon)
        md += self._generate_cries_section(pokemon)

        # Write to file
        output_file = self.output_dir / f"{pokemon.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_pokemon_pages(self, subfolder: str = "default") -> List[Path]:
        """
        Generate markdown pages for all Pokemon in the database, including all forms.

        Args:
            subfolder: Subfolder within pokemon directory to process (legacy parameter,
                      now scans all form subfolders)

        Returns:
            List of paths to generated markdown files
        """
        self.logger.info("Starting generation of all Pokemon pages including forms")

        # Get base Pokemon directory
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"

        # Subfolders to scan for forms (all form categories)
        generated_files = []
        total_pokemon = 0

        for folder in POKEMON_FORM_SUBFOLDERS_ALL:
            pokemon_dir = pokemon_base_dir / folder

            if not pokemon_dir.exists():
                self.logger.debug(f"Subfolder not found, skipping: {folder}")
                continue

            pokemon_files = sorted(pokemon_dir.glob("*.json"))
            self.logger.info(
                f"Found {len(pokemon_files)} Pokemon in subfolder: {folder}"
            )
            total_pokemon += len(pokemon_files)

            for pokemon_file in pokemon_files:
                try:
                    pokemon_name = pokemon_file.stem
                    pokemon = PokeDBLoader.load_pokemon(pokemon_name, subfolder=folder)

                    if pokemon:
                        output_path = self.generate_pokemon_page(pokemon)
                        generated_files.append(output_path)
                    else:
                        self.logger.warning(
                            f"Could not load Pokemon: {pokemon_name} from {folder}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error generating page for {pokemon_file.stem} in {folder}: {e}",
                        exc_info=True,
                    )

        self.logger.info(
            f"Generated {len(generated_files)} Pokemon pages from {total_pokemon} total Pokemon across all subfolders"
        )
        return generated_files

    def generate_pokedex_index(self, subfolder: str = "default") -> Path:
        """
        Generate the main Pokedex index page with links to all Pokemon.

        Args:
            subfolder: Subfolder within pokemon directory to process

        Returns:
            Path to the generated index file
        """
        self.logger.info("Generating Pokedex index page")

        # Get all Pokemon
        pokemon_dir = (
            self.project_root / "data" / "pokedb" / "parsed" / "pokemon" / subfolder
        )
        pokemon_files = sorted(pokemon_dir.glob("*.json"))

        # Load Pokemon data for the index (deduplicate by identity)
        pokemon_list = []
        seen_pokemon = set()  # Track (dex_number, name) to prevent duplicates

        for pokemon_file in pokemon_files:
            try:
                pokemon = PokeDBLoader.load_pokemon(
                    pokemon_file.stem, subfolder=subfolder
                )
                if (
                    pokemon and pokemon.is_default
                ):  # Only include default forms in main list
                    # Create unique key to prevent duplicates
                    pokemon_key = (
                        pokemon.pokedex_numbers.get("national"),
                        pokemon.name,
                    )

                    if pokemon_key not in seen_pokemon:
                        seen_pokemon.add(pokemon_key)
                        pokemon_list.append(pokemon)
            except Exception as e:
                self.logger.error(f"Error loading {pokemon_file.stem}: {e}")

        # Sort by national dex number
        pokemon_list.sort(key=lambda p: p.pokedex_numbers.get("national", 9999))

        # Generate markdown
        md = "# Pokédex\n\n"
        md += "Complete list of all Pokémon in **Blaze Black 2 & Volt White 2 Redux**.\n\n"
        md += "> Click on any Pokémon to see detailed stats, moves, evolutions, and more.\n\n"

        # Group Pokemon by generation
        gen_definitions = [
            ("Generation I", 1, 151, ":material-numeric-1-circle:"),
            ("Generation II", 152, 251, ":material-numeric-2-circle:"),
            ("Generation III", 252, 386, ":material-numeric-3-circle:"),
            ("Generation IV", 387, 493, ":material-numeric-4-circle:"),
            ("Generation V", 494, 649, ":material-numeric-5-circle:"),
        ]

        for gen_name, start, end, icon in gen_definitions:
            # Filter Pokemon for this generation
            gen_pokemon = [
                p
                for p in pokemon_list
                if start <= p.pokedex_numbers.get("national", 0) <= end
            ]

            if not gen_pokemon:
                continue

            # Add generation header
            md += f"## {icon} {gen_name}\n\n"
            md += f"*National Dex #{start:03d} - #{end:03d}*\n\n"

            # Build table rows for this generation
            rows = []
            for pokemon in gen_pokemon:
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = format_display_name(pokemon.name)
                link = f"[{name}](pokemon/{pokemon.name}.md)"
                # Stack types vertically with spacing
                type_badges = " ".join([format_type_badge(t) for t in pokemon.types])
                types = f'<div class="badges-vstack">{type_badges}</div>'

                # Get sprite URL using utility function
                sprite_url = get_pokemon_sprite_url(pokemon)

                # Create sprite cell
                if sprite_url:
                    sprite_cell = f'<img src="{sprite_url}" alt="{name}" style="max-width: 80px; image-rendering: pixelated;" />'
                else:
                    sprite_cell = "—"

                # Get non-hidden abilities
                abilities = [a.name for a in pokemon.abilities if not a.is_hidden]
                abilities_str = ", ".join(
                    [format_display_name(a) for a in abilities[:2]]
                )  # Show max 2

                rows.append(
                    [f"**{dex_num:03d}**", sprite_cell, link, types, abilities_str]
                )

            # Use standardized table utility
            md += create_pokemon_index_table(rows)
            md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "pokemon.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated Pokemon index: {output_file}")
        return output_file

    def update_mkdocs_navigation(self, subfolder: str = "default") -> bool:
        """
        Update mkdocs.yml with navigation links to all Pokemon pages.

        Args:
            subfolder: Subfolder within pokemon directory to process

        Returns:
            bool: True if update succeeded, False if it failed
        """
        try:
            mkdocs_path = self.project_root / "mkdocs.yml"

            if not mkdocs_path.exists():
                self.logger.error(f"mkdocs.yml not found at {mkdocs_path}")
                return False

            # Load current mkdocs.yml using utility
            config = load_mkdocs_config(mkdocs_path)

            # Get all Pokemon for navigation from multiple subfolders
            pokemon_base_dir = (
                self.project_root / "data" / "pokedb" / "parsed" / "pokemon"
            )

            # Load all Pokemon and group by national dex number
            all_pokemon = []
            seen_pokemon = set()  # Track (dex_number, name) to prevent duplicates

            for folder in POKEMON_FORM_SUBFOLDERS_ALL:
                folder_path = pokemon_base_dir / folder
                if not folder_path.exists():
                    continue

                pokemon_files = sorted(folder_path.glob("*.json"))
                for pokemon_file in pokemon_files:
                    try:
                        pokemon = PokeDBLoader.load_pokemon(
                            pokemon_file.stem, subfolder=folder
                        )
                        if pokemon:
                            # Create unique key to prevent duplicates
                            pokemon_key = (
                                pokemon.pokedex_numbers.get("national"),
                                pokemon.name,
                            )

                            if pokemon_key not in seen_pokemon:
                                seen_pokemon.add(pokemon_key)
                                all_pokemon.append(pokemon)
                    except Exception as e:
                        self.logger.warning(
                            f"Could not load {pokemon_file.stem} from {folder}: {e}"
                        )

            # Group Pokemon by national dex number first for form handling
            from collections import defaultdict

            pokemon_by_dex: Dict[int, List[Pokemon]] = defaultdict(list)

            for pokemon in all_pokemon:
                dex_num = pokemon.pokedex_numbers.get("national")
                if dex_num:
                    pokemon_by_dex[dex_num].append(pokemon)

            # Sort each group: default form first, then alternates
            for dex_num in pokemon_by_dex:
                pokemon_by_dex[dex_num].sort(key=lambda p: (not p.is_default, p.name))

            # Group Pokemon by generation attribute
            pokemon_by_generation: Dict[str, Dict[int, List[Pokemon]]] = defaultdict(
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
            for gen_key in GENERATION_ORDER:
                if gen_key not in pokemon_by_generation:
                    continue

                display_name = GENERATION_DISPLAY_NAMES.get(gen_key, gen_key)
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
                                form_display = self._format_form_name(
                                    form.name, base_name
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
                                form_display = self._format_form_name(
                                    alt_form.name, base_name
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
            pokedex_nav = cast(List[Dict[str, Any]], pokedex_nav)

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
            total_forms = len(all_pokemon)
            total_generations = len(
                [g for g in GENERATION_ORDER if g in pokemon_by_generation]
            )
            self.logger.info(
                f"Updated mkdocs.yml with {total_pokemon} Pokemon ({total_forms} total forms including alternates) organized into {total_generations} generations"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False

    def generate(self, subfolder: str = "default") -> bool:
        """
        Generate Pokemon pages and Pokedex index.

        Args:
            subfolder: Subfolder within pokemon directory to process

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        self.logger.info("Starting Pokedex generation...")
        try:
            # Generate all Pokemon pages
            self.logger.info("Generating individual Pokemon pages...")
            pokemon_files = self.generate_all_pokemon_pages(subfolder=subfolder)

            if not pokemon_files:
                self.logger.error("No Pokemon pages were generated")
                return False

            # Generate the Pokedex index
            self.logger.info("Generating Pokedex index...")
            index_path = self.generate_pokedex_index(subfolder=subfolder)

            # Update mkdocs.yml navigation
            self.logger.info("Updating mkdocs.yml navigation...")
            nav_success = self.update_mkdocs_navigation(subfolder=subfolder)

            if not nav_success:
                self.logger.warning(
                    "Failed to update mkdocs.yml navigation, but pages were generated successfully"
                )

            self.logger.info(
                f"Successfully generated {len(pokemon_files)} Pokemon pages and index"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate Pokedex: {e}", exc_info=True)
            return False
