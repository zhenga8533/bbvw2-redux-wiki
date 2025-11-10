"""
Location parser base class for parsers that generate location data.

This parser extends BaseParser to add location data management functionality,
allowing parsers to safely load, modify, and save location JSON files without
dependencies on execution order.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.text.text_util import sanitize_filename

from .base_parser import BaseParser


class LocationParser(BaseParser):
    """
    Base class for parsers that generate location data files.

    This class handles:
    - Loading existing location data from JSON files
    - Merging new data with existing data
    - Safe concurrent updates to location files
    - Parsing location/sublocation patterns
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Location parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
        super().__init__(input_file=input_file, output_dir=output_dir)

        # Location data tracking
        self._locations_data: Dict[str, Dict[str, Any]] = {}
        self._current_location = ""
        self._current_sublocation = ""
        self._location_data_dir = Path("data/locations")

        # Tracking sets for preventing duplicates across parse runs
        # Subclasses can register their own tracking keys
        self._initialized_data: Dict[str, set] = {}

    def parse(self) -> None:
        """Parse the input file and generate markdown output.

        Override to reset tracking state before parsing.
        Subclasses can override this to add custom tracking resets.
        """
        # Clear all tracking sets at the start of each parse run
        for key in self._initialized_data:
            self._initialized_data[key].clear()
        super().parse()

    def _register_tracking_key(self, key: str) -> None:
        """Register a tracking key for duplicate prevention.

        Args:
            key (str): The tracking key name (e.g., "trainers", "wild_encounters").
        """
        if key not in self._initialized_data:
            self._initialized_data[key] = set()

    def _is_first_encounter(self, tracking_key: str, location_key: Optional[str] = None) -> bool:
        """Check if this is the first encounter of a location for a specific data type.

        Args:
            tracking_key (str): The tracking key (e.g., "trainers", "wild_encounters").
            location_key (str, optional): Custom location key. If None, uses current location/sublocation.

        Returns:
            bool: True if this is the first encounter, False otherwise.
        """
        if tracking_key not in self._initialized_data:
            self._register_tracking_key(tracking_key)

        if location_key is None:
            location_key = f"{self._current_location}/{self._current_sublocation}" if self._current_sublocation else self._current_location

        return location_key not in self._initialized_data[tracking_key]

    def _mark_as_initialized(self, tracking_key: str, location_key: Optional[str] = None) -> None:
        """Mark a location as initialized for a specific data type.

        Args:
            tracking_key (str): The tracking key (e.g., "trainers", "wild_encounters").
            location_key (str, optional): Custom location key. If None, uses current location/sublocation.
        """
        if tracking_key not in self._initialized_data:
            self._register_tracking_key(tracking_key)

        if location_key is None:
            location_key = f"{self._current_location}/{self._current_sublocation}" if self._current_sublocation else self._current_location

        self._initialized_data[tracking_key].add(location_key)

    def _clear_location_data_on_first_encounter(
        self, tracking_key: str, data_key: str, location_key: Optional[str] = None
    ) -> bool:
        """Clear location data on first encounter and mark as initialized.

        This is a helper method that combines the common pattern of:
        1. Checking if this is the first encounter
        2. Clearing data if it is
        3. Marking as initialized
        4. Ensuring the data key exists

        Args:
            tracking_key (str): The tracking key (e.g., "trainers", "wild_encounters").
            data_key (str): The key in the location data to clear (e.g., "trainers", "wild_encounters").
            location_key (str, optional): Custom location key. If None, uses current location/sublocation.

        Returns:
            bool: True if this was the first encounter and data was cleared, False otherwise.
        """
        if self._current_location not in self._locations_data:
            return False

        if location_key is None:
            location_key = f"{self._current_location}/{self._current_sublocation}" if self._current_sublocation else self._current_location

        is_first = self._is_first_encounter(tracking_key, location_key)

        # Determine target (sublocation or root location)
        if self._current_sublocation:
            target = self._get_or_create_sublocation(
                self._locations_data[self._current_location], self._current_sublocation
            )
        else:
            target = self._locations_data[self._current_location]

        if is_first:
            # Clear the data on first encounter
            # Determine the correct type based on data_key
            if data_key in ["trainers"]:  # Keys that should be lists
                target[data_key] = []
            else:  # Keys that should be dicts (wild_encounters, hidden_grotto, etc.)
                target[data_key] = {}
            self._mark_as_initialized(tracking_key, location_key)
        else:
            # Ensure key exists but don't clear
            if data_key not in target:
                if data_key in ["trainers"]:  # Keys that should be lists
                    target[data_key] = []
                else:  # Keys that should be dicts
                    target[data_key] = {}

        return is_first

    def _parse_location_name(self, location_raw: str) -> tuple[str, Optional[str]]:
        """Parse a location string to extract parent location and sublocation.

        Handles patterns like:
        - "Route 1" -> ("Route 1", None)
        - "Castelia City - Battle Company" -> ("Castelia City", "Battle Company")

        Args:
            location_raw (str): The raw location string.

        Returns:
            tuple[str, Optional[str]]: (parent_location, sublocation_name)
        """
        if " - " in location_raw:
            parts = location_raw.split(" - ", 1)
            return parts[0], parts[1]
        return location_raw, None

    def _get_location_file_path(self, location: str) -> Path:
        """Get the file path for a location's JSON file.

        Args:
            location (str): The location name (parent location only).

        Returns:
            Path: The path to the location's JSON file.
        """
        filename = sanitize_filename(location)
        filename = f"{filename}.json"
        return self._location_data_dir / filename

    def _load_location_data(self, location: str) -> Dict[str, Any]:
        """Load existing location data from file or create new structure.

        Args:
            location (str): The parent location name.

        Returns:
            Dict[str, Any]: The location data dictionary.
        """
        file_path = self._get_location_file_path(location)

        if file_path.exists():
            self.logger.debug(f"Loading existing location data from {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Ensure required keys exist
                if "name" not in data:
                    data["name"] = location
                if "sublocations" not in data:
                    data["sublocations"] = {}

                return data
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(
                    f"Error loading {file_path}: {e}. Creating new data structure."
                )

        # Create new structure
        self.logger.debug(f"Creating new location data structure for {location}")
        return {
            "name": location,
            "sublocations": {},
        }

    def _initialize_location_data(self, location_raw: str) -> None:
        """Initialize or load data structure for a location.

        Args:
            location_raw (str): The raw location name (may include sublocation).
        """
        parent_location, sublocation_name = self._parse_location_name(location_raw)

        # Load or create location data if not already loaded
        if parent_location not in self._locations_data:
            self._locations_data[parent_location] = self._load_location_data(
                parent_location
            )

        # Store current working location
        self._current_location = parent_location
        self._current_sublocation = sublocation_name or ""

        # If this is a sublocation, ensure it exists in the structure
        if sublocation_name:
            self._ensure_sublocation_exists(parent_location, sublocation_name)

    def _ensure_sublocation_exists(
        self, parent_location: str, sublocation_name: str
    ) -> None:
        """Ensure a sublocation exists in the location data structure.

        Args:
            parent_location (str): The parent location name.
            sublocation_name (str): The sublocation name (can contain "/" for nesting).
        """
        if parent_location not in self._locations_data:
            return

        location_data = self._locations_data[parent_location]

        if "sublocations" not in location_data:
            location_data["sublocations"] = {}

        # Handle nested sublocations (e.g., "Battle Company/47F")
        parts = sublocation_name.split("/")
        current = location_data["sublocations"]

        for i, part in enumerate(parts):
            if part not in current:
                current[part] = {
                    "name": part,
                    "sublocations": {},
                }

            # Navigate to next level if not the last part
            if i < len(parts) - 1:
                if "sublocations" not in current[part]:
                    current[part]["sublocations"] = {}
                current = current[part]["sublocations"]

    def _get_or_create_sublocation(
        self, location_data: Dict[str, Any], sublocation_path: str
    ) -> Dict[str, Any]:
        """Get or create a nested sublocation using path notation.

        Args:
            location_data (Dict[str, Any]): The parent location data.
            sublocation_path (str): The sublocation path (can contain "/" for nesting).

        Returns:
            Dict[str, Any]: The target sublocation dictionary.
        """
        if "sublocations" not in location_data:
            location_data["sublocations"] = {}

        # Split path by "/" to handle nesting
        parts = sublocation_path.split("/")
        current = location_data["sublocations"]

        for i, part in enumerate(parts):
            if part not in current:
                current[part] = {
                    "name": part,
                    "sublocations": {},
                }

            # If this is not the last part, navigate into nested sublocations
            if i < len(parts) - 1:
                if "sublocations" not in current[part]:
                    current[part]["sublocations"] = {}
                current = current[part]["sublocations"]
            else:
                # Return the final sublocation
                return current[part]

        return current[parts[-1]]

    def _save_location_data(self, location: str) -> None:
        """Save location data to a JSON file.

        Args:
            location (str): The parent location name (without sublocation suffix).
        """
        if location not in self._locations_data:
            self.logger.warning(
                f"Attempted to save location '{location}' but no data found"
            )
            return

        # Create data directory if it doesn't exist
        self._location_data_dir.mkdir(parents=True, exist_ok=True)

        output_path = self._get_location_file_path(location)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    self._locations_data[location], f, indent=2, ensure_ascii=False
                )
            self.logger.debug(f"Saved location data to {output_path}")
        except IOError as e:
            self.logger.error(f"Error saving location data to {output_path}: {e}")

    def finalize(self) -> None:
        """Finalize parsing and save all location data."""
        # Save all loaded locations
        for location in list(self._locations_data.keys()):
            self._save_location_data(location)

        super().finalize()
