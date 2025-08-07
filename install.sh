#!/bin/bash
# CK PyBIS Toolkit Installation Script - Enhanced for GitHub distribution

set -e  # Exit on error

echo "🔧 Installing CK PyBIS Toolkit..."
echo "=================================================="

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
        if "$py" -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" 2>/dev/null; then
            PYTHON_CMD="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.7+ not found. Please install Python 3.7 or higher."
    echo "   Linux: sudo apt install python3 python3-pip"
    echo "   macOS: brew install python3"
    exit 1
fi

# Find corresponding pip command
for pip in pip3 pip "$PYTHON_CMD -m pip"; do
    if eval "command -v $pip >/dev/null 2>&1" || eval "$pip --version >/dev/null 2>&1"; then
        PIP_CMD="$pip"
        break
    fi
done

if [ -z "$PIP_CMD" ]; then
    echo "❌ pip not found. Please install pip."
    echo "   Try: $PYTHON_CMD -m ensurepip --upgrade"
    exit 1
fi

echo "✅ Using Python: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"
echo "✅ Using pip: $PIP_CMD"

# Install the package
echo "📦 Installing CK PyBIS Toolkit package..."
if ! eval "$PIP_CMD install -e ."; then
    echo "❌ Installation failed, trying user install..."
    if ! eval "$PIP_CMD install --user -e ."; then
        echo "❌ Installation failed completely"
        exit 1
    fi
    echo "✅ Installed in user directory"
else
    echo "✅ Package installed successfully"
fi

# Create credentials directory
CONFIG_DIR="$HOME/.openbis"
echo "📁 Setting up credentials directory: $CONFIG_DIR"
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

# Copy credentials template if it doesn't exist
if [ ! -f "$CONFIG_DIR/credentials" ] && [ -f "credentials.example" ]; then
    echo "📋 Creating credentials template..."
    cp credentials.example "$CONFIG_DIR/credentials"
    chmod 600 "$CONFIG_DIR/credentials"
    echo "⚠️  Please edit $CONFIG_DIR/credentials with your OpenBIS connection details"
elif [ -f "$CONFIG_DIR/credentials" ]; then
    echo "✅ Credentials file already exists"
    chmod 600 "$CONFIG_DIR/credentials"
fi

# Enhanced PATH and shell setup
echo "🔗 Setting up command access..."
mkdir -p "$HOME/.local/bin"

# Try to find the installed pybis command
PYBIS_LOCATION=""
for location in "$HOME/.local/bin/pybis" "$(which pybis 2>/dev/null)"; do
    if [ -n "$location" ] && [ -x "$location" ]; then
        PYBIS_LOCATION="$location"
        break
    fi
done

if [ -n "$PYBIS_LOCATION" ]; then
    ln -sf "$PYBIS_LOCATION" "$HOME/.local/bin/pybis"
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