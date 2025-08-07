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
from pathlib import Path

def get_openbis_connection():
    """Get authenticated OpenBIS connection with token caching"""
    url = os.environ.get('OPENBIS_URL')
    username = os.environ.get('OPENBIS_USERNAME')
    password = os.environ.get('OPENBIS_PASSWORD')
    
    if not all([url, username, password]):
        print("❌ Missing OpenBIS credentials in environment")
        sys.exit(1)
    
    o = Openbis(url, verify_certificates=False)
    
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
    """PyBIS Search Tool - Search for experiments, samples, and datasets"""
    parser = argparse.ArgumentParser(description='Search OpenBIS for experiments, samples, and datasets')
    parser.add_argument('query', help='Search query (supports wildcards)')
    parser.add_argument('--type', choices=['experiments', 'samples', 'datasets', 'all'], 
                       default='all', help='What to search for')
    parser.add_argument('--limit', type=int, default=10, help='Maximum results to show')
    
    parsed_args = parser.parse_args(args)
    
    print(f"🔍 OpenBIS Search Tool")
    print(f"Query: {parsed_args.query}")
    print(f"Type: {parsed_args.type}")
    print("=" * 50)
    
    o = get_openbis_connection()
    
    if parsed_args.type in ['experiments', 'all']:
        _search_experiments(o, parsed_args.query)
        if parsed_args.type == 'all':
            print()
    
    if parsed_args.type in ['samples', 'all']:
        _search_samples(o, parsed_args.query)
        if parsed_args.type == 'all':
            print()
    
    if parsed_args.type in ['datasets', 'all']:
        _search_datasets(o, parsed_args.query)

def pybis_download_main(args):
    """PyBIS Download Tool - Download datasets and files"""
    parser = argparse.ArgumentParser(description='Download datasets and files from OpenBIS')
    parser.add_argument('dataset_code', help='Dataset code to download')
    parser.add_argument('--output', '-o', default='{{ data_base_dir }}/openbis/', 
                       help='Output directory (default: {{ data_base_dir }}/openbis/)')
    parser.add_argument('--list-only', action='store_true', 
                       help='Only list files, do not download')
    
    parsed_args = parser.parse_args(args)
    
    print(f"📦 OpenBIS Download Tool")
    print(f"Dataset: {parsed_args.dataset_code}")
    print(f"Output: {parsed_args.output}")
    print("=" * 50)
    
    o = get_openbis_connection()
    
    if parsed_args.list_only:
        _list_dataset_files(o, parsed_args.dataset_code)
    else:
        _download_dataset(o, parsed_args.dataset_code, parsed_args.output)

def pybis_download_collection_main(args):
    """PyBIS Download Collection Tool - Download all datasets from a collection"""
    parser = argparse.ArgumentParser(description='Download all datasets from an OpenBIS collection')
    parser.add_argument('collection', help='Collection path (required)')
    parser.add_argument('--output', '-o', default='{{ data_base_dir }}/openbis/', 
                       help='Output directory (default: {{ data_base_dir }}/openbis/)')
    parser.add_argument('--list-only', action='store_true', 
                       help='Only list datasets, do not download')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of datasets to download')
    
    parsed_args = parser.parse_args(args)
    
    print(f"📦 OpenBIS Collection Download Tool")
    print(f"Collection: {parsed_args.collection}")
    print(f"Output: {parsed_args.output}")
    print("=" * 50)
    
    o = get_openbis_connection()
    
    if parsed_args.list_only:
        _list_collection_datasets(o, parsed_args.collection, parsed_args.limit)
    else:
        _download_collection_datasets(o, parsed_args.collection, parsed_args.output, parsed_args.limit)

def pybis_info_main(args):
    """PyBIS Info Tool - Get detailed information about objects"""
    parser = argparse.ArgumentParser(description='Get detailed information about OpenBIS objects')
    parser.add_argument('--spaces', action='store_true', help='Show all spaces')
    parser.add_argument('--dataset', help='Show dataset information')
    parser.add_argument('--sample', help='Show sample information')
    
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
        _show_dataset_info(o, parsed_args.dataset)
    
    if parsed_args.sample:
        _show_sample_info(o, parsed_args.sample)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _search_experiments(o, query):
    """Search for experiments"""
    print(f"🔬 Searching experiments for: {query}")
    try:
        experiments = o.get_experiments(code=f"*{query}*")
        print(f"Found {len(experiments)} experiments")
        
        if len(experiments) > 0:
            if hasattr(experiments, 'head'):
                for i, (idx, exp) in enumerate(experiments.head(10).iterrows()):
                    code = getattr(exp, 'code', 'N/A')
                    exp_type = getattr(exp, 'type', 'N/A')
                    print(f"  - {code} ({exp_type})")
            else:
                for exp in experiments[:10]:
                    code = getattr(exp, 'code', 'N/A')
                    exp_type = getattr(exp, 'type', 'N/A')
                    print(f"  - {code} ({exp_type})")
                    
    except Exception as e:
        print(f"❌ Experiment search failed: {e}")

