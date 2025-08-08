# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CK PyBIS Toolkit v1.0.2 standalone development environment with oBIS-inspired enhancements. This is a Python-based OpenBIS client toolkit for debugging dataset download issues, developing new PyBIS functionality, and prototyping improvements. Built on PyBIS 1.37.3.

**Enhanced Features:**
- Advanced search with oBIS-style filtering and CSV export
- JSON-based configuration system (global + project-specific)
- Intelligent parent-child dataset relationship management with auto-linking
- Interactive dataset suggestions based on metadata analysis
- **NEW v1.0.2**: High-performance relationship queries with 15-minute caching
- **NEW v1.0.2**: Batch query optimization reduces API calls by ~80%
- **NEW v1.0.2**: Sub-second cached responses for dataset relationships

## Project Versioning and Tags

- Project Version: v1.0.2  
- PyBIS Library Version: 1.37.3
- Release Tags: `v1.0.0`, `v1.0.1`, `v1.0.2`

## Configuration System

### JSON Configuration (oBIS-Inspired)
The toolkit now supports JSON-based configuration with priority hierarchy:
1. Environment variables (highest priority)
2. Local project config: `./.pybis/config.json`
3. Global config: `~/.pybis/config.json`
4. Legacy credentials: `~/.openbis/credentials` (backward compatibility)

```bash
# Initialize global configuration
pybis config init -g --init-example

# Set configuration values with dot notation
pybis config set -g openbis_url "https://your-server.com/openbis/"
pybis config set search.default_limit 20
pybis config set default_collections.fasta "/DDB/CK/CUSTOM_FASTA"
```

### Legacy Credentials (Backward Compatible)
The CLI **still supports** the original credentials file `~/.openbis/credentials`:

- `OPENBIS_URL` - Server URL (required)
- `OPENBIS_USERNAME` - Username (required) 
- `OPENBIS_PASSWORD` - Password (required)
- `PYBIS_DOWNLOAD_DIR` - Default download directory (optional)
- `PYBIS_VERIFY_CERTIFICATES` - SSL certificate verification (optional, defaults to false)

### Configurable Options via JSON or Environment:
```bash
# Download directory
pybis config set -g pybis_download_dir "~/Downloads/openbis-data"

# SSL certificate verification (useful for production servers)
pybis config set -g pybis_verify_certificates true

# PyBIS caching (performance tuning)
pybis config set -g pybis_use_cache true
```

Uses PyBIS built-in token caching for session persistence - login once, reuse token automatically.

## PyBIS Documentation

https://openbis.readthedocs.io/en/20.10.x/software-developer-documentation/apis/python-v3-api.html

## Development Guidelines

When adding or changing PyBIS functionality:

1. **Always consult the PyBIS documentation first** - Review the official API documentation above to understand available methods, parameters, and best practices.

2. **Follow existing patterns** - Look at current implementations in `pybis_common.py` for:
   - Connection management (`get_openbis_connection()`)
   - Error handling patterns
   - Token caching usage
   - Dataset/sample/experiment operations

3. **Test thoroughly** - Use the test datasets mentioned in this file:
   - Working dataset: `20250807085639331-1331542`

4. **Update documentation** - Always update both `CLAUDE.md` and `README.md` with:
   - New functionality descriptions
   - Usage examples
   - Any new environment variables or configuration options

5. **Version management** - When adding significant functionality:
   - Update version in `setup.py`
   - Update version references in `CLAUDE.md` and `README.md`
   - Follow semantic versioning (major.minor.patch)

## Enhanced Parent-Child Relationships (oBIS-Inspired)

**Implemented Feature:** Intelligent parent dataset detection and linking

### Auto-linking Usage:
```bash
# Automatic parent suggestions for spectral libraries
pybis upload library.tsv --log-file diann.log --auto-link

# Manual parent specification (still supported)
pybis upload library.tsv --parent-dataset 20250502110701494-1323378

# Works with all upload commands
pybis upload-fasta processed.fasta --auto-link
```

### Interactive Workflow:
1. Parse metadata (DIA-NN logs, FASTA filenames, version patterns)
2. Search OpenBIS for matching datasets by properties/names
3. Present ranked suggestions with confidence levels:
   ```
   🎯 [1] 20250502110701494-1323378
       Name: UniProt Human Database v2024.08
       Match: FASTA database reference: uniprot_human_20240801.fasta
       Confidence: high
   ```
4. Interactive selection: `1,3,5` or `1-3` or `all`
5. Auto-link confirmed datasets

### Advanced Search & Export:
```bash
# oBIS-style filtering with CSV export
pybis search --space DDB --dataset-type BIO_DB --save results.csv
pybis search --property version --property-value "2024.08" --registration-date ">2024-01-01"

# Relationship queries with export
pybis search --children-of 20250502110701494-1323378 --save children.csv
```

**Benefits:**
- ✅ Implemented intelligent parent dataset suggestions
- ✅ Interactive confirmation with confidence scoring  
- ✅ Advanced search with oBIS-style filtering
- ✅ CSV export for external analysis
- ✅ Backward compatible with manual linking
- ✅ **NEW v1.0.2**: High-performance relationship queries with intelligent caching
- ✅ **NEW v1.0.2**: Batch processing optimizations for faster parent suggestions
- ✅ **NEW v1.0.2**: Performance monitoring and fallback systems

## Parent-Child Dataset Relationships

**Current Implementation:** Manual parent dataset linking with relationship queries

**Upload with Parent Relationships:**
```bash
# Single parent dataset
pybis upload database.fasta --version "1.0" --parent-dataset 20250502110701494-1323378

# Multiple parents (e.g., DIA-NN search results linking to FASTA + library)
pybis upload-fasta processed.fasta \
    --parent-dataset 20250502110701494-1323378 \
    --parent-dataset 20250502110516300-1323376

# Works with all upload commands
pybis upload-lib library.tsv --log-file diann.log --parent-dataset 20250502110701494-1323378

# Preview relationships before upload
pybis upload database.fasta --version "1.0" --parent-dataset 20250502110701494-1323378 --dry-run
```

**Query Relationships:**
```bash
# Show dataset with full lineage tree
pybis info --dataset 20250502110516300-1323376 --show-lineage

# Find all children of a dataset
pybis search --children-of 20250502110701494-1323378

# Find all parents of a dataset  
pybis search --parents-of 20250502110516300-1323376
```

**Common Use Cases:**
- Spectral library → FASTA database: `pybis upload-lib library.tsv --parent-dataset <fasta_dataset_id>`
- DIA-NN search results → Multiple parents: `pybis upload results.tsv --parent-dataset <fasta_id> --parent-dataset <library_id>`
- Processed data → Raw data: Track data processing lineage through OpenBIS

