#!/usr/bin/env python3
"""
Standalone PyBIS Development Scripts
Extracted from Ansible container project for development and testing

This module provides direct access to PyBIS functionality without container overhead.
Perfect for debugging, development, and testing.
"""
import os
import sys
from pathlib import Path

def load_credentials():
    """Load credentials from ~/.openbis/credentials file"""
    creds_file = Path.home() / '.openbis' / 'credentials'
    
    if creds_file.exists():
        with open(creds_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

# Load credentials before importing other modules
load_credentials()

# Load PyBIS common functionality
from pybis_common import *

def main():
    """Main CLI interface for PyBIS tools"""
    if len(sys.argv) < 2:
        print("PyBIS Development Tools")
        print("=" * 40)
        print("Available tools:")
        print("  connect            - Test OpenBIS connection")
        print("  config             - Manage configuration (oBIS-inspired JSON)")
        print("  search             - Enhanced search with advanced filtering")
        print("  download           - Download datasets")
        print("  download-collection - Download all datasets from a collection")
        print("  info               - Get detailed object information")
        print("  upload             - Upload files with auto-linking (auto-detects type)")
        print("  upload-lib         - Upload spectral libraries")
        print("  upload-fasta       - Upload FASTA database files")
        print()
        print("Usage: python pybis_scripts.py <tool> [args...]")
        print("Examples:")
        print("  python pybis_scripts.py download 20250807085639331-1331542 --output ~/data/")
        print("  python pybis_scripts.py download-collection /DDB/CK/FASTA --list-only")
        sys.exit(1)
    
    tool = sys.argv[1]
    args = sys.argv[2:]
    
    # Route to appropriate tool function
    if tool == "connect":
        pybis_connect_main(args)
    elif tool == "config":
        pybis_config_main(args)
    elif tool == "search":
        pybis_search_main(args)
    elif tool == "download":
        pybis_download_main(args)
    elif tool == "download-collection":
        pybis_download_collection_main(args)
    elif tool == "info":
        pybis_info_main(args)
    elif tool == "upload":
        pybis_upload_main(args)
    elif tool == "upload-lib":
        pybis_upload_library_main(args)
    elif tool == "upload-fasta":
        pybis_upload_fasta_main(args)
    else:
        print(f"❌ Unknown tool: {tool}")
        print("Available tools: connect, config, search, download, download-collection, info, upload, upload-lib, upload-fasta")
        sys.exit(1)

if __name__ == "__main__":
    main()