#!/usr/bin/env python3
"""
PyBIS Common Module
Shared functionality for all PyBIS container scripts
"""
from pybis import Openbis
import os
import sys
import argparse
import re
import time
import hashlib
from pathlib import Path

def _load_credentials_if_available():
    """Load credentials from configuration files (oBIS-inspired JSON + legacy support)"""
    # Try JSON config first (oBIS-style)
    json_config = _load_json_config()
    if json_config:
        for key, value in json_config.items():
            if key.upper() in ['OPENBIS_URL', 'OPENBIS_USERNAME', 'OPENBIS_PASSWORD', 'PYBIS_DOWNLOAD_DIR', 'PYBIS_VERIFY_CERTIFICATES']:
                os.environ[key.upper()] = str(value)
    
    # Fall back to legacy credentials file (backward compatibility)
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

def _load_json_config():
    """Load JSON configuration files (oBIS-inspired)"""
    config = {}
    
    # Global config from ~/.pybis/config.json (similar to oBIS ~/.obis)
    global_config_file = Path.home() / '.pybis' / 'config.json'
    if global_config_file.exists():
        try:
            import json
            with open(global_config_file) as f:
                global_config = json.load(f)
                config.update(global_config)
        except Exception as e:
            print(f"⚠️  Warning: Could not load global config: {e}")
    
    # Local config from ./.pybis/config.json (project-specific)
    local_config_file = Path('.pybis') / 'config.json'
    if local_config_file.exists():
        try:
            import json
            with open(local_config_file) as f:
                local_config = json.load(f)
                config.update(local_config)  # Local overrides global
        except Exception as e:
            print(f"⚠️  Warning: Could not load local config: {e}")
    
    return config

def _get_config_value(key, default=None):
    """Get configuration value with priority: env > local JSON > global JSON > default"""
    # Environment variables have highest priority
    if key.upper() in os.environ:
        return os.environ[key.upper()]
    
    # Try JSON config
    config = _load_json_config()
    return config.get(key.lower(), config.get(key.upper(), default))

def get_openbis_connection(use_cache=True):
    """Get authenticated OpenBIS connection with token caching and performance options"""
    # Try to load credentials if not in environment
    if not os.environ.get('OPENBIS_URL'):
        _load_credentials_if_available()
    
    url = os.environ.get('OPENBIS_URL')
    username = os.environ.get('OPENBIS_USERNAME')
    password = os.environ.get('OPENBIS_PASSWORD')
    
    if not all([url, username, password]):
        print("❌ Missing OpenBIS credentials in environment")
        print("💡 Make sure ~/.openbis/credentials exists or use 'pybis config' to configure")
        sys.exit(1)
    
    # Get certificate verification setting (default: False for backward compatibility)
    verify_certs_str = os.environ.get('PYBIS_VERIFY_CERTIFICATES', 'false').lower()
    verify_certificates = verify_certs_str in ['true', '1', 'yes', 'on']
    
    # Performance optimization: configurable cache for large systems
    use_cache_str = os.environ.get('PYBIS_USE_CACHE', str(use_cache)).lower()
    use_cache_final = use_cache_str in ['true', '1', 'yes', 'on']
    
    o = Openbis(url, verify_certificates=verify_certificates, use_cache=use_cache_final)
    
    try:
        # Try to use existing token first
        o.get_spaces()
        return o
    except:
        # Token missing/expired - login with password and save new token
        o.login(username, password, save_token=True)
        return o

# ============================================================================
# PYBIS TOOL IMPLEMENTATIONS
# ============================================================================

def pybis_connect_main(args):
    """PyBIS Connect Tool - Test connection and display basic info"""
    parser = argparse.ArgumentParser(description='Connect to OpenBIS and show basic information')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    
    parsed_args = parser.parse_args(args)
    
    print("🔌 PyBIS Connection Tool")
    print("=" * 50)
    
    o = get_openbis_connection()
    
    try:
        spaces = o.get_spaces()
        print(f"✅ Connected successfully!")
        print(f"📊 Found {len(spaces)} spaces")
        
        if parsed_args.verbose:
            print("\n🌌 Available Spaces:")
            if hasattr(spaces, 'iterrows'):
                for i, (idx, space) in enumerate(spaces.iterrows()):
                    code = getattr(space, 'code', 'N/A')
                    description = getattr(space, 'description', 'No description') or 'No description'
                    print(f"  📁 {code}: {description}")
            else:
                for space in spaces:
                    code = getattr(space, 'code', 'N/A')
                    description = getattr(space, 'description', 'No description') or 'No description'
                    print(f"  📁 {code}: {description}")
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def pybis_search_main(args):
    """PyBIS Search Tool - Enhanced search with oBIS-style filtering capabilities"""
    parser = argparse.ArgumentParser(description='Search OpenBIS with advanced filtering (inspired by oBIS)')
    
    # Basic search parameters
    parser.add_argument('query', nargs='?', help='Search query (supports wildcards)')
    parser.add_argument('--type', choices=['experiments', 'samples', 'datasets', 'all'], 
                       default='all', help='What to search for')
    parser.add_argument('--limit', type=int, default=10, help='Maximum results to show')
    parser.add_argument('--save', help='Save results to CSV file')
    
    # Relationship queries
    parser.add_argument('--children-of', help='Find children of specified dataset')
    parser.add_argument('--parents-of', help='Find parents of specified dataset')
    
    # Advanced filtering (oBIS-inspired)
    parser.add_argument('--space', help='Filter by space code')
    parser.add_argument('--project', help='Filter by project code') 
    parser.add_argument('--collection', help='Filter by collection/experiment path')
    parser.add_argument('--dataset-type', help='Filter by dataset type code')
    parser.add_argument('--property', help='Filter by property code')
    parser.add_argument('--property-value', help='Filter by property value')
    parser.add_argument('--registration-date', help='Filter by registration date (format: ">YYYY-MM-DD" or "<YYYY-MM-DD")')
    parser.add_argument('--recursive', '-r', action='store_true', help='Search recursively through child objects')
    
    parsed_args = parser.parse_args(args)
    
    print(f"🔍 Enhanced OpenBIS Search Tool")
    
    # Handle relationship queries
    if parsed_args.children_of or parsed_args.parents_of:
        o = get_openbis_connection()
        
        if parsed_args.children_of:
            print(f"Finding children of dataset: {parsed_args.children_of}")
            print("=" * 50)
            results = _search_dataset_children(o, parsed_args.children_of)
            if parsed_args.save and results:
                _save_search_results(results, parsed_args.save, 'children')
        
        if parsed_args.parents_of:
            print(f"Finding parents of dataset: {parsed_args.parents_of}")
            print("=" * 50)
            results = _search_dataset_parents(o, parsed_args.parents_of)
            if parsed_args.save and results:
                _save_search_results(results, parsed_args.save, 'parents')
        
        return
    
    # Check if any advanced filters are provided
    has_advanced_filters = any([
        parsed_args.space, parsed_args.project, parsed_args.collection,
        parsed_args.dataset_type, parsed_args.property, parsed_args.property_value,
        parsed_args.registration_date
    ])
    
    # Handle advanced filtered search
    if has_advanced_filters:
        print("Using advanced filtering...")
        _show_search_filters(parsed_args)
        print("=" * 50)
        
        o = get_openbis_connection()
        results = _advanced_search(o, parsed_args)
        
        if parsed_args.save and results:
            _save_search_results(results, parsed_args.save, 'advanced_search')
        return
    
    # Handle regular search
    if not parsed_args.query:
        print("❌ Must specify query or use filtering options")
        print("💡 Use --help to see available filtering options")
        return
        
    print(f"Query: {parsed_args.query}")
    print(f"Type: {parsed_args.type}")
    print("=" * 50)
    
    o = get_openbis_connection()
    all_results = []
    
    if parsed_args.type in ['experiments', 'all']:
        results = _search_experiments(o, parsed_args.query, parsed_args.limit)
        all_results.extend(results or [])
        if parsed_args.type == 'all':
            print()
    
    if parsed_args.type in ['samples', 'all']:
        results = _search_samples(o, parsed_args.query, parsed_args.limit)
        all_results.extend(results or [])
        if parsed_args.type == 'all':
            print()
    
    if parsed_args.type in ['datasets', 'all']:
        results = _search_datasets(o, parsed_args.query, parsed_args.limit)
        all_results.extend(results or [])
    
    if parsed_args.save and all_results:
        _save_search_results(all_results, parsed_args.save, 'basic_search')

def pybis_config_main(args):
    """PyBIS Config Tool - Manage JSON-based configuration (oBIS-inspired)"""
    parser = argparse.ArgumentParser(description='Manage PyBIS configuration settings')
    parser.add_argument('action', choices=['get', 'set', 'clear', 'list', 'init'], 
                       help='Configuration action')
    parser.add_argument('key', nargs='?', help='Configuration key')
    parser.add_argument('value', nargs='?', help='Configuration value (for set action)')
    parser.add_argument('-g', '--global', dest='global_scope', action='store_true',
                       help='Use global configuration (~/.pybis/config.json)')
    parser.add_argument('--init-example', action='store_true',
                       help='Initialize with example configuration')
    
    parsed_args = parser.parse_args(args)
    
    print(f"⚙️  PyBIS Configuration Manager")
    
    scope = "global" if parsed_args.global_scope else "local"
    config_file = _get_config_file_path(parsed_args.global_scope)
    
    if parsed_args.action == 'init':
        _init_config(config_file, parsed_args.init_example)
    elif parsed_args.action == 'list':
        _list_config(parsed_args.global_scope)
    elif parsed_args.action == 'get':
        _get_config(parsed_args.key, parsed_args.global_scope)
    elif parsed_args.action == 'set':
        if not parsed_args.key or parsed_args.value is None:
            print("❌ Both key and value required for 'set' action")
            return
        _set_config(parsed_args.key, parsed_args.value, parsed_args.global_scope)
    elif parsed_args.action == 'clear':
        if not parsed_args.key:
            print("❌ Key required for 'clear' action")
            return
        _clear_config(parsed_args.key, parsed_args.global_scope)

def _get_config_file_path(global_scope):
    """Get path to config file based on scope"""
    if global_scope:
        config_dir = Path.home() / '.pybis'
    else:
        config_dir = Path('.pybis')
    
    return config_dir / 'config.json'

def _ensure_config_dir(config_file):
    """Ensure config directory exists"""
    config_file.parent.mkdir(parents=True, exist_ok=True)

