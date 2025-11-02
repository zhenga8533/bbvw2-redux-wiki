"""
Main entry point for initializing data and running parsers.
"""

import argparse
import sys
import importlib
from src.data.pokedb_initializer import PokeDBInitializer
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


def get_generator_registry():
    """
    Get the registry of available generators by dynamically loading them from the config.

    Returns:
        dict: Registry mapping generator names to (GeneratorClass, output_dir) tuples
    """
    config = get_config()
    generator_config = config.get("generators", {}).get("registry", {})
    registry = {}

    for name, details in generator_config.items():
        try:
            module_name = details["module"]
            class_name = details["class"]
            output_dir = details["output_dir"]

            # Dynamically import the module and get the class
            module = importlib.import_module(module_name)
            GeneratorClass = getattr(module, class_name)

            registry[name] = (GeneratorClass, output_dir)
        except (KeyError, ImportError, AttributeError) as e:
            logger.error(f"Failed to load generator '{name}': {e}", exc_info=True)
            continue

    return registry


def initialize_data():
    """Initialize PokeDB data (download and prepare parsed directory)."""
    logger.info("Starting PokeDB data initialization...")
    initializer = PokeDBInitializer()
    initializer.run()


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


def run_generators(generator_names: list[str]):
    """
    Run specified generators.

    Args:
        generator_names: List of generator names to run (or ['all'] for all generators)

    Returns:
        bool: True if all generators succeeded, False if any failed
    """
    generator_registry = get_generator_registry()

    # Determine which generators to run
    if "all" in generator_names:
        generators_to_run = generator_registry.keys()
    else:
        generators_to_run = generator_names
        # Validate generator names
        invalid = set(generators_to_run) - set(generator_registry.keys())
        if invalid:
            logger.error(f"Unknown generators: {', '.join(invalid)}")
            logger.info(
                f"Available generators: {', '.join(generator_registry.keys())}"
            )
            sys.exit(1)

    # Run each generator and track failures
    failed_generators = []
    for name in generators_to_run:
        GeneratorClass, output_dir = generator_registry[name]
        logger.info(f"Running generator: {name}")

        try:
            generator = GeneratorClass(output_dir)
            success = generator.run()
            if success:
                logger.info(f"[OK] {name} completed successfully")
            else:
                logger.error(f"[FAIL] {name} failed")
                failed_generators.append((name, "generation failed"))
        except NotImplementedError as e:
            logger.warning(f"[SKIP] {name} not yet implemented: {e}")
            failed_generators.append((name, "not implemented"))
        except FileNotFoundError as e:
            logger.error(f"[FAIL] {name} failed - file not found: {e}", exc_info=True)
            failed_generators.append((name, "file not found"))
        except (OSError, IOError, PermissionError) as e:
            logger.error(
                f"[FAIL] {name} failed - file system error: {e}", exc_info=True
            )
            failed_generators.append((name, "file system error"))
        except Exception as e:
            logger.error(f"[FAIL] {name} failed: {e}", exc_info=True)
            failed_generators.append((name, "unexpected error"))

    # Report results
    if failed_generators:
        logger.error(f"\nFailed generators ({len(failed_generators)}):")
        for name, reason in failed_generators:
            logger.error(f"  - {name}: {reason}")
        return False
    else:
        logger.info(
            f"All {len(generators_to_run)} generator(s) completed successfully"
        )
        return True


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
        success = run_parsers(args.parsers)

        # Clear cache after parsers to ensure generators load fresh data
        if args.generators:
            from src.data.pokedb_loader import PokeDBLoader
            logger.info("Clearing cache before running generators...")
            PokeDBLoader.clear_cache()

    if args.generators:
        success = run_generators(args.generators) and success

    if success:
        logger.info("Complete!")
        sys.exit(0)
    else:
        logger.error("Completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
