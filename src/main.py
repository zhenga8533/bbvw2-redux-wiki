"""
Main entry point for initializing data and running parsers.
"""

import argparse
import sys
import importlib
from src.data.pokedb_initializer import PokeDBInitializer
from src.generators.pokemon_page_generator import PokemonPageGenerator
from src.utils.logger_util import get_logger
from src.utils.config_util import get_config

logger = get_logger(__name__)


def get_parser_registry():
    """
    Get the registry of available parsers by dynamically loading them from the config.

    Returns:
        dict: Registry mapping parser names to (ParserClass, input_file, output_dir) tuples
    """
    config = get_config()
    parser_config = config.get("parsers", {}).get("registry", {})
    registry = {}

    for name, details in parser_config.items():
        try:
            module_name = details["module"]
            class_name = details["class"]
            input_file = details["input_file"]
            output_dir = details["output_dir"]

            # Dynamically import the module and get the class
            module = importlib.import_module(module_name)
            ParserClass = getattr(module, class_name)

            registry[name] = (ParserClass, input_file, output_dir)
        except (KeyError, ImportError, AttributeError) as e:
            logger.error(f"Failed to load parser '{name}': {e}", exc_info=True)
            continue

    return registry


def initialize_data():
    """Initialize PokeDB data (download and prepare parsed directory)."""
    logger.info("Starting PokeDB data initialization...")
    initializer = PokeDBInitializer()
    initializer.run()


def generate_pokedex(subfolder: str = "default"):
    """
    Generate Pokemon pages and Pokedex index.

    Args:
        subfolder: Subfolder within pokemon directory to process

    Returns:
        bool: True if generation succeeded, False if it failed
    """
    logger.info("Starting Pokedex generation...")
    try:
        generator = PokemonPageGenerator()

        # Generate all Pokemon pages
        logger.info("Generating individual Pokemon pages...")
        pokemon_files = generator.generate_all_pokemon_pages(subfolder=subfolder)

        if not pokemon_files:
            logger.error("No Pokemon pages were generated")
            return False

        # Generate the Pokedex index
        logger.info("Generating Pokedex index...")
        index_path = generator.generate_pokedex_index(subfolder=subfolder)

        # Update mkdocs.yml navigation
        logger.info("Updating mkdocs.yml navigation...")
        nav_success = generator.update_mkdocs_navigation(subfolder=subfolder)

        if not nav_success:
            logger.warning("Failed to update mkdocs.yml navigation, but pages were generated successfully")

        logger.info(f"Successfully generated {len(pokemon_files)} Pokemon pages and index")
        return True

    except Exception as e:
        logger.error(f"Failed to generate Pokedex: {e}", exc_info=True)
        return False


def run_parsers(parser_names: list[str]):
    """
    Run specified parsers.

    Args:
        parser_names: List of parser names to run (or ['all'] for all parsers)

    Returns:
        bool: True if all parsers succeeded, False if any failed
    """
    parser_registry = get_parser_registry()

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
            logger.info(f"[OK] {name} completed: {markdown_path}")
        except NotImplementedError as e:
            logger.warning(f"[SKIP] {name} not yet implemented: {e}")
            failed_parsers.append((name, "not implemented"))
        except FileNotFoundError as e:
            logger.error(f"[FAIL] {name} failed - file not found: {e}", exc_info=True)
            failed_parsers.append((name, "file not found"))
        except (OSError, IOError, PermissionError) as e:
            logger.error(
                f"[FAIL] {name} failed - file system error: {e}", exc_info=True
            )
            failed_parsers.append((name, "file system error"))
        except Exception as e:
            logger.error(f"[FAIL] {name} failed: {e}", exc_info=True)
            failed_parsers.append((name, "unexpected error"))

    # Report results
    if failed_parsers:
        logger.error(f"\nFailed parsers ({len(failed_parsers)}):")
        for name, reason in failed_parsers:
            logger.error(f"  - {name}: {reason}")
        return False
    else:
        logger.info(f"All {len(parsers_to_run)} parser(s) completed successfully")
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

    parser.add_argument(
        "--generate-pokedex",
        action="store_true",
        help="Generate individual Pokemon pages and Pokedex index",
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

    # Run requested operations
    success = True

    if args.init:
        initialize_data()

    if args.parsers:
        success = run_parsers(args.parsers)

    if args.generate_pokedex:
        success = generate_pokedex() and success

    if success:
        logger.info("Complete!")
        sys.exit(0)
    else:
        logger.error("Completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
