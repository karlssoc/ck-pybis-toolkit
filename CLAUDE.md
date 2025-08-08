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