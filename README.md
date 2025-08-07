# PyBIS CLI Tool

A command-line interface for OpenBIS operations with enhanced upload functionality, metadata extraction, and automatic file type detection.

**Standalone PyBIS development environment extracted from the CKS Ansible container project.** This environment allows for faster iteration, debugging, and testing of PyBIS scripts without container overhead.

## 🚀 Quick Start

### Installation

```bash
# Navigate to the project directory
cd /Users/medk-cka/Documents/Projects/pybis-1.37.3

# Run the installer
./install.sh
```

The installer will:
- Install the `pybis` command to `~/.local/bin/`
- Use your existing `pybis-1.37.3` conda environment
- Set up credential loading from `~/.openbis/credentials`
- Check PATH configuration and provide guidance if needed

### Configuration

Edit your OpenBIS credentials file:
```bash
nano ~/.openbis/credentials
```

Required format:
```bash
OPENBIS_URL="https://your-openbis-server.com/openbis/"
OPENBIS_USERNAME="your-username"
OPENBIS_PASSWORD="your-password"
OPENBIS_WORKSPACE="/openbis"
```

## 📋 Commands

### Connection & Info

```bash
# Test connection
pybis connect --verbose

# Search for datasets, samples, experiments
pybis search proteome --type datasets --limit 10
pybis search "mouse liver" --type samples
pybis search experiment1 --type experiments

# Get detailed information
pybis info --spaces
pybis info --dataset 20250807085639331-1331542
pybis info --sample SAMPLE001
```

### Download

```bash
# Download datasets
pybis download 20250807085639331-1331542 --output ~/data/
pybis download 20250807085639331-1331542 --list-only

# Custom output directory
pybis download DATASET_CODE --output /path/to/output/
```

### Upload (New Enhanced Functionality)

#### Unified Upload (Auto-Detection)
```bash
# Auto-detects file type and sets appropriate defaults
pybis upload database.fasta --version "2024.08"
pybis upload library.tsv --log-file diann.log
pybis upload unknown_file.txt --collection "/DDB/CK/MISC"

# Preview before uploading
pybis upload database.fasta --version "2024.08" --dry-run
```

#### FASTA Database Upload
```bash
# Basic FASTA upload
pybis upload-fasta database.fasta --version "2024.08.19"

# Custom name and description
pybis upload-fasta uniprot_human.fasta \
    --name "Human Proteome Database" \
    --version "2024.08" \
    --notes "Complete human protein sequences from UniProt"

# Custom collection
pybis upload-fasta database.fasta \
    --collection "/DDB/CK/CUSTOM_FASTA" \
    --version "1.0"

# Preview before upload
pybis upload-fasta database.fasta --version "1.0" --dry-run
```

#### Spectral Library Upload
```bash
# Upload library with DIA-NN log
pybis upload-lib library.tsv --log-file diann.log

# Custom collection and name
pybis upload-lib predicted_library.tsv \
    --collection "/DDB/CK/CUSTOM_LIBS" \
    --name "Mouse Liver Predicted Library" \
    --log-file diann_generation.log

# Preview before upload
pybis upload-lib library.tsv --log-file diann.log --dry-run
```

## 🔍 File Type Detection

The unified `upload` command automatically detects file types:

| File Extension | Detected Type | Default Collection | Default Dataset Type |
|---|---|---|---|
| `.fasta`, `.fa`, `.fas` | FASTA Database | `/DDB/CK/FASTA` | `BIO_DB` |
| `.tsv`, `.csv` (with "lib") | Spectral Library | `/DDB/CK/PREDSPECLIB` | `SPECTRAL_LIBRARY` |
| `.speclib`, `.sptxt` | Spectral Library | `/DDB/CK/PREDSPECLIB` | `SPECTRAL_LIBRARY` |
| Other | Unknown | `/DDB/CK/UNKNOWN` | `UNKNOWN` |

## 📊 Metadata Extraction

### FASTA Files
Automatically extracts:
- **Number of entries** (protein sequences)
- **Primary species** (most common organism)
- **Species breakdown** (top 5 species with percentages)
- **File size** in MB
- **Version** information

Supports organism formats:
- UniProt: `OS=Homo sapiens`
- NCBI: `[Homo sapiens]`
- Generic: `(Homo sapiens)`

### Spectral Libraries (DIA-NN)
Extracts from log files:
- **DIA-NN version** and compilation info
- **Generation statistics** (precursors, proteins, genes)
- **FASTA database** used
- **Parameters** (peptide length, m/z ranges, modifications)
- **Generation method** (deep learning, in silico, etc.)
- **Processing details** (threads, system info)

