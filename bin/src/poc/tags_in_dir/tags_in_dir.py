#!/usr/bin/env python3
"""
ctags-based code analysis tool with location URI extraction.

This module uses subprocess to run ctags and parse its output to extract
symbols (functions, classes, etc.) with their location URIs in the format:
file:///absolute/path/to/file.py#L<line_number>
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    """Represents a symbol (function, class, etc.) extracted by ctags."""

    name: str
    kind: str
    location_uri: str
    scope: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        """Validate location_uri format."""
        if not self.location_uri.startswith("file://"):
            raise ValueError(f"Invalid location_uri format: {self.location_uri}")


@dataclass
class CtagsParser:
    """Parser for ctags output to extract symbols with location URIs."""

    def __init__(self):
        self.symbols: List[Symbol] = []

    def run_ctags(self, directory: str, extensions: Optional[List[str]] = None) -> str:
        """
        Run ctags on a directory and return the output.

        Args:
            directory: Path to the directory to analyze
            extensions: List of file extensions to include (e.g., ['.py', '.js'])

        Returns:
            Raw ctags output as string
        """
        # Default to Python files if no extensions specified
        if extensions is None:
            extensions = [".py"]

        # Build ctags command
        cmd = [
            "ctags",
            "--output-format=json",
            "--fields=+n+S+K",  # Include line number, signature, and kind
            "--kinds-Python=+fcm",  # Include functions, classes, and methods
            "--sort=no",
            "-o",
            "-",  # Output to stdout
        ]

        # Find all files with specified extensions
        files = []
        directory_path = Path(directory)
        for ext in extensions:
            files.extend(directory_path.rglob(f"*{ext}"))

        if not files:
            return ""

        # Add file paths to the command
        cmd.extend(str(f) for f in files)

        # Run ctags on the files
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ctags failed: {e.stderr}")

    def parse_ctags_output(self, ctags_output: str) -> List[Symbol]:
        """
        Parse ctags JSON output and convert to Symbol objects.

        Args:
            ctags_output: Raw JSON output from ctags

        Returns:
            List of Symbol objects
        """
        symbols = []

        for line in ctags_output.strip().split("\n"):
            if not line:
                continue

            try:
                entry = json.loads(line)

                # Extract required fields
                name = entry.get("name", "")
                kind = entry.get("kind", "")
                path = entry.get("path", "")
                line_no = entry.get("line", 0)

                # Skip if essential fields are missing
                if not name or not path or not line_no:
                    continue

                # Convert to absolute path
                abs_path = os.path.abspath(path)

                # Create location URI
                location_uri = f"file://{abs_path}#L{line_no}"

                # Extract optional fields
                scope = None
                if "scope" in entry:
                    scope = f"{entry['scope']}:{entry.get('scopeKind', '')}"

                signature = entry.get("signature")

                symbol = Symbol(
                    name=name,
                    kind=kind,
                    location_uri=location_uri,
                    scope=scope,
                    signature=signature,
                )

                symbols.append(symbol)

            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue

        return symbols

    def extract_symbols(
        self, directory: str, extensions: Optional[List[str]] = None
    ) -> List[Symbol]:
        """
        Extract symbols from a directory using ctags.

        Args:
            directory: Path to the directory to analyze
            extensions: List of file extensions to include

        Returns:
            List of Symbol objects
        """
        ctags_output = self.run_ctags(directory, extensions)
        self.symbols = self.parse_ctags_output(ctags_output)
        return self.symbols

    def get_symbols_by_kind(self, kind: str) -> List[Symbol]:
        """Get all symbols of a specific kind (e.g., 'function', 'class')."""
        return [s for s in self.symbols if s.kind == kind]

    def get_symbols_by_file(self, file_path: str) -> List[Symbol]:
        """Get all symbols from a specific file."""
        abs_path = os.path.abspath(file_path)
        file_uri_prefix = f"file://{abs_path}#"
        return [s for s in self.symbols if s.location_uri.startswith(file_uri_prefix)]


def main():
    """Example usage of the CtagsParser."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tags_in_dir.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]

    parser = CtagsParser()

    try:
        symbols = parser.extract_symbols(directory)

        print(f"Found {len(symbols)} symbols in {directory}\n")

        # Group by kind
        by_kind = {}
        for symbol in symbols:
            by_kind.setdefault(symbol.kind, []).append(symbol)

        for kind, syms in by_kind.items():
            print(f"{kind}s ({len(syms)}):")
            for sym in syms[:5]:  # Show first 5 of each kind
                print(f"  - {sym.name} at {sym.location_uri}")
            if len(syms) > 5:
                print(f"  ... and {len(syms) - 5} more")
            print()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
