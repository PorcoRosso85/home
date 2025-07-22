from setuptools import setup, find_packages

setup(
    name="vss_kuzu",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],  # Dependencies are provided by Nix
    python_requires=">=3.11",
    description="Vector Similarity Search with KuzuDB",
    long_description="A library for performing vector similarity search using KuzuDB's VECTOR extension",
    author="VSS Team",
    keywords=["vector search", "similarity search", "kuzu", "embeddings"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)