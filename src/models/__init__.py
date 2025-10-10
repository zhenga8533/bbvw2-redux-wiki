"""
Domain models for the wiki generator.

This module exports all data structures (dataclasses) that represent
the domain entities: Pokemon, moves, items, abilities, and their related structures.
"""

from .pokedb import (
    # Pokemon-related models
    Pokemon,
    PokemonAbility,
    PokemonMoves,
    Stats,
    EVYield,
    Cries,
    Sprites,
    Form,
    # Evolution models
    EvolutionChain,
    EvolutionNode,
    EvolutionDetails,
    # Move-related models
    Move,
    MoveLearn,
    MoveMetadata,
    # Item models
    Item,
    # Ability models
    Ability,
    # Sprite-related models
    OtherSprites,
    AnimatedSprites,
    GenerationSprites,
    Versions,
    DreamWorld,
    Home,
    OfficialArtwork,
    Showdown,
)

__all__ = [
    # Pokemon-related models
    "Pokemon",
    "PokemonAbility",
    "PokemonMoves",
    "Stats",
    "EVYield",
    "Cries",
    "Sprites",
    "Form",
    # Evolution models
    "EvolutionChain",
    "EvolutionNode",
    "EvolutionDetails",
    # Move-related models
    "Move",
    "MoveLearn",
    "MoveMetadata",
    # Item models
    "Item",
    # Ability models
    "Ability",
    # Sprite-related models
    "OtherSprites",
    "AnimatedSprites",
    "GenerationSprites",
    "Versions",
    "DreamWorld",
    "Home",
    "OfficialArtwork",
    "Showdown",
]
