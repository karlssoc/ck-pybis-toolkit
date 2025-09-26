# PyBIS Toolkit Quick Reference v1.0.3

## 🚀 Installation
```bash
# Install with pipx (recommended - requires Python 3.8+)
pipx install .

# Alternative: Install pipx first if needed
pip install pipx
pipx install .

# Legacy installation script (still available)
./install.sh
```

## ⚙️ Configuration

### 🆕 JSON Configuration (Recommended - oBIS-inspired)
```bash
# Initialize with example template
pybis config init -g --init-example

# Edit JSON configuration
nano ~/.pybis/config.json

# Set values via command line
pybis config set -g openbis_url "https://your-server.com/openbis/"
pybis config set -g openbis_username "username"
pybis config set -g openbis_password "password"

# View current configuration
pybis config list -g

# Set nested values with dot notation
pybis config set search.default_limit 20
pybis config set default_collections.fasta "/DDB/CK/CUSTOM_FASTA"
```

**Configuration Priority:**
1. Environment variables (highest)
2. Local project: `./.pybis/config.json`
3. Global: `~/.pybis/config.json`
4. Legacy: `~/.openbis/credentials` (fallback)

### 📁 Legacy Configuration (Still Supported)
```bash
# Edit credentials file
nano ~/.openbis/credentials

# Format:
OPENBIS_URL="https://your-server.com/openbis/"
OPENBIS_USERNAME="username"
OPENBIS_PASSWORD="password"
PYBIS_DOWNLOAD_DIR="~/Downloads/openbis-data"
PYBIS_VERIFY_CERTIFICATES="false"
```

## 📋 Core Commands

### Connection & Basic Search
```bash
pybis connect --verbose                           # Test connection
pybis search proteome --type datasets --limit 10 # Basic search
pybis info --spaces                               # List spaces
pybis info --dataset DATASET_ID                  # Dataset details
```

### 🔍 Advanced Search (oBIS-style)
```bash
# Property-based filtering
pybis search --space DDB --dataset-type BIO_DB --save results.csv
pybis search --property version --property-value "2024.08"
pybis search --collection "/DDB/CK/FASTA" --registration-date ">2024-01-01"

# Relationship queries (🚀 OPTIMIZED with caching)
pybis search --children-of 20250502110701494-1323378 --save children.csv
pybis search --parents-of 20250502110516300-1323376 --save parents.csv
```

### Upload with Smart Features
```bash
# Auto-detection with intelligent parent linking
pybis upload library.tsv --log-file diann.log --auto-link
pybis upload database.fasta --version "2024.08" --auto-link

# Manual parent relationships
pybis upload processed.fasta --parent-dataset 20250502110701494-1323378

# Preview before uploading
pybis upload file.fasta --version "1.0" --dry-run

# Traditional specific uploads
pybis upload-fasta database.fasta --version "2024.08"
pybis upload-lib library.tsv --log-file diann.log
```

### Download
```bash
pybis download DATASET_ID --output ~/data/       # Download dataset
pybis download DATASET_ID --list-only            # List files only
```

## 🔍 File Type Auto-Detection

| Extension | Type | Default Collection | Auto-Link Support |
|---|---|---|---|
| `.fasta`, `.fa`, `.fas` | FASTA Database | `/DDB/CK/FASTA` | ✅ Version-based |
| `.tsv`, `.csv` (with "lib") | Spectral Library | `/DDB/CK/PREDSPECLIB` | ✅ DIA-NN log parsing |
| `.speclib`, `.sptxt` | Spectral Library | `/DDB/CK/PREDSPECLIB` | ✅ Metadata-based |
| Other | Unknown | `/DDB/CK/UNKNOWN` | ❌ Manual only |

## 🚀 Performance Features (v1.0.2)

### Intelligent Caching
```bash
# First query - fetches from server
pybis search --children-of DATASET_ID
# Results: Found 5 children in 2.34s

# Subsequent queries - cached response  
pybis search --children-of DATASET_ID
# Results: Using cached result (5 children) in 0.02s
```

### Batch Processing
- **~80% fewer API calls** for parent suggestions
- **Sub-second cached responses** for relationships
- **Performance timing** displayed automatically
- **Graceful fallback** if optimized methods fail

## 🛠️ Configuration Management

### JSON Config Commands
```bash
# Initialize configurations
pybis config init -g --init-example              # Global with examples
pybis config init                                 # Local project

# View configurations
pybis config list -g                              # Global settings
pybis config list                                 # Local settings

# Get specific values
pybis config get -g openbis_url                   # Single value
pybis config get search.default_limit             # Nested value

# Set configurations
pybis config set -g pybis_download_dir "~/data/"  # Global setting
pybis config set auto_link_parents true           # Local setting

# Clear configurations
pybis config clear -g openbis_password             # Remove specific key
```

