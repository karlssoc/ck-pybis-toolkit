# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CK PyBIS Toolkit 1.37.3 standalone development environment extracted from CKS Ansible container project. This is a Python-based OpenBIS client toolkit for debugging dataset download issues, developing new PyBIS functionality, and prototyping improvements.

## Key Commands

### Setup (CLI Installation)
```bash
# One-time installation - installs PyBIS CLI as pip package
./install.sh

# This creates:
# - pip package installation with console script entry point
# - ~/.local/bin/pybis symlink for easy access
# - ~/.openbis/credentials file (if not exists)
# - Automatic credential loading on every command
```

### CLI Usage (Recommended)
```bash
# Test connection to OpenBIS
pybis connect --verbose

# All commands now work from any directory with automatic credential loading
pybis download 20250807085639331-1331542 --output ~/data/
pybis download-collection /DDB/CK/FASTA --list-only
pybis search proteome --type datasets --limit 5
pybis upload-fasta database.fasta --version "2024.08"
pybis info --dataset 20250807085639331-1331542
```

### Legacy Development Mode
```bash
# Direct Python script execution (for development/debugging)
python pybis_scripts.py connect --verbose

# Run dataset download test suite (debug specific failing datasets)
python test_datasets.py

# Test individual dataset downloads
python pybis_scripts.py download 20250807085639331-1331542 --output ~/data/
python pybis_scripts.py download 20250807085639331-1331542 --list-only

# Download all datasets from a collection
python pybis_scripts.py download-collection /DDB/CK/FASTA --list-only
python pybis_scripts.py download-collection /DDB/CK/FASTA --output ~/data/ --limit 5

# Search and info commands
python pybis_scripts.py search proteome --type datasets --limit 5
python pybis_scripts.py info --dataset 20250807085639331-1331542

# Upload FASTA databases
python pybis_scripts.py upload-fasta database.fasta --version "2024.08.19"
python pybis_scripts.py upload-fasta database.fasta --name "Custom Database Name" --version "v1.0" --notes "Description" --dry-run
```

### Interactive Development
```bash
# Python REPL for API exploration
python
>>> from pybis_common import get_openbis_connection
>>> o = get_openbis_connection()
>>> dataset = o.get_dataset('20250502110701494-1323378')
```

## Architecture

### Core Modules

- **`pybis_common.py`** - Shared PyBIS functionality with connection management and all tool implementations
  - `get_openbis_connection()` - Handles authentication with token caching
  - `pybis_*_main()` functions - Individual tool implementations (connect, search, download, download-collection, info, upload-lib, upload-fasta)
  - `parse_fasta_metadata()` - Extracts metadata from FASTA files (entries, species, file size)
- **`pybis_scripts.py`** - Main CLI dispatcher with automatic credential loading
  - `load_credentials()` - Automatically loads `~/.openbis/credentials` at import time
  - Console script entry point for pip-installed CLI
- **`setup.py`** - Pip package configuration with console script entry points
- **`install.sh`** - One-command installation script
- **`test_datasets.py`** - Debugging script for testing specific dataset download issues

### Authentication Flow
**Automatic credential loading**: The CLI automatically loads credentials from `~/.openbis/credentials` on every command execution. No manual environment setup required. Uses PyBIS built-in token caching for session persistence across commands - login once, reuse token automatically.

### CLI Installation Architecture
- **Pip package**: Installed as `pybis-cli-local` with console script entry point
- **Symlink**: `~/.local/bin/pybis` → conda environment pybis command
- **Automatic credentials**: Loaded from `~/.openbis/credentials` on every execution
- **Cross-directory usage**: Works from any directory without PATH issues

### Known Issues
- Working dataset: `20250807085639331-1331542`
- Failing dataset: `20250502110701494-1323378`
- Focus area: Dataset download functionality debugging

## Download Tools

### Collection Download (`download-collection`)

Download all datasets from an OpenBIS collection sequentially with progress tracking.

**Usage:**
```bash
python pybis_scripts.py download-collection <collection_path> [options]
```

**Features:**
- **Sequential downloads**: Downloads datasets one by one to avoid overwhelming OpenBIS server
- **Progress tracking**: Shows [1/5], [2/5], etc. with success/failure counts
- **Token reuse**: Uses cached authentication tokens like all other commands
- **Error handling**: Continues if individual datasets fail, reports final summary
- **Same logic**: Each dataset uses identical download process as single dataset downloads

**Arguments:**
- `collection_path` - OpenBIS collection path (required, no default for safety)
- `--output` - Output directory (default: `{{ data_base_dir }}/openbis/`)
- `--list-only` - Only list datasets, do not download
- `--limit` - Maximum number of datasets to download

**Examples:**
```bash
# List datasets in FASTA collection
python pybis_scripts.py download-collection /DDB/CK/FASTA --list-only

# Download first 5 datasets from FASTA collection
python pybis_scripts.py download-collection /DDB/CK/FASTA --limit 5 --output ~/data/

# Download all datasets from spectral library collection  
python pybis_scripts.py download-collection /DDB/CK/PREDSPECLIB --output ~/downloads/

# Handle collection codes (not dataset codes)
python pybis_scripts.py download-collection 20250502110701494-1323378 --list-only
```

