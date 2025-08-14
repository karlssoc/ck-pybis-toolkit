#!/bin/bash
# CK PyBIS Toolkit Installation Script - Enhanced for GitHub distribution

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Parse command line arguments
DRY_RUN=false
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "CK PyBIS Toolkit Installation Script"
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be done without making changes"
            echo "  --verbose    Enable verbose output for debugging"
            echo "  --help       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Enable verbose output if requested
if [ "$VERBOSE" = true ]; then
    set -x
fi

echo "🔧 Installing CK PyBIS Toolkit..."
echo "=================================================="
if [ "$DRY_RUN" = true ]; then
    echo "🧪 DRY RUN MODE - No changes will be made"
fi

# Platform detection
PLATFORM="$(uname -s)"
case "${PLATFORM}" in
    Linux*)     PLATFORM="Linux";;
    Darwin*)    PLATFORM="macOS";;
    *)          PLATFORM="Unknown";;
esac

echo "🖥️  Platform: $PLATFORM"

# Auto-detect Python command
PYTHON_CMD=""
PIP_CMD=""

for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        if "$py" -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
            PYTHON_CMD="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.8+ not found. Please install Python 3.8 or higher."
    echo "   Linux: sudo apt install python3 python3-pip"
    echo "   macOS: brew install python3"
    exit 1
fi

# Find corresponding pip command
for pip in pip3 pip; do
    if command -v "$pip" >/dev/null 2>&1; then
        PIP_CMD="$pip"
        break
    fi
done

# Try python -m pip as fallback
if [ -z "$PIP_CMD" ]; then
    if "$PYTHON_CMD" -m pip --version >/dev/null 2>&1; then
        PIP_CMD="$PYTHON_CMD -m pip"
    fi
fi

if [ -z "$PIP_CMD" ]; then
    echo "❌ pip not found. Please install pip."
    echo "   Try: $PYTHON_CMD -m ensurepip --upgrade"
    exit 1
fi

echo "✅ Using Python: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"
echo "✅ Using pip: $PIP_CMD"

# Install the package
echo "📦 Installing CK PyBIS Toolkit package..."
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would run: $PIP_CMD install -e ."
else
    if ! $PIP_CMD install -e .; then
        echo "❌ Installation failed, trying user install..."
        if ! $PIP_CMD install --user -e .; then
            echo "❌ Installation failed completely"
            exit 1
        fi
        echo "✅ Installed in user directory"
    else
        echo "✅ Package installed successfully"
    fi
fi

# Create credentials directory
CONFIG_DIR="$HOME/.openbis"
echo "📁 Setting up credentials directory: $CONFIG_DIR"
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would create directory: $CONFIG_DIR"
    echo "[DRY RUN] Would set permissions: chmod 700 $CONFIG_DIR"
else
    mkdir -p "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR"
fi

# Copy credentials template if it doesn't exist
if [ ! -f "$CONFIG_DIR/credentials" ] && [ -f "credentials.example" ]; then
    echo "📋 Creating credentials template..."
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would copy: credentials.example -> $CONFIG_DIR/credentials"
        echo "[DRY RUN] Would set permissions: chmod 600 $CONFIG_DIR/credentials"
    else
        cp credentials.example "$CONFIG_DIR/credentials"
        chmod 600 "$CONFIG_DIR/credentials"
    fi
    echo "⚠️  Please edit $CONFIG_DIR/credentials with your OpenBIS connection details"
elif [ -f "$CONFIG_DIR/credentials" ]; then
    echo "✅ Credentials file already exists"
    if [ "$DRY_RUN" = false ]; then
        chmod 600 "$CONFIG_DIR/credentials"
    fi
fi

# Enhanced PATH and shell setup
echo "🔗 Setting up command access..."
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would create directory: $HOME/.local/bin"
else
    mkdir -p "$HOME/.local/bin"
fi

# Try to find the installed pybis command (excluding the symlink we're about to create)
PYBIS_LOCATION=""
location="$(which pybis 2>/dev/null)"
if [ -n "$location" ]; then
    # Skip if it's the symlink we're trying to create
    if [ -x "$location" ] && [ "$location" != "$HOME/.local/bin/pybis" ]; then
        PYBIS_LOCATION="$location"
    fi
fi

# If we couldn't find it, try Python module execution
if [ -z "$PYBIS_LOCATION" ]; then
    # Test if the module is available
    if "$PYTHON_CMD" -c 'import pybis_scripts' 2>/dev/null; then
        # Create a wrapper script instead of a symlink
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY RUN] Would create wrapper script: $HOME/.local/bin/pybis"
            echo "[DRY RUN] Would set executable permissions"
        else
            cat > "$HOME/.local/bin/pybis" << EOF
#!/bin/bash
exec $PYTHON_CMD -c "
import sys
import pybis_scripts
sys.exit(pybis_scripts.main())
" "\$@"
EOF
            chmod +x "$HOME/.local/bin/pybis"
        fi
        echo "✅ Command wrapper created: ~/.local/bin/pybis"
    else
        echo "⚠️  Could not locate pybis command automatically"
    fi
elif [ -n "$PYBIS_LOCATION" ]; then
    # Remove existing symlink if it exists
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would remove existing symlink: $HOME/.local/bin/pybis"
        echo "[DRY RUN] Would create symlink: $PYBIS_LOCATION -> $HOME/.local/bin/pybis"
    else
        rm -f "$HOME/.local/bin/pybis"
        ln -sf "$PYBIS_LOCATION" "$HOME/.local/bin/pybis"
    fi
    echo "✅ Command linked: ~/.local/bin/pybis"
else
    echo "⚠️  Could not locate pybis command automatically"
fi

# Check if ~/.local/bin is in PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo ""
    echo "⚠️  PATH Configuration Needed:"
    echo "   Add ~/.local/bin to your PATH to use 'pybis' from anywhere."
    echo ""
    
    # Detect shell and provide instructions
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
        bash)
            PROFILE_FILE="$HOME/.bashrc"
            if [ "$PLATFORM" = "macOS" ]; then
                PROFILE_FILE="$HOME/.bash_profile"
            fi
            echo "   For bash, add this to $PROFILE_FILE:"
            echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
            ;;
        zsh)
            echo "   For zsh, add this to ~/.zshrc:"
            echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
            ;;
        fish)
            echo "   For fish shell, run:"
            echo "   fish_add_path ~/.local/bin"
            ;;
        *)
            echo "   Add this line to your shell profile:"
            echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
            ;;
    esac
    echo ""
    echo "   Then restart your terminal or run: source ~/.bashrc (or equivalent)"
    echo ""
fi

# Test installation
echo "🧪 Testing installation..."
if command -v pybis >/dev/null 2>&1 && pybis connect --help >/dev/null 2>&1; then
    echo "✅ CK PyBIS Toolkit installed successfully!"
    echo "✅ Command available: $(command -v pybis)"
else
    echo "⚠️  Installation completed but 'pybis' command not immediately available"
    echo "   This is likely a PATH issue. Follow the instructions above."
    echo "   You can also use: $PYTHON_CMD -m pybis_scripts"
fi

echo ""
echo "=================================================="
echo "✅ Installation complete!"
echo "=================================================="
echo ""
echo "Usage examples:"
echo "  pybis connect --verbose"
echo "  pybis download 20250807085639331-1331542 --output ~/data/"
echo "  pybis download-collection /DDB/CK/FASTA --list-only"
echo "  pybis upload-fasta database.fasta --version '2024.08'"
echo "  pybis search proteome --type datasets --limit 5"
echo ""
echo "📝 Configure your OpenBIS credentials in:"
echo "   $CONFIG_DIR/credentials"