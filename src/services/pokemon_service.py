"""
Service for copying new moves from gen8 to parsed data folder.
"""

import json
from collections import Counter
from typing import Any

from src.data.pokedb_loader import PokeDBLoader
from src.utils.logger_util import get_logger
from src.utils.text_util import name_to_id

logger = get_logger(__name__)


class PokemonService:

    @staticmethod
    def update_attribute(pokemon: str, attribute: str, value: str) -> None:
        pass