def _load_config_file(config_file):
    """Load JSON config file"""
    if not config_file.exists():
        return {}
    
    try:
        import json
        with open(config_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return {}

def _save_config_file(config_file, config):
    """Save JSON config file with secure permissions"""
    try:
        import json
        import os
        _ensure_config_dir(config_file)
        
        # Create file with secure permissions (600 - owner read/write only)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Ensure file has secure permissions (readable/writable only by owner)
        os.chmod(config_file, 0o600)
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

def _init_config(config_file, with_example):
    """Initialize configuration file"""
    scope = "global" if "pybis" in str(config_file.parent) else "local"
    
    if config_file.exists():
        print(f"⚠️  {scope.title()} config already exists: {config_file}")
        return
    
    config = {}
    if with_example:
        config = {
            "openbis_url": "https://your-server.com/openbis/",
            "openbis_username": "your-username",
            "openbis_password": "your-password",
            "pybis_download_dir": "~/data/openbis/",
            "pybis_verify_certificates": False,
            "pybis_use_cache": True,
            "auto_link_parents": False,
            "default_collections": {
                "fasta": "/DDB/CK/FASTA",
                "spectral_library": "/DDB/CK/PREDSPECLIB",
                "unknown": "/DDB/CK/UNKNOWN"
            },
            "search": {
                "default_limit": 10,
                "save_format": "csv"
            }
        }
    
    if _save_config_file(config_file, config):
        print(f"✅ Initialized {scope} config: {config_file}")
        if with_example:
            print("💡 Please edit the config file to add your OpenBIS credentials")
    else:
        print(f"❌ Failed to initialize {scope} config")

def _list_config(global_scope):
    """List all configuration settings"""
    scope = "global" if global_scope else "local"
    config_file = _get_config_file_path(global_scope)
    
    print(f"📋 {scope.title()} configuration ({config_file}):")
    print("=" * 60)
    
    config = _load_config_file(config_file)
    
    if not config:
        print("  (No configuration found)")
        print(f"💡 Initialize with: pybis config init {'-g' if global_scope else ''}")
        return
    
    def print_nested(obj, indent=0):
        for key, value in obj.items():
            if isinstance(value, dict):
                print("  " * indent + f"📁 {key}:")
                print_nested(value, indent + 1)
            else:
                print("  " * indent + f"🔧 {key}: {value}")
    
    print_nested(config)

def _get_config(key, global_scope):
    """Get configuration value"""
    if not key:
        _list_config(global_scope)
        return
    
    scope = "global" if global_scope else "local"
    config_file = _get_config_file_path(global_scope)
    config = _load_config_file(config_file)
    
    # Support nested keys with dot notation
    keys = key.split('.')
    value = config
    
    try:
        for k in keys:
            value = value[k]
        print(f"🔧 {key} ({scope}): {value}")
    except (KeyError, TypeError):
        print(f"❌ Configuration key '{key}' not found in {scope} config")

def _set_config(key, value, global_scope):
    """Set configuration value"""
    scope = "global" if global_scope else "local"
    config_file = _get_config_file_path(global_scope)
    config = _load_config_file(config_file)
    
    # Support nested keys with dot notation
    keys = key.split('.')
    current = config
    
    # Navigate to parent of target key
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # Convert value type if needed
    if value.lower() in ['true', 'false']:
        value = value.lower() == 'true'
    elif value.isdigit():
        value = int(value)
    elif value.replace('.', '').isdigit():
        value = float(value)
    
    # Set the value
    current[keys[-1]] = value
    
    if _save_config_file(config_file, config):
        print(f"✅ Set {key} = {value} ({scope})")
    else:
        print(f"❌ Failed to set {key}")

def _clear_config(key, global_scope):
    """Clear configuration value"""
    scope = "global" if global_scope else "local"
    config_file = _get_config_file_path(global_scope)
    config = _load_config_file(config_file)
    
    # Support nested keys with dot notation
    keys = key.split('.')
    current = config
    
    try:
        # Navigate to parent of target key
        for k in keys[:-1]:
            current = current[k]
        
        # Delete the key
        del current[keys[-1]]
        
        if _save_config_file(config_file, config):
            print(f"✅ Cleared {key} ({scope})")
        else:
            print(f"❌ Failed to clear {key}")
    except (KeyError, TypeError):
        print(f"❌ Configuration key '{key}' not found in {scope} config")

def pybis_download_main(args):
    """PyBIS Download Tool - Download datasets and files"""
    parser = argparse.ArgumentParser(description='Download datasets and files from OpenBIS')
    parser.add_argument('dataset_code', help='Dataset code to download')
    parser.add_argument('--output', '-o', default=os.environ.get('PYBIS_DOWNLOAD_DIR', os.path.expanduser('~/data/openbis/')), 
                       help='Output directory (default: $PYBIS_DOWNLOAD_DIR or ~/data/openbis/)')
    parser.add_argument('--list-only', action='store_true', 
                       help='Only list files, do not download')
    parser.add_argument('--force', action='store_true', 
                       help='Force re-download even if files exist')
    parser.add_argument('--verify-checksum', action='store_true', 
                       help='Verify file integrity using checksums (slower)')
    
    parsed_args = parser.parse_args(args)
    
    print(f"📦 OpenBIS Download Tool")
    print(f"Dataset: {parsed_args.dataset_code}")
    print(f"Output: {parsed_args.output}")
    print("=" * 50)
    
    o = get_openbis_connection()
    
    if parsed_args.list_only:
        _list_dataset_files(o, parsed_args.dataset_code)
    else:
        _download_dataset(o, parsed_args.dataset_code, parsed_args.output, 
                         force=parsed_args.force, verify_checksum=parsed_args.verify_checksum)

def pybis_download_collection_main(args):
    """PyBIS Download Collection Tool - Download all datasets from a collection"""
    parser = argparse.ArgumentParser(description='Download all datasets from an OpenBIS collection')
    parser.add_argument('collection', help='Collection path (required)')
    parser.add_argument('--output', '-o', default=os.environ.get('PYBIS_DOWNLOAD_DIR', os.path.expanduser('~/data/openbis/')), 
                       help='Output directory (default: $PYBIS_DOWNLOAD_DIR or ~/data/openbis/)')
    parser.add_argument('--list-only', action='store_true', 
                       help='Only list datasets, do not download')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of datasets to download')
    parser.add_argument('--force', action='store_true', 
                       help='Force re-download even if files exist')
    parser.add_argument('--verify-checksum', action='store_true', 
                       help='Verify file integrity using checksums (slower)')
    
    parsed_args = parser.parse_args(args)
    
    print(f"📦 OpenBIS Collection Download Tool")
    print(f"Collection: {parsed_args.collection}")
    print(f"Output: {parsed_args.output}")
    print("=" * 50)
    
    o = get_openbis_connection()
    
    if parsed_args.list_only:
        _list_collection_datasets(o, parsed_args.collection, parsed_args.limit)
    else:
        _download_collection_datasets(o, parsed_args.collection, parsed_args.output, parsed_args.limit, 
                                     force=parsed_args.force, verify_checksum=parsed_args.verify_checksum)

def pybis_info_main(args):
    """PyBIS Info Tool - Get detailed information about objects"""
    parser = argparse.ArgumentParser(description='Get detailed information about OpenBIS objects')
    parser.add_argument('--spaces', action='store_true', help='Show all spaces')
    parser.add_argument('--dataset', help='Show dataset information')
    parser.add_argument('--sample', help='Show sample information')
    parser.add_argument('--show-lineage', action='store_true', help='Show parent-child relationships for dataset')
    
    parsed_args = parser.parse_args(args)
    
    if not any([parsed_args.spaces, parsed_args.dataset, parsed_args.sample]):
        parser.print_help()
        sys.exit(1)
    
    print(f"ℹ️ OpenBIS Info Tool")
    print("=" * 50)
    
    o = get_openbis_connection()
    
    if parsed_args.spaces:
        _show_spaces_info(o)
    
    if parsed_args.dataset:
        _show_dataset_info(o, parsed_args.dataset, show_lineage=parsed_args.show_lineage)
    
    if parsed_args.sample:
        _show_sample_info(o, parsed_args.sample)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _search_experiments(o, query, limit=10):
    """Search for experiments"""
    print(f"🔬 Searching experiments for: {query}")
    try:
        experiments = o.get_experiments(code=f"*{query}*")
        print(f"Found {len(experiments)} experiments")
        results = []
        
        if len(experiments) > 0:
            display_limit = min(limit, len(experiments))
            if hasattr(experiments, 'head'):
                for i, (idx, exp) in enumerate(experiments.head(display_limit).iterrows()):
                    code = getattr(exp, 'code', 'N/A')
                    exp_type = getattr(exp, 'type', 'N/A')
                    print(f"  - {code} ({exp_type})")
                    results.append({'type': 'experiment', 'code': code, 'object_type': exp_type})
            else:
                for i, exp in enumerate(experiments[:display_limit]):
                    code = getattr(exp, 'code', 'N/A')
                    exp_type = getattr(exp, 'type', 'N/A')
                    print(f"  - {code} ({exp_type})")
                    results.append({'type': 'experiment', 'code': code, 'object_type': exp_type})
            
            if len(experiments) > display_limit:
                print(f"  ... and {len(experiments) - display_limit} more experiments")
        
        return results
                    
    except Exception as e:
        print(f"❌ Experiment search failed: {e}")
        return []

def _search_samples(o, query, limit=10):
    """Search for samples"""
    print(f"🧪 Searching samples for: {query}")
    try:
        samples = o.get_samples(code=f"*{query}*")
        print(f"Found {len(samples)} samples")
        results = []
        
        if len(samples) > 0:
            display_limit = min(limit, len(samples))
            if hasattr(samples, 'head'):
                for i, (idx, sample) in enumerate(samples.head(display_limit).iterrows()):
                    code = getattr(sample, 'code', 'N/A')
                    sample_type = getattr(sample, 'type', 'N/A')
                    print(f"  - {code} ({sample_type})")
                    results.append({'type': 'sample', 'code': code, 'object_type': sample_type})
            else:
                for i, sample in enumerate(samples[:display_limit]):
                    code = getattr(sample, 'code', 'N/A')
                    sample_type = getattr(sample, 'type', 'N/A')
                    print(f"  - {code} ({sample_type})")
                    results.append({'type': 'sample', 'code': code, 'object_type': sample_type})
            
            if len(samples) > display_limit:
                print(f"  ... and {len(samples) - display_limit} more samples")
        
        return results
                    
    except Exception as e:
        print(f"❌ Sample search failed: {e}")
        return []

def _search_datasets(o, query, limit=10):
    """Search for datasets"""
    print(f"📊 Searching datasets for: {query}")
    try:
        datasets = o.get_datasets(code=f"*{query}*")
        print(f"Found {len(datasets)} datasets")
        results = []
        
        if len(datasets) > 0:
            display_limit = min(limit, len(datasets))
            if hasattr(datasets, 'head'):
                for i, (idx, ds) in enumerate(datasets.head(display_limit).iterrows()):
                    code = getattr(ds, 'code', 'N/A')
                    ds_type = getattr(ds, 'type', 'N/A')
                    print(f"  - {code} ({ds_type})")
                    results.append({'type': 'dataset', 'code': code, 'object_type': ds_type})
            else:
                for i, ds in enumerate(datasets[:display_limit]):
                    code = getattr(ds, 'code', 'N/A')
                    ds_type = getattr(ds, 'type', 'N/A')
                    print(f"  - {code} ({ds_type})")
                    results.append({'type': 'dataset', 'code': code, 'object_type': ds_type})
            
            if len(datasets) > display_limit:
                print(f"  ... and {len(datasets) - display_limit} more datasets")
        
        return results
                    
    except Exception as e:
        print(f"❌ Dataset search failed: {e}")
        return []

# ============================================================================
# ENHANCED SEARCH FUNCTIONS (oBIS-INSPIRED)
# ============================================================================

def _show_search_filters(args):
    """Display active search filters"""
    filters = []
    if args.space:
        filters.append(f"Space: {args.space}")
    if args.project:
        filters.append(f"Project: {args.project}")
    if args.collection:
        filters.append(f"Collection: {args.collection}")
    if args.dataset_type:
        filters.append(f"Dataset Type: {args.dataset_type}")
    if args.property:
        filters.append(f"Property: {args.property}")
    if args.property_value:
        filters.append(f"Property Value: {args.property_value}")
    if args.registration_date:
        filters.append(f"Registration Date: {args.registration_date}")
    if args.recursive:
        filters.append("Recursive: Yes")
    
    if filters:
        print("🔧 Active Filters:")
        for f in filters:
            print(f"  • {f}")

def _advanced_search(o, args):
    """Perform advanced search with filtering (oBIS-inspired)"""
    results = []
    
    try:
        # Build search parameters for PyBIS
        search_params = {}
        
        if args.space:
            search_params['space'] = args.space
        if args.project:
            search_params['project'] = args.project
        if args.collection:
            search_params['experiment'] = args.collection
        if args.dataset_type:
            search_params['type'] = args.dataset_type
            
        # Search datasets with basic filters
        if args.type in ['datasets', 'all']:
            print(f"📊 Advanced dataset search...")
            try:
                datasets = o.get_datasets(**search_params)
                
                # Apply additional filters
                filtered_datasets = _apply_advanced_filters(datasets, args)
                
                print(f"Found {len(filtered_datasets)} datasets after filtering")
                display_limit = min(args.limit, len(filtered_datasets))
                
                for i, ds in enumerate(filtered_datasets[:display_limit]):
                    code = getattr(ds, 'code', 'N/A')
                    ds_type = getattr(ds, 'type', 'N/A')
                    reg_date = str(getattr(ds, 'registrationDate', 'N/A'))[:10]
                    print(f"  📊 {code} ({ds_type}) - {reg_date}")
                    results.append({
                        'type': 'dataset', 
                        'code': code, 
                        'object_type': ds_type,
                        'registration_date': reg_date
                    })
                
                if len(filtered_datasets) > display_limit:
                    print(f"  ... and {len(filtered_datasets) - display_limit} more datasets")
                    
            except Exception as e:
                print(f"❌ Advanced dataset search failed: {e}")
        
        # Search samples if requested
        if args.type in ['samples', 'all']:
            print(f"🧪 Advanced sample search...")
            try:
                # Remove dataset-specific parameters for sample search
                sample_params = {k: v for k, v in search_params.items() 
                               if k not in ['type']}  # type is dataset-specific
                samples = o.get_samples(**sample_params)
                
                filtered_samples = _apply_advanced_filters(samples, args)
                print(f"Found {len(filtered_samples)} samples after filtering")
                display_limit = min(args.limit, len(filtered_samples))
                
                for i, sample in enumerate(filtered_samples[:display_limit]):
                    code = getattr(sample, 'code', 'N/A')
                    sample_type = getattr(sample, 'type', 'N/A')
                    reg_date = str(getattr(sample, 'registrationDate', 'N/A'))[:10]
                    print(f"  🧪 {code} ({sample_type}) - {reg_date}")
                    results.append({
                        'type': 'sample',
                        'code': code, 
                        'object_type': sample_type,
                        'registration_date': reg_date
                    })
                
                if len(filtered_samples) > display_limit:
                    print(f"  ... and {len(filtered_samples) - display_limit} more samples")
                    
            except Exception as e:
                print(f"❌ Advanced sample search failed: {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ Advanced search failed: {e}")
        return []

def _apply_advanced_filters(objects, args):
    """Apply property and date filters to search results"""
    if not objects or len(objects) == 0:
        return []
    
    filtered = []
    
    # Convert to list if it's a DataFrame
    if hasattr(objects, 'iterrows'):
        object_list = [row for idx, row in objects.iterrows()]
    else:
        object_list = list(objects) if hasattr(objects, '__iter__') else [objects]
    
    for obj in object_list:
        include = True
        
        # Filter by property
        if args.property and args.property_value:
            try:
                if hasattr(obj, 'properties') and obj.properties:
                    props = obj.properties
                    if hasattr(props, 'get'):
                        prop_value = props.get(args.property)
                    else:
                        prop_value = getattr(props, args.property, None)
                    
                    if not prop_value or str(prop_value).lower() != args.property_value.lower():
                        include = False
                else:
                    include = False
            except:
                include = False
        
        # Filter by registration date
        if args.registration_date and include:
            try:
                reg_date = getattr(obj, 'registrationDate', None)
                if reg_date:
                    reg_date_str = str(reg_date)[:10]  # YYYY-MM-DD format
                    if args.registration_date.startswith('>'):
                        target_date = args.registration_date[1:]
                        if reg_date_str <= target_date:
                            include = False
                    elif args.registration_date.startswith('<'):
                        target_date = args.registration_date[1:]
                        if reg_date_str >= target_date:
                            include = False
            except:
                pass
        
        if include:
            filtered.append(obj)
    
    return filtered

def _save_search_results(results, filename, search_type):
    """Save search results to CSV file (oBIS-inspired)"""
    if not results:
        print("⚠️  No results to save")
        return
    
    try:
        import csv
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if results:
                fieldnames = results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
                
        print(f"💾 Saved {len(results)} results to {filename}")
        
    except Exception as e:
        print(f"❌ Failed to save results: {e}")

# ============================================================================
# ENHANCED PARENT-CHILD RELATIONSHIP MANAGEMENT
# ============================================================================

# Global relationship cache for performance optimization
_relationship_cache = {}
_cache_timestamps = {}
CACHE_EXPIRY_MINUTES = 15

def _get_relationship_cache(cache_key):
    """Get cached relationship data if still valid"""
    import time
    current_time = time.time()
    
    if (cache_key in _relationship_cache and 
        cache_key in _cache_timestamps and
        current_time - _cache_timestamps[cache_key] < CACHE_EXPIRY_MINUTES * 60):
        return _relationship_cache[cache_key]
    return None

def _set_relationship_cache(cache_key, data):
    """Cache relationship data with timestamp"""
    import time
    _relationship_cache[cache_key] = data
    _cache_timestamps[cache_key] = time.time()

def _process_relationship_results(results):
    """Efficiently process relationship query results"""
    processed = []
    
    try:
        if hasattr(results, 'iterrows'):
            # DataFrame format
            for idx, item in results.iterrows():
                processed.append({
                    'code': getattr(item, 'code', 'N/A'),
                    'type': getattr(item, 'type', 'Unknown'),
                    'name': getattr(item, 'name', '') or '',
                    'registration_date': str(getattr(item, 'registrationDate', ''))[:10]
                })
        else:
            # List or other iterable format
            for item in results:
                processed.append({
                    'code': getattr(item, 'code', str(item)),
                    'type': getattr(item, 'type', 'Unknown'),
                    'name': getattr(item, 'name', '') or '',
                    'registration_date': str(getattr(item, 'registrationDate', ''))[:10]
                })
    except Exception as e:
        print(f"⚠️  Warning: Error processing results: {e}")
        # Fallback to simple list
        processed = [{'code': str(r), 'type': 'Unknown', 'name': '', 'registration_date': ''} for r in results]
    
    return processed

def _display_relationship_results(results, relationship_type, emoji):
    """Display relationship results with optimized formatting"""
    if not results:
        return
        
    display_limit = min(10, len(results))
    
    for i, item in enumerate(results[:display_limit]):
        code = item.get('code', 'N/A')
        data_type = item.get('type', 'Unknown')
        reg_date = item.get('registration_date', '')
        name = item.get('name', '')
        
        # Show name if available and different from code
        display_name = f" - {name}" if name and name != code else ""
        
        print(f"  📊 {code} ({data_type}) - {reg_date}{display_name}")
    
    if len(results) > display_limit:
        print(f"  ... and {len(results) - display_limit} more {relationship_type}s")

def _batch_process_parent_suggestions(o, datasets, search_terms):
    """Batch process multiple datasets for parent suggestions (performance optimization)"""
    suggestions = []
    
    try:
        # Single query for all BIO_DB datasets
        all_bio_datasets = o.get_datasets(type='BIO_DB')
        
        # Pre-process dataset attributes for faster matching
        bio_dataset_data = []
        for ds in (all_bio_datasets if hasattr(all_bio_datasets, '__iter__') else [all_bio_datasets]):
            if not ds:
                continue
                
            ds_info = {
                'code': getattr(ds, 'code', ''),
                'name': getattr(ds, 'name', '') or '',
                'registration_date': str(getattr(ds, 'registrationDate', ''))[:10],
                'properties': {}
            }
            
            # Cache properties for faster lookups
            if hasattr(ds, 'properties') and ds.properties:
                try:
                    props = ds.properties
                    if hasattr(props, 'items'):
                        ds_info['properties'] = {k: str(v).lower() for k, v in props.items()}
                    else:
                        # Handle property objects
                        ds_info['properties'] = {attr: str(getattr(props, attr, '')).lower() 
                                               for attr in dir(props) if not attr.startswith('_')}
                except:
                    pass
            
            bio_dataset_data.append(ds_info)
        
        # Batch match against all search terms
        for term in search_terms:
            term_lower = term.lower()
            
            for ds_info in bio_dataset_data:
                match_found = False
                match_reason = ""
                
                # Check code/name matches
                if (term_lower in ds_info['code'].lower() or 
                    term_lower in ds_info['name'].lower()):
                    match_found = True
                    match_reason = f"Name/code match: {term}"
                
                # Check property matches
                if not match_found:
                    for prop_key, prop_value in ds_info['properties'].items():
                        if term_lower in prop_value:
                            match_found = True
                            match_reason = f"Property match ({prop_key}): {term}"
                            break
                
                if match_found:
                    suggestions.append({
                        'code': ds_info['code'],
                        'name': ds_info['name'],
                        'type': 'BIO_DB',
                        'registration_date': ds_info['registration_date'],
                        'match_reason': match_reason,
                        'confidence': 'high' if term_lower in ds_info['name'].lower() else 'medium'
                    })
                    
                    if len(suggestions) >= 10:  # Limit total suggestions
                        break
            
            if len(suggestions) >= 10:
                break
                
    except Exception as e:
        print(f"⚠️  Batch processing failed, falling back to individual queries: {e}")
    
    return suggestions[:5]  # Return top 5

def _suggest_parent_datasets(o, file_path, file_type, kwargs):
    """Suggest potential parent datasets based on file metadata and type"""
    suggestions = []
    
    try:
        if file_type == 'spectral_library':
            # For spectral libraries, look for referenced FASTA databases
            suggestions = _suggest_fasta_parents(o, file_path, kwargs.get('log_file'))
        elif file_type == 'fasta':
            # For FASTA files, look for version relationships or similar databases
            suggestions = _suggest_fasta_version_parents(o, file_path, kwargs.get('version'))
        
        return suggestions[:5]  # Limit to top 5 suggestions
        
    except Exception as e:
        print(f"⚠️  Warning: Could not generate parent suggestions: {e}")
        return []

def _suggest_fasta_parents(o, library_file, log_file):
    """Suggest FASTA database parents for spectral libraries"""
    suggestions = []
    
    if not log_file or not Path(log_file).exists():
        return suggestions
    
    try:
        # Parse DIA-NN log for FASTA database references
        metadata = parse_diann_log(log_file)
        fasta_database = metadata.get('FASTA_DATABASE')
        
        if fasta_database:
            # Search for datasets with matching FASTA filename
            print(f"  🔍 Looking for FASTA database: {fasta_database}")
            
            # Search by filename in dataset properties or metadata
            search_terms = [
                fasta_database,
                Path(fasta_database).stem,  # without extension
                Path(fasta_database).name   # with extension
            ]
            
            # Use optimized batch processing instead of individual queries
            suggestions = _batch_process_parent_suggestions(o, None, search_terms)
            
            # Update match reasons for FASTA-specific context
            for suggestion in suggestions:
                suggestion['match_reason'] = f'FASTA database reference: {fasta_database}'
                suggestion['confidence'] = 'high'
                    
    except Exception as e:
        print(f"⚠️  Error parsing log file: {e}")
    
    return suggestions

def _suggest_fasta_version_parents(o, fasta_file, version):
    """Suggest parent FASTA databases based on versioning patterns"""
    suggestions = []
    
    try:
        fasta_path = Path(fasta_file)
        base_name = fasta_path.stem
        
        # Look for similar named databases with different versions
        search_terms = [
            base_name.split('_')[0] if '_' in base_name else base_name,  # base name
            base_name.replace(version, '') if version else base_name,    # without version
        ]
        
        # Filter out very short search terms
        valid_terms = [term for term in search_terms if len(term) >= 3]
        
        if valid_terms:
            # Use optimized batch processing
            suggestions = _batch_process_parent_suggestions(o, None, valid_terms)
            
            # Update match reasons for version-specific context
            for suggestion in suggestions:
                suggestion['match_reason'] = f'Similar naming pattern: {suggestion.get("match_reason", "").split(": ")[-1] if ": " in suggestion.get("match_reason", "") else valid_terms[0]}'
                suggestion['confidence'] = 'medium'
                
    except Exception as e:
        print(f"⚠️  Error generating version suggestions: {e}")
    
    return suggestions[:5]

def _interactive_parent_linking(suggestions):
    """Present parent dataset suggestions to user for confirmation"""
    confirmed_parents = []
    
    if not suggestions:
        return confirmed_parents
        
    print(f"\n📋 Found {len(suggestions)} potential parent dataset(s):")
    print("=" * 60)
    
    for i, suggestion in enumerate(suggestions, 1):
        confidence_emoji = "🎯" if suggestion['confidence'] == 'high' else "🔍"
        print(f"{confidence_emoji} [{i}] {suggestion['code']}")
        print(f"    Name: {suggestion.get('name', 'N/A')}")
        print(f"    Type: {suggestion['type']}")
        print(f"    Date: {suggestion['registration_date']}")
        print(f"    Match: {suggestion['match_reason']}")
        print()
    
    print("Select datasets to link as parents:")
    print("  • Enter numbers (e.g., '1,3,5' or '1-3')")
    print("  • Press Enter to skip all")
    print("  • Type 'all' to select all")
    
    try:
        user_input = input("👉 Your choice: ").strip()
        
        if not user_input:
            return confirmed_parents
            
        if user_input.lower() == 'all':
            for suggestion in suggestions:
                confirmed_parents.append(suggestion['code'])
                print(f"✅ Linked: {suggestion['code']}")
        else:
            # Parse user selection
            selected_indices = []
            
            for part in user_input.split(','):
                part = part.strip()
                if '-' in part:
                    # Handle ranges like '1-3'
                    start, end = map(int, part.split('-'))
                    selected_indices.extend(range(start-1, end))
                else:
                    # Handle single numbers
                    selected_indices.append(int(part) - 1)
            
            for idx in selected_indices:
                if 0 <= idx < len(suggestions):
                    confirmed_parents.append(suggestions[idx]['code'])
                    print(f"✅ Linked: {suggestions[idx]['code']}")
    
    except (ValueError, KeyboardInterrupt):
        print("❌ Invalid selection or cancelled")
    
    return confirmed_parents

def _search_dataset_children(o, dataset_code):
    """Find children of a specific dataset - highly optimized with caching"""
    print(f"📥 Searching for children of {dataset_code}...")
    
    # Check cache first
    cache_key = f"children_{dataset_code}"
    cached_result = _get_relationship_cache(cache_key)
    if cached_result is not None:
        print(f"🚀 Using cached result ({len(cached_result)} children)")
        _display_relationship_results(cached_result, "child", "📥")
        return cached_result
    
    try:
        # Optimized batch query with minimal data fetching
        start_time = time.time()
        
        # Use withParents parameter for efficient server-side filtering
        children = o.get_datasets(
            withParents=dataset_code,
            fetchOptions={
                'withProperties': False,  # Skip properties for performance
                'withSamples': False,     # Skip sample relationships
                'withExperiment': False   # Skip experiment details
            }
        )
        
        query_time = time.time() - start_time
        
        if children is not None and len(children) > 0:
            print(f"📥 Found {len(children)} child dataset(s) in {query_time:.2f}s")
            
            # Process results efficiently
            processed_children = _process_relationship_results(children)
            
            # Cache results for future use
            _set_relationship_cache(cache_key, processed_children)
            
            _display_relationship_results(processed_children, "child", "📥")
            return processed_children
        else:
            print(f"📥 No child datasets found for {dataset_code}")
            _set_relationship_cache(cache_key, [])  # Cache empty result
            return []
            
    except Exception as e:
        print(f"❌ Optimized search failed: {e}")
        print("🔄 Trying fallback method...")
        result = _search_dataset_children_fallback(o, dataset_code)
        if result:
            _set_relationship_cache(cache_key, result)
        return result if result is not None else []

def _search_dataset_parents(o, dataset_code):
    """Find parents of a specific dataset - highly optimized with caching"""
    print(f"📤 Searching for parents of {dataset_code}...")
    
    # Check cache first
    cache_key = f"parents_{dataset_code}"
    cached_result = _get_relationship_cache(cache_key)
    if cached_result is not None:
        print(f"🚀 Using cached result ({len(cached_result)} parents)")
        _display_relationship_results(cached_result, "parent", "📤")
        return cached_result
    
    try:
        # Optimized batch query with minimal data fetching
        start_time = time.time()
        
        # Use withChildren parameter for efficient server-side filtering
        parents = o.get_datasets(
            withChildren=dataset_code,
            fetchOptions={
                'withProperties': False,  # Skip properties for performance
                'withSamples': False,     # Skip sample relationships
                'withExperiment': False   # Skip experiment details
            }
        )
        
        query_time = time.time() - start_time
        
        if parents is not None and len(parents) > 0:
            print(f"📤 Found {len(parents)} parent dataset(s) in {query_time:.2f}s")
            
            # Process results efficiently
            processed_parents = _process_relationship_results(parents)
            
            # Cache results for future use
            _set_relationship_cache(cache_key, processed_parents)
            
            _display_relationship_results(processed_parents, "parent", "📤")
            return processed_parents
        else:
            print(f"📤 No parent datasets found for {dataset_code}")
            _set_relationship_cache(cache_key, [])  # Cache empty result
            return []
            
    except Exception as e:
        print(f"❌ Optimized search failed: {e}")
        print("🔄 Trying fallback method...")
        result = _search_dataset_parents_fallback(o, dataset_code)
        if result:
            _set_relationship_cache(cache_key, result)
        return result if result is not None else []

def _search_dataset_children_fallback(o, dataset_code):
    """Fallback method using dataset.get_children()"""
    try:
        datasets = o.get_datasets(code=dataset_code)
        if len(datasets) == 0:
            print(f"❌ Dataset {dataset_code} not found")
            return
        
        dataset = datasets.iloc[0] if hasattr(datasets, 'iloc') else datasets[0]
        children = dataset.get_children()
        
        if children:
            print(f"📥 Found {len(children)} child dataset(s) (fallback):")
            for child in children[:5]:  # Limit to 5
                child_code = getattr(child, 'code', str(child))
                child_type = getattr(child, 'type', 'Unknown')
                print(f"  📊 {child_code} ({child_type})")
        else:
            print(f"📥 No child datasets found")
    except Exception as e:
        print(f"❌ Fallback also failed: {e}")

def _search_dataset_parents_fallback(o, dataset_code):
    """Fallback method using dataset.get_parents()"""
    try:
        datasets = o.get_datasets(code=dataset_code)
        if len(datasets) == 0:
            print(f"❌ Dataset {dataset_code} not found")
            return
        
        dataset = datasets.iloc[0] if hasattr(datasets, 'iloc') else datasets[0]
        parents = dataset.get_parents()
        
        if parents:
            print(f"📤 Found {len(parents)} parent dataset(s) (fallback):")
            for parent in parents[:5]:  # Limit to 5
                parent_code = getattr(parent, 'code', str(parent))
                parent_type = getattr(parent, 'type', 'Unknown')
                print(f"  📊 {parent_code} ({parent_type})")
        else:
            print(f"📤 No parent datasets found")
    except Exception as e:
        print(f"❌ Fallback also failed: {e}")

def _compute_file_checksum(file_path, algorithm='sha1'):
    """Compute checksum for a file using specified algorithm"""
    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"⚠️ Failed to compute checksum for {file_path}: {e}")
        return None

