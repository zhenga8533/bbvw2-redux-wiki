"""
Main entry point for initializing data and running parsers.
"""

import argparse
import sys

from src.utils.core.executor import run_generators, run_parsers
from src.utils.core.initializer import PokeDBInitializer
from src.utils.core.logger import get_logger
from src.utils.core.registry import get_generator_registry, get_parser_registry

logger = get_logger(__name__)


def initialize_data():
    """Initialize PokeDB data (download and prepare parsed directory)."""
    logger.info("Starting PokeDB data initialization...")
    initializer = PokeDBInitializer()
    initializer.run()


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Initialize data and run parsers/generators for bbvw2-redux-wiki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --init                        # Initialize PokeDB data
  python -m src.main --parsers all                 # Run all parsers
  python -m src.main --parsers npcs items          # Run specific parsers
  python -m src.main --generators all              # Run all generators
  python -m src.main --generators pokemon          # Run specific generator
  python -m src.main --init --parsers all          # Initialize data and run all parsers
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
        parser_registry = get_parser_registry()
        print("Available parsers:")
        for name in parser_registry.keys():
            print(f"  - {name}")
        sys.exit(0)

    # List generators if requested
    if args.list_generators:
        generator_registry = get_generator_registry()
        print("Available generators:")
        for name in generator_registry.keys():
            print(f"  - {name}")
        sys.exit(0)

    # Run requested operations
    success = True

    if args.init:
        initialize_data()

    if args.parsers:
        parser_registry = get_parser_registry()
        success = run_parsers(args.parsers, parser_registry)

        # Clear cache after parsers to ensure generators load fresh data
        if args.generators:
            from src.utils.core.loader import PokeDBLoader

            logger.info("Clearing cache before running generators...")
            PokeDBLoader.clear_cache()

    if args.generators:
        generator_registry = get_generator_registry()
        success = run_generators(args.generators, generator_registry) and success

    if success:
        logger.info("Complete!")
        sys.exit(0)
    else:
        logger.error("Completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
