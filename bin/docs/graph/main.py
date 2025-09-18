#!/usr/bin/env python3
"""Main entry point for the flake-graph CLI application.

This module provides a simple entry point that delegates to the main CLI module.
The primary CLI implementation is in flake_graph.cli.
"""

import sys
from flake_graph.cli import main

if __name__ == "__main__":
    sys.exit(main())