def _should_skip_file(local_file_path, remote_file_info, verify_checksum=False):
    """Check if file should be skipped based on existence and integrity"""
    if not local_file_path.exists():
        return False, "File does not exist locally"
    
    # Size comparison (fast check)
    local_size = local_file_path.stat().st_size
    remote_size = getattr(remote_file_info, 'fileLength', None)
    
    if remote_size is not None and local_size != remote_size:
        return False, f"Size mismatch (local: {local_size}, remote: {remote_size})"
    
    # Modification time check (if available)
    try:
        local_mtime = local_file_path.stat().st_mtime
        remote_mtime = getattr(remote_file_info, 'modificationDate', None)
        if remote_mtime is not None:
            # Convert remote mtime if it's a timestamp object
            if hasattr(remote_mtime, 'timestamp'):
                remote_mtime = remote_mtime.timestamp()
            elif isinstance(remote_mtime, str):
                # Skip string parsing for now - too variable
                remote_mtime = None
            
            if remote_mtime and local_mtime >= remote_mtime:
                return True, f"Local file is newer or same age"
    except Exception:
        # Skip mtime comparison if it fails
        pass
    
    # Optional checksum validation (slower but thorough)
    if verify_checksum:
        remote_checksum = getattr(remote_file_info, 'checksum', None) or getattr(remote_file_info, 'crc32', None)
        if remote_checksum:
            local_checksum = _compute_file_checksum(local_file_path)
            if local_checksum and local_checksum.lower() != str(remote_checksum).lower():
                return False, f"Checksum mismatch"
            elif local_checksum:
                return True, "Checksum verified"
    
    # Default: skip if file exists and size matches
    if remote_size is None or local_size == remote_size:
        return True, "File exists with matching size"
    
    return False, "Unknown verification failure"