def _search_samples(o, query):
    """Search for samples"""
    print(f"🧪 Searching samples for: {query}")
    try:
        samples = o.get_samples(code=f"*{query}*")
        print(f"Found {len(samples)} samples")
        
        if len(samples) > 0:
            if hasattr(samples, 'head'):
                for i, (idx, sample) in enumerate(samples.head(10).iterrows()):
                    code = getattr(sample, 'code', 'N/A')
                    sample_type = getattr(sample, 'type', 'N/A')
                    print(f"  - {code} ({sample_type})")
            else:
                for sample in samples[:10]:
                    code = getattr(sample, 'code', 'N/A')
                    sample_type = getattr(sample, 'type', 'N/A')
                    print(f"  - {code} ({sample_type})")
                    
    except Exception as e:
        print(f"❌ Sample search failed: {e}")

def _search_datasets(o, query):
    """Search for datasets"""
    print(f"📊 Searching datasets for: {query}")
    try:
        datasets = o.get_datasets(code=f"*{query}*")
        print(f"Found {len(datasets)} datasets")
        
        if len(datasets) > 0:
            if hasattr(datasets, 'head'):
                for i, (idx, ds) in enumerate(datasets.head(10).iterrows()):
                    code = getattr(ds, 'code', 'N/A')
                    ds_type = getattr(ds, 'type', 'N/A')
                    print(f"  - {code} ({ds_type})")
            else:
                for ds in datasets[:10]:
                    code = getattr(ds, 'code', 'N/A')
                    ds_type = getattr(ds, 'type', 'N/A')
                    print(f"  - {code} ({ds_type})")
                    
    except Exception as e:
        print(f"❌ Dataset search failed: {e}")

def _download_dataset(o, dataset_code, output_dir):
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
        
        try:
            # Use PyBIS download method (following user's pattern)
            print(f"🚀 Starting download...")
            dataset.download(destination=str(output_path))
            
            # Check if download was successful by looking for created files
            downloaded_files = list(output_path.rglob('*'))
            file_count = len([f for f in downloaded_files if f.is_file()])
            
            if file_count > 0:
                print(f"✅ Download complete: {file_count} files downloaded to {output_path}")
                
                # Show some downloaded files
                print("📂 Downloaded files:")
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

def _show_dataset_info(o, dataset_code):
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
            files = o.get_dataset_files(dataset_code)
            print(f"\n📂 Files: {len(files)}")
            for i, file_info in enumerate(files[:5]):  # Show first 5 files
                try:
                    file_path = getattr(file_info, 'path', f'file_{i}') if hasattr(file_info, 'path') else f'file_{i}'
                    file_size = getattr(file_info, 'size', 'Unknown') if hasattr(file_info, 'size') else 'Unknown'
                    print(f"  📄 {file_path} ({file_size} bytes)")
                except:
                    print(f"  📄 File {i+1}")
            
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")
        except Exception as file_error:
            print(f"\n📂 Files: Unable to retrieve ({file_error})")
            
    except Exception as e:
        print(f"❌ Failed to retrieve dataset info: {e}")

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

def _download_collection_datasets(o, collection_path, output_dir, limit=None):
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
                
                if _download_dataset(o, code, output_dir):
                    success_count += 1
                else:
                    failed_count += 1
        else:
            for i, ds in enumerate(datasets_to_download):
                code = getattr(ds, 'code', f'dataset_{i}')
                print(f"\n📥 [{i+1}/{limit or total_count}] Downloading: {code}")
                
                if _download_dataset(o, code, output_dir):
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
                   additional_files=None, dry_run=False, **kwargs):
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
                                    dataset_type, notes, metadata, additional_files)
        
        # Perform actual upload
        return self._perform_upload(file_path, dataset_type, collection, 
                                  human_readable_name, notes, metadata, additional_files)
    
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
                     notes, metadata, additional_files):
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
        print(f"  Metadata fields: {len(metadata)}")
        return True
    
    def _perform_upload(self, file_path, dataset_type, collection, human_readable_name, 
                       notes, metadata, additional_files):
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
        
        result = uploader.upload_file(
            parsed_args.file,
            dataset_type,
            collection,
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
            version=parsed_args.version,
            dry_run=parsed_args.dry_run
        )
        
        return result is not None
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False