"""
Configuration for Blaze Black 2 & Volt White 2 Redux Wiki.

This module creates a WikiConfig instance for use throughout the project.
"""

from pathlib import Path

from rom_wiki_core.config import WikiConfig

# Find the project root (where pyproject.toml is located)
_current_file = Path(__file__).resolve()
_package_root = _current_file.parent
PROJECT_ROOT = _package_root.parent.parent

# Create the configuration instance
CONFIG = WikiConfig(
    # Project paths
    project_root=PROJECT_ROOT,
    # Game information
    game_title="Blaze Black 2 & Volt White 2 Redux",
    version_group="black_2_white_2",
    version_group_friendly="Black 2 & White 2",
    # PokeDB configuration
    pokedb_repo_url="https://github.com/zhenga8533/pokedb",
    pokedb_branch="data",
    pokedb_data_dir=str(PROJECT_ROOT / "data" / "pokedb"),
    pokedb_generations=["gen5", "gen8"],
    pokedb_version_groups=["black_white", "black_2_white_2"],
    pokedb_game_versions=["black", "white", "black_2", "white_2"],
    pokedb_sprite_version="black_white",
    # Logging configuration
    logging_level="DEBUG",
    logging_format="text",
    logging_log_dir=str(PROJECT_ROOT / "logs"),
    logging_max_log_size_mb=10,
    logging_backup_count=5,
    logging_console_colors=True,
    logging_clear_on_run=True,
    # Parser registry (keep your existing parsers)
    parsers_registry={
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
    },
    # Parser configuration
    parser_dex_relative_path="..",
    # Generator registry
    generators_registry={
        "pokemon": {
            "module": "rom_wiki_core.generators.pokemon_generator",
            "class": "PokemonGenerator",
            "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
        },
        "abilities": {
            "module": "rom_wiki_core.generators.ability_generator",
            "class": "AbilityGenerator",
            "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
        },
        "items": {
            "module": "rom_wiki_core.generators.item_generator",
            "class": "ItemGenerator",
            "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
        },
        "moves": {
            "module": "rom_wiki_core.generators.move_generator",
            "class": "MoveGenerator",
            "output_dir": str(PROJECT_ROOT / "docs" / "pokedex"),
        },
        "locations": {
            "module": "rom_wiki_core.generators.location_generator",
            "class": "LocationGenerator",
            "output_dir": str(PROJECT_ROOT / "docs" / "locations"),
        },
    },
    # Generator configuration
    generator_dex_relative_path="../..",
    generator_index_relative_path="..",
)
