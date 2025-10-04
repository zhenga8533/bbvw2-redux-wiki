"""
PokeDB initializer to download and set up data from a GitHub repository.
"""

import shutil
import json
import requests
import traceback
import zipfile
import io
from pathlib import Path
from typing import List, Tuple
from .logger import setup_logger

logger = setup_logger(__name__, __file__)


class PokeDBInitializer:
    """Download PokeDB data from a GitHub repository and initialize parsed data."""

    def __init__(self, config_path: str = "src/config.json"):
        """Initialize the PokeDB initializer with configuration."""
        self._config = self._load_config(config_path)
        pokedb_config = self._config.get("pokedb", {})
        self.repo_url = pokedb_config.get("repo_url")
        self.branch = pokedb_config.get("branch")
        self.data_dir = Path(pokedb_config.get("data_dir", "data/pokedb"))
        self.parsed_dir = self.data_dir / "parsed"
        self.generations: List[str] = pokedb_config.get("generations", [])
        self.repo_owner, self.repo_name = self._parse_repo_url()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from a JSON file."""
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

    def _parse_repo_url(self) -> Tuple[str, str]:
        """Parse the repository owner and name from the URL."""
        if not self.repo_url:
            raise ValueError("Repository URL is not defined in the config.")
        repo_parts = self.repo_url.rstrip("/").split("/")
        return repo_parts[-2], repo_parts[-1]

    def _download_and_extract_repo(self) -> Path:
        """Download the repository as a zip and extract it to a temporary directory."""
        zip_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/refs/heads/{self.branch}.zip"
        logger.info(f"Downloading repository from {zip_url}...")

        response = requests.get(zip_url, stream=True, timeout=30)
        response.raise_for_status()

        temp_extract_path = self.data_dir.parent / "temp_pokedb"
        if temp_extract_path.exists():
            shutil.rmtree(temp_extract_path)

        logger.info(f"Extracting to temporary directory '{temp_extract_path}'...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            namelist = z.namelist()
            if not namelist:
                raise ValueError("Downloaded zip file is empty")
            repo_root_dir_name = namelist[0].split("/")[0]
            z.extractall(temp_extract_path)

        return temp_extract_path / repo_root_dir_name

    def _initialize_parsed_data(self):
        """Copy gen5 data to parsed directory for processing."""
        gen5_dir = self.data_dir / "gen5"

        if not gen5_dir.exists():
            logger.warning(
                "gen5 directory not found, skipping parsed data initialization"
            )
            return

        if self.parsed_dir.exists():
            logger.info(f"Removing existing parsed directory '{self.parsed_dir}'...")
            shutil.rmtree(self.parsed_dir)

        logger.info(f"Copying gen5 data to '{self.parsed_dir}' for processing...")
        shutil.copytree(gen5_dir, self.parsed_dir)
        logger.info(f"Parsed directory initialized with gen5 data")

    def run(self):
        """Execute the download and initialization process."""
        if not self.repo_url:
            logger.warning(
                "PokeDB repository URL not configured. Skipping initialization."
            )
            return

        if self.data_dir.exists() and any(self.data_dir.iterdir()):
            logger.info(
                f"Data directory '{self.data_dir}' already exists and is not empty."
            )
            user_input = input(
                "Do you want to re-download and replace it? (y/n): "
            ).lower()
            if user_input != "y":
                logger.info("Initialization cancelled.")
                return
            logger.info(f"Removing existing directory '{self.data_dir}'...")
            shutil.rmtree(self.data_dir)

        logger.info(
            f"Downloading PokeDB data to '{self.data_dir}' from {self.repo_url} (branch: {self.branch})..."
        )

        extracted_repo_path = None
        try:
            extracted_repo_path = self._download_and_extract_repo()
            self.data_dir.mkdir(parents=True, exist_ok=True)

            logger.info(
                f"Copying desired generation data: {', '.join(self.generations)}"
            )
            for gen in self.generations:
                source_path = extracted_repo_path / gen
                destination_path = self.data_dir / gen
                if source_path.exists():
                    shutil.copytree(str(source_path), str(destination_path))
                else:
                    logger.warning(
                        f"Generation folder '{gen}' not found in repository."
                    )

            logger.info(
                f"Download and extraction complete! Data saved to '{self.data_dir}'"
            )

            # Initialize parsed directory with gen5 data
            self._initialize_parsed_data()

        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred during download: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            logger.debug(traceback.format_exc())
        finally:
            if extracted_repo_path and extracted_repo_path.parent.exists():
                logger.info("Cleaning up temporary files...")
                shutil.rmtree(extracted_repo_path.parent)


if __name__ == "__main__":
    initializer = PokeDBInitializer()
    initializer.run()
