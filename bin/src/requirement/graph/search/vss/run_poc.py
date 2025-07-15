#!/usr/bin/env python3
"""Ruri v3 + KuzuDB Vector Search POC - エントリーポイント"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from vss package
sys.path.insert(0, str(Path(__file__).parent.parent))

from vss.main import main

if __name__ == "__main__":
    main()