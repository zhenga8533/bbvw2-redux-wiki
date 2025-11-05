"""
Configuration constants for the wiki generator.

This module centralizes all configuration values that were previously in config.json.
Values are defined as Python constants for better type safety and easier maintenance.
"""

from typing import Any

# ============================================================================
# PokeDB Configuration
# ============================================================================

POKEDB_REPO_URL = "https://github.com/zhenga8533/pokedb"
POKEDB_BRANCH = "data"
POKEDB_DATA_DIR = "data/pokedb"
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
LOGGING_LOG_DIR = "logs"
LOGGING_MAX_LOG_SIZE_MB = 10
LOGGING_BACKUP_COUNT = 5
LOGGING_CONSOLE_COLORS = True
LOGGING_CLEAR_ON_RUN = True

# ============================================================================
# Parser Registry
# ============================================================================

PARSERS_REGISTRY: dict[str, dict[str, Any]] = {
    "evolution_changes": {
        "module": "src.parsers.evolution_changes_parser",
        "class": "EvolutionChangesParser",
        "input_file": "Evolution Changes.txt",
        "output_dir": "docs/changes",
    },
    "gift_pokemon": {
        "module": "src.parsers.gift_pokemon_parser",
        "class": "GiftPokemonParser",
        "input_file": "Gift Pokemon.txt",
        "output_dir": "docs/reference",
    },
    "item_changes": {
        "module": "src.parsers.item_changes_parser",
        "class": "ItemChangesParser",
        "input_file": "Item Changes.txt",
        "output_dir": "docs/changes",
    },
    "legendary_locations": {
        "module": "src.parsers.legendary_locations_parser",
        "class": "LegendaryLocationsParser",
        "input_file": "Legendary Locations.txt",
        "output_dir": "docs/reference",
    },
    "move_changes": {
        "module": "src.parsers.move_changes_parser",
        "class": "MoveChangesParser",
        "input_file": "Move Changes.txt",
        "output_dir": "docs/changes",
    },
    "pokemon_changes": {
        "module": "src.parsers.pokemon_changes_parser",
        "class": "PokemonChangesParser",
        "input_file": "Pokemon Changes.txt",
        "output_dir": "docs/changes",
    },
    "trade_changes": {
        "module": "src.parsers.trade_changes_parser",
        "class": "TradeChangesParser",
        "input_file": "Trade Changes.txt",
        "output_dir": "docs/changes",
    },
    "trainer_changes": {
        "module": "src.parsers.trainer_changes_parser",
        "class": "TrainerChangesParser",
        "input_file": "Trainer Changes.txt",
        "output_dir": "docs/changes",
    },
    "type_changes": {
        "module": "src.parsers.type_changes_parser",
        "class": "TypeChangesParser",
        "input_file": "Type Changes.txt",
        "output_dir": "docs/changes",
    },
    "wild_area_changes": {
        "module": "src.parsers.wild_area_changes_parser",
        "class": "WildAreaChangesParser",
        "input_file": "Wild Area Changes.txt",
        "output_dir": "docs/changes",
    },
}

# ============================================================================
# Generator Registry
# ============================================================================

GENERATORS_REGISTRY: dict[str, dict[str, Any]] = {
    "pokemon": {
        "module": "src.generators.pokemon_generator",
        "class": "PokemonGenerator",
        "output_dir": "docs/pokedex",
    },
    "abilities": {
        "module": "src.generators.ability_generator",
        "class": "AbilityGenerator",
        "output_dir": "docs/pokedex",
    },
    "items": {
        "module": "src.generators.item_generator",
        "class": "ItemGenerator",
        "output_dir": "docs/pokedex",
    },
    "moves": {
        "module": "src.generators.move_generator",
        "class": "MoveGenerator",
        "output_dir": "docs/pokedex",
    },
}
