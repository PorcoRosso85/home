#!/usr/bin/env python3
"""
CLI wrapper for search_symbols
Avoids relative import issues
"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from types import SearchResult, SearchSuccessDict, SearchErrorDict, SymbolDict
from search import search_symbols


def main():
    if len(sys.argv) < 2:
        print("Usage: search-symbols <path>", file=sys.stderr)
        sys.exit(1)
    
    result = search_symbols(sys.argv[1])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()