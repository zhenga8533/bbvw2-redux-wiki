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
from src.utils.logger_util import get_logger

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
    def _clean_existing_evolution_methods(
        evolves_to: list[EvolutionNode],
        evolution_id: str,
    ) -> None:
        """
        Clean out existing evolution methods for the target evolution.

        Keeps only one evolution path to the target, removing its details
        so it can be replaced with new details. This ensures we don't have
        duplicate evolution paths with old methods.

        Args:
            evolves_to: List of evolution nodes to clean
            evolution_id: The ID of the evolution target to clean
        """
        found = False

        # Use reverse iteration to safely remove items while iterating
        for i in range(len(evolves_to) - 1, -1, -1):
            evo = evolves_to[i]
            if evo.species_name != evolution_id:
                continue

            # Remove all but one existing evolution method
            if found:
                # We already kept one, remove this duplicate
                evolves_to.pop(i)
            else:
                # Keep this one but clear its evolution details for replacement
                evo.evolution_details = None
                found = True

    @staticmethod
    def _apply_evolution_update(
        evolves_to: list[EvolutionNode],
        evolution_id: str,
        evolution_details: EvolutionDetails,
    ) -> None:
        """
        Apply new evolution details to the target evolution.

        If an evolution node without details exists, it fills in the details.
        If all existing nodes have details, it creates a new node with the
        new details (for alternate evolution methods).

        Args:
            evolves_to: List of evolution nodes to update
            evolution_id: The ID of the evolution target
            evolution_details: The new evolution details to apply
        """
        for evo in evolves_to:
            # Skip if not the target evolution
            if evo.species_name != evolution_id:
                continue

            # Update the evolution details
            if evo.evolution_details is None:
                # Fill in the empty slot we created during cleanup
                evo.evolution_details = evolution_details
            else:
                # Add as an alternate evolution method
                node_copy = copy.deepcopy(evo)
                node_copy.evolution_details = evolution_details
                evolves_to.append(node_copy)
            break

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
        """
        Recursively update evolution nodes in the chain.

        This method traverses the evolution chain tree to find the Pokemon
        that is evolving (pokemon_id), then updates its evolution to the
        target (evolution_id) with new details.

        Args:
            original_chain: The root of the evolution chain
            evolution_node: Current node being processed
            pokemon_id: ID of the Pokemon that is evolving
            evolution_id: ID of the evolution target
            evolution_details: New evolution details to apply
            keep_existing: If True, add to existing methods; if False, replace
            processed: Set tracking which Pokemon have been processed
        """
        species_name = evolution_node.species_name
        evolves_to = evolution_node.evolves_to

        # Check if this node is the Pokemon we're looking for
        species_match = species_name == pokemon_id

        # Clean out old evolution methods if we're replacing (not adding)
        if species_match and not keep_existing and pokemon_id not in processed:
            processed.add(pokemon_id)
            EvolutionService._clean_existing_evolution_methods(evolves_to, evolution_id)

        # Process each evolution path
        for evo in evolves_to:
            # If this isn't the target Pokemon, recurse deeper
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

            # Skip if this evolution isn't our target
            if evo.species_name != evolution_id:
                continue

            # Apply the evolution update
            EvolutionService._apply_evolution_update(
                evolves_to, evolution_id, evolution_details
            )
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
        """
        Save the evolution node to all form files for this Pokemon.

        This ensures that Pokemon with multiple forms (e.g., wormadam-plant,
        wormadam-sandy) all get the updated evolution chain.
        """
        # Get all form files and the pre-loaded base Pokemon object
        form_files, base_pokemon_data = PokeDBLoader.find_all_form_files(pokemon_id)

        if not form_files:
            logger.warning(
                f"No form files found for {pokemon_id}, cannot save evolution chain."
            )
            return

        # Save to all form files
        for form_name, category in form_files:
            try:
                logger.debug(
                    f"Saving evolution chain for {pokemon_id} form: {form_name} (category: {category})"
                )

                # If we are processing the base form that we already loaded, reuse the object.
                # Otherwise, load the specific form data from disk.
                if base_pokemon_data and form_name == base_pokemon_data.name:
                    pokemon_data = base_pokemon_data
                else:
                    pokemon_data = PokeDBLoader.load_pokemon(
                        form_name, subfolder=category
                    )
                    if not pokemon_data:
                        logger.error(
                            f"Failed to load form file during save: {form_name} in {category}, skipping"
                        )
                        continue

                # Update the evolution chain and save
                pokemon_data.evolution_chain = evolution_chain
                PokeDBLoader.save_pokemon(form_name, pokemon_data, subfolder=category)

            except FileNotFoundError:
                logger.warning(
                    f"Form file not found during save: {form_name} in {category}, skipping"
                )
