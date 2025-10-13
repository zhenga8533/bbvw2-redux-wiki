"""
Regular expression patterns used across the parsing system.

This module contains shared regex patterns for parsing Pokemon data from
documentation files. These patterns are designed to match the specific
formatting conventions used in the documentation.
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
