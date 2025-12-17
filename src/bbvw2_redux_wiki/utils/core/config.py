"""
Configuration constants for the wiki generator.

This module centralizes all configuration values that were previously in config.json.
Values are defined as Python constants for better type safety and easier maintenance.
"""

from pathlib import Path
from typing import Any

# ============================================================================
# Project Root Configuration
# ============================================================================

# Find the project root (where pyproject.toml is located)
# This ensures paths work regardless of where the script is run from
_current_file = Path(__file__).resolve()
_package_root = _current_file.parent.parent.parent
PROJECT_ROOT = _package_root.parent.parent

# ============================================================================
# PokeDB Configuration
# ============================================================================

POKEDB_REPO_URL = "https://github.com/zhenga8533/pokedb"
POKEDB_BRANCH = "data"
POKEDB_DATA_DIR = str(PROJECT_ROOT / "data" / "pokedb")
POKEDB_GENERATIONS = ["gen5", "gen8"]
POKEDB_VERSION_GROUPS = ["black_white", "black_2_white_2"]
POKEDB_GAME_VERSIONS = ["black", "white", "black_2", "white_2"]
POKEDB_SPRITE_VERSION = "black_white"

VERSION_GROUP = "black_2_white_2"
VERSION_GROUP_FRIENDLY = "Black 2 & White 2"
GAME_TITLE = "Blaze Black 2 & Volt White 2 Redux"

# ============================================================================
# Logging Configuration
# ============================================================================

LOGGING_LEVEL = "DEBUG"
LOGGING_FORMAT = "text"
LOGGING_LOG_DIR = str(PROJECT_ROOT / "logs")
LOGGING_MAX_LOG_SIZE_MB = 10
LOGGING_BACKUP_COUNT = 5
LOGGING_CONSOLE_COLORS = True
LOGGING_CLEAR_ON_RUN = True

# ============================================================================
# Parser Registry
# ============================================================================

PARSERS_REGISTRY: dict[str, dict[str, Any]] = {
    "evolution_changes": {
        "module": "bbvw2_redux_wiki.parsers.evolution_changes_parser",
        "class": "EvolutionChangesParser",
        "input_file": "Evolution Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
    "gift_pokemon": {
        "module": "bbvw2_redux_wiki.parsers.gift_pokemon_parser",
        "class": "GiftPokemonParser",
        "input_file": "Gift Pokemon.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "reference"),
    },
    "item_changes": {
        "module": "bbvw2_redux_wiki.parsers.item_changes_parser",
        "class": "ItemChangesParser",
        "input_file": "Item Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
    "legendary_locations": {
        "module": "bbvw2_redux_wiki.parsers.legendary_locations_parser",
        "class": "LegendaryLocationsParser",
        "input_file": "Legendary Locations.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "reference"),
    },
    "move_changes": {
        "module": "bbvw2_redux_wiki.parsers.move_changes_parser",
        "class": "MoveChangesParser",
        "input_file": "Move Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
    "pokemon_changes": {
        "module": "bbvw2_redux_wiki.parsers.pokemon_changes_parser",
        "class": "PokemonChangesParser",
        "input_file": "Pokemon Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
    "trade_changes": {
        "module": "bbvw2_redux_wiki.parsers.trade_changes_parser",
        "class": "TradeChangesParser",
        "input_file": "Trade Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
    "trainer_changes": {
        "module": "bbvw2_redux_wiki.parsers.trainer_changes_parser",
        "class": "TrainerChangesParser",
        "input_file": "Trainer Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
    "type_changes": {
        "module": "bbvw2_redux_wiki.parsers.type_changes_parser",
        "class": "TypeChangesParser",
        "input_file": "Type Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
    "wild_area_changes": {
        "module": "bbvw2_redux_wiki.parsers.wild_area_changes_parser",
        "class": "WildAreaChangesParser",
        "input_file": "Wild Area Changes.txt",
        "output_dir": str(PROJECT_ROOT / "docs" / "changes"),
    },
}

PARSER_DEX_RELATIVE_PATH = ".."

# ============================================================================
# Generator Registry
# ============================================================================

GENERATORS_REGISTRY: dict[str, dict[str, Any]] = {
    "pokemon": {
        "module": "bbvw2_redux_wiki.generators.pokemon_generator",
        "class": "PokemonGenerator",
        "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
    },
    "abilities": {
        "module": "bbvw2_redux_wiki.generators.ability_generator",
        "class": "AbilityGenerator",
        "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
    },
    "items": {
        "module": "bbvw2_redux_wiki.generators.item_generator",
        "class": "ItemGenerator",
        "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
    },
    "moves": {
        "module": "bbvw2_redux_wiki.generators.move_generator",
        "class": "MoveGenerator",
        "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
    },
    "locations": {
        "module": "bbvw2_redux_wiki.generators.location_generator",
        "class": "LocationGenerator",
        "output_dir": str(PROJECT_ROOT / "docs" / "locations"),
    },
}

GENERATOR_DEX_RELATIVE_PATH = "../.."
GENERATOR_INDEX_RELATIVE_PATH = ".."
