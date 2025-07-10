#!/usr/bin/env python3
"""Ruri v3 + KuzuDB Vector Search POC - エントリーポイント"""

import sys
from pathlib import Path

# 親ディレクトリをパスに追加
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from embeddings.main import main

if __name__ == "__main__":
    main()