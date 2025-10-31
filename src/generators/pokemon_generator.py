"""
Generator for individual Pokemon markdown pages.

This generator:
1. Reads Pokemon data from data/pokedb/parsed/pokemon/
2. Generates individual markdown files for each Pokemon to docs/pokedex/pokemon/
3. Handles Pokemon forms and variations
"""

from pathlib import Path
from typing import Optional, Dict, List
from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Pokemon, Move
from src.utils.markdown_util import format_item
from src.utils.text_util import extract_form_suffix
from src.utils.yaml_util import load_mkdocs_config, save_mkdocs_config
from .base_generator import BaseGenerator
import html


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

    # Type colors for badges and styling
    TYPE_COLORS = {
        "normal": "#A8A878",
        "fire": "#F08030",
        "water": "#6890F0",
        "electric": "#F8D030",
        "grass": "#78C850",
        "ice": "#98D8D8",
        "fighting": "#C03028",
        "poison": "#A040A0",
        "ground": "#E0C068",
        "flying": "#A890F0",
        "psychic": "#F85888",
        "bug": "#A8B820",
        "rock": "#B8A038",
        "ghost": "#705898",
        "dragon": "#7038F8",
        "dark": "#705848",
        "steel": "#B8B8D0",
        "fairy": "#EE99AC",
    }

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

    def _format_name(self, name: str) -> str:
        """Format a Pokemon name for display (capitalize and handle special cases)."""
        # Handle special characters and formatting
        name = name.replace("-", " ")

        # Special cases for proper capitalization
        special_cases = {
            "nidoran f": "Nidoran♀",
            "nidoran m": "Nidoran♂",
            "mr mime": "Mr. Mime",
            "mime jr": "Mime Jr.",
            "type null": "Type: Null",
            "ho oh": "Ho-Oh",
        }

        lower_name = name.lower()
        if lower_name in special_cases:
            return special_cases[lower_name]

        # Default: title case
        return name.title()

    def _format_type(self, type_name: str) -> str:
        """Format a type name with modern color badge."""
        color = self.TYPE_COLORS.get(type_name.lower(), "#777777")
        formatted_name = type_name.title()

        # Modern badge with gradient and better shadow
        return f'<span style="display: inline-block; background: linear-gradient(135deg, {color}, {color}dd); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; margin: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.15), 0 1px 3px rgba(0,0,0,0.1); text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px;">{formatted_name}</span>'

    def _stat_bar(self, value: int, max_value: int = 255) -> str:
        """Create a modern visual progress bar for a stat."""
        percentage = min(100, (value / max_value) * 100)

        # Color based on value with gradients
        if value >= 150:
            gradient = "linear-gradient(90deg, #4CAF50, #66BB6A)"  # Green gradient
        elif value >= 100:
            gradient = "linear-gradient(90deg, #2196F3, #42A5F5)"  # Blue gradient
        elif value >= 70:
            gradient = "linear-gradient(90deg, #FF9800, #FFA726)"  # Orange gradient
        else:
            gradient = "linear-gradient(90deg, #F44336, #EF5350)"  # Red gradient

        # Return just the bar without the number (number is shown in the Value column)
        return f'<div style="width: 100%; background: linear-gradient(to right, #e8e8e8, #f5f5f5); border-radius: 10px; height: 24px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);"><div style="width: {percentage}%; background: {gradient}; height: 100%; transition: width 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div></div>'

    def _format_ability(self, ability_name: str, is_hidden: bool = False) -> str:
        """Format an ability name with link and hidden indicator."""
        formatted_name = self._format_name(ability_name)
        hidden_tag = " *(Hidden)*" if is_hidden else ""
        return f"{formatted_name}{hidden_tag}"

    def _generate_status_badges(self, pokemon: Pokemon) -> str:
        """Generate modern status badges for legendary/mythical/baby Pokemon."""
        badges = []

        if pokemon.is_legendary:
            badges.append(
                '<span style="display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 700; margin: 4px; box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4), 0 2px 4px rgba(0,0,0,0.2); text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; border: 2px solid rgba(255,255,255,0.3);">⭐ LEGENDARY</span>'
            )
        elif pokemon.is_mythical:
            badges.append(
                '<span style="display: inline-block; background: linear-gradient(135deg, #9370DB 0%, #8A2BE2 100%); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 700; margin: 4px; box-shadow: 0 4px 12px rgba(147, 112, 219, 0.4), 0 2px 4px rgba(0,0,0,0.2); text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; border: 2px solid rgba(255,255,255,0.3);">✨ MYTHICAL</span>'
            )

        if pokemon.is_baby:
            badges.append(
                '<span style="display: inline-block; background: linear-gradient(135deg, #FFB6C1 0%, #FF69B4 100%); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 700; margin: 4px; box-shadow: 0 4px 12px rgba(255, 182, 193, 0.4), 0 2px 4px rgba(0,0,0,0.2); text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; border: 2px solid rgba(255,255,255,0.3);">🍼 BABY</span>'
            )

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
        return self.TYPE_COLORS.get(type_name.lower(), "#777777")

    def _format_move_with_tooltip(
        self, move_name: str, move_data: Optional[Move]
    ) -> str:
        """Format a move name with type color and tooltip."""
        if not move_data:
            return self._format_name(move_name)

        # Get move type and color
        move_type = move_data.type.black_2_white_2
        type_color = self._get_type_color(move_type) if move_type else "#777"

        # Get flavor text for tooltip
        flavor = move_data.flavor_text.black_2_white_2
        if flavor:
            escaped_flavor = html.escape(flavor)
            style = f"border-bottom: 1px dashed {type_color}; cursor: help; color: {type_color};"
            return f'<span style="{style}" title="{escaped_flavor}">{self._format_name(move_name)}</span>'
        else:
            return f'<span style="color: {type_color};">{self._format_name(move_name)}</span>'

    def _get_type_effectiveness(self, types: List[str]) -> Dict[str, List[str]]:
        """Calculate type effectiveness based on Pokemon's types."""
        # Type effectiveness chart (simplified for Gen 5)
        effectiveness = {
            "normal": {
                "weak_to": ["fighting"],
                "resistant_to": [],
                "immune_to": ["ghost"],
            },
            "fire": {
                "weak_to": ["water", "ground", "rock"],
                "resistant_to": ["fire", "grass", "ice", "bug", "steel", "fairy"],
                "immune_to": [],
            },
            "water": {
                "weak_to": ["electric", "grass"],
                "resistant_to": ["fire", "water", "ice", "steel"],
                "immune_to": [],
            },
            "electric": {
                "weak_to": ["ground"],
                "resistant_to": ["electric", "flying", "steel"],
                "immune_to": [],
            },
            "grass": {
                "weak_to": ["fire", "ice", "poison", "flying", "bug"],
                "resistant_to": ["water", "electric", "grass", "ground"],
                "immune_to": [],
            },
            "ice": {
                "weak_to": ["fire", "fighting", "rock", "steel"],
                "resistant_to": ["ice"],
                "immune_to": [],
            },
            "fighting": {
                "weak_to": ["flying", "psychic", "fairy"],
                "resistant_to": ["bug", "rock", "dark"],
                "immune_to": [],
            },
            "poison": {
                "weak_to": ["ground", "psychic"],
                "resistant_to": ["grass", "fighting", "poison", "bug", "fairy"],
                "immune_to": [],
            },
            "ground": {
                "weak_to": ["water", "grass", "ice"],
                "resistant_to": ["poison", "rock"],
                "immune_to": ["electric"],
            },
            "flying": {
                "weak_to": ["electric", "ice", "rock"],
                "resistant_to": ["grass", "fighting", "bug"],
                "immune_to": ["ground"],
            },
            "psychic": {
                "weak_to": ["bug", "ghost", "dark"],
                "resistant_to": ["fighting", "psychic"],
                "immune_to": [],
            },
            "bug": {
                "weak_to": ["fire", "flying", "rock"],
                "resistant_to": ["grass", "fighting", "ground"],
                "immune_to": [],
            },
            "rock": {
                "weak_to": ["water", "grass", "fighting", "ground", "steel"],
                "resistant_to": ["normal", "fire", "poison", "flying"],
                "immune_to": [],
            },
            "ghost": {
                "weak_to": ["ghost", "dark"],
                "resistant_to": ["poison", "bug"],
                "immune_to": ["normal", "fighting"],
            },
            "dragon": {
                "weak_to": ["ice", "dragon", "fairy"],
                "resistant_to": ["fire", "water", "electric", "grass"],
                "immune_to": [],
            },
            "dark": {
                "weak_to": ["fighting", "bug", "fairy"],
                "resistant_to": ["ghost", "dark"],
                "immune_to": ["psychic"],
            },
            "steel": {
                "weak_to": ["fire", "fighting", "ground"],
                "resistant_to": [
                    "normal",
                    "grass",
                    "ice",
                    "flying",
                    "psychic",
                    "bug",
                    "rock",
                    "dragon",
                    "steel",
                    "fairy",
                ],
                "immune_to": ["poison"],
            },
            "fairy": {
                "weak_to": ["poison", "steel"],
                "resistant_to": ["fighting", "bug", "dark"],
                "immune_to": ["dragon"],
            },
        }

        # Calculate combined effectiveness
        weak_multiplier = {}
        resist_multiplier = {}
        immune_types = set()

        for poke_type in types:
            type_data = effectiveness.get(poke_type.lower(), {})
            for weak_type in type_data.get("weak_to", []):
                weak_multiplier[weak_type] = weak_multiplier.get(weak_type, 1) * 2
            for resist_type in type_data.get("resistant_to", []):
                resist_multiplier[resist_type] = (
                    resist_multiplier.get(resist_type, 1) * 0.5
                )
            for immune_type in type_data.get("immune_to", []):
                immune_types.add(immune_type)

        # Process resistances (some might be neutralized by weaknesses)
        for resist_type, mult in list(resist_multiplier.items()):
            if resist_type in weak_multiplier:
                # Combine multipliers
                combined = weak_multiplier[resist_type] * mult
                if combined > 1:
                    weak_multiplier[resist_type] = combined
                elif combined < 1:
                    resist_multiplier[resist_type] = combined
                else:
                    # Neutral - remove from both
                    weak_multiplier.pop(resist_type, None)
                    resist_multiplier.pop(resist_type, None)
                # Remove from weak since we've combined
                if resist_type in weak_multiplier and resist_type in resist_multiplier:
                    weak_multiplier.pop(resist_type, None)

        # Filter out immunities from weaknesses and resistances
        for immune in immune_types:
            weak_multiplier.pop(immune, None)
            resist_multiplier.pop(immune, None)

        return {
            "4x_weak": [t for t, m in weak_multiplier.items() if m >= 4],
            "2x_weak": [t for t, m in weak_multiplier.items() if m == 2],
            "0.5x_resist": [t for t, m in resist_multiplier.items() if m == 0.5],
            "0.25x_resist": [t for t, m in resist_multiplier.items() if m <= 0.25],
            "immune": list(immune_types),
        }

    def _generate_hero_section(self, pokemon: Pokemon) -> str:
        """Generate a modern hero section with sprite, types, and badges."""
        md = ""

        # Get sprite URL
        sprite_url = None
        if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
            bw = pokemon.sprites.versions.black_white
            if bw.animated and bw.animated.front_default:
                sprite_url = bw.animated.front_default

        # Get type colors for dynamic gradient
        color_1 = "#667eea"  # Default
        color_2 = "#667eea"  # Default

        if pokemon.types:
            color_1 = self.TYPE_COLORS.get(pokemon.types[0].lower(), "#667eea")
            # Default color 2 to a faded version of color 1
            color_2 = f"{color_1}55"

            if len(pokemon.types) > 1:
                # Get the second type color, but fade it slightly
                color_2 = f"{self.TYPE_COLORS.get(pokemon.types[1].lower(), color_1)}99"

        # Modern hero container with dynamic gradient based on type(s)
        md += f'<div style="text-align: center; padding: 32px 24px; background: linear-gradient(135deg, {color_1}dd 0%, {color_2} 100%), linear-gradient(to bottom, rgba(255,255,255,0.1), rgba(0,0,0,0.1)); border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 24px rgba(0,0,0,0.2), 0 2px 8px rgba(0,0,0,0.1); position: relative; overflow: hidden;">\n'

        # Subtle pattern overlay
        md += '  <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.05; background-image: repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.1) 10px, rgba(255,255,255,.1) 20px);"></div>\n'
        md += '  <div style="position: relative; z-index: 1;">\n'

        # Sprite with glow effect (fixed scaling)
        if sprite_url:
            md += f'    <div style="margin-bottom: 16px;">\n'
            md += f'      <img src="{sprite_url}" alt="{pokemon.name}" style="height: 128px; width: auto; image-rendering: pixelated; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));" />\n'
            md += "    </div>\n"

        # Pokedex number with modern styling
        if "national" in pokemon.pokedex_numbers:
            dex_num = pokemon.pokedex_numbers["national"]
            md += f'    <div style="color: white; font-size: 24px; font-weight: 800; margin-bottom: 12px; text-shadow: 0 2px 8px rgba(0,0,0,0.3); letter-spacing: 1px;">#{dex_num:03d}</div>\n'

        # Regional dex numbers with modern badges
        regional_dex = {
            k: v
            for k, v in pokemon.pokedex_numbers.items()
            if k != "national" and v is not None
        }
        if regional_dex:
            dex_badges = []
            for region, number in sorted(regional_dex.items()):
                region_name = self._format_name(region)
                dex_badges.append(
                    f'<span style="display: inline-block; background-color: rgba(255,255,255,0.25); backdrop-filter: blur(10px); color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; margin: 3px; font-weight: 600; border: 1px solid rgba(255,255,255,0.3);">{region_name}: #{number:03d}</span>'
                )
            md += (
                f'    <div style="margin-bottom: 16px;">{" ".join(dex_badges)}</div>\n'
            )

        # Types with better spacing
        types_str = " ".join([self._format_type(t) for t in pokemon.types])
        md += f'    <div style="margin: 16px 0;">{types_str}</div>\n'

        # Status badges
        status_badges = self._generate_status_badges(pokemon)
        if status_badges:
            md += f'    <div style="margin-top: 16px;">{status_badges}</div>\n'

        md += "  </div>\n"  # Close relative div
        md += "</div>\n\n"

        return md

    def _generate_basic_info(self, pokemon: Pokemon) -> str:
        """Generate the basic information section."""
        md = ""

        # Use grid layout for information cards
        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Abilities
        md += "- **:material-shield-star: Abilities**\n\n"
        md += "    ---\n\n"
        for ability in pokemon.abilities:
            hidden_emoji = " :material-eye-off:" if ability.is_hidden else ""
            # Load ability data for tooltip
            ability_data = PokeDBLoader.load_ability(ability.name)
            if ability_data and ability_data.flavor_text.black_2_white_2:
                flavor = ability_data.flavor_text.black_2_white_2
                escaped_flavor = html.escape(flavor)
                ability_display = f'<span style="border-bottom: 1px dashed #777; cursor: help;" title="{escaped_flavor}">{self._format_name(ability.name)}</span>{hidden_emoji}'
            else:
                ability_display = f"{self._format_name(ability.name)}{hidden_emoji}"
            md += f"    - {ability_display}\n"
        md += "\n"

        # Card 2: Physical Attributes
        height_m = pokemon.height / 10
        weight_kg = pokemon.weight / 10
        md += "- **:material-ruler: Physical Attributes**\n\n"
        md += "    ---\n\n"
        md += f"    **Height:** {height_m:.1f} m\n\n"
        md += f"    **Weight:** {weight_kg:.1f} kg\n\n"
        md += "\n"

        # Card 3: Training Info
        md += "- **:material-book-education: Training**\n\n"
        md += "    ---\n\n"
        md += f"    **Base Experience:** {pokemon.base_experience}\n\n"
        md += f"    **Base Happiness:** {pokemon.base_happiness}\n\n"
        md += f"    **Capture Rate:** {pokemon.capture_rate}\n\n"
        md += f"    **Growth Rate:** {self._format_name(pokemon.growth_rate)}\n\n"
        if pokemon.habitat:
            md += f"    **Habitat:** {self._format_name(pokemon.habitat)}\n\n"
        md += "\n"

        # Card 4: Breeding Info
        md += "- **:material-egg: Breeding**\n\n"
        md += "    ---\n\n"
        if pokemon.gender_rate == -1:
            md += "    **Gender:** Genderless\n\n"
        else:
            female_pct = (pokemon.gender_rate / 8) * 100
            male_pct = 100 - female_pct
            md += f"    **Gender Ratio:** {male_pct:.1f}% ♂ / {female_pct:.1f}% ♀\n\n"
        md += f"    **Egg Groups:** {', '.join([self._format_name(eg) for eg in pokemon.egg_groups])}\n\n"
        md += f"    **Hatch Counter:** {pokemon.hatch_counter} cycles\n\n"

        md += "</div>\n\n"

        return md

    def _generate_held_items_section(self, pokemon: Pokemon) -> str:
        """Generate the held items section showing what items this Pokemon can hold in the wild."""
        if not pokemon.held_items:
            return ""

        md = "## :material-treasure-chest: Wild Held Items\n\n"
        md += '!!! tip "Wild Encounters"\n\n'
        md += "    These items can be found when catching or defeating this Pokémon in the wild:\n\n"

        # Create a modern table
        md += "    | Item | Black | White | Black 2 | White 2 |\n"
        md += "    |------|:-----:|:-----:|:-------:|:-------:|\n"

        for item_name, rates in pokemon.held_items.items():
            item_display = format_item(item_name.replace("_", " ").title())

            # Get rates for each version with better formatting
            black_rate = f"**{rates.get('black', 0)}%**" if rates.get("black") else "—"
            white_rate = f"**{rates.get('white', 0)}%**" if rates.get("white") else "—"
            black_2_rate = (
                f"**{rates.get('black_2', 0)}%**" if rates.get("black_2") else "—"
            )
            white_2_rate = (
                f"**{rates.get('white_2', 0)}%**" if rates.get("white_2") else "—"
            )

            md += f"    | **{item_display}** | {black_rate} | {white_rate} | {black_2_rate} | {white_2_rate} |\n"

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
            md += "    ---\n\n"
            if effectiveness["4x_weak"]:
                md += "    **4× Damage**\n\n"
                md += "    "
                md += " ".join(
                    [self._format_type(t) for t in sorted(effectiveness["4x_weak"])]
                )
                md += "\n\n"
            if effectiveness["2x_weak"]:
                md += "    **2× Damage**\n\n"
                md += "    "
                md += " ".join(
                    [self._format_type(t) for t in sorted(effectiveness["2x_weak"])]
                )
                md += "\n\n"

        # Resistances card
        if effectiveness["0.25x_resist"] or effectiveness["0.5x_resist"]:
            md += "- **:material-shield-check: Resists**\n\n"
            md += "    ---\n\n"
            if effectiveness["0.25x_resist"]:
                md += "    **¼× Damage**\n\n"
                md += "    "
                md += " ".join(
                    [
                        self._format_type(t)
                        for t in sorted(effectiveness["0.25x_resist"])
                    ]
                )
                md += "\n\n"
            if effectiveness["0.5x_resist"]:
                md += "    **½× Damage**\n\n"
                md += "    "
                md += " ".join(
                    [self._format_type(t) for t in sorted(effectiveness["0.5x_resist"])]
                )
                md += "\n\n"

        # Immunities card
        if effectiveness["immune"]:
            md += "- **:material-shield: Immune To**\n\n"
            md += "    ---\n\n"
            md += "    **No Damage**\n\n"
            md += "    "
            md += " ".join(
                [self._format_type(t) for t in sorted(effectiveness["immune"])]
            )
            md += "\n\n"

        md += "</div>\n\n"

        return md

    def _generate_stats_table(self, pokemon: Pokemon) -> str:
        """Generate the stats table section with modern visual bars."""
        md = "## :material-chart-bar: Base Stats\n\n"

        stats_display = [
            ("HP", pokemon.stats.hp),
            ("Attack", pokemon.stats.attack),
            ("Defense", pokemon.stats.defense),
            ("Sp. Atk", pokemon.stats.special_attack),
            ("Sp. Def", pokemon.stats.special_defense),
            ("Speed", pokemon.stats.speed),
        ]

        total = sum([s[1] for s in stats_display])

        # Create a modern table with stat bars
        md += "| Stat | Value | Distribution |\n"
        md += "|------|------:|:-------------|\n"

        for stat_name, value in stats_display:
            bar = self._stat_bar(value)
            md += f"| **{stat_name}** | **{value}** | {bar} |\n"

        # Total with highlight
        md += f"| **Base Stat Total** | **{total}** | |\n\n"

        # EV Yield in a modern admonition
        if pokemon.ev_yield:
            md += '!!! success "EV Yield"\n'
            md += "    Defeating this Pokémon awards:\n\n"
            for ev in pokemon.ev_yield:
                stat_name = self._format_name(ev.stat)
                md += f"    - **+{ev.effort}** {stat_name} EV\n"
            md += "\n"

        return md

    def _generate_evolution_chain(self, pokemon: Pokemon) -> str:
        """Generate the evolution chain section."""
        md = "## :material-swap-horizontal: Evolution Chain\n\n"

        if pokemon.evolves_from_species:
            md += f'!!! info "Evolution"\n\n'
            md += f"    Evolves from **{self._format_name(pokemon.evolves_from_species)}**\n\n"

        def format_evolution_node(node, level=0, evolution_method="") -> str:
            result = ""
            indent = "  " * level

            # Format the current Pokemon
            display_name = self._format_name(node.species_name)

            # Try to load Pokemon data to get stat total AND actual file name
            stat_total_str = ""
            actual_pokemon_name = node.species_name
            try:
                # Try to load from different subfolders
                evo_pokemon = None
                for subfolder in ["default", "transformation", "variant"]:
                    try:
                        evo_pokemon = PokeDBLoader.load_pokemon(
                            node.species_name, subfolder=subfolder
                        )
                        if evo_pokemon:
                            # Use the actual Pokemon's name for the link (handles forms correctly)
                            actual_pokemon_name = evo_pokemon.name
                            break
                    except:
                        continue
            except:
                pass

            # Create link using the actual Pokemon name (which includes form suffix if needed)
            pokemon_link = f"[{display_name}]({actual_pokemon_name}.md)"

            # Show evolution method if provided (for non-root Pokemon)
            method_str = f" — *{evolution_method}*" if evolution_method else ""
            result += f"{indent}- {pokemon_link}{stat_total_str}{method_str}\n"

            # If this has evolutions, show them
            if node.evolves_to:
                for evo in node.evolves_to:
                    # Collect evolution method details
                    details = []
                    evo_details = evo.evolution_details

                    if evo_details:
                        if evo_details.min_level:
                            details.append(f"Level {evo_details.min_level}")
                        if evo_details.item:
                            details.append(f"Use {self._format_name(evo_details.item)}")
                        if evo_details.held_item:
                            details.append(
                                f"Hold {self._format_name(evo_details.held_item)}"
                            )
                        if evo_details.known_move:
                            details.append(
                                f"Know {self._format_name(evo_details.known_move)}"
                            )
                        if evo_details.min_happiness:
                            details.append(f"Happiness {evo_details.min_happiness}+")
                        if evo_details.time_of_day:
                            details.append(f"During {evo_details.time_of_day}")
                        if evo_details.location:
                            details.append(
                                f"At {self._format_name(evo_details.location)}"
                            )

                    detail_str = ", ".join(details) if details else "Unknown method"
                    result += format_evolution_node(evo, level + 1, detail_str)

            return result

        md += format_evolution_node(pokemon.evolution_chain)
        md += "\n"

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
        md = ""

        # Generate header
        if include_level:
            md += "    | Level | Move | Type | Category | Power | Acc | PP |\n"
            md += "    |-------|------|------|----------|-------|-----|----|\n"
        else:
            md += "    | Move | Type | Category | Power | Acc | PP |\n"
            md += "    |------|------|----------|-------|-----|----|\n"

        # Sort moves
        if sort_by_level:
            sorted_moves = sorted(moves, key=lambda m: m.level_learned_at)
        else:
            sorted_moves = sorted(moves, key=lambda m: m.name)

        # Generate rows
        for move_learn in sorted_moves:
            move_data = PokeDBLoader.load_move(move_learn.name)
            move_name_formatted = self._format_move_with_tooltip(
                move_learn.name, move_data
            )

            if move_data:
                # Get move details
                move_type = move_data.type.black_2_white_2 or "???"
                type_badge = self._format_type(move_type)

                damage_class = move_data.damage_class
                category_icon = damage_class_icons.get(damage_class, "")

                power = move_data.power.black_2_white_2
                power_str = str(power) if power is not None else "—"

                accuracy = move_data.accuracy.black_2_white_2
                accuracy_str = str(accuracy) if accuracy is not None else "—"

                pp = move_data.pp.black_2_white_2
                pp_str = str(pp) if pp is not None else "—"

                if include_level:
                    level = move_learn.level_learned_at
                    md += f"    | {level} | {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
                else:
                    md += f"    | {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
            else:
                # Fallback if move data not available
                if include_level:
                    level = move_learn.level_learned_at
                    md += f"    | {level} | {self._format_name(move_learn.name)} | — | — | — | — | — |\n"
                else:
                    md += f"    | {self._format_name(move_learn.name)} | — | — | — | — | — |\n"

        return md

    def _generate_moves_section(self, pokemon: Pokemon) -> str:
        """Generate the moves learnset section with detailed move information."""
        md = "## :material-sword-cross: Moves\n\n"

        # Damage class icons (using valid Material Design icons)
        damage_class_icons = {
            "physical": ":material-sword:",
            "special": ":material-auto-fix:",
            "status": ":material-shield-outline:",
        }

        # Use tabs for different move categories
        md += '=== ":material-arrow-up-bold: Level-Up"\n\n'
        if pokemon.moves.level_up:
            md += self._generate_move_table(
                pokemon.moves.level_up,
                damage_class_icons,
                include_level=True,
                sort_by_level=True,
            )
        else:
            md += "    *No level-up moves available*\n"
        md += "\n"

        # TM/HM moves
        md += '=== ":material-disc: TM/HM"\n\n'
        if pokemon.moves.machine:
            md += self._generate_move_table(
                pokemon.moves.machine, damage_class_icons, include_level=False
            )
        else:
            md += "    *No TM/HM moves available*\n"
        md += "\n"

        # Egg moves
        md += '=== ":material-egg-outline: Egg Moves"\n\n'
        if pokemon.moves.egg:
            md += self._generate_move_table(
                pokemon.moves.egg, damage_class_icons, include_level=False
            )
        else:
            md += "    *No egg moves available*\n"
        md += "\n"

        # Tutor moves
        md += '=== ":material-school: Tutor"\n\n'
        if pokemon.moves.tutor:
            md += self._generate_move_table(
                pokemon.moves.tutor, damage_class_icons, include_level=False
            )
        else:
            md += "    *No tutor moves available*\n"
        md += "\n"

        return md

    def _generate_flavor_text(self, pokemon: Pokemon) -> str:
        """Generate the Pokedex flavor text section."""
        md = "## :material-book-open: Pokédex Entries\n\n"

        # Create tabs for different versions
        md += '=== ":material-circle-outline: Black"\n\n'
        if pokemon.flavor_text.black:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.black}\n\n"

        md += '=== ":material-circle: White"\n\n'
        if pokemon.flavor_text.white:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.white}\n\n"

        md += '=== ":material-numeric-2-circle-outline: Black 2"\n\n'
        if pokemon.flavor_text.black_2:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.black_2}\n\n"

        md += '=== ":material-numeric-2-circle: White 2"\n\n'
        if pokemon.flavor_text.white_2:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.white_2}\n\n"

        return md

    def _generate_sprites_section(self, pokemon: Pokemon) -> str:
        """Generate the sprites section with multiple sprite versions."""
        md = "## :material-image-multiple: Sprites\n\n"

        sprites = pokemon.sprites

        # Use tabs for different sprite types
        md += '=== "Gen 5 Animated"\n\n'
        md += '    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin: 20px 0;">\n'

        if hasattr(sprites, "versions") and sprites.versions:
            bw = sprites.versions.black_white
            if bw.animated:
                # Front and back sprites in columns
                if bw.animated.front_default:
                    md += '      <div style="text-align: center;">\n'
                    md += '        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">Front</div>\n'
                    md += f'        <img src="{bw.animated.front_default}" alt="Normal Front" style="image-rendering: pixelated; background: linear-gradient(135deg, #f5f5f5, #e0e0e0); padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />\n'
                    md += "      </div>\n"
                if bw.animated.back_default:
                    md += '      <div style="text-align: center;">\n'
                    md += '        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">Back</div>\n'
                    md += f'        <img src="{bw.animated.back_default}" alt="Normal Back" style="image-rendering: pixelated; background: linear-gradient(135deg, #f5f5f5, #e0e0e0); padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />\n'
                    md += "      </div>\n"

        md += "    </div>\n\n"

        md += '=== "Shiny"\n\n'
        md += '    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin: 20px 0;">\n'

        if hasattr(sprites, "versions") and sprites.versions:
            bw = sprites.versions.black_white
            if bw.animated:
                if bw.animated.front_shiny:
                    md += '      <div style="text-align: center;">\n'
                    md += '        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">Front</div>\n'
                    md += f'        <img src="{bw.animated.front_shiny}" alt="Shiny Front" style="image-rendering: pixelated; background: linear-gradient(135deg, #fff8e1, #ffe082); padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(255,215,0,0.3);" />\n'
                    md += "      </div>\n"
                if bw.animated.back_shiny:
                    md += '      <div style="text-align: center;">\n'
                    md += '        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">Back</div>\n'
                    md += f'        <img src="{bw.animated.back_shiny}" alt="Shiny Back" style="image-rendering: pixelated; background: linear-gradient(135deg, #fff8e1, #ffe082); padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(255,215,0,0.3);" />\n'
                    md += "      </div>\n"

        md += "    </div>\n\n"

        # Official Artwork - use the correct path
        md += '=== "Official Artwork"\n\n'
        md += '    <div style="text-align: center; margin: 20px 0;">\n'

        if (
            hasattr(sprites, "other")
            and sprites.other
            and hasattr(sprites.other, "official_artwork")
        ):
            artwork = sprites.other.official_artwork
            if artwork.front_default:
                md += f'      <img src="{artwork.front_default}" alt="Official Artwork" style="max-width: 300px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.15));" />\n'

        md += "    </div>\n\n"

        # Show HOME sprites if available
        if (
            hasattr(sprites, "other")
            and sprites.other
            and hasattr(sprites.other, "home")
        ):
            md += '=== "HOME Sprites"\n\n'
            md += '    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin: 20px 0;">\n'

            home = sprites.other.home
            if home.front_default:
                md += '      <div style="text-align: center;">\n'
                md += '        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">Normal</div>\n'
                md += f'        <img src="{home.front_default}" alt="HOME Normal" style="max-width: 150px; background: linear-gradient(135deg, #f5f5f5, #e0e0e0); padding: 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />\n'
                md += "      </div>\n"
            if home.front_shiny:
                md += '      <div style="text-align: center;">\n'
                md += '        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">Shiny</div>\n'
                md += f'        <img src="{home.front_shiny}" alt="HOME Shiny" style="max-width: 150px; background: linear-gradient(135deg, #fff8e1, #ffe082); padding: 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(255,215,0,0.3);" />\n'
                md += "      </div>\n"

            md += "    </div>\n\n"

        # Add Pokemon cry audio player OUTSIDE the tabs
        md += "---\n\n"
        md += "### :material-volume-high: Cry\n\n"

        if hasattr(pokemon, "cries") and pokemon.cries:
            md += '<div style="text-align: center; margin: 20px 0;">\n'

            # Prefer latest cry, fallback to legacy
            cry_url = getattr(pokemon.cries, "latest", None) or getattr(
                pokemon.cries, "legacy", None
            )
            if cry_url:
                md += f'  <audio controls style="max-width: 400px; width: 100%;">\n'
                md += f'    <source src="{cry_url}" type="audio/ogg">\n'
                md += "    Your browser does not support the audio element.\n"
                md += "  </audio>\n"

            md += "</div>\n\n"
        else:
            md += "*Cry audio not available*\n\n"

        return md

    def generate_pokemon_page(self, pokemon: Pokemon) -> Path:
        """
        Generate a markdown page for a single Pokemon.

        Args:
            pokemon: The Pokemon data to generate a page for

        Returns:
            Path to the generated markdown file
        """
        display_name = self._format_name(pokemon.name)

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
        md += self._generate_flavor_text(pokemon)
        md += self._generate_moves_section(pokemon)
        md += self._generate_sprites_section(pokemon)

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

        # Subfolders to scan for forms (same as navigation)
        subfolders_to_scan = ["default", "transformation", "variant"]

        generated_files = []
        total_pokemon = 0

        for folder in subfolders_to_scan:
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
        md += "Complete list of all Pokémon in Blaze Black 2 & Volt White 2 Redux.\n\n"

        # Generate table
        md += "| # | Pokémon | Types | Abilities |\n"
        md += "|---|---------|-------|----------|\n"

        for pokemon in pokemon_list:
            dex_num = pokemon.pokedex_numbers.get("national", "???")
            name = self._format_name(pokemon.name)
            link = f"[{name}](pokemon/{pokemon.name}.md)"
            types = " / ".join([self._format_type(t) for t in pokemon.types])

            # Get non-hidden abilities
            abilities = [a.name for a in pokemon.abilities if not a.is_hidden]
            abilities_str = ", ".join(
                [self._format_name(a) for a in abilities[:2]]
            )  # Show max 2

            md += f"| {dex_num:03d} | {link} | {types} | {abilities_str} |\n"

        md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "pokedex.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated Pokedex index: {output_file}")
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

            # Subfolders to scan for forms (in priority order)
            subfolders_to_scan = ["default", "transformation", "variant"]

            # Load all Pokemon and group by national dex number
            all_pokemon = []
            seen_pokemon = set()  # Track (dex_number, name) to prevent duplicates

            for folder in subfolders_to_scan:
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

            # Group Pokemon by national dex number
            from collections import defaultdict

            pokemon_by_dex: Dict[int, List[Pokemon]] = defaultdict(list)

            for pokemon in all_pokemon:
                dex_num = pokemon.pokedex_numbers.get("national")
                if dex_num:
                    pokemon_by_dex[dex_num].append(pokemon)

            # Sort each group: default form first, then alternates
            for dex_num in pokemon_by_dex:
                pokemon_by_dex[dex_num].sort(key=lambda p: (not p.is_default, p.name))

            # Get sorted list of dex numbers
            sorted_dex_numbers = sorted(pokemon_by_dex.keys())

            # Group Pokemon by generation
            gen_names = [
                ("Gen 1", 1, 151),
                ("Gen 2", 152, 251),
                ("Gen 3", 252, 386),
                ("Gen 4", 387, 493),
                ("Gen 5", 494, 649),
            ]

            # Create navigation structure
            pokedex_nav: Dict[str, List[Dict[str, object]]] = {
                "Pokédex": [{"Overview": "pokedex/pokedex.md"}]
            }

            # Build navigation for each generation
            for gen_name, start, end in gen_names:
                gen_dex_numbers = [
                    dex for dex in sorted_dex_numbers if start <= dex <= end
                ]

                if gen_dex_numbers:
                    gen_nav = []
                    for dex_num in gen_dex_numbers:
                        pokemon_forms = pokemon_by_dex[dex_num]

                        # Get the default form (should be first after sorting)
                        default_form = pokemon_forms[0]
                        base_name = default_form.species

                        # Check if default form has a suffix
                        default_form_suffix = extract_form_suffix(
                            default_form.name, base_name
                        )

                        # Create main entry for default form
                        main_entry = {
                            f"#{dex_num:03d} {self._format_name(default_form.name)}": f"pokedex/pokemon/{default_form.name}.md"
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
                                        {
                                            form_display: f"pokedex/pokemon/{form.name}.md"
                                        }
                                    )

                                main_entry = {
                                    f"#{dex_num:03d} {self._format_name(base_name)}": all_forms
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
                                    f"#{dex_num:03d} {self._format_name(default_form.name)}": [
                                        {
                                            "Default": f"pokedex/pokemon/{default_form.name}.md"
                                        }
                                    ]
                                    + alternate_forms
                                }

                        gen_nav.append(main_entry)

                    pokedex_nav["Pokédex"].append({gen_name: gen_nav})

            # Find and replace Pokédex section in nav
            if "nav" in config:
                # Find the Pokédex entry and replace it
                nav_list = config["nav"]
                pokedex_index = None

                for i, item in enumerate(nav_list):
                    if isinstance(item, dict) and "Pokédex" in item:
                        pokedex_index = i
                        break

                if pokedex_index is not None:
                    nav_list[pokedex_index] = pokedex_nav
                else:
                    # Add Pokédex section if it doesn't exist
                    nav_list.append(pokedex_nav)

                config["nav"] = nav_list

            # Write updated mkdocs.yml using utility
            save_mkdocs_config(mkdocs_path, config)

            total_pokemon = len(sorted_dex_numbers)
            total_forms = len(all_pokemon)
            self.logger.info(
                f"Updated mkdocs.yml with {total_pokemon} Pokemon ({total_forms} total forms including alternates)"
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
