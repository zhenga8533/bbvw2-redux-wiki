# BBVW2 Redux Wiki Generator

An automated documentation generation system for **Blaze Black 2 & Volt White 2 Redux** - a comprehensive ROM hack of Pokémon Black 2 and White 2.

**Live Site:** [https://zhenga8533.github.io/bbvw2-redux-wiki/](https://zhenga8533.github.io/bbvw2-redux-wiki/)

## Overview

This project generates and maintains a complete wiki website with detailed information about all Pokémon, moves, abilities, items, locations, and game changes for the Blaze Black 2 & Volt White 2 Redux ROM hack.

The generator:

1. Downloads Pokémon data from an external PokeDB repository
2. Parses custom ROM hack documentation files
3. Generates comprehensive markdown documentation pages
4. Builds a static website using MkDocs with Material theme

## Features

### Documentation Coverage

- **649 Pokémon** - Complete stats, moves, evolutions, and type effectiveness
- **All Abilities** - Descriptions and which Pokémon have them
- **All Items** - Effects, locations, and availability
- **All Moves** - Power, accuracy, type, and learning methods
- **50+ Locations** - Wild encounters and trainer rosters
- **ROM Hack Changes** - Evolution methods, type effectiveness, move changes, and more

### Technical Features

- **Thread-safe caching system** with LRU eviction for optimal performance
- **Modular architecture** with registry-based component loading
- **Type-safe data models** using Python dataclasses
- **Concurrent file operations** with read-write locks
- **Fast JSON processing** using orjson
- **Configurable generation** for specific components

## Installation

### Prerequisites

- Python 3.12 or higher
- Git

### Setup

1. Clone the repository:

```bash
git clone https://github.com/zhenga8533/bbvw2-redux-wiki.git
cd bbvw2-redux-wiki
```

2. Install the package and dependencies:

```bash
pip install -e .
```

3. Initialize the PokeDB data:

```bash
python -m bbvw2_wiki --init
# or
bbvw2-wiki --init
```

This downloads the Pokémon database from the external PokeDB repository and sets up the necessary data structures.

## Usage

### Command Line Interface

The main script provides several commands:

#### Initialize Data

Download and set up the PokeDB data:

```bash
python -m bbvw2_wiki --init
# or
bbvw2-wiki --init
```

#### Run Parsers

Parse documentation files and convert them to markdown:

```bash
# Run all parsers
python -m bbvw2_wiki --parsers all

# Run specific parsers
python -m bbvw2_wiki --parsers evolution_changes gift_pokemon

# List available parsers
python -m bbvw2_wiki --list-parsers
```

Available parsers:

- `evolution_changes` - Evolution method changes
- `gift_pokemon` - Gift Pokémon information
- `item_changes` - Item modifications
- `legendary_locations` - Legendary Pokémon locations
- `move_changes` - Move modifications
- `pokemon_changes` - Pokémon stat/ability changes
- `trade_changes` - Trade evolution alternatives
- `trainer_changes` - Trainer roster changes
- `type_changes` - Type matchup changes
- `wild_area_changes` - Wild encounter modifications

#### Run Generators

Generate reference pages from PokeDB data:

```bash
# Run all generators
python -m bbvw2_wiki --generators all

# Run specific generators
python -m bbvw2_wiki --generators pokemon abilities

# List available generators
python -m bbvw2_wiki --list-generators
```

Available generators:

- `pokemon` - Individual Pokémon pages with stats, moves, and evolutions
- `abilities` - Ability descriptions and Pokémon that have them
- `items` - Item information and locations
- `moves` - Move details and learning methods
- `locations` - Location wild encounters and trainers

#### Build the Website

Generate and serve the static site:

```bash
# Build the site
mkdocs build

# Serve locally for preview (http://127.0.0.1:8000)
mkdocs serve

# Deploy to GitHub Pages
mkdocs gh-deploy
```

## Project Structure

```
bbvw2-redux-wiki/
├── data/                           # Source data
│   ├── documentation/              # ROM hack documentation files (.txt)
│   ├── pokedb/                     # Pokémon database (downloaded)
│   │   ├── gen5/                   # Generation 5 baseline data
│   │   ├── gen8/                   # Generation 8 data for modern features
│   │   └── parsed/                 # Working copy with modifications
│   └── locations/                  # Generated location data (.json)
├── docs/                           # Generated markdown documentation
│   ├── index.md                    # Homepage
│   ├── getting_started/            # Setup guides, FAQ, changelog
│   ├── changes/                    # ROM hack modifications
│   ├── reference/                  # Reference information
│   ├── locations/                  # Location encounter data
│   ├── pokedex/                    # Pokémon, abilities, items, moves
│   └── stylesheets/                # Custom CSS
├── src/                            # Python source code
│   └── bbvw2_wiki/                 # Main package
│       ├── __init__.py             # Package initialization
│       ├── __main__.py             # CLI entry point
│       ├── py.typed                # Type hint marker
│       ├── parsers/                # Documentation parsers
│       │   ├── base_parser.py      # Base class for all parsers
│       │   ├── location_parser.py  # Base class for location parsers
│       │   └── *_parser.py         # Individual parser implementations
│       ├── generators/             # Reference page generators
│       │   ├── base_generator.py   # Base class for all generators
│       │   └── *_generator.py      # Individual generator implementations
│       └── utils/                  # Utility modules
│           ├── core/               # Core infrastructure
│           │   ├── config.py       # Configuration constants
│           │   ├── executor.py     # Component execution
│           │   ├── initializer.py  # Data initialization
│           │   ├── loader.py       # Thread-safe data loader
│           │   ├── logger.py       # Logging setup
│           │   └── registry.py     # Component registration
│           ├── data/               # Data models and constants
│           │   ├── models.py       # Pokemon, Move, Ability, Item models
│           │   ├── constants.py    # Game constants
│           │   └── pokemon.py      # Pokemon utilities
│           ├── formatters/         # Output formatters
│           │   ├── markdown_formatter.py  # Markdown generation
│           │   ├── table_formatter.py     # Table creation
│           │   └── yaml_formatter.py      # MkDocs YAML manipulation
│           ├── services/           # Business logic
│           │   ├── attribute_service.py    # Attribute processing
│           │   ├── evolution_service.py    # Evolution chains
│           │   ├── move_service.py         # Move data enrichment
│           │   ├── pokemon_item_service.py # Pokémon-item relationships
│           │   └── pokemon_move_service.py # Learnset processing
│           └── text/               # Text utilities
│               ├── text_util.py    # String formatting
│               └── dict_util.py    # Dictionary helpers
├── logs/                           # Application logs
├── pyproject.toml                  # Modern packaging configuration (PEP 621)
└── mkdocs.yml                      # MkDocs configuration
```

## Architecture

### Data Flow

**Data Initialization:**
```
External PokeDB Repository → Download → data/pokedb/parsed/
```

**Documentation Processing:**
```
data/documentation/*.txt → Parsers → docs/changes/*.md + docs/reference/*.md
```

**Reference Generation:**
```
data/pokedb/parsed/*.json → Generators → docs/pokedex/* + docs/locations/*
```

**Site Building:**
```
docs/**/*.md → MkDocs → Static HTML Site
```

### Design Patterns

- **Registry Pattern** - Dynamic component loading and discovery
- **Factory Pattern** - Parser/Generator instantiation
- **Template Method** - Base classes with customizable hooks
- **Singleton Pattern** - PokeDBLoader with class-level caching
- **Strategy Pattern** - Different parsers for different formats

### Key Components

#### 1. Parsers (`src/bbvw2_wiki/parsers/`)

Convert text documentation files to markdown pages.

**Base Classes:**

- `BaseParser` - Abstract base for all parsers
- `LocationParser` - Base class for parsers that generate location data

**Input:** `data/documentation/*.txt`
**Output:** `docs/changes/*.md` and `docs/reference/*.md`

#### 2. Generators (`src/bbvw2_wiki/generators/`)

Generate comprehensive reference pages from PokeDB data.

**Base Class:** `BaseGenerator`

**Input:** `data/pokedb/parsed/*/*.json`
**Output:** `docs/pokedex/*` and `docs/locations/*`

#### 3. Data Loader (`src/bbvw2_wiki/utils/core/loader.py`)

Thread-safe JSON data loader with:

- LRU caching (configurable, default 9,999 entries)
- Read-write locks for concurrent access
- Cache statistics tracking
- Automatic eviction

#### 4. Configuration (`src/bbvw2_wiki/utils/core/config.py`)

Centralized configuration for:

- PokeDB settings (repository, branch, generations)
- Logging configuration
- Component registries
- Version group settings

## Configuration

### PokeDB Settings

Located in `src/bbvw2_wiki/utils/core/config.py`:

```python
# PokeDB Repository
POKEDB_REPO = "https://github.com/zhenga8533/pokedb"
POKEDB_BRANCH = "data"

# Generation Configuration
POKEDB_GENERATIONS = ["gen5", "gen8"]

# Version Groups
VERSION_GROUPS = ["black_white", "black_2_white_2"]
GAME_VERSIONS = ["black", "white", "black_2", "white_2"]
```

### Logging Configuration

Configurable logging with:

- Level: DEBUG
- Max file size: 10 MB
- Backup count: 5 files
- Console colors enabled
- Format: text or JSON

## Dependencies

All dependencies are managed in `pyproject.toml`:

### Core Technologies

- **Python 3.12+** - Required (uses modern type hints and features)
- **MkDocs** - Static site generator
- **MkDocs Material** - Material Design theme

### Python Packages

- **mkdocs** - Documentation generator
- **mkdocs-material** - Material Design theme
- **mkdocs-git-authors-plugin** - Author tracking
- **mkdocs-git-committers-plugin** - Committer tracking
- **dacite** - Dataclass deserialization
- **orjson** - Fast JSON parsing
- **requests** - HTTP client

Install all dependencies with: `pip install -e .`

## ROM Hack Features Documented

### Complete Version

- All 649 Gen V Pokémon catchable
- Fairy type implementation
- Gen VI+ moves and abilities
- Revamped trainer battles
- 3 difficulty modes (Easy, Normal, Challenge)
- No trade evolutions (Link Cable item)
- Increased shiny rate (1/512)
- Revamped level curve
- 2-3 hours postgame content
- Custom Pokémon buffs (e.g., Serperior as Grass/Dragon)

### Classic Version

- Same as Complete but without custom buffs
- Pokémon only updated to Gen VIII appearances

## Development

### Adding a New Parser

1. Create a new parser class extending `BaseParser` or `LocationParser`:

```python
# src/bbvw2_wiki/parsers/my_parser.py
from .base_parser import BaseParser

class MyParser(BaseParser):
    def parse(self) -> None:
        # Implementation
        pass
```

2. Import and export in `src/bbvw2_wiki/parsers/__init__.py`:

```python
from .my_parser import MyParser

__all__ = [
    # ... existing parsers
    "MyParser",
]
```

3. Register in `src/bbvw2_wiki/utils/core/config.py`:

```python
PARSER_REGISTRY = {
    # ... existing parsers
    "my_parser": ParserConfig(
        name="my_parser",
        class_name="MyParser",
        description="Description of what it does",
        input_file=Path("data/documentation/My File.txt"),
        output_dir=Path("docs/changes"),
    ),
}
```

### Adding a New Generator

Follow similar steps as adding a parser, but extend `BaseGenerator` and register in `GENERATOR_REGISTRY`.

### Code Quality Features

- **Type Safety** - Extensive use of type hints and dataclasses
- **Thread Safety** - Read-write locks and concurrent operation protection
- **Error Handling** - Comprehensive exception handling and logging
- **Performance** - LRU caching, orjson, parallel file operations
- **Extensibility** - Easy to add new parsers and generators

## Troubleshooting

### Cache Issues

If you encounter stale data, clear the cache:

```python
from bbvw2_wiki.utils.core.loader import PokeDBLoader
PokeDBLoader.clear_cache()
```

### Build Errors

1. Ensure data is initialized: `python -m bbvw2_wiki --init`
2. Check logs in the `logs/` directory
3. Verify all parsers and generators have run successfully

### Missing Data

- Verify input files exist in `data/documentation/`
- Check that PokeDB data downloaded correctly to `data/pokedb/`
- Review log files for errors during parsing/generation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all parsers and generators run successfully
5. Submit a pull request

## License

This project is for documentation purposes for the Blaze Black 2 & Volt White 2 Redux ROM hack.

## Credits

- **ROM Hack:** Blaze Black 2 & Volt White 2 Redux by Drayano
- **PokeDB:** External Pokémon database repository
- **Documentation Generator:** This project

## Links

- **GitHub Repository:** [https://github.com/zhenga8533/bbvw2-redux-wiki](https://github.com/zhenga8533/bbvw2-redux-wiki)
- **Live Wiki:** [https://zhenga8533.github.io/bbvw2-redux-wiki/](https://zhenga8533.github.io/bbvw2-redux-wiki/)
- **PokeDB:** [https://github.com/zhenga8533/pokedb](https://github.com/zhenga8533/pokedb)
