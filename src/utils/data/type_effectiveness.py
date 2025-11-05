"""
Type effectiveness chart for Pokemon battles.

This module contains the type matchup data for calculating damage multipliers
in Pokemon battles. Based on Generation 5 mechanics.

Usage:
    from src.utils.data.type_effectiveness import calculate_type_effectiveness

    effectiveness = calculate_type_effectiveness(["fire", "flying"])
    print(effectiveness["4x_weak"])  # ['rock', 'water']
"""

from src.utils.data.constants import TYPE_CHART


def calculate_type_effectiveness(types: list[str]) -> dict[str, list[str]]:
    """
    Calculate type effectiveness for a Pokemon with one or two types.

    Args:
        types: List of 1-2 type names (lowercase, e.g., ["fire", "flying"])

    Returns:
        Dictionary containing:
        - "4x_weak": Types that deal 4x damage
        - "2x_weak": Types that deal 2x damage
        - "0.5x_resist": Types that deal 0.5x damage
        - "0.25x_resist": Types that deal 0.25x damage
        - "immune": Types that deal 0x damage (immune)

    Example:
        >>> effectiveness = calculate_type_effectiveness(["fire", "flying"])
        >>> effectiveness["4x_weak"]
        ['rock']
        >>> effectiveness["immune"]
        ['ground']
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
