"""
PokeDB initializer to download and set up data from a GitHub repository.
"""

import io
import os
import shutil
import zipfile
from pathlib import Path

import requests

from src.utils.core.config import (
    POKEDB_BRANCH,
    POKEDB_DATA_DIR,
    POKEDB_GENERATIONS,
    POKEDB_REPO_URL,
)
from src.utils.core.logger import get_logger

logger = get_logger(__name__)


class PokeDBInitializer:
    """Initializer for the PokeDB data repository."""

    def __init__(self):
        """Initialize the PokeDB initializer with configuration."""
        self.repo_url = POKEDB_REPO_URL
        self.branch = POKEDB_BRANCH
        self.data_dir = Path(POKEDB_DATA_DIR)
        self.parsed_dir = self.data_dir / "parsed"
        self.generations = POKEDB_GENERATIONS
        self.repo_owner, self.repo_name = self._parse_repo_url()

    def _parse_repo_url(self) -> tuple[str, str]:
        """Parse the repository URL to extract the owner and repository name.

        Raises:
            ValueError: If the repository URL is not defined in the config.

        Returns:
            tuple[str, str]: A tuple of (owner, repo_name) extracted from the repository URL
        """
        if not self.repo_url:
            raise ValueError("Repository URL is not defined in the config.")
        repo_parts = self.repo_url.rstrip("/").split("/")
        return repo_parts[-2], repo_parts[-1]

    def _download_and_extract_repo(self) -> Path:
        """Download and extract the PokeDB repository from GitHub.

        Raises:
            ValueError: If the downloaded zip is empty.

        Returns:
            Path: Path to the extracted repository root directory.
        """
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

    def _initialize_parsed_data(self) -> None:
        """Initialize the parsed data directory."""
        base_gen = POKEDB_GENERATIONS[0]
        base_gen_dir = self.data_dir / base_gen

        if not base_gen_dir.exists():
            logger.warning(
                f"{base_gen} directory not found, skipping parsed data initialization"
            )
            return

        if self.parsed_dir.exists():
            logger.info(f"Removing existing parsed directory '{self.parsed_dir}'...")
            shutil.rmtree(self.parsed_dir)

        logger.info(f"Copying {base_gen} data to '{self.parsed_dir}' for processing...")
        shutil.copytree(base_gen_dir, self.parsed_dir)
        logger.info(f"Parsed directory initialized with {base_gen} data")

    def run(self) -> None:
        """Run the PokeDB initialization process.

        Raises:
            RuntimeError: If the repository URL is not configured.
            RuntimeError: If the data directory already exists and is not empty.
            RuntimeError: If the download and extraction process fails.
        """
        if not self.repo_url:
            logger.warning(
                "PokeDB repository URL not configured. Skipping initialization."
            )
            return

        if self.data_dir.exists() and any(self.data_dir.iterdir()):
            logger.info(
                f"Data directory '{self.data_dir}' already exists and is not empty."
            )

            # Check for non-interactive mode
            skip_prompt = os.getenv("WIKI_NON_INTERACTIVE", "false").lower() in (
                "true",
                "1",
                "yes",
            )
            if skip_prompt:
                logger.info("Non-interactive mode: skipping re-download")
                return

            try:
                user_input = (
                    input("Do you want to re-download and replace it? (yes/no): ")
                    .strip()
                    .lower()
                )

                # Accept various affirmative responses
                if user_input not in ("yes", "y"):
                    logger.info("Initialization cancelled by user.")
                    return

            except (EOFError, KeyboardInterrupt):
                # Handle Ctrl+C, Ctrl+D, or automated environments
                logger.info("\nInitialization cancelled by user.")
                return
            except OSError as e:
                # Handle I/O errors when reading from stdin (e.g., closed stdin)
                logger.error(f"Error reading user input: {e}")
                logger.info("Initialization cancelled due to input error.")
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

            # Initialize parsed directory with base generation data
            self._initialize_parsed_data()

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during download: {e}", exc_info=True)
            raise RuntimeError(f"Failed to download repository data: {e}") from e
        except (zipfile.BadZipFile, ValueError) as e:
            logger.error(f"Invalid repository data: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process repository archive: {e}") from e
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File system error during initialization: {e}", exc_info=True)
            raise RuntimeError(f"Failed to create or copy files: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}", exc_info=True)
            raise
        finally:
            # Always attempt cleanup, but don't fail if cleanup fails
            if extracted_repo_path and extracted_repo_path.parent.exists():
                try:
                    logger.info("Cleaning up temporary files...")
                    shutil.rmtree(extracted_repo_path.parent)
                except (OSError, PermissionError) as cleanup_error:
                    logger.warning(
                        f"Failed to clean up temporary files: {cleanup_error}"
                    )


if __name__ == "__main__":
    initializer = PokeDBInitializer()
    initializer.run()
