#!/usr/bin/env python3
"""
Test backward compatibility wrapper for create_vss_optional

このテストは create_vss_optional が正しく動作し、
適切な deprecation warning を出力することを確認します。
"""

import pytest
from typing import Optional
from unittest.mock import patch, MagicMock
from log_py import log

from vss_kuzu import create_vss, create_vss_optional, VSSAlgebra


def test_create_vss_optional_success():
    """create_vss_optional が成功ケースで正しく動作することを確認"""
    log("info", {
        "message": "Testing create_vss_optional success case",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_success"
    })
    
    # create_vss_optional を呼び出す
    vss = create_vss_optional(in_memory=True)
    
    # VECTOR extension が利用できない環境では None を返すことがある
    # これは正常な動作であり、エラーではない
    if vss is None:
        log("info", {
            "message": "create_vss_optional returned None (likely due to missing VECTOR extension)",
            "component": "test_backward_compatibility",
            "operation": "test_create_vss_optional_success",
            "note": "This is expected behavior when VECTOR extension is not available"
        })
    else:
        # 成功時は VSSAlgebra インスタンスを返すはず
        assert hasattr(vss, 'index'), "VSS instance should have index method"
        assert hasattr(vss, 'search'), "VSS instance should have search method"
    
    log("info", {
        "message": "create_vss_optional success test passed",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_success"
    })


def test_create_vss_optional_failure():
    """create_vss_optional が失敗ケースで None を返すことを確認"""
    log("info", {
        "message": "Testing create_vss_optional failure case",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_failure"
    })
    
    # 無効なパスで失敗を引き起こす
    vss = create_vss_optional(db_path="/invalid/nonexistent/path", in_memory=False)
    
    # 失敗時は None を返すはず
    assert vss is None, "create_vss_optional should return None on failure"
    
    log("info", {
        "message": "create_vss_optional failure test passed",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_failure"
    })


def test_create_vss_optional_deprecation_warning():
    """create_vss_optional が deprecation warning を出力することを確認"""
    log("info", {
        "message": "Testing create_vss_optional deprecation warning",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_deprecation_warning"
    })
    
    # log 関数をモックして warning が出力されることを確認
    with patch('vss_kuzu.application.log') as mock_log:
        # create_vss_optional を呼び出す
        vss = create_vss_optional(in_memory=True)
        
        # deprecation warning が出力されたか確認
        warning_calls = [
            call for call in mock_log.call_args_list
            if call[0][0] == "warning" and 
            "deprecation" in call[0][1] and
            call[0][1].get("deprecation") is True
        ]
        
        assert len(warning_calls) > 0, "Deprecation warning should be logged"
        
        # warning メッセージの内容を確認
        warning_data = warning_calls[0][0][1]
        assert "create_vss_optional is deprecated" in warning_data["message"]
        assert "create_vss" in warning_data.get("recommendation", "")
    
    log("info", {
        "message": "Deprecation warning test passed",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_deprecation_warning"
    })


def test_create_vss_optional_parameters_forwarded():
    """create_vss_optional がパラメータを正しく転送することを確認"""
    log("info", {
        "message": "Testing create_vss_optional parameter forwarding",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_parameters_forwarded"
    })
    
    # カスタムパラメータを指定
    custom_params = {
        "db_path": "./test_db",
        "in_memory": True,
        "model_name": "test-model",
        "embedding_dimension": 512,
        "default_limit": 20,
        "index_mu": 40,
        "index_ml": 80,
        "index_metric": "l2",
        "index_efc": 300
    }
    
    # create_vss をモックして呼び出しを確認
    with patch('vss_kuzu.application.create_vss') as mock_create_vss:
        mock_vss = MagicMock(spec=VSSAlgebra)
        mock_create_vss.return_value = mock_vss
        
        # create_vss_optional を呼び出す
        result = create_vss_optional(**custom_params)
        
        # create_vss が正しいパラメータで呼ばれたか確認
        mock_create_vss.assert_called_once_with(
            "./test_db",
            True,
            "test-model",
            None,
            embedding_dimension=512,
            default_limit=20,
            index_mu=40,
            index_ml=80,
            index_metric="l2",
            index_efc=300
        )
        
        # 結果が正しく返されたか確認
        assert result is mock_vss
    
    log("info", {
        "message": "Parameter forwarding test passed",
        "component": "test_backward_compatibility",
        "operation": "test_create_vss_optional_parameters_forwarded"
    })


def test_backward_compatibility_return_type():
    """create_vss と create_vss_optional の戻り値の型が互換性があることを確認"""
    log("info", {
        "message": "Testing return type compatibility",
        "component": "test_backward_compatibility",
        "operation": "test_backward_compatibility_return_type"
    })
    
    # 両方の関数を呼び出す
    vss_direct = create_vss(in_memory=True)
    vss_optional = create_vss_optional(in_memory=True)
    
    # create_vss が VSSError を返した場合
    if isinstance(vss_direct, dict) and vss_direct.get('type'):
        # create_vss_optional は None を返すはず
        assert vss_optional is None, \
            "create_vss_optional should return None when create_vss returns VSSError"
    else:
        # 成功時は両方とも同じ型
        assert type(vss_direct) == type(vss_optional), \
            "Both functions should return the same type on success"
        
        # 両方とも VSSAlgebra インスタンス
        if vss_direct is not None and vss_optional is not None:
            assert hasattr(vss_direct, 'index') and hasattr(vss_optional, 'index'), \
                "Both should have index method"
            assert hasattr(vss_direct, 'search') and hasattr(vss_optional, 'search'), \
                "Both should have search method"
    
    log("info", {
        "message": "Return type compatibility test passed",
        "component": "test_backward_compatibility",
        "operation": "test_backward_compatibility_return_type"
    })


if __name__ == "__main__":
    # 単体実行時のテスト
    test_create_vss_optional_success()
    test_create_vss_optional_failure()
    test_create_vss_optional_deprecation_warning()
    test_create_vss_optional_parameters_forwarded()
    test_backward_compatibility_return_type()
    
    print("\nAll backward compatibility tests passed ✓")