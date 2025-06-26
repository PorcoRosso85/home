"""
pytest configuration for KuzuDB
"""
import os
import pytest

# KuzuDBのライブラリパスを設定
os.environ['LD_LIBRARY_PATH'] = '/nix/store/4gk773fqcsv4fh2rfkhs9bgfih86fdq8-gcc-13.3.0-lib/lib'