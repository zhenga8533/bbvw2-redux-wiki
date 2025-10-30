"""
Utility module for handling MkDocs YAML files with custom tags.

This module provides functionality to load and save mkdocs.yml files
while preserving MkDocs-specific YAML tags like !ENV.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class EnvVar:
    """
    Wrapper for !ENV tag values to preserve them during load/dump cycles.

    MkDocs uses !ENV tags to reference environment variables in configuration.
    This class wraps those values so they can be properly preserved when
    reading and writing mkdocs.yml files.
    """
    def __init__(self, value):
        self.value = value


class PythonName:
    """
    Wrapper for !!python/name: tag values to preserve them during load/dump cycles.

    MkDocs uses !!python/name: tags to reference Python objects/functions.
    This class wraps those values so they can be properly preserved when
    reading and writing mkdocs.yml files.
    """
    def __init__(self, value):
        self.value = value


class MkDocsLoader(yaml.SafeLoader):
    """Custom YAML loader that handles MkDocs-specific tags like !ENV and !!python/name:"""
    pass


def env_constructor(loader, node):
    """
    Handle !ENV tags in mkdocs.yml - can be scalar or sequence.

    Examples:
        !ENV VARIABLE_NAME -> EnvVar("VARIABLE_NAME")
        !ENV [CI, false] -> EnvVar(["CI", False])
    """
    if isinstance(node, yaml.ScalarNode):
        return EnvVar(loader.construct_scalar(node))
    elif isinstance(node, yaml.SequenceNode):
        return EnvVar(loader.construct_sequence(node))
    else:
        return EnvVar(loader.construct_object(node))


def python_name_constructor(loader, tag_suffix, node):
    """
    Handle !!python/name: tags in mkdocs.yml.

    The tag suffix contains the Python object path (e.g., 'material.extensions.emoji.twemoji').
    We wrap it in PythonName to preserve it during load/dump cycles.

    Examples:
        !!python/name:material.extensions.emoji.twemoji
        -> PythonName("material.extensions.emoji.twemoji")
    """
    return PythonName(tag_suffix)


# Register the !ENV constructor
MkDocsLoader.add_constructor("!ENV", env_constructor)
# Register the !!python/name: multi-constructor to handle all python/name tags
MkDocsLoader.add_multi_constructor("tag:yaml.org,2002:python/name:", python_name_constructor)


class MkDocsDumper(yaml.SafeDumper):
    """Custom YAML dumper that preserves MkDocs-specific tags like !ENV and !!python/name:"""
    pass


def env_representer(dumper, data):
    """
    Preserve !ENV tags when dumping YAML.

    This representer ensures that EnvVar objects are written back
    with the !ENV tag and proper formatting.
    """
    if isinstance(data.value, list):
        # For sequences like [CI, false], create sequence node with !ENV tag
        # and flow style (inline representation)
        return yaml.SequenceNode(
            tag='!ENV',
            value=[dumper.represent_data(item) for item in data.value],
            flow_style=True
        )
    else:
        # For scalars
        return dumper.represent_scalar("!ENV", str(data.value))


def python_name_representer(dumper, data):
    """
    Preserve !!python/name: tags when dumping YAML.

    This representer ensures that PythonName objects are written back
    with the !!python/name: tag. The tag includes the object path.
    """
    tag = f"tag:yaml.org,2002:python/name:{data.value}"
    return dumper.represent_scalar(tag, "")


# Register the EnvVar representer
MkDocsDumper.add_representer(EnvVar, env_representer)
# Register the PythonName representer
MkDocsDumper.add_representer(PythonName, python_name_representer)


def load_mkdocs_config(mkdocs_path: Path) -> Dict[str, Any]:
    """
    Load mkdocs.yml configuration file with custom tag support.

    Args:
        mkdocs_path: Path to mkdocs.yml file

    Returns:
        Dictionary containing the parsed configuration

    Raises:
        FileNotFoundError: If mkdocs.yml doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    if not mkdocs_path.exists():
        raise FileNotFoundError(f"mkdocs.yml not found at {mkdocs_path}")

    with open(mkdocs_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=MkDocsLoader)


def save_mkdocs_config(mkdocs_path: Path, config: Dict[str, Any]) -> None:
    """
    Save mkdocs.yml configuration file with custom tag support.

    Args:
        mkdocs_path: Path to mkdocs.yml file
        config: Dictionary containing the configuration to save

    Raises:
        IOError: If the file cannot be written
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
    """
    Update the navigation section of mkdocs.yml while preserving other sections.

    This function specifically updates the "nav" key in mkdocs.yml while
    preserving all other configuration including custom tags like !ENV.

    Args:
        mkdocs_path: Path to mkdocs.yml file
        nav_section: Dictionary containing the new navigation structure

    Returns:
        True if update succeeded, False otherwise

    Example:
        nav_section = {
            "Pokédex": [
                {"Overview": "pokedex/pokedex.md"},
                {"Gen 5": [
                    {"#494 Victini": "pokedex/pokemon/victini.md"}
                ]}
            ]
        }
        update_mkdocs_nav(Path("mkdocs.yml"), nav_section)
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
