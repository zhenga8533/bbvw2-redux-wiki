"""
Main entry point for initializing data and running parsers.
"""

import argparse
import sys
from src.data.pokedb_initializer import PokeDBInitializer
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_parser_registry():
    """
    Get the registry of available parsers.

    Returns:
        dict: Registry mapping parser names to (ParserClass, input_file, output_dir) tuples
    """
    # Import parsers here to avoid circular imports
    from .parsers.evolution_changes_parser import EvolutionChangesParser
    from .parsers.gift_pokemon_parser import GiftPokemonParser
    from .parsers.item_changes_parser import ItemChangesParser
    from .parsers.legendary_locations_parser import LegendaryLocationsParser
    from .parsers.move_changes_parser import MoveChangesParser
    from .parsers.pokemon_changes_parser import PokemonChangesParser
    from .parsers.trade_changes_parser import TradeChangesParser
    from .parsers.trainer_changes_parser import TrainerChangesParser
    from .parsers.type_changes_parser import TypeChangesParser
    from .parsers.wild_area_changes_parser import WildAreaChangesParser

    return {
        "evolution_changes": (
            EvolutionChangesParser,
            "Evolution Changes.txt",
            "docs/changes",
        ),
        "gift_pokemon": (
            GiftPokemonParser,
            "Gift Pokemon.txt",
            "docs",
        ),
        "item_changes": (
            ItemChangesParser,
            "Item Changes.txt",
            "docs/changes",
        ),
        "legendary_locations": (
            LegendaryLocationsParser,
            "Legendary Locations.txt",
            "docs",
        ),
        "move_changes": (
            MoveChangesParser,
            "Move Changes.txt",
            "docs/changes",
        ),
        "pokemon_changes": (
            PokemonChangesParser,
            "Pokemon Changes.txt",
            "docs/changes",
        ),
        "trade_changes": (
            TradeChangesParser,
            "Trade Changes.txt",
            "docs/changes",
        ),
        "trainer_changes": (
            TrainerChangesParser,
            "Trainer Changes.txt",
            "docs/changes",
        ),
        "type_changes": (
            TypeChangesParser,
            "Type Changes.txt",
            "docs/changes",
        ),
        "wild_area_changes": (
            WildAreaChangesParser,
            "Wild Area Changes.txt",
            "docs",
        ),
    }


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
    parser_registry = get_parser_registry()

    if not parser_registry:
        logger.warning(
            "No parsers registered yet. Add parsers to main.py parser_registry."
        )
        return False

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

    # Run each parser and track failures
    failed_parsers = []
    for name in parsers_to_run:
        ParserClass, input_file, output_dir = parser_registry[name]
        logger.info(f"Running parser: {name}")

        try:
            parser = ParserClass(input_file, output_dir)
            markdown_path = parser.run()
            logger.info(f"✓ {name} completed: {markdown_path}")
        except NotImplementedError as e:
            logger.warning(f"⊘ {name} not yet implemented: {e}")
            failed_parsers.append((name, "not implemented"))
        except FileNotFoundError as e:
            logger.error(f"✗ {name} failed - file not found: {e}", exc_info=True)
            failed_parsers.append((name, "file not found"))
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"✗ {name} failed - file system error: {e}", exc_info=True)
            failed_parsers.append((name, "file system error"))
        except Exception as e:
            logger.error(f"✗ {name} failed: {e}", exc_info=True)
            failed_parsers.append((name, "unexpected error"))

    # Report results
    if failed_parsers:
        logger.error(f"\nFailed parsers ({len(failed_parsers)}):")
        for name, reason in failed_parsers:
            logger.error(f"  - {name}: {reason}")
        return False
    else:
        logger.info(f"\nAll {len(parsers_to_run)} parser(s) completed successfully")
        return True


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
        parser_registry = get_parser_registry()

        if parser_registry:
            print("Available parsers:")
            for name in parser_registry.keys():
                print(f"  - {name}")
        else:
            print("No parsers registered yet.")
        sys.exit(0)

    # Run requested operations
    success = True

    if args.init:
        initialize_data()

    if args.parsers:
        success = run_parsers(args.parsers)

    if success:
        logger.info("Complete!")
        sys.exit(0)
    else:
        logger.error("Completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
