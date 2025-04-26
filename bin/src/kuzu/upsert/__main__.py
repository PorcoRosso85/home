"""
Upsertパッケージのエントリーポイント

このモジュールはUpsertパッケージのメインエントリーポイントとして機能し、
CLIインターフェースを呼び出します。
"""

import os
import sys

# 現在のディレクトリをPythonのパスに追加（相対インポートのため）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upsert.interface import cli

if __name__ == "__main__":
    cli.main()