**Process Flow:**
1. Get collection object from OpenBIS
2. Retrieve all datasets in collection  
3. Download each dataset sequentially using existing download logic
4. Track and report success/failure summary

## Upload Tools

### FASTA Database Upload (`upload-fasta`)

Upload protein FASTA database files to OpenBIS with automatic metadata extraction.

**Usage:**
```bash
python pybis_scripts.py upload-fasta <fasta_file> [options]
```

**Features:**
- **Automatic metadata extraction**: Parses FASTA headers to extract species information and count entries
- **Dataset type**: BIO_DB with properties: `$name`, `version`, `product.description`
- **Default collection**: `/DDB/CK/FASTA`
- **Species parsing**: Supports UniProt (OS=), NCBI ([]), and parentheses formats
- **Auto-generated names**: Uses filename + version + primary species

**Arguments:**
- `--name` - Custom human-readable name (default: filename stem)
- `--version` - Version/release identifier (recommended)
- `--notes` - Additional description (stored in user notes, not OpenBIS properties)
- `--collection` - OpenBIS collection path (default: `/DDB/CK/FASTA`)
- `--dataset-type` - Dataset type (default: `BIO_DB`)
- `--dry-run` - Preview upload without actually uploading

**Examples:**
```bash
# Basic upload with auto-generated name
python pybis_scripts.py upload-fasta uniprot_human.fasta --version "2024.08"

# Custom name and description
python pybis_scripts.py upload-fasta database.fasta \
    --name "Human Proteome" \
    --version "2024.08.19" \
    --notes "Complete human protein database"

# Preview before uploading
python pybis_scripts.py upload-fasta database.fasta --version "1.0" --dry-run
```

**Metadata Extracted:**
- `N_ENTRIES` - Number of protein sequences
- `PRIMARY_SPECIES` - Most common species (e.g., "Homo sapiens")
- `SPECIES_COUNT` - Number of different species
- `SPECIES_BREAKDOWN` - Top 5 species with percentages
- `FILE_SIZE_MB` - File size in megabytes
- `VERSION` - User-provided version

**OpenBIS Properties Set:**
- `$name` - Auto-generated: "filename v{version} ({primary_species})"
- `version` - Version identifier
- `product.description` - Comprehensive summary: "X entries | Primary species: Y | Z species | A.B MB"

### Spectral Library Upload (`upload-lib`)

Upload spectral library files with DIA-NN log metadata extraction.

**Usage:**
```bash
python pybis_scripts.py upload-lib <library_file> [options]
```

**Features:**
- **Dataset type**: SPECTRAL_LIBRARY with DIA-NN log metadata extraction
- **Default collection**: Configurable
- **Log file parsing**: Extracts comprehensive metadata from DIA-NN log files

**Metadata Extracted from DIA-NN logs:**
- `N_PROTEINS` - Number of proteins in library
- `N_PRECURSORS` - Number of precursor ions
- `N_GENES` - Number of unique genes
- `DIANN_VERSION` - DIA-NN software version
- `FASTA_DATABASE` - Source protein database file
- `GENERATION_DATE` - Library creation timestamp
- `GENERATION_METHOD` - In silico generation methods used
- `MODIFICATIONS` - Post-translational modifications enabled
- `MIN/MAX_PEPTIDE_LENGTH` - Peptide length constraints
- `THREADS_USED` - Computational threads utilized

**OpenBIS Properties Set (SPECTRAL_LIBRARY):**
- `notes` - Human-readable name (SPECTRAL_LIBRARY doesn't support $name property)
- `n_proteins` - Number of proteins
- `n_peptides` - Number of precursors/peptides

## Dataset Type Metadata Summary

The upload system extracts and stores different metadata based on dataset type:

### BIO_DB (FASTA databases)
**Available OpenBIS Properties:** `$name`, `version`, `product.description`, `location_status`, `irt_protein`, `contaminants`, `decoy_type`

**Metadata Used:**
- `$name` - Generated from filename, version, and primary species
- `version` - User-provided version identifier  
- `product.description` - Comprehensive summary with entries count, primary species, species count, file size
- **Notes not supported** - BIO_DB dataset type doesn't allow notes property

**Example `product.description`:** "6065 entries | Primary species: Saccharomyces cerevisiae | 1 species | 3.68 MB"

### SPECTRAL_LIBRARY (DIA-NN libraries)
**Available OpenBIS Properties:** Include `notes`, `n_proteins`, `n_peptides`, others vary

**Metadata Used:**
- `notes` - Human-readable name (since $name not supported)
- `n_proteins` - Protein count from DIA-NN log
- `n_peptides` - Precursor count from DIA-NN log
- **Comprehensive notes** - Additional DIA-NN metadata stored in notes field

### Property Mapping Architecture
The `PROPERTY_MAPPINGS` registry in `pybis_common.py` defines how metadata fields map to OpenBIS properties for each dataset type. This allows dataset-specific handling of metadata extraction and property assignment.

## Development Workflow

This is a development/debugging environment separate from production container deployment. Changes should be tested here first, then ported back to Ansible templates in the main CKS project (`/Users/medk-cka/cks-ansible`).

## Maintenance Memories

- Update CLI (install.sh) when functionality is changed or added

## Documentation Resources

- Documentation for pybis can be found here https://openbis.readthedocs.io/en/20.10.x/software-developer-documentation/apis/python-v3-api.html