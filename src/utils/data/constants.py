"""
Shared constants for Pokemon-related data and formatting.

This module centralizes all commonly-used constants across the codebase to ensure
consistency and make updates easier. Rather than duplicating these values across
multiple files, they are defined once here and imported where needed.
"""

from typing import Dict

# ============================================================================
# Type-Related Constants
# ============================================================================

# IMPORTANT: These colors MUST match the CSS type badge colors defined in:
#   docs/stylesheets/pokemon.css (lines 45-62)
#
# When updating these colors:
# 1. Update both this dict AND the corresponding CSS classes (.type-{type})
# 2. Run: grep -n "type-{type}" docs/stylesheets/pokemon.css to find the CSS rule
# 3. Ensure color consistency across Python badge generation and CSS styling
#
# The CSS uses these colors with a gradient effect:
#   background: linear-gradient(135deg, {COLOR}, {COLOR}dd);
# where 'dd' adds transparency to create depth.

TYPE_COLORS: Dict[str, str] = {
    # Hex color codes for Pokemon type badges
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

# ============================================================================
# Name Formatting Special Cases
# ============================================================================

ITEM_NAME_SPECIAL_CASES: Dict[str, str] = {
    # Special capitalization cases for item names (including abbreviations)
    "tm": "TM",
    "hm": "HM",
    "hp": "HP",
    "pp": "PP",
}

# ============================================================================
# Pokemon Form Subfolders
# ============================================================================

# All Pokemon form categories including cosmetic forms
POKEMON_FORM_SUBFOLDERS_ALL = ["default", "transformation", "variant", "cosmetic"]

# Standard Pokemon form categories (excludes cosmetic forms)
POKEMON_FORM_SUBFOLDERS_STANDARD = ["default", "transformation", "variant"]

# ============================================================================
# Generation-Related Constants
# ============================================================================

GENERATION_DISPLAY_NAMES: Dict[str, str] = {
    # Mapping from generation identifiers to display names
    "generation-i": "Gen I",
    "generation-ii": "Gen II",
    "generation-iii": "Gen III",
    "generation-iv": "Gen IV",
    "generation-v": "Gen V",
}

# Canonical ordering of generations
GENERATION_ORDER = [
    "generation-i",
    "generation-ii",
    "generation-iii",
    "generation-iv",
    "generation-v",
]

# ============================================================================
# Move/Damage Class Icons
# ============================================================================

DAMAGE_CLASS_ICONS: Dict[str, str] = {
    # Material Design icon identifiers for damage classes/move categories
    "physical": ":material-sword:",
    "special": ":material-auto-fix:",
    "status": ":material-shield-outline:",
}

# ============================================================================
# Path Constants
# ============================================================================

# Default relative path from subdirectory pages to docs root (for use_directory_urls: true)
DEFAULT_RELATIVE_PATH = "../.."
