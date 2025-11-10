"""
Utility functions for running parsers and generators with unified error handling.

This module provides a generic component runner that eliminates code duplication
between run_parsers() and run_generators() in main.py.
"""

import sys
from typing import Any, Callable

from src.utils.core.logger import get_logger

logger = get_logger(__name__)


def run_components(
    component_names: list[str],
    registry: dict[str, tuple[Any, ...]],
    component_type: str,
    instantiate_component: Callable[[tuple[Any, ...]], Any],
) -> bool:
    """Run specified components (parsers or generators) with unified error handling.

    Args:
        component_names (list[str]): List of component names to run (or ['all'] for all components)
        registry (dict[str, tuple[Any, ...]]): Registry mapping component names to (Class, *args) tuples
        component_type (str): Type of component for logging ('parser' or 'generator')
        instantiate_component (Callable[[tuple[Any, ...]], Any]): Function that takes a registry tuple and returns an
                              instantiated component ready to run

    Returns:
        bool: True if all components succeeded, False if any failed
    """
    # Determine which components to run
    if "all" in component_names:
        components_to_run = list(registry.keys())
    else:
        components_to_run = component_names
        # Validate component names
        invalid = set(components_to_run) - set(registry.keys())
        if invalid:
            logger.error(f"Unknown {component_type}s: {', '.join(invalid)}")
            logger.info(f"Available {component_type}s: {', '.join(registry.keys())}")
            sys.exit(1)

    # Run each component and track failures
    failed_components = []
    for name in components_to_run:
        registry_tuple = registry[name]
        logger.info(f"Running {component_type}: {name}")

        try:
            component = instantiate_component(registry_tuple)
            result = component.run()

            # Handle different return types (generators return bool, parsers return path)
            if isinstance(result, bool):
                # Generator-style: explicit success boolean
                if result:
                    logger.info(f"[OK] {name} completed successfully")
                else:
                    logger.error(f"[FAIL] {name} failed")
                    failed_components.append((name, "generation failed"))
            else:
                # Parser-style: returns path (truthy if succeeded)
                logger.info(f"[OK] {name} completed: {result}")

        except NotImplementedError as e:
            logger.warning(f"[SKIP] {name} not yet implemented: {e}")
            failed_components.append((name, "not implemented"))
        except FileNotFoundError as e:
            logger.error(f"[FAIL] {name} failed - file not found: {e}", exc_info=True)
            failed_components.append((name, "file not found"))
        except (OSError, IOError, PermissionError) as e:
            logger.error(
                f"[FAIL] {name} failed - file system error: {e}", exc_info=True
            )
            failed_components.append((name, "file system error"))
        except Exception as e:
            logger.error(f"[FAIL] {name} failed: {e}", exc_info=True)
            failed_components.append((name, "unexpected error"))

    # Report results
    if failed_components:
        logger.error(f"Failed {component_type}s ({len(failed_components)}):")
        for name, reason in failed_components:
            logger.error(f"  - {name}: {reason}")
        return False
    else:
        logger.info(
            f"All {len(components_to_run)} {component_type}(s) completed successfully"
        )
        return True


def run_parsers(
    parser_names: list[str], parser_registry: dict[str, tuple[Any, str, str]]
) -> bool:
    """Run specified parsers.

    Args:
        parser_names (list[str]): List of parser names to run (or ['all'] for all parsers)
        parser_registry (dict[str, tuple[Any, str, str]]): Registry mapping parser names to (ParserClass, input_file, output_dir) tuples

    Returns:
        bool: True if all parsers succeeded, False if any failed
    """

    def instantiate_parser(registry_tuple):
        ParserClass, input_file, output_dir = registry_tuple
        return ParserClass(input_file, output_dir)

    return run_components(parser_names, parser_registry, "parser", instantiate_parser)


def run_generators(
    generator_names: list[str], generator_registry: dict[str, tuple[Any, str]]
) -> bool:
    """Run specified generators.

    Args:
        generator_names (list[str]): List of generator names to run (or ['all'] for all generators)
        generator_registry (dict[str, tuple[Any, str]]): Registry mapping generator names to (GeneratorClass, output_dir) tuples

    Returns:
        bool: True if all generators succeeded, False if any failed
    """

    def instantiate_generator(registry_tuple):
        GeneratorClass, output_dir = registry_tuple
        return GeneratorClass(output_dir)

    return run_components(
        generator_names, generator_registry, "generator", instantiate_generator
    )
