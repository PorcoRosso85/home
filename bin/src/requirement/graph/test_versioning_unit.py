"""
バージョニング機能の単体テスト（pytestで実行可能）
"""
import pytest
import tempfile
import os
from datetime import datetime

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()


class TestVersioningUnit:
    """バージョニング機能の単体テスト"""
    
