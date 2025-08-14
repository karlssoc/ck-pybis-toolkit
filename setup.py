#!/usr/bin/env python3
"""
PyBIS CLI Setup - Simple pip installable package
"""

from setuptools import setup
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="ck-pybis-toolkit",
    version="1.0.3",
    description="CK PyBIS Toolkit - Enhanced OpenBIS client for dataset management and debugging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="CK",
    py_modules=["pybis_scripts", "pybis_common"],
    entry_points={
        'console_scripts': [
            'pybis=pybis_scripts:main',
        ],
    },
    install_requires=[
        'pybis==1.37.3',
    ],
    python_requires='>=3.8',
)