## 🏗️ Architecture

### Modular Upload System
- **`OpenBISUploader`**: Base class with common functionality
- **`FASTAUploader`**: Specialized for FASTA database files
- **`SpectralLibraryUploader`**: Specialized for spectral library files
- **Property mapping registry**: Handles dataset type-specific properties
- **File type detection**: Automatic format recognition

### Benefits
- **50% code reduction** from original implementation
- **Consistent error handling** across all upload types
- **Extensible design** for adding new file types
- **Backward compatibility** with existing commands

## Original Purpose

- **Debug PyBIS download issues** (e.g., working vs failing dataset IDs)
- **Develop new PyBIS functionality** in a clean environment
- **Test OpenBIS integrations** with direct Python access
- **Prototype improvements** before porting back to container deployment

## Files

### Core Files
- `pybis_common.py` - Shared PyBIS functionality (copied from Ansible templates)
- `pybis_scripts.py` - Main CLI interface for all PyBIS tools
- `test_datasets.py` - Test script for debugging download issues

### Configuration
- `credentials.example` - OpenBIS credentials template (copied from ~/.openbis/credentials)

## Setup

### 1. Environment Setup
```bash
# Ensure PyBIS 1.37.3 is available in your conda environment
conda activate your-pybis-env
pip install pybis==1.37.3
```

### 2. Credentials Configuration
```bash
# Copy and configure credentials
cp credentials.example ~/.openbis/credentials
# Edit ~/.openbis/credentials with your OpenBIS connection details
```

The credentials file should contain:
```
OPENBIS_URL=https://your-openbis-server.com
OPENBIS_USERNAME=your_username
OPENBIS_PASSWORD=your_password
```

### 3. Test Setup
```bash
# Test connection
pybis connect --verbose

# List available spaces
pybis info --spaces

# Test upload with dry-run
pybis upload test.fasta --dry-run
```

## 🔧 Advanced Usage

### Custom Collections and Dataset Types
```bash
# Override defaults
pybis upload database.fasta \
    --collection "/CUSTOM/PROJECT/EXPERIMENT" \
    --dataset-type "CUSTOM_DB" \
    --version "1.0"

# Force file type
pybis upload ambiguous_file.txt \
    --type fasta \
    --version "1.0"
```

### Batch Operations
```bash
# Upload multiple files
for file in *.fasta; do
    pybis upload "$file" --version "2024.08" --dry-run
done

# Search and download
pybis search "mouse" --type datasets --limit 5 | \
    grep -o "DATASET_[0-9-]*" | \
    while read dataset; do
        pybis download "$dataset" --output ~/downloads/
    done
```

## 🛠️ Development

### Project Structure
```
pybis-1.37.3/
├── pybis_common.py      # Core functionality and upload classes
├── pybis_scripts.py     # CLI command dispatcher
├── pybis                # Python wrapper script
├── install.sh           # Installation script
├── test_datasets.py     # Testing utilities
└── ~/.openbis/
    └── credentials      # OpenBIS connection details
```

### Adding New File Types

1. **Create uploader class**:
```python
class MyFileUploader(OpenBISUploader):
    def parse_metadata(self, file_path, **kwargs):
        # Extract metadata from your file type
        return {'KEY': 'value'}
    
    def generate_name(self, file_path, metadata, custom_name):
        # Generate human-readable names
        return custom_name or f"My File {file_path.stem}"
```

2. **Update file type detection**:
```python
def detect_file_type(file_path):
    if suffix == '.myext':
        return 'my_file_type'
```

3. **Add to factory**:
```python
uploaders = {
    'my_file_type': MyFileUploader,
}
```

## 🐛 Troubleshooting

### Common Issues

**Credentials not loaded**:
```bash
# Check if file exists and has correct format
cat ~/.openbis/credentials

# Test manual sourcing
source ~/.openbis/credentials && echo $OPENBIS_URL
```

**Command not found**:
```bash
# Check if ~/.local/bin is in PATH
echo $PATH | grep ~/.local/bin

# Add to PATH if missing
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Conda environment issues**:
```bash
# Check if environment exists
conda env list | grep pybis-1.37.3

# Recreate if needed
conda create -n pybis-1.37.3 python=3.9
conda activate pybis-1.37.3
pip install pybis==1.37.3
```

**Connection timeouts**:
- Check VPN connection
- Verify OpenBIS server URL
- Test network connectivity: `ping bioms.med.lu.se`

## 📚 Examples

### Typical Workflow
```bash
# 1. Test connection
pybis connect --verbose

