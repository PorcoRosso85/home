from setuptools import setup, find_packages

setup(
    name="kuzu_py",
    version="0.1.0",
    packages=["kuzu_py"],
    package_dir={"kuzu_py": "."},
    install_requires=[],  # kuzu is provided by Nix
    python_requires=">=3.12",
    description="KuzuDB thin wrapper for Nix environments",
)