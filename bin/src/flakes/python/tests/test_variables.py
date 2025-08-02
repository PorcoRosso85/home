#!/usr/bin/env python3
"""
環境変数管理のテスト

variables.pyの機能をテストします。
"""

import pytest
import os
import sys

# テストからモジュールをインポートできるようにパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from variables import get_tool_config, get_security_config


def test_get_tool_config_defaults():
    """デフォルト設定が正しく取得できることを確認"""
    # 環境変数をクリア
    for key in ['PYTHON_TOOL_TIMEOUT', 'PYTHON_ALLOWED_TOOLS', 'PYTHON_MAX_OUTPUT_SIZE']:
        os.environ.pop(key, None)
    
    config = get_tool_config()
    
    assert config['timeout'] == 60
    assert config['allowed_tools'] == ['pytest', 'ruff', 'pyright']
    assert config['max_output_size'] == 1048576
    assert config['pyright_version'] is None
    assert config['ruff_version'] is None


def test_get_tool_config_custom():
    """カスタム設定が正しく取得できることを確認"""
    os.environ['PYTHON_TOOL_TIMEOUT'] = '120'
    os.environ['PYTHON_ALLOWED_TOOLS'] = 'pytest,mypy'
    os.environ['PYTHON_MAX_OUTPUT_SIZE'] = '2097152'
    os.environ['PYTHON_PYRIGHT_VERSION'] = '1.2.3'
    
    config = get_tool_config()
    
    assert config['timeout'] == 120
    assert config['allowed_tools'] == ['pytest', 'mypy']
    assert config['max_output_size'] == 2097152
    assert config['pyright_version'] == '1.2.3'
    
    # クリーンアップ
    for key in ['PYTHON_TOOL_TIMEOUT', 'PYTHON_ALLOWED_TOOLS', 'PYTHON_MAX_OUTPUT_SIZE', 'PYTHON_PYRIGHT_VERSION']:
        os.environ.pop(key, None)


def test_get_tool_config_invalid_timeout():
    """無効なタイムアウト値でエラーが発生することを確認"""
    os.environ['PYTHON_TOOL_TIMEOUT'] = 'invalid'
    
    with pytest.raises(ValueError, match="PYTHON_TOOL_TIMEOUT must be an integer"):
        get_tool_config()
    
    os.environ.pop('PYTHON_TOOL_TIMEOUT', None)


def test_get_security_config():
    """セキュリティ設定が正しく取得できることを確認"""
    config = get_security_config()
    
    assert isinstance(config['dangerous_patterns'], list)
    assert len(config['dangerous_patterns']) > 0
    assert 'os' in config['forbidden_imports']
    assert 'eval' in config['forbidden_functions']