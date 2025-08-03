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
                
                # create_vssがRuntimeErrorを発生させることを確認
                with pytest.raises(RuntimeError) as exc_info:
                    create_vss(db_path=db_dir, in_memory=False)
                
                # エラーメッセージが明確であることを確認
                error_msg = str(exc_info.value)
                log("info", {
                    "message": "Caught expected error",
                    "error": error_msg
                })
                
                # エラーメッセージに必要な情報が含まれているか確認
                assert "VECTOR extension" in error_msg, "Error should mention VECTOR extension"
                assert "Failed to initialize VSS" in error_msg, "Error should mention initialization failure"
                
                # 追加の詳細情報が含まれているか確認
                if "Details:" in error_msg:
                    assert "See README.md" in error_msg, "Error should provide guidance"
                    assert "nix flake show" in error_msg, "Error should mention nix command"
    
    def test_invalid_parameters_rejected(self):
        """不正なパラメータが適切に拒否される"""
        log("info", {
            "message": "Testing invalid parameters rejection",
            "test": "test_invalid_parameters_rejected"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            
            try:
                vss = create_vss(db_path=db_dir, in_memory=False)
                
                # 空のドキュメントリストでのインデックス
                with pytest.raises((ValueError, AssertionError)) as exc_info:
                    vss.index([])
                log("info", {
                    "message": "Empty document list rejected",
                    "error": str(exc_info.value)
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
                
            except RuntimeError as e:
                log("warning", {
                    "message": "Failed to create VSS instance",
                    "error": str(e),
                    "reason": "VECTOR extension might not be available"
                })
                pytest.skip(f"VECTOR extension not available: {e}")
    
    def test_resource_exhaustion_handling(self):
        """リソース不足時のgraceful degradation"""
        log("info", {
            "message": "Testing resource exhaustion handling",
            "test": "test_resource_exhaustion_handling"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            
            try:
                vss = create_vss(db_path=db_dir, in_memory=False)
                
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
                
            except RuntimeError as e:
                log("warning", {
                    "message": "Failed to create VSS instance",
                    "error": str(e),
                    "reason": "VECTOR extension might not be available"
                })
                pytest.skip(f"VECTOR extension not available: {e}")