#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="asvs-arrow-converter",
    version="0.1.0",
    description="Convert OWASP ASVS from GitHub to Apache Arrow/Parquet format",
    author="ASVS Reference Team",
    python_requires=">=3.10",
    install_requires=[
        "pyarrow>=14.0.0",
    ],
    py_modules=[
        "asvs_arrow_converter",
        "asvs_arrow_types",
        "arrow_cli",
    ],
    entry_points={
        "console_scripts": [
            "asvs-arrow-cli=arrow_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)