"""
Main entry point for bbvw2-redux-wiki.
"""

import argparse
import sys
from pathlib import Path

from rom_wiki_core.utils.core.config_registry import set_config
from rom_wiki_core.utils.core.executor import run_generators, run_parsers
from rom_wiki_core.utils.core.initializer import PokeDBInitializer
from rom_wiki_core.utils.core.loader import PokeDBLoader
from rom_wiki_core.utils.core.logger import configure_logging_system, get_logger
from rom_wiki_core.utils.core.registry import (
    get_generator_registry,
    get_parser_registry,
)
from rom_wiki_core.utils.data import models

from bbvw2_redux_wiki.config import CONFIG

# Set config globally
set_config(CONFIG)

# Configure modules on import
models.configure_models(CONFIG)
configure_logging_system(CONFIG)

# Set the data directory to the correct location in this project
PokeDBLoader.set_data_dir(Path(CONFIG.pokedb_data_dir) / "parsed")

logger = get_logger(__name__)


def initialize_data():
    """Initialize PokeDB data (download and prepare parsed directory)."""
    logger.info("Starting PokeDB data initialization...")
    initializer = PokeDBInitializer(CONFIG)
    initializer.run()


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Initialize data and run parsers/generators for Blaze Black 2 & Volt White 2 Redux Wiki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m bbvw2_redux_wiki --init                        # Initialize PokeDB data
  python -m bbvw2_redux_wiki --parsers all                 # Run all parsers
  python -m bbvw2_redux_wiki --parsers pokemon_changes     # Run specific parser
  python -m bbvw2_redux_wiki --generators all              # Run all generators
  python -m bbvw2_redux_wiki --generators pokemon          # Run specific generator
  python -m bbvw2_redux_wiki --init --parsers all          # Initialize and run all parsers
        """,
    )

    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize PokeDB data (download and prepare parsed directory)",
    )

    parser.add_argument(
        "--parsers",
        nargs="+",
        metavar="PARSER",
        help='Parser(s) to run. Use "all" to run all parsers, or specify parser names',
    )

    parser.add_argument(
        "--list-parsers", action="store_true", help="List all available parsers"
    )

    parser.add_argument(
        "--generators",
        nargs="+",
        metavar="GENERATOR",
        help='Generator(s) to run. Use "all" to run all generators, or specify generator names',
    )

    parser.add_argument(
        "--list-generators", action="store_true", help="List all available generators"
    )

    args = parser.parse_args()

    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # List parsers if requested
    if args.list_parsers:
        parser_registry = get_parser_registry(CONFIG)
        print("Available parsers:")
        for name in parser_registry.keys():
            print(f"  - {name}")
        sys.exit(0)

    # List generators if requested
    if args.list_generators:
        generator_registry = get_generator_registry(CONFIG)
        print("Available generators:")
        for name in generator_registry.keys():
            print(f"  - {name}")
        sys.exit(0)

    # Run requested operations
    success = True

    if args.init:
        initialize_data()

    if args.parsers:
        parser_registry = get_parser_registry(CONFIG)
        success = run_parsers(args.parsers, parser_registry)

        # Clear cache after parsers to ensure generators load fresh data
        if args.generators:
            from rom_wiki_core.utils.core.loader import PokeDBLoader

            logger.info("Clearing cache before running generators...")
            PokeDBLoader.clear_cache()

    if args.generators:
        generator_registry = get_generator_registry(CONFIG)
        success = run_generators(args.generators, generator_registry) and success

    if success:
        logger.info("Complete!")
        sys.exit(0)
    else:
        logger.error("Completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
