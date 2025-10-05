"""
Parser for Evolution Changes documentation file.

This parser:
1. Reads data/documentation/Evolution Changes.txt
2. Updates pokemon evolution data in data/pokedb/parsed/
3. Generates a markdown file to docs/evolution_changes.md
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from .base_parser import BaseParser
from ..utils.pokedb_loader import PokeDBLoader


class EvolutionChangesParser(BaseParser):
    """
    Parser for Evolution Changes documentation.

    Extracts evolution method changes and updates Pokemon JSON files.
    """

    def __init__(self):
        """Initialize the Evolution Changes parser."""
        super().__init__(input_file="Evolution Changes.txt", output_dir="docs")
        self.loader = PokeDBLoader(use_parsed=True)
        self.pokedb_dir = self.project_root / "data" / "pokedb" / "parsed"