### Advanced JSON Settings
```bash
# Performance tuning
pybis config set -g pybis_use_cache true
pybis config set -g pybis_verify_certificates false

# Auto-linking preferences
pybis config set -g auto_link_parents false

# Default collections
pybis config set default_collections.fasta "/CUSTOM/FASTA"
pybis config set default_collections.spectral_library "/CUSTOM/LIBS"

# Search preferences
pybis config set search.default_limit 20
pybis config set search.save_format "csv"
```

## 🧬 Parent-Child Relationships

### Auto-Linking Workflow
```bash
# Upload with intelligent suggestions
pybis upload library.tsv --log-file diann.log --auto-link

# Interactive selection example:
# 🎯 [1] 20250502110701494-1323378
#     Name: UniProt Human Database v2024.08
#     Match: FASTA database reference: uniprot_human_20240801.fasta
#     Confidence: high
# 
# 🔍 [2] 20250502110516300-1323376
#     Name: Human Proteome v2024.07
#     Match: Similar naming pattern: human
#     Confidence: medium
#
# Select datasets to link as parents:
# 👉 Your choice: 1,2
```

### Manual Relationships
```bash
# Single parent
pybis upload database.fasta --version "1.0" --parent-dataset PARENT_ID

# Multiple parents
pybis upload results.tsv \
    --parent-dataset FASTA_ID \
    --parent-dataset LIBRARY_ID
```

## 📊 Advanced Search Examples

### Property Filtering
```bash
# Search by dataset properties
pybis search --property organism --property-value "homo sapiens"
pybis search --property version --property-value "2024.08"

# Date range filtering
pybis search --registration-date ">2024-01-01"
pybis search --registration-date "<2024-06-01"

# Hierarchical filtering
pybis search --space DDB --project CK --collection "/DDB/CK/FASTA"
```

### Export Results
```bash
# Save to CSV for analysis
pybis search --dataset-type BIO_DB --save fasta_databases.csv
pybis search --children-of PARENT_ID --save child_datasets.csv

# Combine filters and export
pybis search --space DDB \
    --dataset-type SPECTRAL_LIBRARY \
    --registration-date ">2024-01-01" \
    --save recent_libraries.csv
```

## 🐛 Troubleshooting

### Check Configuration
```bash
# Test JSON config
pybis config list -g
pybis connect --verbose

# Test legacy config
source ~/.openbis/credentials && echo $OPENBIS_URL

# Check PATH
echo $PATH | grep ~/.local/bin
```

### Performance Issues
```bash
# Clear relationship cache
rm -rf ~/.cache/pybis/  # (if implemented)

# Disable caching for testing
pybis config set -g pybis_use_cache false

# Check server connectivity
pybis connect --verbose
```

### Fix Common Issues
```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Reset configuration
pybis config clear -g openbis_password
pybis config init -g --init-example
```

## 💡 Pro Tips

### Performance
1. **Use caching**: Relationship queries are cached for 15 minutes
2. **Batch operations**: Multiple related queries use optimized batch processing
3. **Server-side filtering**: Use `--space`, `--project` etc. for faster searches

### Configuration
1. **JSON over legacy**: Use `pybis config` for better organization
2. **Project-specific**: Use local `.pybis/config.json` for per-project settings
3. **Environment override**: Set `OPENBIS_URL` etc. to override config files

### Auto-linking
1. **DIA-NN logs**: Always provide `--log-file` for spectral libraries
2. **Version patterns**: Use consistent naming for automatic version linking
3. **Preview first**: Use `--dry-run` to see suggested parents before upload

### Advanced Search
1. **Export results**: Use `--save` to analyze results in spreadsheets
2. **Combine filters**: Mix property, date, and hierarchy filters
3. **Relationship mapping**: Use parent/child queries to map data lineage

## 🔗 Help & Documentation

```bash
# Command help
pybis --help                    # General help
pybis config --help            # Configuration help
pybis search --help            # Search options
pybis upload --help            # Upload options

# Configuration examples
pybis config init -g --init-example  # See all available options
```

## 📈 What's New in v1.0.2

### 🚀 Performance Optimizations
- **15-minute intelligent caching** for relationship queries
- **~80% reduction** in API calls through batch processing
- **Sub-second responses** for cached relationship data
- **Performance monitoring** with query timing display

### 🔧 Enhanced Features  
- **JSON configuration system** inspired by oBIS
- **Advanced search filtering** with property and date filters
- **CSV export capabilities** for external analysis
- **Intelligent parent-child linking** with confidence scoring
- **Interactive dataset selection** with user-friendly prompts

### 🛡️ Reliability Improvements
- **Graceful fallback systems** if optimized methods fail
- **Multiple configuration methods** with priority hierarchy
- **Enhanced error handling** across all operations
- **Backward compatibility** with existing workflows