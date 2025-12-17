"""
Utility module for handling MkDocs YAML files with custom tags.

This module provides functionality to load and save mkdocs.yml files
while preserving MkDocs-specific YAML tags like !ENV.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class EnvVar:
    """Wrapper for !ENV tag values to preserve them during load/dump cycles."""

    def __init__(self, value: Any):
        """Initialize the EnvVar wrapper.

        Args:
            value (Any): The value to wrap.
        """
        self.value = value


class PythonName:
    """Wrapper for !!python/name: tag values to preserve them during load/dump cycles."""

    def __init__(self, value: str):
        """Initialize the PythonName wrapper.

        Args:
            value (str): The Python object path to wrap.
        """
        self.value = value


class MkDocsLoader(yaml.SafeLoader):
    """Custom YAML loader that handles MkDocs-specific tags like !ENV and !!python/name:"""

    pass


def env_constructor(loader: MkDocsLoader, node: yaml.Node) -> EnvVar:
    """Construct an EnvVar from a YAML node.

    Args:
        loader (MkDocsLoader): The YAML loader instance
        node (yaml.Node): The YAML node to construct from

    Returns:
        EnvVar: The constructed EnvVar instance
    """
    if isinstance(node, yaml.ScalarNode):
        return EnvVar(loader.construct_scalar(node))
    elif isinstance(node, yaml.SequenceNode):
        return EnvVar(loader.construct_sequence(node))
    else:
        return EnvVar(loader.construct_object(node))


def python_name_constructor(
    loader: MkDocsLoader, tag_suffix: str, node: yaml.Node
) -> PythonName:
    """Construct a PythonName from a YAML node.

    Args:
        loader (MkDocsLoader): The YAML loader instance
        tag_suffix (str): The suffix of the tag (object path)
        node (yaml.Node): The YAML node to construct from

    Returns:
        PythonName: The constructed PythonName instance
    """
    return PythonName(tag_suffix)


# Register the !ENV constructor
MkDocsLoader.add_constructor("!ENV", env_constructor)
# Register the !!python/name: multi-constructor to handle all python/name tags
MkDocsLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", python_name_constructor
)


class MkDocsDumper(yaml.SafeDumper):
    """Custom YAML dumper that preserves MkDocs-specific tags like !ENV and !!python/name:"""

    pass


def env_representer(dumper: MkDocsDumper, data: EnvVar) -> yaml.Node:
    """Represent an EnvVar instance as a YAML node.

    Args:
        dumper (MkDocsDumper): The YAML dumper instance
        data (EnvVar): The EnvVar instance to represent

    Returns:
        yaml.Node: The YAML node representation of the EnvVar instance
    """
    if isinstance(data.value, list):
        # For sequences like [CI, false], create sequence node with !ENV tag
        # and flow style (inline representation)
        return yaml.SequenceNode(
            tag="!ENV",
            value=[dumper.represent_data(item) for item in data.value],
            flow_style=True,
        )
    else:
        # For scalars
        return dumper.represent_scalar("!ENV", str(data.value))


def python_name_representer(dumper: MkDocsDumper, data: PythonName) -> yaml.Node:
    """Represent a PythonName instance as a YAML node.

    Args:
        dumper (MkDocsDumper): The YAML dumper instance
        data (PythonName): The PythonName instance to represent

    Returns:
        yaml.Node: The YAML node representation of the PythonName instance
    """
    tag = f"tag:yaml.org,2002:python/name:{data.value}"
    return dumper.represent_scalar(tag, "")


# Register the EnvVar representer
MkDocsDumper.add_representer(EnvVar, env_representer)
# Register the PythonName representer
MkDocsDumper.add_representer(PythonName, python_name_representer)


def load_mkdocs_config(mkdocs_path: Path) -> Dict[str, Any]:
    """Load mkdocs.yml configuration file with custom tag support.

    Args:
        mkdocs_path (Path): Path to mkdocs.yml file

    Raises:
        FileNotFoundError: If mkdocs.yml doesn't exist
        yaml.YAMLError: If the YAML is invalid

    Returns:
        Dict[str, Any]: The parsed configuration
    """
    if not mkdocs_path.exists():
        raise FileNotFoundError(f"mkdocs.yml not found at {mkdocs_path}")

    with open(mkdocs_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=MkDocsLoader)


def save_mkdocs_config(mkdocs_path: Path, config: Dict[str, Any]) -> None:
    """Save mkdocs.yml configuration file with custom tag support.

    Args:
        mkdocs_path (Path): Path to mkdocs.yml file
        config (Dict[str, Any]): Configuration data to save
    """
    with open(mkdocs_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            Dumper=MkDocsDumper,
        )


def update_mkdocs_nav(mkdocs_path: Path, nav_section: Dict[str, Any]) -> bool:
    """Update the navigation section of mkdocs.yml while preserving other sections.

    Args:
        mkdocs_path (Path): Path to mkdocs.yml file
        nav_section (Dict[str, Any]): Navigation section to update or add

    Returns:
        bool: True if update succeeded, False if it failed
    """
    try:
        config = load_mkdocs_config(mkdocs_path)

        if "nav" not in config:
            config["nav"] = []

        nav_list = config["nav"]

        # Find and replace the section (e.g., "Pokédex")
        section_key = list(nav_section.keys())[0]  # e.g., "Pokédex"
        section_index = None

        for i, item in enumerate(nav_list):
            if isinstance(item, dict) and section_key in item:
                section_index = i
                break

        if section_index is not None:
            nav_list[section_index] = nav_section
        else:
            # Add section if it doesn't exist
            nav_list.append(nav_section)

        config["nav"] = nav_list

        save_mkdocs_config(mkdocs_path, config)
        return True

    except Exception as e:
        return False


def update_pokedex_subsection(
    mkdocs_path: Path,
    subsection_name: str,
    nav_items: list,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Update or create a subsection within the Pokédex navigation section.

    Args:
        mkdocs_path (Path): Path to mkdocs.yml file
        subsection_name (str): Name of the subsection to update (e.g., "Pokémon", "Moves", "Items", "Abilities")
        nav_items (list): List of navigation items for the subsection
        logger (Optional[logging.Logger], optional): Logger for logging messages. Defaults to None.

    Raises:
        ValueError: If mkdocs.yml is malformed or missing required sections
        ValueError: If Pokédex section is missing in nav

    Returns:
        bool: True if the update was successful, False otherwise
    """
    try:
        if not mkdocs_path.exists():
            if logger:
                logger.error(f"mkdocs.yml not found at {mkdocs_path}")
            return False

        # Load current mkdocs.yml
        config = load_mkdocs_config(mkdocs_path)

        # Find the Pokédex section in nav
        if "nav" not in config:
            raise ValueError("mkdocs.yml does not contain a 'nav' section")

        nav_list = config["nav"]
        pokedex_index = None

        # Find the Pokédex section
        for i, item in enumerate(nav_list):
            if isinstance(item, dict) and "Pokédex" in item:
                pokedex_index = i
                break

        if pokedex_index is None:
            raise ValueError(
                "mkdocs.yml nav section does not contain 'Pokédex'. "
                "Please add a 'Pokédex' section to the navigation first."
            )

        # Get the Pokédex navigation items
        pokedex_nav = nav_list[pokedex_index]["Pokédex"]
        if not isinstance(pokedex_nav, list):
            pokedex_nav = []

        # Find or create subsection within Pokédex
        subsection_index = None
        for i, item in enumerate(pokedex_nav):
            if isinstance(item, dict) and subsection_name in item:
                subsection_index = i
                break

        # Update or append subsection
        subsection = {subsection_name: nav_items}
        if subsection_index is not None:
            pokedex_nav[subsection_index] = subsection
        else:
            pokedex_nav.append(subsection)

        # Update the config
        nav_list[pokedex_index] = {"Pokédex": pokedex_nav}
        config["nav"] = nav_list

        # Write updated mkdocs.yml
        save_mkdocs_config(mkdocs_path, config)

        if logger:
            logger.info(f"Updated mkdocs.yml with {subsection_name} subsection")
        return True

    except Exception as e:
        if logger:
            logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
        return False
