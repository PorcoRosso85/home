#!/usr/bin/env python3
"""
VECTOR拡張の自動インストール機能をテストする

VSS-KuzuDBの価値：
- ユーザーは手動でVECTOR拡張をインストールする必要がない
- 自動的に必要な拡張がセットアップされる
- "Test-Friendly"な環境を提供する
"""

import pytest
from unittest.mock import MagicMock, patch, call
from typing import Tuple, Optional, Dict, Any

from vss_kuzu.infrastructure.vector import check_vector_extension, VECTOR_EXTENSION_NAME


class TestVectorExtensionAutoInstall:
    """VECTOR拡張の自動インストール機能のテスト"""
    
    def test_自動インストールが試行される(self):
        """VECTOR拡張が未インストールの場合、自動的にインストールを試みる"""
        # Arrange
        mock_connection = MagicMock()
        
        # Act
        result, error = check_vector_extension(mock_connection)
        
        # Assert
        # インストールとロードのコマンドが実行されたことを確認
        expected_calls = [
            call(f"INSTALL {VECTOR_EXTENSION_NAME}"),
            call(f"LOAD EXTENSION {VECTOR_EXTENSION_NAME}")
        ]
        mock_connection.execute.assert_has_calls(expected_calls, any_order=False)
        
        # 成功時はTrueとNoneを返す
        assert result is True
        assert error is None
    
    def test_すでにインストール済みでも正常動作(self):
        """VECTOR拡張がすでにインストール済みの場合も正常に動作する"""
        # Arrange
        mock_connection = MagicMock()
        # INSTALLコマンドは既存の拡張に対しても無害
        
        # Act
        result, error = check_vector_extension(mock_connection)
        
        # Assert
        assert result is True
        assert error is None
        # インストールコマンドは実行されるが、エラーにはならない
        assert mock_connection.execute.call_count == 2
    
    def test_インストール失敗時のエラーハンドリング(self):
        """インストールに失敗した場合、適切なエラー情報を返す"""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = Exception("Network error: Unable to download extension")
        
        # Act
        result, error = check_vector_extension(mock_connection)
        
        # Assert
        assert result is False
        assert error is not None
        assert error["error"] == "Failed to install/load VECTOR extension"
        assert "Network error" in error["details"]["raw_error"]
    
    def test_ロード失敗時のエラーハンドリング(self):
        """インストールは成功したがロードに失敗した場合のエラーハンドリング"""
        # Arrange
        mock_connection = MagicMock()
        # INSTALLは成功、LOADで失敗
        def side_effect(query):
            if "INSTALL" in query:
                return None  # 成功
            else:
                raise Exception("Failed to load extension: incompatible version")
        
        mock_connection.execute.side_effect = side_effect
        
        # Act
        result, error = check_vector_extension(mock_connection)
        
        # Assert
        assert result is False
        assert error is not None
        assert "Failed to install/load VECTOR extension" in error["error"]
        assert "incompatible version" in error["details"]["raw_error"]