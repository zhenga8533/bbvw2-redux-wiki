"""
Service class for managing Pokemon evolution chain operations.

This service encapsulates the logic for updating and manipulating
evolution chains, separating it from the parser implementation.
"""

import copy
from typing import Optional

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import (
    EvolutionChain,
    EvolutionNode,
    EvolutionDetails,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EvolutionService:
    """
    Service for managing Pokemon evolution chain updates.

    Provides methods to update evolution chains with new evolution methods
    while preserving or replacing existing data as needed.
    """

    @staticmethod
    def update_evolution_chain(
        pokemon_id: str,
        evolution_id: str,
        evolution_chain: EvolutionChain,
        evolution_details: EvolutionDetails,
        keep_existing: bool = False,
        processed: Optional[set] = None,
    ) -> EvolutionChain:
        """
        Update an evolution chain with new evolution details.

        Args:
            pokemon_id: ID of the Pokemon that is evolving
            evolution_id: ID of the evolution target
            evolution_chain: The evolution chain to update
            evolution_details: The new evolution details
            keep_existing: If True, add to existing methods; if False, replace
            processed: Set of pokemon_ids already processed (for internal use)

        Returns:
            EvolutionChain: The updated evolution chain
        """
        if processed is None:
            processed = set()

        mode = "addition" if keep_existing else "replacement"
        logger.debug(
            f"Updating evolution chain: {pokemon_id} -> {evolution_id} (mode: {mode})",
            extra={
                "pokemon_id": pokemon_id,
                "evolution_id": evolution_id,
                "keep_existing": keep_existing,
            },
        )

        EvolutionService._update_evolution_node(
            evolution_chain,
            evolution_chain,
            pokemon_id,
            evolution_id,
            evolution_details,
            keep_existing,
            processed,
        )

        # Save the updated chain to ALL Pokemon in the chain
        all_species = EvolutionService._collect_all_species(evolution_chain)
        for species_id in all_species:
            EvolutionService._save_evolution_node(species_id, evolution_chain)

        logger.debug(f"Successfully updated evolution chain for {pokemon_id}")
        return evolution_chain

    @staticmethod
    def _update_evolution_node(
        original_chain: EvolutionChain,
        evolution_node: EvolutionChain | EvolutionNode,
        pokemon_id: str,
        evolution_id: str,
        evolution_details: EvolutionDetails,
        keep_existing: bool,
        processed: set,
    ) -> None:
        """Recursively update evolution nodes."""
        species_name = evolution_node.species_name
        evolves_to = evolution_node.evolves_to
        # Match on the PARENT species (the one that evolves)
        species_match = species_name == pokemon_id

        # Clean out evolution methods (keeps one backup)
        if species_match and not keep_existing and pokemon_id not in processed:
            processed.add(pokemon_id)
            found = False

            # Use reverse iteration to safely remove items
            for i in range(len(evolves_to) - 1, -1, -1):
                evo = evolves_to[i]
                if evo.species_name != evolution_id:
                    continue

                # Remove all but one existing evolution method
                if found:
                    evolves_to.pop(i)
                else:
                    evo.evolution_details = None
                    found = True

        for evo in evolves_to:
            # Recurse if not the target species
            if not species_match:
                EvolutionService._update_evolution_node(
                    original_chain,
                    evo,
                    pokemon_id,
                    evolution_id,
                    evolution_details,
                    keep_existing,
                    processed,
                )
                continue

            # Skip if not the target evolution
            if evo.species_name != evolution_id:
                continue

            # Update the evolution details
            if evo.evolution_details is None:
                evo.evolution_details = evolution_details
            else:
                node_copy = copy.deepcopy(evo)
                node_copy.evolution_details = evolution_details
                evolves_to.append(node_copy)
            break

    @staticmethod
    def _collect_all_species(node: EvolutionChain | EvolutionNode) -> set[str]:
        """
        Recursively collect all species IDs in an evolution chain.

        Args:
            node: The evolution chain or node to traverse

        Returns:
            Set of all species IDs in the chain
        """
        species_ids = {node.species_name}
        for evolution in node.evolves_to:
            species_ids.update(EvolutionService._collect_all_species(evolution))
        return species_ids

    @staticmethod
    def _save_evolution_node(pokemon_id: str, evolution_chain: EvolutionChain):
        """Save the evolution node to a file."""
        logger.debug(f"Saving evolution chain for {pokemon_id}")
        pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
        pokemon_data.evolution_chain = evolution_chain
        PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
