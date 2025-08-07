# PyBIS CLI Quick Reference

## 🚀 Installation
```bash
./install.sh
```

## ⚙️ Configuration
```bash
# Edit credentials
nano ~/.openbis/credentials

# Format:
OPENBIS_URL="https://your-server.com/openbis/"
OPENBIS_USERNAME="username"
OPENBIS_PASSWORD="password"
```

## 📋 Common Commands

### Connection & Search
```bash
pybis connect --verbose                           # Test connection
pybis search proteome --type datasets --limit 10 # Search datasets
pybis info --spaces                               # List spaces
pybis info --dataset DATASET_ID                  # Dataset details
```

### Upload (New!)
```bash
# Auto-detection (recommended)
pybis upload database.fasta --version "2024.08"
pybis upload library.tsv --log-file diann.log

# Preview first
pybis upload file.fasta --version "1.0" --dry-run

# Specific file types
pybis upload-fasta database.fasta --version "2024.08"
pybis upload-lib library.tsv --log-file diann.log
```

### Download
```bash
pybis download DATASET_ID --output ~/data/       # Download dataset
pybis download DATASET_ID --list-only            # List files only
```

## 🔍 File Type Auto-Detection

| Extension | Type | Default Collection |
|---|---|---|
| `.fasta`, `.fa`, `.fas` | FASTA Database | `/DDB/CK/FASTA` |
| `.tsv`, `.csv` (with "lib") | Spectral Library | `/DDB/CK/PREDSPECLIB` |
| `.speclib`, `.sptxt` | Spectral Library | `/DDB/CK/PREDSPECLIB` |
| Other | Unknown | `/DDB/CK/UNKNOWN` |

## 🛠️ Advanced Options

### Custom Settings
```bash
pybis upload file.fasta \
    --collection "/CUSTOM/PROJECT/EXPERIMENT" \
    --dataset-type "CUSTOM_TYPE" \
    --name "Custom Name" \
    --notes "Description" \
    --version "1.0"
```

### Batch Operations
```bash
# Multiple uploads
for file in *.fasta; do
    pybis upload "$file" --version "2024.08"
done

# Search and download
pybis search "mouse" --type datasets --limit 5 | \
    grep -o "DATASET_[0-9-]*" | \
    while read dataset; do
        pybis download "$dataset" --output ~/downloads/
    done
```

## 🐛 Troubleshooting

### Check Setup
```bash
# Test credentials
source ~/.openbis/credentials && echo $OPENBIS_URL

# Check PATH
echo $PATH | grep ~/.local/bin

# Test conda environment
conda env list | grep pybis-1.37.3
```

### Fix Common Issues
```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Recreate conda environment
conda create -n pybis-1.37.3 python=3.9
conda activate pybis-1.37.3
pip install pybis==1.37.3
```

## 📊 Metadata Auto-Extraction

### FASTA Files
- Number of protein entries
- Primary species (most common)
- Species breakdown (top 5 with %)
- File size in MB

### Spectral Libraries
- DIA-NN version and statistics
- Number of precursors/proteins/genes
- FASTA database used
- Generation parameters

## 💡 Pro Tips

1. **Always use `--dry-run` first** to preview uploads
2. **File type detection is automatic** - just use `pybis upload`
3. **Credentials are loaded automatically** from `~/.openbis/credentials`
4. **Conda environment is activated automatically**
5. **All commands support `--help`** for detailed options

## 🔗 Help
```bash
pybis --help                    # General help
pybis upload --help            # Upload help
pybis connect --help           # Connection help
```