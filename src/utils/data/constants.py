"""
Shared constants for Pokemon-related data and formatting.

This module centralizes all commonly-used constants across the codebase to ensure
consistency and make updates easier. Rather than duplicating these values across
multiple files, they are defined once here and imported where needed.
"""

# ============================================================================
# Display Name Special Cases
# ============================================================================
POKEMON_DISPLAY_CASES: dict[str, str] = {
    "mr-mime": "Mr. Mime",
    "mime-jr": "Mime Jr.",
    "farfetchd": "Farfetchˈd",
    "nidoran-m": "Nidoran♂",
    "nidoran-f": "Nidoran♀",
    "ho-oh": "Ho-Oh",
}

ITEM_DISPLAY_CASES: dict[str, str] = {
    "pp": "PP",
    "tm": "TM",
    "hm": "HM",
    "hp": "HP",
    "x-sp": "X Sp.",
}

ITEM_DISPLAY_ABBREVIATIONS: dict[str, str] = {
    "exp-share": "Exp. Share",
    "kings-rock": "King's Rock",
}

# ============================================================================
# Type-Related Constants
# ============================================================================

TYPE_COLORS: dict[str, str] = {
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
    "shadow": "#4B4B7B",
}

TYPE_CATEGORY_COLORS: dict[str, str] = {
    "physical": "#C03028",
    "special": "#6890F0",
    "status": "#A8A878",
}

TYPE_CHART: dict[str, dict[str, list[str]]] = {
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

# ============================================================================
# Pokemon Form Subfolders
# ============================================================================

POKEMON_FORM_SUBFOLDERS = ["default", "transformation", "variant", "cosmetic"]

