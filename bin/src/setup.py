from setuptools import setup, find_packages

setup(
    name="telemetry-storage",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "test": ["pytest>=7.0.0"],
    },
)