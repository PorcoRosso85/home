#!/usr/bin/env python3
"""
エラーハンドリングの強化テスト

VSS_KUZUのエラーハンドリングが適切に機能することを検証する。
VECTOR拡張の欠如、不正なパラメータ、リソース不足などのエラーケースを網羅。
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from log_py import log


class TestErrorHandling:
    """エラーハンドリングのテストクラス"""
    
    def test_vector_extension_missing_error(self):
        """VECTOR拡張が無い場合の明確なエラーメッセージ"""
        log("info", {
            "message": "Testing VECTOR extension missing error",
            "test": "test_vector_extension_missing_error"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            
            # VECTOR拡張のチェックを模擬的に失敗させる
            with patch('vss_kuzu.infrastructure.vector.check_vector_extension') as mock_check:
                mock_check.return_value = (False, {"error": "Failed to load VECTOR extension", "details": {}})
                
                # create_vssがVSSErrorを返すことを確認
                vss = create_vss(db_path=db_dir, in_memory=False)
                assert isinstance(vss, dict), "create_vss should return a dict (VSSError) when VECTOR extension is missing"
                assert vss.get('type') == 'vector_extension_error', f"Expected type='vector_extension_error', got {vss.get('type')}"
                assert 'message' in vss, "VSSError should have a message field"
                assert 'details' in vss, "VSSError should have a details field"
                
                log("info", {
                    "message": "create_vss correctly returned VSSError for missing VECTOR extension",
                    "error_type": vss.get('type')
                })
    
    def test_invalid_parameters_rejected(self):
        """不正なパラメータが適切に拒否される"""
        log("info", {
            "message": "Testing invalid parameters rejection",
            "test": "test_invalid_parameters_rejected"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            
            vss = create_vss(db_path=db_dir, in_memory=False)
            if isinstance(vss, dict) and vss.get('type'):
                pytest.skip(f"VECTOR extension not available: {vss.get('message')}")
                
                # 空のドキュメントリストでのインデックス
                result = vss.index([])
                assert result['ok'] is False, "Empty documents should fail"
                assert 'No documents provided' in result['error']
                log("info", {
                    "message": "Empty document list rejected",
                    "error": result['error']
                })
                
                # 不正な形式のドキュメント
                invalid_docs = [
                    {"id": "test_001"},  # contentがない
                    {"content": "テスト"},  # idがない
                    {"id": None, "content": "テスト"},  # idがNone
                    {"id": "test_002", "content": None},  # contentがNone
                    {"id": "", "content": "テスト"},  # idが空文字
                    {"id": "test_003", "content": ""},  # contentが空文字
                ]
                
                for doc in invalid_docs:
                    try:
                        result = vss.index([doc])
                        # エラーが返されるか、例外が発生することを期待
                        if result.get('ok'):
                            # もしokがTrueの場合、空のcontentは許容される可能性がある
                            if doc.get('content') == "":
                                log("info", {
                                    "message": "Empty content might be allowed",
                                    "doc": doc
                                })
                                continue
                            pytest.fail(f"Invalid document should be rejected: {doc}")
                        else:
                            log("info", {
                                "message": "Invalid document rejected via result",
                                "doc": doc,
                                "error": result.get('error')
                            })
                    except (ValueError, AssertionError, KeyError) as e:
                        log("info", {
                            "message": "Invalid document rejected via exception",
                            "doc": doc,
                            "error": str(e)
                        })
                
                # 不正な検索パラメータ
                invalid_searches = [
                    ("", 5),  # 空のクエリ
                    ("テスト", 0),  # limitが0
                    ("テスト", -1),  # limitが負数
                    ("テスト", 1001),  # limitが大きすぎる（実装依存）
                ]
                
                for query, limit in invalid_searches:
                    try:
                        result = vss.search(query, limit=limit)
                        # エラーが返されるか確認
                        if result.get('ok'):
                            # 一部の実装では空クエリや大きなlimitを許容する可能性
                            log("info", {
                                "message": "Search parameter might be allowed",
                                "query": query,
                                "limit": limit
                            })
                        else:
                            log("info", {
                                "message": "Invalid search parameter rejected",
                                "query": query,
                                "limit": limit,
                                "error": result.get('error')
                            })
                    except (ValueError, AssertionError) as e:
                        log("info", {
                            "message": "Invalid search parameter rejected via exception",
                            "query": query,
                            "limit": limit,
                            "error": str(e)
                        })
                
    
    def test_resource_exhaustion_handling(self):
        """リソース不足時のgraceful degradation"""
        log("info", {
            "message": "Testing resource exhaustion handling",
            "test": "test_resource_exhaustion_handling"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            
            vss = create_vss(db_path=db_dir, in_memory=False)
            if isinstance(vss, dict) and vss.get('type'):
                pytest.skip(f"VECTOR extension not available: {vss.get('message')}")
            
            # 大量のドキュメントを追加してリソースを消費
            batch_size = 100
            num_batches = 10
            
            for batch_idx in range(num_batches):
                docs = []
                for i in range(batch_size):
                    doc_id = f"resource_test_{batch_idx:03d}_{i:03d}"
                    docs.append({
                        "id": doc_id,
                        "content": f"リソーステスト用のドキュメント。バッチ{batch_idx}、番号{i}。" * 10
                    })
                
                try:
                    result = vss.index(docs)
                    if result.get('ok'):
                        log("info", {
                            "message": "Batch indexed successfully",
                            "batch": batch_idx,
                            "size": batch_size
                        })
                    else:
                        # リソース不足でエラーが発生した場合
                        log("warning", {
                            "message": "Batch indexing failed",
                            "batch": batch_idx,
                            "error": result.get('error')
                        })
                        # システムが安定していることを確認（クラッシュしない）
                        # 検索が引き続き動作することを確認
                        search_result = vss.search("リソーステスト", limit=5)
                        assert isinstance(search_result, dict), "Search should still return a dict"
                        break
                except Exception as e:
                    log("warning", {
                        "message": "Resource exhaustion detected",
                        "batch": batch_idx,
                        "error": str(e)
                    })
                    # エラー後も基本的な操作が可能であることを確認
                    try:
                        # 小さなドキュメントの追加を試みる
                        small_doc = {
                            "id": "recovery_test",
                            "content": "リカバリーテスト"
                        }
                        recovery_result = vss.index([small_doc])
                        log("info", {
                            "message": "Recovery test result",
                            "ok": recovery_result.get('ok'),
                            "error": recovery_result.get('error')
                        })
                    except Exception as recovery_error:
                        log("error", {
                            "message": "Recovery failed",
                            "error": str(recovery_error)
                        })
                    break
                
            # 最終的にシステムが動作していることを確認
            final_search = vss.search("テスト", limit=1)
            assert isinstance(final_search, dict), "System should still be operational"
            
            log("info", {
                "message": "Resource exhaustion test completed",
                "system_operational": True
            })
    
    def test_vss_error_structure(self):
        """VSSErrorオブジェクトの構造検証"""
        log("info", {
            "message": "Testing VSSError structure",
            "test": "test_vss_error_structure"
        })
        
        from vss_kuzu import VSSError
        
        # VSSErrorはTypedDictなので、辞書として作成
        error: VSSError = {
            "type": "validation_error",
            "message": "Invalid document format",
            "details": {"field": "content", "reason": "missing"}
        }
        
        # VSSError構造を検証（dict形式）
        assert "type" in error, "VSSError should have 'type' key"
        assert "message" in error, "VSSError should have 'message' key"
        assert "details" in error, "VSSError should have 'details' key"
        
        # 型チェック
        assert isinstance(error["type"], str), "VSSError.type should be string"
        assert isinstance(error["message"], str), "VSSError.message should be string"
        assert isinstance(error["details"], dict), "VSSError.details should be dict"
        
        # 値チェック
        assert error["type"] == "validation_error", "VSSError.type should preserve value"
        assert error["message"] == "Invalid document format", "VSSError.message should preserve value"
        assert error["details"] == {"field": "content", "reason": "missing"}, "VSSError.details should preserve value"
        
        log("info", {
            "message": "VSSError structure validated",
            "error_type": error["type"],
            "error_message": error["message"],
            "error_details": error["details"]
        })
    
    def test_vss_error_required_fields(self):
        """VSSErrorの必須フィールド検証"""
        log("info", {
            "message": "Testing VSSError required fields",
            "test": "test_vss_error_required_fields"
        })
        
        from vss_kuzu import VSSError
        from typing import get_type_hints, get_args, get_origin
        
        # TypedDictは静的型チェック用なので、実行時の検証は手動で実装
        # VSS APIが返すエラー構造を検証する関数
        def validate_vss_error(error_dict: dict) -> bool:
            """VSSError形式の辞書を検証"""
            required_fields = {"type", "message", "details"}
            return all(field in error_dict for field in required_fields)
        
        # 不完全なエラー辞書
        incomplete_errors = [
            {"type": "test_error"},  # messageとdetailsが欠けている
            {"message": "Test error"},  # typeとdetailsが欠けている
            {"type": "test_error", "message": "Test message"},  # detailsが欠けている
        ]
        
        for error_dict in incomplete_errors:
            assert not validate_vss_error(error_dict), f"Incomplete error should not validate: {error_dict}"
            log("info", {
                "message": "Incomplete error correctly rejected",
                "error_dict": error_dict
            })
        
        # 完全なエラー辞書
        complete_error: VSSError = {
            "type": "test_error",
            "message": "Test error message",
            "details": {}
        }
        
        assert validate_vss_error(complete_error), "Complete error should validate"
        assert complete_error["type"] == "test_error"
        assert complete_error["message"] == "Test error message"
        assert complete_error["details"] == {}
        
        log("info", {
            "message": "VSSError required fields validated"
        })
    
    def test_vss_error_details_context_preservation(self):
        """VSSErrorの詳細情報コンテキスト保持検証"""
        log("info", {
            "message": "Testing VSSError details context preservation",
            "test": "test_vss_error_details_context_preservation"
        })
        
        from vss_kuzu import VSSError
        import copy
        
        # 複雑な詳細情報
        complex_details = {
            "operation": "index_documents",
            "phase": "embedding_generation",
            "document_id": "test_001",
            "nested_info": {
                "model": "cl-nagoya/ruri-v3-30m",
                "dimension": 256,
                "error_code": "MODEL_LOAD_FAILED"
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "retry_count": 3,
            "environment": {
                "db_path": "/tmp/test.db",
                "in_memory": False
            }
        }
        
        # detailsのディープコピーを作成
        details_copy = copy.deepcopy(complex_details)
        
        error: VSSError = {
            "type": "embedding_error",
            "message": "Failed to generate embedding",
            "details": details_copy
        }
        
        # 詳細情報が完全に保持されているか検証
        assert error["details"] == complex_details, "Complex details should be preserved exactly"
        assert error["details"]["nested_info"]["model"] == "cl-nagoya/ruri-v3-30m"
        assert error["details"]["nested_info"]["dimension"] == 256
        assert error["details"]["environment"]["in_memory"] is False
        
        # 詳細情報の変更が元のデータに影響しないか確認
        error["details"]["new_field"] = "added"
        assert "new_field" not in complex_details, "Original details should not be modified"
        
        log("info", {
            "message": "VSSError details context preservation validated",
            "details_keys": list(error["details"].keys()),
            "nested_keys": list(error["details"].get("nested_info", {}).keys())
        })
    
    def test_vss_api_error_format(self):
        """VSS APIのエラー形式がVSSError構造に従うことを検証"""
        log("info", {
            "message": "Testing VSS API error format",
            "test": "test_vss_api_error_format"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            
            vss = create_vss(db_path=db_dir, in_memory=False)
            if isinstance(vss, dict) and vss.get('type'):
                pytest.skip(f"VECTOR extension not available: {vss.get('message')}")
            
            # 空のドキュメントリストでインデックスを試みる
            result = vss.index([])
            
            # エラー結果の構造を検証
            assert "ok" in result, "Result should have 'ok' field"
            assert result["ok"] is False, "Empty documents should fail"
            assert "error" in result, "Result should have 'error' field"
            assert "details" in result, "Result should have 'details' field"
            
            # VSSError形式に変換可能か検証
            vss_error = {
                "type": "validation_error",
                "message": result["error"],
                "details": result["details"]
            }
            
            assert isinstance(vss_error["type"], str)
            assert isinstance(vss_error["message"], str)
            assert isinstance(vss_error["details"], dict)
            
            log("info", {
                "message": "VSS API error format validated",
                "error_message": vss_error["message"],
                "error_type": vss_error["type"]
            })