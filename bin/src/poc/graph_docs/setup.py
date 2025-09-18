#!/usr/bin/env python3
"""Setup script for graph_docs package."""

from setuptools import setup, find_packages

setup(
    name="graph_docs",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "graph-docs=graph_docs.main:main",
        ],
    },
)