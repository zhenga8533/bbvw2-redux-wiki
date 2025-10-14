"""
Regular expression patterns and constants used across the parsing system.

This module contains shared regex patterns for parsing Pokemon data from
documentation files. These patterns are designed to match the specific
formatting conventions used in the documentation.

IMPORTANT NAMING CONVENTIONS:
- JSON field names: snake_case (e.g., "special_attack", "ev_yield")
- File names: kebab-case (e.g., "mr-mime.json", "mime-jr.json")
- String values in JSON: kebab-case (e.g., "name": "mr-mime")
- The name_to_id() function produces kebab-case for file/value lookups
"""

import re

# Regex pattern for matching Pokemon names in documentation files
# Matches capitalized names with support for:
# - Multi-word names (e.g., "Mr. Mime")
# - Apostrophes (e.g., "Farfetch'd")
# - Hyphens (e.g., "Ho-Oh")
# - Colons (e.g., "Type: Null")
# - Periods (e.g., "Mime Jr.")
#
# Examples of valid matches:
#   - "Pikachu"
#   - "Mr. Mime"
#   - "Farfetch'd"
#   - "Ho-Oh"
#   - "Type: Null"
#   - "Mime Jr."
POKEMON_PATTERN_STR = r"([A-Z][\w':.-]*(?:\s[A-Z][\w':.-]*)*)"
POKEMON_PATTERN = re.compile(POKEMON_PATTERN_STR)

# Markdown formatting constants
# Default width for Pokemon sprite images in generated markdown
POKEMON_SPRITE_WIDTH = 96
