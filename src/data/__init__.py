"""
Data access layer for the wiki generator.

This module handles all data loading, saving, and initialization operations
for PokeDB data.
"""

from .pokedb_loader import PokeDBLoader
from .pokedb_initializer import PokeDBInitializer

__all__ = [
    "PokeDBLoader",
    "PokeDBInitializer",
]