def _download_dataset(o, dataset_code, output_dir, force=False, verify_checksum=False):
    """Download a specific dataset"""
    print(f"📥 Downloading dataset: {dataset_code}")
    
    try:
        # Get dataset object using permid/code
        print(f"🔍 Getting dataset object...")
        dataset = o.get_dataset(dataset_code)
        
        if dataset is None:
            print(f"❌ Dataset {dataset_code} not found")
            return False
        
        print(f"✅ Found dataset: {dataset_code}")
        
        # Expand tilde in output directory path
        expanded_output_dir = os.path.expanduser(output_dir)
        
        # Create output directory
        output_path = Path(expanded_output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {output_path}")
        
        # Smart download with skip-existing logic
        if not force:
            try:
                # Get file list from dataset to check what needs downloading
                print(f"🔍 Analyzing files to download...")
                files = dataset.get_files(start_folder="/")
                
                skip_count = 0
                download_count = 0
                files_to_download = []
                
                if hasattr(files, 'iterrows'):
                    # DataFrame format
                    for _, file_info in files.iterrows():
                        file_path = getattr(file_info, 'pathInDataSet', None)
                        if file_path:
                            local_file_path = output_path / file_path.lstrip('/')
                            should_skip, reason = _should_skip_file(local_file_path, file_info, verify_checksum)
                            
                            if should_skip:
                                skip_count += 1
                                print(f"⏭️  Skipping {file_path} ({reason})")
                            else:
                                download_count += 1
                                files_to_download.append(file_path)
                                print(f"📥 Will download {file_path} ({reason})")
                else:
                    # List format - fallback to simple existence check
                    for file_info in files:
                        file_path = getattr(file_info, 'pathInDataSet', str(file_info))
                        local_file_path = output_path / file_path.lstrip('/')
                        should_skip, reason = _should_skip_file(local_file_path, file_info, verify_checksum)
                        
                        if should_skip:
                            skip_count += 1
                            print(f"⏭️  Skipping {file_path} ({reason})")
                        else:
                            download_count += 1
                            files_to_download.append(file_path)
                            print(f"📥 Will download {file_path} ({reason})")
                
                print(f"📊 Analysis complete: {skip_count} files to skip, {download_count} files to download")
                
                if download_count == 0:
                    print(f"✅ All files already exist and are up-to-date!")
                    return True
                    
            except Exception as analysis_error:
                print(f"⚠️ Could not analyze files individually: {analysis_error}")
                print(f"🚀 Falling back to full dataset download...")
                files_to_download = None
        else:
            print(f"🚀 Force mode: downloading all files...")
            files_to_download = None
        
        try:
            # Download the dataset (PyBIS will handle individual files)
            if files_to_download is None:
                print(f"🚀 Starting full dataset download...")
                dataset.download(destination=str(output_path))
            else:
                print(f"🚀 Starting selective download of {len(files_to_download)} files...")
                dataset.download(destination=str(output_path))
            
            # Check if download was successful by looking for created files
            downloaded_files = list(output_path.rglob('*'))
            file_count = len([f for f in downloaded_files if f.is_file()])
            
            if file_count > 0:
                print(f"✅ Download complete: {file_count} total files in {output_path}")
                
                # Show some downloaded files
                print("📂 Files in dataset:")
                for f in downloaded_files[:5]:
                    if f.is_file():
                        size = f.stat().st_size
                        print(f"  📄 {f.relative_to(output_path)} ({size} bytes)")
                
                if file_count > 5:
                    print(f"  ... and {file_count - 5} more files")
                
                return True
            else:
                print("⚠️ Download completed but no files found")
                return False
                
        except Exception as download_error:
            print(f"❌ Download failed: {download_error}")
            return False
        
    except Exception as e:
        print(f"❌ Failed to get dataset: {e}")
        return False

def _list_dataset_files(o, dataset_code):
    """List files in a dataset"""
    print(f"📋 Listing files in dataset: {dataset_code}")
    
    try:
        # Get dataset object using the same method as download
        dataset = o.get_dataset(dataset_code)
        
        if dataset is None:
            print(f"❌ Dataset {dataset_code} not found")
            return
        
        # Try to get file list using PyBIS methods
        try:
            files = dataset.get_files(start_folder="/")
            print(f"Found {len(files)} files:")
            
            if hasattr(files, 'iterrows'):
                # DataFrame
                for i, (idx, file_info) in enumerate(files.iterrows()):
                    file_path = getattr(file_info, 'pathInDataSet', f'file_{i}')
                    file_size = getattr(file_info, 'fileLength', 'Unknown size')
                    print(f"  📄 {file_path} ({file_size} bytes)")
            else:
                # List or other format
                for i, file_info in enumerate(files):
                    file_path = getattr(file_info, 'pathInDataSet', f'file_{i}')
                    file_size = getattr(file_info, 'fileLength', 'Unknown size')
                    print(f"  📄 {file_path} ({file_size} bytes)")
                    
        except Exception as files_error:
            print(f"⚠️ Could not get detailed file list: {files_error}")
            
            # Fallback: try file_list attribute
            try:
                if hasattr(dataset, 'file_list'):
                    files = dataset.file_list
                    print(f"Found {len(files)} files (basic list):")
                    for i, file_path in enumerate(files):
                        print(f"  📄 {file_path}")
                else:
                    print("❌ No file listing method available")
            except Exception as fallback_error:
                print(f"❌ Fallback file listing failed: {fallback_error}")
                
    except Exception as e:
        print(f"❌ Failed to list files: {e}")

def _show_spaces_info(o):
    """Show information about all spaces"""
    print("🌌 Spaces Overview")
    print("=" * 50)
    
    try:
        spaces = o.get_spaces()
        print(f"Total spaces: {len(spaces)}")
        
        if len(spaces) > 0:
            if hasattr(spaces, 'head'):
                for i, (idx, space) in enumerate(spaces.iterrows()):
                    code = getattr(space, 'code', 'N/A')
                    description = getattr(space, 'description', 'No description') or 'No description'
                    print(f"\n📁 Space: {code}")
                    print(f"   Description: {description}")
                    
                    # Get projects in space
                    try:
                        projects = o.get_projects(space=code)
                        print(f"   Projects: {len(projects)}")
                    except:
                        print(f"   Projects: Unable to retrieve")
            else:
                for space in spaces:
                    code = getattr(space, 'code', 'N/A')
                    description = getattr(space, 'description', 'No description') or 'No description'
                    print(f"\n📁 Space: {code}")
                    print(f"   Description: {description}")
                    
    except Exception as e:
        print(f"❌ Failed to retrieve spaces: {e}")

def _show_dataset_info(o, dataset_code, show_lineage=False):
    """Show detailed information about a dataset"""
    print(f"📊 Dataset Information: {dataset_code}")
    print("=" * 50)
    
    try:
        datasets = o.get_datasets(code=dataset_code)
        if len(datasets) == 0:
            print(f"❌ Dataset {dataset_code} not found")
            return
            
        dataset = datasets.iloc[0] if hasattr(datasets, 'iloc') else datasets[0]
        
        # Basic info
        code = getattr(dataset, 'code', 'N/A')
        ds_type = getattr(dataset, 'type', 'N/A')
        registration_date = getattr(dataset, 'registrationDate', 'N/A')
        
        print(f"Code: {code}")
        print(f"Type: {ds_type}")
        print(f"Registration Date: {registration_date}")
        
        # Properties
        if hasattr(dataset, 'properties') and dataset.properties:
            print(f"\n🏷️ Properties:")
            props = dataset.properties
            if hasattr(props, 'items'):
                for key, value in props.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {props}")
        
        # Files  
        try:
            # Use the dataset object to get files
            if hasattr(dataset, 'file_list') and dataset.file_list is not None:
                files = dataset.file_list
                print(f"\n📂 Files: {len(files)}")
                for i, file_path in enumerate(files[:5]):  # Show first 5 files
                    print(f"  📄 {file_path}")
                
                if len(files) > 5:
                    print(f"  ... and {len(files) - 5} more files")
            else:
                print(f"\n📂 Files: File list not available")
        except Exception as file_error:
            print(f"\n📂 Files: Unable to retrieve ({file_error})")
        
        # Show parent-child relationships if requested
        if show_lineage:
            _show_dataset_lineage(o, dataset, dataset_code)
            
    except Exception as e:
        print(f"❌ Failed to retrieve dataset info: {e}")

def _show_dataset_lineage(o, dataset, dataset_code):
    """Show parent-child relationships for a dataset - optimized approach"""
    print(f"\n🌳 Dataset Lineage:")
    
    # Try optimized search first (should be faster than dataset.get_parents())
    try:
        print(f"  🔍 Checking parents via optimized search...")
        parents = o.get_datasets(withChildren=dataset_code)
        if len(parents) > 0:
            display_limit = min(5, len(parents))
            print(f"  📤 Parents ({len(parents)}):")
            
            if hasattr(parents, 'iterrows'):
                for i, (idx, parent) in enumerate(parents.head(display_limit).iterrows()):
                    parent_code = getattr(parent, 'code', 'N/A')
                    parent_type = getattr(parent, 'type', 'Unknown')
                    print(f"    ↳ {parent_code} ({parent_type})")
            else:
                for parent in parents[:display_limit]:
                    parent_code = getattr(parent, 'code', str(parent))
                    parent_type = getattr(parent, 'type', 'Unknown')
                    print(f"    ↳ {parent_code} ({parent_type})")
            
            if len(parents) > display_limit:
                print(f"    ↳ ... and {len(parents) - display_limit} more parents")
        else:
            print(f"  📤 Parents: None")
    except Exception as parent_error:
        print(f"  📤 Parents: Optimized search failed, trying fallback... ({parent_error})")
        try:
            parents = dataset.get_parents()
            if parents:
                print(f"  📤 Parents ({len(parents)}) [fallback]:")
                for parent in parents[:3]:  # Limit to 3
                    parent_code = getattr(parent, 'code', str(parent))
                    parent_type = getattr(parent, 'type', 'Unknown')
                    print(f"    ↳ {parent_code} ({parent_type})")
            else:
                print(f"  📤 Parents: None")
        except Exception as fallback_error:
            print(f"  📤 Parents: Unable to retrieve ({fallback_error})")
    
    try:
        print(f"  🔍 Checking children via optimized search...")
        children = o.get_datasets(withParents=dataset_code)
        if len(children) > 0:
            display_limit = min(5, len(children))
            print(f"  📥 Children ({len(children)}):")
            
            if hasattr(children, 'iterrows'):
                for i, (idx, child) in enumerate(children.head(display_limit).iterrows()):
                    child_code = getattr(child, 'code', 'N/A')
                    child_type = getattr(child, 'type', 'Unknown')
                    print(f"    ↳ {child_code} ({child_type})")
            else:
                for child in children[:display_limit]:
                    child_code = getattr(child, 'code', str(child))
                    child_type = getattr(child, 'type', 'Unknown')
                    print(f"    ↳ {child_code} ({child_type})")
            
            if len(children) > display_limit:
                print(f"    ↳ ... and {len(children) - display_limit} more children")
        else:
            print(f"  📥 Children: None")
    except Exception as child_error:
        print(f"  📥 Children: Optimized search failed, trying fallback... ({child_error})")
        try:
            children = dataset.get_children()
            if children:
                print(f"  📥 Children ({len(children)}) [fallback]:")
                for child in children[:3]:  # Limit to 3
                    child_code = getattr(child, 'code', str(child))
                    child_type = getattr(child, 'type', 'Unknown')
                    print(f"    ↳ {child_code} ({child_type})")
            else:
                print(f"  📥 Children: None")
        except Exception as fallback_error:
            print(f"  📥 Children: Unable to retrieve ({fallback_error})")

def _show_sample_info(o, sample_code):
    """Show detailed information about a sample"""
    print(f"🧪 Sample Information: {sample_code}")
    print("=" * 50)
    
    try:
        samples = o.get_samples(code=sample_code)
        if len(samples) == 0:
            print(f"❌ Sample {sample_code} not found")
            return
            
        sample = samples.iloc[0] if hasattr(samples, 'iloc') else samples[0]
        
        # Basic info
        code = getattr(sample, 'code', 'N/A')
        sample_type = getattr(sample, 'type', 'N/A')
        registration_date = getattr(sample, 'registrationDate', 'N/A')
        
        print(f"Code: {code}")
        print(f"Type: {sample_type}")
        print(f"Registration Date: {registration_date}")
        
        # Properties
        if hasattr(sample, 'properties') and sample.properties:
            print(f"\n🏷️ Properties:")
            props = sample.properties
            if hasattr(props, 'items'):
                for key, value in props.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {props}")
                
        # Related datasets
        try:
            datasets = o.get_datasets(sample=sample_code)
            print(f"\n📊 Related Datasets: {len(datasets)}")
            for i, ds in enumerate(datasets[:5] if hasattr(datasets, '__getitem__') else datasets):
                ds_code = getattr(ds, 'code', f'dataset_{i}')
                ds_type = getattr(ds, 'type', 'Unknown')
                print(f"  📊 {ds_code} ({ds_type})")
            
            if hasattr(datasets, '__len__') and len(datasets) > 5:
                print(f"  ... and {len(datasets) - 5} more datasets")
        except Exception as ds_error:
            print(f"\n📊 Related Datasets: Unable to retrieve ({ds_error})")
            
    except Exception as e:
        print(f"❌ Failed to retrieve sample info: {e}")

def _list_collection_datasets(o, collection_path, limit=None):
    """List all datasets in a collection"""
    print(f"📋 Listing datasets in collection: {collection_path}")
    
    try:
        # Try to get the collection and its datasets
        collection = o.get_collection(collection_path)
        
        if collection is None:
            print(f"❌ Collection {collection_path} not found")
            return
        
        print(f"✅ Found collection: {collection_path}")
        
        # Get datasets in the collection
        datasets = o.get_datasets(collection=collection_path)
        
        if hasattr(datasets, '__len__'):
            total_count = len(datasets)
        else:
            total_count = "Unknown"
        
        print(f"📊 Found {total_count} datasets in collection")
        
        # Apply limit if specified
        datasets_to_show = datasets
        if limit is not None and hasattr(datasets, '__getitem__'):
            datasets_to_show = datasets[:limit]
            print(f"📄 Showing first {limit} datasets:")
        
        # Display datasets
        if hasattr(datasets_to_show, 'iterrows'):
            for i, (idx, ds) in enumerate(datasets_to_show.iterrows()):
                code = getattr(ds, 'code', f'dataset_{i}')
                ds_type = getattr(ds, 'type', 'Unknown')
                reg_date = getattr(ds, 'registrationDate', 'Unknown')
                print(f"  📊 {code} ({ds_type}) - {reg_date}")
        else:
            for i, ds in enumerate(datasets_to_show):
                code = getattr(ds, 'code', f'dataset_{i}')
                ds_type = getattr(ds, 'type', 'Unknown')
                reg_date = getattr(ds, 'registrationDate', 'Unknown')
                print(f"  📊 {code} ({ds_type}) - {reg_date}")
                
        if limit is not None and hasattr(datasets, '__len__') and len(datasets) > limit:
            print(f"  ... and {len(datasets) - limit} more datasets")
            
    except Exception as e:
        print(f"❌ Failed to list collection datasets: {e}")

def _download_collection_datasets(o, collection_path, output_dir, limit=None, force=False, verify_checksum=False):
    """Download all datasets from a collection"""
    print(f"📦 Downloading datasets from collection: {collection_path}")
    
    try:
        # First, get the list of datasets
        collection = o.get_collection(collection_path)
        
        if collection is None:
            print(f"❌ Collection {collection_path} not found")
            return False
        
        datasets = o.get_datasets(collection=collection_path)
        
        if hasattr(datasets, '__len__'):
            total_count = len(datasets)
            if total_count == 0:
                print("📄 No datasets found in collection")
                return True
        else:
            total_count = "Unknown"
        
        print(f"📊 Found {total_count} datasets in collection")
        
        # Apply limit if specified
        datasets_to_download = datasets
        if limit is not None and hasattr(datasets, '__getitem__'):
            datasets_to_download = datasets[:limit]
            print(f"📄 Downloading first {limit} datasets")
        
        success_count = 0
        failed_count = 0
        
        # Download each dataset
        if hasattr(datasets_to_download, 'iterrows'):
            for i, (idx, ds) in enumerate(datasets_to_download.iterrows()):
                code = getattr(ds, 'code', f'dataset_{i}')
                print(f"\n📥 [{i+1}/{limit or total_count}] Downloading: {code}")
                
                if _download_dataset(o, code, output_dir, force=force, verify_checksum=verify_checksum):
                    success_count += 1
                else:
                    failed_count += 1
        else:
            for i, ds in enumerate(datasets_to_download):
                code = getattr(ds, 'code', f'dataset_{i}')
                print(f"\n📥 [{i+1}/{limit or total_count}] Downloading: {code}")
                
                if _download_dataset(o, code, output_dir, force=force, verify_checksum=verify_checksum):
                    success_count += 1
                else:
                    failed_count += 1
        
        print(f"\n✅ Collection download summary:")
        print(f"   📊 Successful downloads: {success_count}")
        print(f"   ❌ Failed downloads: {failed_count}")
        print(f"   📁 Output directory: {os.path.expanduser(output_dir)}")
        
        return failed_count == 0
        
    except Exception as e:
        print(f"❌ Failed to download collection datasets: {e}")
        return False

# ============================================================================
# UPLOAD INFRASTRUCTURE - REFACTORED
# ============================================================================

class OpenBISUploader:
    """Base class for uploading files to OpenBIS with common functionality"""
    
    def __init__(self, connection):
        self.o = connection
    
    def upload_file(self, file_path, dataset_type, collection, name=None, notes=None, 
                   additional_files=None, parent_datasets=None, dry_run=False, **kwargs):
        """Common upload workflow for all file types"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Parse metadata specific to file type
        metadata = self.parse_metadata(file_path, **kwargs)
        
        # Generate human-readable name
        human_readable_name = self.generate_name(file_path, metadata, name)
        
        if dry_run:
            return self._show_dry_run(file_path, human_readable_name, collection, 
                                    dataset_type, notes, metadata, additional_files, parent_datasets)
        
        # Perform actual upload
        return self._perform_upload(file_path, dataset_type, collection, 
                                  human_readable_name, notes, metadata, additional_files, parent_datasets)
    
    def parse_metadata(self, file_path, **kwargs):
        """Override in subclasses to extract file-specific metadata"""
        return {}
    
    def generate_name(self, file_path, metadata, custom_name):
        """Override in subclasses for file-specific naming"""
        return custom_name or file_path.stem
    
    def get_property_mapping(self, dataset_type):
        """Get property mapping for dataset type"""
        return PROPERTY_MAPPINGS.get(dataset_type, PROPERTY_MAPPINGS['default'])
    
    def _show_dry_run(self, file_path, human_readable_name, collection, dataset_type, 
                     notes, metadata, additional_files, parent_datasets):
        """Display what would be uploaded without actually uploading"""
        print(f"\n🔍 Dry run - would upload:")
        print(f"  File: {file_path}")
        print(f"  Name: {human_readable_name}")
        print(f"  Collection: {collection}")
        print(f"  Dataset type: {dataset_type}")
        if notes:
            print(f"  Notes: {notes}")
        if additional_files:
            print(f"  Additional files: {len(additional_files)}")
        if parent_datasets:
            print(f"  Parent datasets: {', '.join(parent_datasets)}")
        print(f"  Metadata fields: {len(metadata)}")
        return True
    
    def _perform_upload(self, file_path, dataset_type, collection, human_readable_name, 
                       notes, metadata, additional_files, parent_datasets):
        """Perform the actual upload to OpenBIS"""
        print(f"\n🚀 Uploading to OpenBIS...")
        print(f"📁 File: {file_path}")
        print(f"📂 Collection: {collection}")
        print(f"🏷️  Dataset type: {dataset_type}")
        
        # Prepare files list
        files_to_upload = [str(file_path)]
        if additional_files:
            files_to_upload.extend([str(f) for f in additional_files if Path(f).exists()])
        
        # Create dataset (collection and experiment are the same in PyBIS)
        dataset = self.o.new_dataset(
            type=dataset_type,
            experiment=collection,
            files=files_to_upload
        )
        
        # Build and apply properties
        props = self._build_properties(dataset_type, human_readable_name, metadata, notes)
        for prop, value in props.items():
            try:
                dataset.props[prop] = value
                print(f"  ✅ {prop}: {value}")
            except Exception as e:
                print(f"  ⚠️  Warning: Could not set {prop}: {e}")
        
        # Save dataset
        print(f"💾 Saving dataset...")
        dataset.save()
        
        # Link to parent datasets if specified
        if parent_datasets:
            print(f"🔗 Linking to parent datasets...")
            try:
                dataset.add_parents(parent_datasets)
                print(f"  ✅ Linked to {len(parent_datasets)} parent dataset(s): {', '.join(parent_datasets)}")
            except Exception as e:
                print(f"  ⚠️  Warning: Could not link to parent datasets: {e}")
        
        print(f"✅ Upload completed successfully!")
        print(f"📊 Dataset ID: {dataset.code}")
        print(f"📈 Metadata fields: {len(metadata)}")
        print(f"📁 Files uploaded: {len(files_to_upload)}")
        
        return dataset
    
    def _build_properties(self, dataset_type, human_readable_name, metadata, notes):
        """Build dataset properties using mapping registry"""
        props = {}
        mapping = self.get_property_mapping(dataset_type)
        
        # Apply basic properties
        if 'name' in mapping:
            prop_name, _ = mapping['name']
            props[prop_name] = human_readable_name
        
        # Apply metadata-based properties
        for meta_key, value in metadata.items():
            if meta_key.lower() in mapping:
                prop_name, converter = mapping[meta_key.lower()]
                try:
                    props[prop_name] = converter(value)
                except (ValueError, TypeError):
                    print(f"⚠️  Warning: Could not convert {meta_key}={value}")
        
        # Handle special comprehensive description for BIO_DB
        if 'comprehensive_description' in mapping:
            prop_name, converter = mapping['comprehensive_description']
            if converter == 'build_comprehensive_description':
                props[prop_name] = self._build_comprehensive_description(metadata)
        
        # Build comprehensive notes (skip for BIO_DB as it doesn't support notes)
        if dataset_type != 'BIO_DB':
            notes_content = self._build_notes(dataset_type, human_readable_name, notes, metadata)
            if notes_content:
                props['notes'] = notes_content
        
        return props
    
    def _build_comprehensive_description(self, metadata):
        """Build comprehensive description for product.description field (BIO_DB format)"""
        parts = []
        
        # Always include entries count first
        if 'N_ENTRIES' in metadata:
            parts.append(f"{metadata['N_ENTRIES']} entries")
        
        # Add primary species
        if 'PRIMARY_SPECIES' in metadata:
            parts.append(f"Primary species: {metadata['PRIMARY_SPECIES']}")
        
        # Add species count
        if 'SPECIES_COUNT' in metadata:
            count = metadata['SPECIES_COUNT']
            species_text = "species" if count != 1 else "species" 
            parts.append(f"{count} {species_text}")
        
        # Add file size
        if 'FILE_SIZE_MB' in metadata:
            parts.append(f"{metadata['FILE_SIZE_MB']} MB")
        
        return ' | '.join(parts) if parts else None

    def _build_notes(self, dataset_type, human_readable_name, user_notes, metadata):
        """Build comprehensive notes field"""
        parts = []
        
        if user_notes:
            parts.append(f"Description: {user_notes}")
        
        # Add key metadata to notes
        for key, value in metadata.items():
            if key not in ['VERSION', 'N_ENTRIES']:  # Skip properties already in main fields
                parts.append(f"{key}: {value}")
        
        return ' | '.join(parts) if parts else None


class FASTAUploader(OpenBISUploader):
    """FASTA database file uploader"""
    
    def parse_metadata(self, file_path, version=None, **kwargs):
        """Extract metadata from FASTA file"""
        return parse_fasta_metadata(str(file_path), version)
    
    def generate_name(self, file_path, metadata, custom_name):
        """Generate FASTA-specific name"""
        if custom_name:
            return custom_name
        
        name = file_path.stem
        if 'VERSION' in metadata:
            name += f" v{metadata['VERSION']}"
        if 'PRIMARY_SPECIES' in metadata:
            name += f" ({metadata['PRIMARY_SPECIES']})"
        return name


class SpectralLibraryUploader(OpenBISUploader):
    """Spectral library file uploader"""
    
    def parse_metadata(self, file_path, log_file=None, **kwargs):
        """Extract metadata from DIA-NN log file"""
        if log_file and Path(log_file).exists():
            return parse_diann_log(log_file)
        return {}
    
    def generate_name(self, file_path, metadata, custom_name):
        """Generate library-specific name"""
        if custom_name:
            return custom_name
        
        name_parts = [file_path.stem]
        
        if 'FASTA_DATABASE' in metadata:
            fasta_name = Path(metadata['FASTA_DATABASE']).stem
            name_parts.append(f"({fasta_name})")
        
        if 'N_PROTEINS' in metadata:
            name_parts.append(f"{metadata['N_PROTEINS']} proteins")
        
        if 'DIANN_VERSION' in metadata:
            name_parts.append(f"DIA-NN v{metadata['DIANN_VERSION']}")
        
        return ' '.join(name_parts)
    
    def upload_file(self, file_path, dataset_type, collection, log_file=None, **kwargs):
        """Override to handle log file as additional file"""
        additional_files = [log_file] if log_file and Path(log_file).exists() else None
        return super().upload_file(file_path, dataset_type, collection, 
                                 additional_files=additional_files, log_file=log_file, **kwargs)


# Property mapping registry for different dataset types
PROPERTY_MAPPINGS = {
    'BIO_DB': {
        'name': ('$name', str),
        'version': ('version', str),
        'comprehensive_description': ('product.description', 'build_comprehensive_description'),
    },
    'SPECTRAL_LIBRARY': {
        'name': ('notes', str),  # SPECTRAL_LIBRARY doesn't support $name
        'n_proteins': ('n_proteins', int),
        'n_precursors': ('n_peptides', int),
    },
    'UNKNOWN': {
        'name': ('$name', str),
    },
    'default': {
        'name': ('$name', str),
    }
}


# File type detection
def detect_file_type(file_path):
    """Detect file type from extension and content"""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    if suffix in ['.fasta', '.fa', '.fas']:
        return 'fasta'
    elif suffix in ['.tsv', '.csv'] and 'lib' in file_path.stem.lower():
        return 'spectral_library'
    elif suffix in ['.speclib', '.sptxt']:
        return 'spectral_library'
    
    return 'unknown'


def get_uploader(file_type, connection):
    """Factory function to get appropriate uploader"""
    uploaders = {
        'fasta': FASTAUploader,
        'spectral_library': SpectralLibraryUploader,
        'unknown': OpenBISUploader,
    }
    
    uploader_class = uploaders.get(file_type, OpenBISUploader)
    return uploader_class(connection)


def pybis_upload_main(args):
    """Unified PyBIS Upload Tool - Auto-detects file type and uploads accordingly"""
    parser = argparse.ArgumentParser(description='Upload files to OpenBIS with automatic type detection')
    parser.add_argument('file', help='File to upload')
    parser.add_argument('--type', choices=['auto', 'fasta', 'spectral_library'], default='auto',
                       help='File type (default: auto-detect)')
    parser.add_argument('--collection', help='OpenBIS collection path')
    parser.add_argument('--dataset-type', help='OpenBIS dataset type (auto-detected if not specified)')
    parser.add_argument('--name', help='Human-readable name for the dataset')
    parser.add_argument('--version', help='Version identifier (for databases)')
    parser.add_argument('--log-file', help='DIA-NN log file for spectral libraries')
    parser.add_argument('--notes', help='Additional notes for the dataset')
    parser.add_argument('--parent-dataset', action='append', 
                       help='Parent dataset code (can be specified multiple times)')
    parser.add_argument('--auto-link', action='store_true', 
                       help='Automatically suggest parent datasets based on metadata')
    parser.add_argument('--dry-run', action='store_true', help='Preview upload without executing')
    
    parsed_args = parser.parse_args(args)
    
    # Auto-detect file type if needed
    file_type = parsed_args.type
    if file_type == 'auto':
        file_type = detect_file_type(parsed_args.file)
        print(f"🔍 Detected file type: {file_type}")
    
    # Set default collection and dataset type based on file type
    defaults = {
        'fasta': {'collection': '/DDB/CK/FASTA', 'dataset_type': 'BIO_DB'},
        'spectral_library': {'collection': '/DDB/CK/PREDSPECLIB', 'dataset_type': 'SPECTRAL_LIBRARY'},
        'unknown': {'collection': '/DDB/CK/UNKNOWN', 'dataset_type': 'UNKNOWN'},
    }
    
    collection = parsed_args.collection or defaults[file_type]['collection']
    dataset_type = parsed_args.dataset_type or defaults[file_type]['dataset_type']
    
    print(f"📤 PyBIS Unified Upload Tool")
    print(f"File type: {file_type}")
    print(f"Collection: {collection}")
    print(f"Dataset type: {dataset_type}")
    print("=" * 50)
    
    try:
        # Get connection
        o = get_openbis_connection()
        
        # Get appropriate uploader
        uploader = get_uploader(file_type, o)
        
        # Upload file with file-type specific handling
        kwargs = {
            'name': parsed_args.name,
            'notes': parsed_args.notes,
            'dry_run': parsed_args.dry_run
        }
        
        # Add file-type specific parameters
        if file_type == 'fasta':
            kwargs['version'] = parsed_args.version
        elif file_type == 'spectral_library':
            kwargs['log_file'] = parsed_args.log_file
        
        # Handle auto-linking (enhanced parent-child relationships)
        parent_datasets = parsed_args.parent_dataset or []
        if parsed_args.auto_link:
            print("🔗 Auto-linking: Searching for potential parent datasets...")
            suggested_parents = _suggest_parent_datasets(o, parsed_args.file, file_type, kwargs)
            if suggested_parents:
                confirmed_parents = _interactive_parent_linking(suggested_parents)
                parent_datasets.extend(confirmed_parents)
        
        result = uploader.upload_file(
            parsed_args.file,
            dataset_type,
            collection,
            parent_datasets=parent_datasets if parent_datasets else None,
            **kwargs
        )
        
        return result is not None
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False


# ============================================================================
# LEGACY UPLOAD HELPERS (TO BE REPLACED)
# ============================================================================

def _generate_library_name(custom_name, library_path, metadata):
    """Generate human-readable library name from custom input or metadata"""
    if custom_name:
        return custom_name
    
    # Auto-generate name from metadata and filename
    library_basename = library_path.stem
    name_parts = [library_basename]
    
    if 'FASTA_DATABASE' in metadata:
        fasta_name = Path(metadata['FASTA_DATABASE']).stem
        name_parts.append(f"({fasta_name})")
    
    if 'N_PROTEINS' in metadata:
        name_parts.append(f"{metadata['N_PROTEINS']} proteins")
    
    if 'DIANN_VERSION' in metadata:
        name_parts.append(f"DIA-NN v{metadata['DIANN_VERSION']}")
        
    return ' '.join(name_parts)

def _build_dataset_properties(dataset_type, human_readable_name, metadata):
    """Build dataset properties dict based on OpenBIS schema constraints"""
    props = {}
    
    if dataset_type == 'SPECTRAL_LIBRARY':
        # SPECTRAL_LIBRARY supports: n_peptides, n_proteins, peptidefdr, notes
        if 'N_PROTEINS' in metadata:
            props['n_proteins'] = metadata['N_PROTEINS']
        
        if 'N_PRECURSORS' in metadata:
            props['n_peptides'] = metadata['N_PRECURSORS']
    
    elif dataset_type == 'BIO_DB':
        # BIO_DB supports: $name, version, product.description, location_status, irt_protein, contaminants, decoy_type
        props['$name'] = human_readable_name
        
        if 'VERSION' in metadata:
            props['version'] = metadata['VERSION']
            
        # Use product.description for detailed metadata
        description_parts = []
        if 'N_ENTRIES' in metadata:
            description_parts.append(f"{metadata['N_ENTRIES']} entries")
        if 'PRIMARY_SPECIES' in metadata:
            description_parts.append(f"Primary species: {metadata['PRIMARY_SPECIES']}")
        if 'SPECIES_COUNT' in metadata:
            description_parts.append(f"{metadata['SPECIES_COUNT']} species")
        if 'FILE_SIZE_MB' in metadata:
            description_parts.append(f"{metadata['FILE_SIZE_MB']} MB")
            
        if description_parts:
            props['product.description'] = ' | '.join(description_parts)
    
    elif dataset_type == 'UNKNOWN':
        # UNKNOWN type supports: $name, comment, location_status
        props['$name'] = human_readable_name
    
    else:
        # Try $name for other dataset types
        props['$name'] = human_readable_name
    
    return props

def _build_dataset_notes(dataset_type, human_readable_name, user_notes, metadata):
    """Build comprehensive notes field with human-readable name and metadata"""
    notes_parts = []
    
    # Add human-readable name based on dataset type
    if dataset_type == 'SPECTRAL_LIBRARY' and human_readable_name:
        notes_parts.append(f"Library: {human_readable_name}")
    elif dataset_type == 'BIO_DB' and human_readable_name:
        notes_parts.append(f"Database: {human_readable_name}")
    
    if user_notes:
        notes_parts.append(f"Description: {user_notes}")
    
    # Add dataset-specific metadata
    if dataset_type == 'SPECTRAL_LIBRARY':
        # SPECTRAL_LIBRARY metadata
        notes_parts.append(f"DIA-NN version: {metadata.get('DIANN_VERSION', 'Unknown')}")
        notes_parts.append(f"Generated: {metadata.get('GENERATION_DATE', 'Unknown')}")
        notes_parts.append(f"FASTA: {metadata.get('FASTA_DATABASE', 'Unknown')}")
        notes_parts.append(f"Method: {metadata.get('GENERATION_METHOD', 'Unknown')}")
        notes_parts.append(f"Precursors: {metadata.get('N_PRECURSORS', 'Unknown')}")
        notes_parts.append(f"Proteins: {metadata.get('N_PROTEINS', 'Unknown')}")
        notes_parts.append(f"Genes: {metadata.get('N_GENES', 'Unknown')}")
        
        # Add parameter details for spectral libraries
        param_details = []
        if 'MIN_PEPTIDE_LENGTH' in metadata and 'MAX_PEPTIDE_LENGTH' in metadata:
            param_details.append(f"Peptide length: {metadata['MIN_PEPTIDE_LENGTH']}-{metadata['MAX_PEPTIDE_LENGTH']}")
        if 'MIN_PRECURSOR_MZ' in metadata and 'MAX_PRECURSOR_MZ' in metadata:
            param_details.append(f"Precursor m/z: {metadata['MIN_PRECURSOR_MZ']}-{metadata['MAX_PRECURSOR_MZ']}")
        if 'MODIFICATIONS' in metadata:
            param_details.append(f"Modifications: {metadata['MODIFICATIONS']}")
        
        if param_details:
            notes_parts.append(f"Parameters: {'; '.join(param_details)}")
    
    elif dataset_type == 'BIO_DB':
        # BIO_DB metadata
        if 'VERSION' in metadata:
            notes_parts.append(f"Version: {metadata['VERSION']}")
        notes_parts.append(f"Entries: {metadata.get('N_ENTRIES', 'Unknown')}")
        if 'FILE_SIZE_MB' in metadata:
            notes_parts.append(f"Size: {metadata['FILE_SIZE_MB']} MB")
        if 'SPECIES_COUNT' in metadata:
            notes_parts.append(f"Species: {metadata['SPECIES_COUNT']}")
        if 'SPECIES_BREAKDOWN' in metadata:
            notes_parts.append(f"Species breakdown: {metadata['SPECIES_BREAKDOWN']}")
    
    return ' | '.join(notes_parts) if notes_parts else None

# ============================================================================
# DIANN LOG PARSING
# ============================================================================

def parse_diann_log(log_file):
    """Extract metadata from DIA-NN log file for spectral library upload"""
    metadata = {}
    
    try:
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # Extract version and compile info
        if match := re.search(r'DIA-NN ([\d.]+)', log_content):
            metadata['DIANN_VERSION'] = match.group(1)
        
        if match := re.search(r'Compiled on (.+)', log_content):
            metadata['COMPILE_DATE'] = match.group(1).strip()
        
        if match := re.search(r'Current date and time: (.+)', log_content):
            metadata['GENERATION_DATE'] = match.group(1).strip()
        
        # Extract library statistics
        if match := re.search(r'(\d+) precursors generated', log_content):
            metadata['N_PRECURSORS'] = int(match.group(1))
        
        if match := re.search(r'Library contains (\d+) proteins', log_content):
            metadata['N_PROTEINS'] = int(match.group(1))
        
        if match := re.search(r'and (\d+) genes', log_content):
            metadata['N_GENES'] = int(match.group(1))
        
        # Extract FASTA database info
        if match := re.search(r'--fasta ([^\s]+)', log_content):
            fasta_path = match.group(1)
            metadata['FASTA_DATABASE'] = os.path.basename(fasta_path)
            metadata['FASTA_PATH'] = fasta_path
        
        # Extract peptide parameters
        if match := re.search(r'--min-pep-len (\d+)', log_content):
            metadata['MIN_PEPTIDE_LENGTH'] = int(match.group(1))
        
        if match := re.search(r'--max-pep-len (\d+)', log_content):
            metadata['MAX_PEPTIDE_LENGTH'] = int(match.group(1))
        
        # Extract precursor parameters
        if match := re.search(r'--min-pr-mz (\d+)', log_content):
            metadata['MIN_PRECURSOR_MZ'] = int(match.group(1))
        
        if match := re.search(r'--max-pr-mz (\d+)', log_content):
            metadata['MAX_PRECURSOR_MZ'] = int(match.group(1))
        
        if match := re.search(r'--min-pr-charge (\d+)', log_content):
            metadata['MIN_PRECURSOR_CHARGE'] = int(match.group(1))
        
        if match := re.search(r'--max-pr-charge (\d+)', log_content):
            metadata['MAX_PRECURSOR_CHARGE'] = int(match.group(1))
        
        # Extract fragment parameters
        if match := re.search(r'--min-fr-mz (\d+)', log_content):
            metadata['MIN_FRAGMENT_MZ'] = int(match.group(1))
        
        if match := re.search(r'--max-fr-mz (\d+)', log_content):
            metadata['MAX_FRAGMENT_MZ'] = int(match.group(1))
        
        # Extract digestion parameters
        if match := re.search(r'--missed-cleavages (\d+)', log_content):
            metadata['MISSED_CLEAVAGES'] = int(match.group(1))
        
        if match := re.search(r'--cut ([^\s]+)', log_content):
            metadata['CLEAVAGE_SITES'] = match.group(1)
        
        # Extract generation method
        generation_methods = []
        if 'Deep learning will be used' in log_content:
            generation_methods.append('Deep learning prediction')
        if '--gen-spec-lib' in log_content:
            generation_methods.append('In silico library generation')
        if '--predictor' in log_content:
            generation_methods.append('RT predictor')
        
        if generation_methods:
            metadata['GENERATION_METHOD'] = ', '.join(generation_methods)
        
        # Extract modifications
        modifications = []
        if 'Cysteine carbamidomethylation enabled' in log_content:
            modifications.append('Cysteine carbamidomethylation (fixed)')
        if '--met-excision' in log_content:
            modifications.append('N-terminal methionine excision')
        if '--unimod4' in log_content:
            modifications.append('Unimod modifications')
        
        if modifications:
            metadata['MODIFICATIONS'] = ', '.join(modifications)
        
        # Extract processing info
        if match := re.search(r'Thread number set to (\d+)', log_content):
            metadata['THREADS_USED'] = int(match.group(1))
        
        if match := re.search(r'Logical CPU cores: (\d+)', log_content):
            metadata['SYSTEM_CORES'] = int(match.group(1))
        
        return metadata
        
    except Exception as e:
        print(f"⚠️  Warning: Could not parse DIA-NN log file: {e}")
        return {}

# ============================================================================
# FASTA FILE PARSING
# ============================================================================

def parse_fasta_metadata(fasta_file, version=None):
    """Extract metadata from FASTA file for database upload"""
    metadata = {}
    species_counts = {}
    total_entries = 0
    
    try:
        with open(fasta_file, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    total_entries += 1
                    # Extract species information from header
                    # Common patterns: OS=Species name, [Species name], (Species name)
                    if 'OS=' in line:
                        # UniProt format: OS=Homo sapiens
                        species_match = re.search(r'OS=([^=]+?)(?:\s+[A-Z]{2}=|$)', line)
                        if species_match:
                            species = species_match.group(1).strip()
                            species_counts[species] = species_counts.get(species, 0) + 1
                    elif '[' in line and ']' in line:
                        # NCBI format: [Homo sapiens]
                        species_match = re.search(r'\[([^\]]+)\]', line)
                        if species_match:
                            species = species_match.group(1).strip()
                            species_counts[species] = species_counts.get(species, 0) + 1
                    elif '(' in line and ')' in line:
                        # Alternative format: (Homo sapiens)
                        species_match = re.search(r'\(([^)]+)\)', line)
                        if species_match:
                            species = species_match.group(1).strip()
                            # Filter out non-species info in parentheses
                            if not any(x in species.lower() for x in ['fragment', 'partial', 'predicted', 'uncharacterized']):
                                species_counts[species] = species_counts.get(species, 0) + 1
        
        metadata['N_ENTRIES'] = total_entries
        
        # Find most common species
        if species_counts:
            most_common_species = max(species_counts, key=species_counts.get)
            metadata['PRIMARY_SPECIES'] = most_common_species
            metadata['SPECIES_COUNT'] = len(species_counts)
            
            # Create species summary (top 5)
            top_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            species_summary = []
            for species, count in top_species:
                percentage = (count / total_entries) * 100
                species_summary.append(f"{species} ({count}, {percentage:.1f}%)")
            metadata['SPECIES_BREAKDOWN'] = '; '.join(species_summary)
        
        if version:
            metadata['VERSION'] = version
            
        # Extract file size
        fasta_path = Path(fasta_file)
        metadata['FILE_SIZE_MB'] = round(fasta_path.stat().st_size / (1024 * 1024), 2)
        
        return metadata
        
    except Exception as e:
        print(f"⚠️  Warning: Could not parse FASTA file: {e}")
        return {}

def pybis_upload_library_main(args):
    """PyBIS Upload Library Tool - Upload spectral libraries with metadata extraction"""
    parser = argparse.ArgumentParser(description='Upload spectral library to OpenBIS with metadata extraction')
    parser.add_argument('library_file', help='Spectral library file to upload')
    parser.add_argument('--log-file', help='DIA-NN log file for metadata extraction (also uploaded for reference)')
    parser.add_argument('--collection', default='/DDB/CK/PREDSPECLIB', 
                       help='OpenBIS collection path (default: /DDB/CK/PREDSPECLIB)')
    parser.add_argument('--dataset-type', default='SPECTRAL_LIBRARY',
                       help='Dataset type (default: SPECTRAL_LIBRARY)')
    parser.add_argument('--name', help='Human-readable name for the spectral library dataset')
    parser.add_argument('--notes', help='Additional notes for the dataset')
    parser.add_argument('--parent-dataset', action='append', 
                       help='Parent dataset code (can be specified multiple times)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show metadata that would be uploaded without actually uploading')
    
    parsed_args = parser.parse_args(args)
    
    # Use new upload infrastructure
    try:
        o = get_openbis_connection()
        uploader = SpectralLibraryUploader(o)
        
        result = uploader.upload_file(
            parsed_args.library_file,
            parsed_args.dataset_type,
            parsed_args.collection,
            name=parsed_args.name,
            notes=parsed_args.notes,
            parent_datasets=parsed_args.parent_dataset,
            log_file=parsed_args.log_file,
            dry_run=parsed_args.dry_run
        )
        
        return result is not None
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def pybis_upload_fasta_main(args):
    """PyBIS Upload FASTA Tool - Upload FASTA database files with metadata extraction"""
    parser = argparse.ArgumentParser(description='Upload FASTA database to OpenBIS with metadata extraction')
    parser.add_argument('fasta_file', help='FASTA database file to upload')
    parser.add_argument('--collection', default='/DDB/CK/FASTA', 
                       help='OpenBIS collection path (default: /DDB/CK/FASTA)')
    parser.add_argument('--dataset-type', default='BIO_DB',
                       help='Dataset type (default: BIO_DB)')
    parser.add_argument('--name', help='Human-readable name for the FASTA database')
    parser.add_argument('--version', help='Version or release identifier for the database')
    parser.add_argument('--notes', help='Additional notes for the dataset')
    parser.add_argument('--parent-dataset', action='append', 
                       help='Parent dataset code (can be specified multiple times)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show metadata that would be uploaded without actually uploading')
    
    parsed_args = parser.parse_args(args)
    
    # Use new upload infrastructure
    try:
        o = get_openbis_connection()
        uploader = FASTAUploader(o)
        
        result = uploader.upload_file(
            parsed_args.fasta_file,
            parsed_args.dataset_type,
            parsed_args.collection,
            name=parsed_args.name,
            notes=parsed_args.notes,
            parent_datasets=parsed_args.parent_dataset,
            version=parsed_args.version,
            dry_run=parsed_args.dry_run
        )
        
        return result is not None
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False