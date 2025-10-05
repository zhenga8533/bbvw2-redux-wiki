"""
Main entry point for initializing data and running parsers.
"""

import argparse
import sys
from .utils.pokedb_initializer import PokeDBInitializer
from .utils.logger import setup_logger

logger = setup_logger(__name__, __file__)


def initialize_data():
    """Initialize PokeDB data (download and prepare parsed directory)."""
    logger.info("Starting PokeDB data initialization...")
    initializer = PokeDBInitializer("src/config.json")
    initializer.run()


def run_parsers(parser_names: list[str]):
    """
    Run specified parsers.

    Args:
        parser_names: List of parser names to run (or ['all'] for all parsers)
    """
    # Import parsers here to avoid circular imports
    from .parsers.evolution_changes_parser import EvolutionChangesParser

    # Registry of available parsers
    # Format: 'name': (ParserClass, input_file)
    parser_registry = {
        "evolution_changes": (
            EvolutionChangesParser,
            "Evolution Changes.txt",
            "docs/changes",
        ),
    }

    if not parser_registry:
        logger.warning(
            "No parsers registered yet. Add parsers to main.py parser_registry."
        )
        return

    # Determine which parsers to run
    if "all" in parser_names:
        parsers_to_run = parser_registry.keys()
    else:
        parsers_to_run = parser_names
        # Validate parser names
        invalid = set(parsers_to_run) - set(parser_registry.keys())
        if invalid:
            logger.error(f"Unknown parsers: {', '.join(invalid)}")
            logger.info(f"Available parsers: {', '.join(parser_registry.keys())}")
            sys.exit(1)

    # Run each parser
    for name in parsers_to_run:
        ParserClass, input_file, output_dir = parser_registry[name]
        logger.info(f"Running parser: {name}")

        try:
            parser = ParserClass(input_file, output_dir)
            markdown_path, data_path = parser.run()
            logger.info(
                f"✓ {name} completed:\n  - Markdown: {markdown_path}\n  - Data: {data_path}"
            )
        except Exception as e:
            logger.error(f"✗ {name} failed: {e}", exc_info=True)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Initialize data and run parsers for bbvw2-redux-wiki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --init                        # Initialize PokeDB data
  python -m src.main --parsers all                 # Run all parsers
  python -m src.main --parsers npcs items          # Run specific parsers
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

    args = parser.parse_args()

    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # List parsers if requested
    if args.list_parsers:
        parser_registry = {}
        if parser_registry:
            print("Available parsers:")
            for name in parser_registry.keys():
                print(f"  - {name}")
        else:
            print("No parsers registered yet.")
        sys.exit(0)

    # Run requested operations
    if args.init:
        initialize_data()

    if args.parsers:
        run_parsers(args.parsers)

    logger.info("Complete!")


if __name__ == "__main__":
    main()
