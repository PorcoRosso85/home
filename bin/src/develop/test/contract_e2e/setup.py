"""Setup configuration for contract_e2e package."""

from setuptools import setup, find_packages

setup(
    name="contract_e2e",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "jsonschema>=4.0.0",
        "hypothesis>=6.0.0",
        "hypothesis-jsonschema>=0.22.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "contract-e2e-runner=contract_e2e.runner:main",
        ],
    },
)