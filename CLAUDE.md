# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CK PyBIS Toolkit v1.0.1 standalone development environment. This is a Python-based OpenBIS client toolkit for debugging dataset download issues, developing new PyBIS functionality, and prototyping improvements. Built on PyBIS 1.37.3.

## Project Versioning and Tags

- Project Version: v1.0.1  
- PyBIS Library Version: 1.37.3
- Release Tags: `v1.0.0`, `v1.0.1`

## Credentials Configuration

The CLI automatically loads credentials from `~/.openbis/credentials` on every command execution. Supported variables:

- `OPENBIS_URL` - Server URL (required)
- `OPENBIS_USERNAME` - Username (required) 
- `OPENBIS_PASSWORD` - Password (required)
- `PYBIS_DOWNLOAD_DIR` - Default download directory (optional, defaults to `~/data/openbis/`)

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