# 2. Search for existing data
pybis search "mouse liver" --type datasets --limit 5

# 3. Upload new database
pybis upload uniprot_mouse.fasta \
    --version "2024.08" \
    --notes "Mouse proteome for liver analysis"

# 4. Upload spectral library
pybis upload predicted_library.tsv \
    --log-file diann_generation.log \
    --name "Mouse Liver DIA Library"

# 5. Download for analysis
pybis download 20250807085639331-1331542 --output ~/analysis/
```

### Integration with Scripts
```bash
#!/bin/bash
# Batch upload script

VERSION="2024.08"
NOTES="Batch upload from analysis pipeline"

for fasta in data/*.fasta; do
    echo "Uploading $fasta..."
    pybis upload "$fasta" \
        --version "$VERSION" \
        --notes "$NOTES" || {
        echo "Failed to upload $fasta"
        exit 1
    }
done

echo "All uploads completed successfully!"
```

## 🔄 Migration from Old Scripts

The new CLI maintains backward compatibility:

```bash
# Old way (still works)
python pybis_scripts.py upload-fasta database.fasta --version "1.0"

# New way (preferred)
pybis upload database.fasta --version "1.0"
```

## 📈 Performance

- **50% less code** than original implementation
- **Consistent error handling** across all operations  
- **Automatic metadata extraction** saves manual data entry
- **Dry-run mode** prevents upload mistakes
- **Conda environment isolation** ensures dependency consistency

## Original Development Notes
```

## Usage Examples

### Basic Tools
```bash
# Test connection
python pybis_scripts.py connect --verbose

# Search for datasets
python pybis_scripts.py search proteome --type datasets --limit 5

# Get dataset information
python pybis_scripts.py info --dataset 20250807085639331-1331542

# Download dataset
python pybis_scripts.py download 20250807085639331-1331542 --output ~/data/

# List dataset files without downloading
python pybis_scripts.py download 20250807085639331-1331542 --list-only
```

### Debug Dataset Download Issues
```bash
# Run comprehensive test of both working and failing datasets
python test_datasets.py
```

This will test:
- `20250807085639331-1331542` (working dataset)
- `20250502110701494-1323378` (failing dataset)

### Spectral Library Upload
```bash
# Upload library with metadata extraction
python pybis_scripts.py upload-lib library.speclib --log-file library.log.txt

# Preview metadata without uploading
python pybis_scripts.py upload-lib library.speclib --log-file library.log.txt --dry-run

# Upload with custom name
python pybis_scripts.py upload-lib library.speclib \
    --name "Yeast Comprehensive Library v2025" \
    --notes "Enhanced library with modifications"
```

## Debugging Workflow

### 1. Issue Reproduction
```bash
# Test both datasets to confirm the issue
python test_datasets.py
```

### 2. Detailed Investigation
```bash
# Get detailed dataset info
python pybis_scripts.py info --dataset 20250502110701494-1323378

# Try listing files
python pybis_scripts.py download 20250502110701494-1323378 --list-only
```

### 3. PyBIS API Exploration
```bash
# Start interactive Python session
python
>>> from pybis_common import get_openbis_connection
>>> o = get_openbis_connection()
>>> dataset = o.get_dataset('20250502110701494-1323378')
>>> # Investigate dataset object properties
>>> dir(dataset)
>>> dataset.props
>>> dataset.type
```

## Development Benefits

- **No container rebuild** for script changes
- **Full IDE support** with breakpoints and debugging
- **Direct library access** for API exploration
- **Fast iteration** for testing fixes
- **Clean environment** separate from production deployment

## Porting Back to Ansible

Once you've developed and tested improvements:

1. **Update the Ansible templates** in the main project:
   - `templates/pybis_common.py.j2`
   - `templates/container-script.py.j2`

2. **Test in container environment**:
   ```bash
   cd /Users/medk-cka/cks-ansible
   ansible-playbook -i inventory/hosts.yml playbooks/deploy-containers.yml
   ```

3. **Verify fixes work** in the deployed container scripts

## Known Issues to Debug

### Dataset Download Problem
- **Working**: `20250807085639331-1331542`
- **Failing**: `20250502110701494-1323378`

Potential causes to investigate:
- Dataset type differences
- File permissions or access rights
- Dataset state (archived, deleted, etc.)
- PyBIS API version compatibility
- OpenBIS server-side issues

### Questions to Answer
1. What's different about the failing dataset?
2. Does `dataset.get_files()` work for the failing dataset?
3. Are there error messages in the PyBIS logs?
4. Does the issue occur with other similar datasets?