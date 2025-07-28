from setuptools import setup

setup(
    name="kuzu_py",
    version="0.1.1",
    py_modules=["kuzu_py", "database", "result_types", "query_loader", "variables", "errors", "typed_query_loader"],
    include_package_data=True,
    install_requires=[],  # kuzu is provided by Nix
    python_requires=">=3.12",
    description="KuzuDB thin wrapper for Nix environments",
)