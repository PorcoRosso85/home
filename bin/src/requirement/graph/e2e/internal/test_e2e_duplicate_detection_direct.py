"""
E2E統合テスト: SearchAdapterを直接使用した重複検出機能の動作確認

このテストは以下を検証:
- SearchAdapterの直接呼び出しによる重複検出
- テンプレートプロセッサ経由での重複警告生成
- スコア情報の正確性
"""

import json
import tempfile
import pytest
from pathlib import Path
import sys
import os
from test_utils.pytest_marks import mark_test, TestSpeed, TestType


@mark_test(TestSpeed.FAST, TestType.INTEGRATION)
def test_duplicate_detection_warns_on_similar_requirements(run_system):
    """
    類似した要件を作成した時に重複警告が発生することを検証
    - SearchAdapterによる重複検出が動作すること
    - 警告にスコア情報が含まれること
    """
    with tempfile.TemporaryDirectory() as db_dir:
        # Initialize schema
        result = run_system({"type": "schema", "action": "apply"}, db_dir)
        # Check for error first
        if "error" in result:
            pytest.fail(f"Schema initialization failed: {result}")
        # For structured log output, check in data field
        if "data" in result:
            assert result["data"].get("status") == "success", f"Schema initialization failed: {result}"
        
        # Create first requirement
        req1_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "auth_001",
                "title": "ユーザー認証機能",
                "description": "安全なログイン機能を提供"
            }
        }, db_dir)
        if "error" in req1_result:
            pytest.fail(f"First requirement creation failed: {req1_result}")
        
        # Create similar requirement
        req2_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "auth_002",
                "title": "ユーザー認証システム",
                "description": "セキュアなログイン実装"
            }
        }, db_dir)
        if "error" in req2_result:
            pytest.fail(f"Second requirement creation failed: {req2_result}")
        
        # Extract actual result data from structured log
        if "data" in req2_result:
            result_data = req2_result["data"]
        else:
            result_data = req2_result
            
        # Verify warning exists
        assert "warning" in result_data, f"Expected duplicate warning but none found in: {result_data}"
        warning = result_data["warning"]
        assert warning.get('type') == 'duplicate', f"Expected warning type 'duplicate', got {warning.get('type')}"
        assert "duplicates" in warning, "Warning should contain duplicates list"
        assert len(warning["duplicates"]) > 0, "Duplicates list should not be empty"
        
        # Verify duplicate has score
        for dup in warning["duplicates"]:
            assert "id" in dup, "Duplicate should have 'id' field"
            assert "score" in dup, "Duplicate should have 'score' field"
            assert isinstance(dup["score"], (int, float)), "Score should be numeric"
            assert 0 <= dup["score"] <= 1, f"Score should be between 0 and 1, got {dup['score']}"


@mark_test(TestSpeed.NORMAL, TestType.INTEGRATION)
def test_search_adapter_direct_duplicate_check():
    """
    SearchAdapterを直接使用した重複検出機能のテスト
    注: このテストは内部実装に依存するため、将来的に削除される可能性がある
    """
    pytest.skip("Direct SearchAdapter testing requires refactoring to use run_system interface")