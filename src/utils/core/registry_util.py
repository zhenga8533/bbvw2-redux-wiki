"""
Utility functions for loading and managing component registries.

This module provides a generic registry loading mechanism that eliminates code
duplication between parser and generator registry loading in main.py.
"""

import importlib
from typing import Any, Dict, Tuple

from src.utils.core.config_util import get_config
from src.utils.core.logger_util import get_logger

logger = get_logger(__name__)


def get_component_registry(
    component_type: str, config_keys: Tuple[str, ...] = None
) -> Dict[str, Tuple[Any, ...]]:
    """
    Get the registry of available components by dynamically loading them from the config.

    This generic function works for both parsers and generators by extracting the
    appropriate configuration, dynamically importing modules and classes, and
    building a registry dictionary.

    Args:
        component_type: The type of component to load ('parsers' or 'generators')
        config_keys: Optional tuple of additional config keys to extract for each component
                    (e.g., ('input_file', 'output_dir') for parsers)

    Returns:
        dict: Registry mapping component names to tuples of (ComponentClass, *additional_values)
              - For parsers: (ParserClass, input_file, output_dir)
              - For generators: (GeneratorClass, output_dir)

    Example:
        >>> # Load parser registry
        >>> parser_registry = get_component_registry('parsers', ('input_file', 'output_dir'))
        >>> # Load generator registry
        >>> generator_registry = get_component_registry('generators', ('output_dir',))
    """
    config = get_config()
    component_config = config.get(component_type, {}).get("registry", {})
    registry = {}

    if config_keys is None:
        config_keys = ()

    for name, details in component_config.items():
        try:
            # Extract required fields
            module_name = details["module"]
            class_name = details["class"]

            # Dynamically import the module and get the class
            module = importlib.import_module(module_name)
            ComponentClass = getattr(module, class_name)

            # Extract additional config values
            additional_values = tuple(details[key] for key in config_keys)

            # Store in registry as (Class, *additional_values)
            registry[name] = (ComponentClass, *additional_values)

        except (KeyError, ImportError, AttributeError) as e:
            logger.error(
                f"Failed to load {component_type[:-1]} '{name}': {e}", exc_info=True
            )
            continue

    return registry


def get_parser_registry() -> Dict[str, Tuple[Any, str, str]]:
    """
    Get the registry of available parsers.

    Returns:
        dict: Registry mapping parser names to (ParserClass, input_file, output_dir) tuples
    """
    return get_component_registry("parsers", ("input_file", "output_dir"))


def get_generator_registry() -> Dict[str, Tuple[Any, str]]:
    """
    Get the registry of available generators.

    Returns:
        dict: Registry mapping generator names to (GeneratorClass, output_dir) tuples
    """
    return get_component_registry("generators", ("output_dir",))
