"""
Utility functions for Pokemon data calculations.

Includes functions to calculate stat ranges and type effectiveness.
"""

from src.utils.core.config import POKEDB_SPRITE_VERSION
from src.utils.data.constants import TYPE_CHART
from src.utils.data.models import Pokemon
from src.utils.text.text_util import name_to_id


def calculate_stat_range(base_stat: int, is_hp: bool = False) -> tuple:
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


def calculate_type_effectiveness(types: list[str]) -> dict[str, list[str]]:
    """Calculate type effectiveness for a Pokemon with one or two types.

    Args:
        types (list[str]): List of 1-2 type names (lowercase, e.g., ["fire", "flying"])

    Returns:
        dict[str, list[str]]: Dictionary containing:
        - "4x_weak": Types that deal 4x damage
        - "2x_weak": Types that deal 2x damage
        - "0.5x_resist": Types that deal 0.5x damage
        - "0.25x_resist": Types that deal 0.25x damage
        - "immune": Types that deal 0x damage (immune)
    """
    # Track damage multipliers for each attacking type
    weak_multiplier: dict[str, float] = {}
    resist_multiplier: dict[str, float] = {}
    immune_types: set[str] = set()

    # Process each of the Pokemon's types
    for poke_type in types:
        type_data = TYPE_CHART.get(poke_type.lower(), {})

        # Accumulate weaknesses (multiply by 2)
        for weak_type in type_data.get("weak_to", []):
            weak_multiplier[weak_type] = weak_multiplier.get(weak_type, 1) * 2

        # Accumulate resistances (multiply by 0.5)
        for resist_type in type_data.get("resistant_to", []):
            resist_multiplier[resist_type] = resist_multiplier.get(resist_type, 1) * 0.5

        # Accumulate immunities (0x damage)
        for immune_type in type_data.get("immune_to", []):
            immune_types.add(immune_type)

    # Process resistances - some might be neutralized by weaknesses
    for resist_type, mult in list(resist_multiplier.items()):
        if resist_type in weak_multiplier:
            # Combine multipliers
            combined = weak_multiplier[resist_type] * mult
            if combined > 1:
                # Net weakness
                weak_multiplier[resist_type] = combined
                resist_multiplier.pop(resist_type)
            elif combined < 1:
                # Net resistance
                resist_multiplier[resist_type] = combined
                weak_multiplier.pop(resist_type)
            else:
                # Neutral - remove from both
                weak_multiplier.pop(resist_type, None)
                resist_multiplier.pop(resist_type, None)

    # Filter out immunities from weaknesses and resistances
    for immune in immune_types:
        weak_multiplier.pop(immune, None)
        resist_multiplier.pop(immune, None)

    # Categorize by multiplier
    return {
        "4x_weak": [t for t, m in weak_multiplier.items() if m >= 4],
        "2x_weak": [t for t, m in weak_multiplier.items() if m == 2],
        "0.5x_resist": [t for t, m in resist_multiplier.items() if m == 0.5],
        "0.25x_resist": [t for t, m in resist_multiplier.items() if m <= 0.25],
        "immune": list(immune_types),
    }


def get_pokemon_sprite(pokemon: str | Pokemon) -> str:
    # Import locally to avoid circular dependency
    from src.utils.core.loader import PokeDBLoader

    # Set pokemon_data based on input type
    if isinstance(pokemon, str):
        pokemon_data = PokeDBLoader.load_pokemon(name_to_id(pokemon))
        if not pokemon_data:
            return pokemon
    else:
        pokemon_data = pokemon

    form_category = next(
        (f.category for f in pokemon_data.forms if f.name == pokemon_data.name),
        "default",
    )

    # Return appropriate sprite based on form category
    if form_category == "cosmetic":
        return pokemon_data.sprites.front_default

    version_sprites = getattr(pokemon_data.sprites.versions, POKEDB_SPRITE_VERSION)
    if (
        version_sprites.animated is None
        or version_sprites.animated.front_default is None
    ):
        return version_sprites.front_default
    else:
        return version_sprites.animated.front_default
