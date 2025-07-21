#!/usr/bin/env python3
"""
requirement/graph出力の契約テスト（最小限設計）

WARN: このテストは例外的にユーザーが許可したモックであり、規約非準拠である
理由: in-memoryデータベースのプロセス間共有が技術的に不可能なため、
      KuzuDBの環境変数のみをモックすることが承認された
"""
import json
import pytest
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any


if __name__ == "__main__":
    pytest.main([__file__, "-v"])