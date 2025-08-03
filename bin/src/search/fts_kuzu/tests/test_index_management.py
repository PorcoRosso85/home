#!/usr/bin/env python3
"""
インデックス管理のテスト

requirement/graphから移行されたテスト
インクリメンタルインデックス、大量ドキュメント、一貫性の検証
"""

import tempfile
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest

from fts_kuzu import create_fts


class TestIndexManagement:
    """インデックス管理のテストスイート"""

    def test_incremental_indexing(self):
        """インクリメンタルなインデックス追加"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/incremental_db"
            fts = create_fts(db_path=db_path)

            # Phase 1: 初期ドキュメントの追加
            initial_docs = [
                {"id": "doc_001", "title": "初期ドキュメント1", "content": "最初のバッチのドキュメント"},
                {"id": "doc_002", "title": "初期ドキュメント2", "content": "インデックスのテスト"}
            ]
            result = fts.index(initial_docs)
            assert result["ok"] is True
            assert result["indexed_count"] == 2

            # 初期ドキュメントが検索可能か確認
            search_result = fts.search("初期ドキュメント")
            assert len(search_result["results"]) == 2

            # Phase 2: 追加ドキュメントのインデックス
            additional_docs = [
                {"id": "doc_003", "title": "追加ドキュメント1", "content": "2番目のバッチ"},
                {"id": "doc_004", "title": "追加ドキュメント2", "content": "インクリメンタル追加"}
            ]
            result = fts.index(additional_docs)
            assert result["ok"] is True
            assert result["indexed_count"] == 2

            # すべてのドキュメントが検索可能か確認
            search_result = fts.search("ドキュメント")
            assert len(search_result["results"]) == 4

            # Phase 3: さらに追加
            more_docs = [
                {"id": "doc_005", "title": "さらに追加", "content": "3番目のバッチのドキュメント"}
            ]
            result = fts.index(more_docs)
            assert result["ok"] is True
            assert result["indexed_count"] == 1

            # 最終的な検索確認
            search_result = fts.search("バッチ")
            assert len(search_result["results"]) == 3  # 3つのバッチドキュメント

            # 既存ドキュメントの更新（同じIDで再インデックス）
            update_doc = [
                {"id": "doc_001", "title": "更新されたドキュメント1", "content": "内容が更新されました"}
            ]
            result = fts.index(update_doc)
            assert result["ok"] is True

            # 更新が反映されているか確認
            search_result = fts.search("更新されました")
            assert len(search_result["results"]) == 1
            assert search_result["results"][0]["id"] == "doc_001"

            # 古い内容では検索できないことを確認
            search_result = fts.search("最初のバッチ")
            assert not any(r["id"] == "doc_001" for r in search_result["results"])

            fts.close()

    def test_large_document_indexing(self):
        """大量ドキュメントのインデックス作成"""
        fts = create_fts(in_memory=True)

        # Test 1: 1000件のドキュメントを一度にインデックス
        large_batch = []
        for i in range(1000):
            large_batch.append({
                "id": f"large_{i:04d}",
                "title": f"ドキュメント {i}",
                "content": f"これは{i}番目のドキュメントです。カテゴリ: {i % 10}"
            })

        start_time = time.time()
        result = fts.index(large_batch)
        index_time = time.time() - start_time

        assert result["ok"] is True
        assert result["indexed_count"] == 1000
        assert "index_time_ms" in result
        
        # パフォーマンスメトリクスの確認（1000件で10秒以内）
        assert index_time < 10.0

        # 検索でドキュメントが見つかることを確認
        search_result = fts.search("カテゴリ: 5")
        assert search_result["ok"] is True
        assert len(search_result["results"]) == 100  # 1000件中100件がカテゴリ5

        # Test 2: 長いコンテンツを持つドキュメント
        long_content_docs = []
        for i in range(10):
            # 各ドキュメントに10KBのテキスト
            long_text = " ".join([f"単語{j}" for j in range(1000)])
            long_content_docs.append({
                "id": f"long_{i}",
                "title": f"長いドキュメント {i}",
                "content": long_text
            })

        result = fts.index(long_content_docs)
        assert result["ok"] is True
        assert result["indexed_count"] == 10

        # Test 3: バッチサイズを変えてのインデックス
        batch_sizes = [10, 50, 100, 500]
        for batch_size in batch_sizes:
            batch = []
            for i in range(batch_size):
                batch.append({
                    "id": f"batch_{batch_size}_{i}",
                    "content": f"バッチサイズ{batch_size}のドキュメント{i}"
                })
            
            result = fts.index(batch)
            assert result["ok"] is True
            assert result["indexed_count"] == batch_size

        fts.close()

    def test_index_consistency(self):
        """インデックスの一貫性保証"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/consistency_db"
            
            # Test 1: インデックス後の即座の検索
            fts = create_fts(db_path=db_path)
            
            docs = [
                {"id": "cons_1", "content": "一貫性テストドキュメント"},
                {"id": "cons_2", "content": "即座に検索可能"}
            ]
            
            result = fts.index(docs)
            assert result["ok"] is True
            
            # インデックス直後に検索
            search_result = fts.search("一貫性テスト")
            assert len(search_result["results"]) >= 1
            assert search_result["results"][0]["id"] == "cons_1"
            
            fts.close()

            # Test 2: 再起動後の一貫性
            fts2 = create_fts(db_path=db_path)
            
            # 以前のドキュメントが検索可能
            search_result = fts2.search("即座に検索可能")
            assert len(search_result["results"]) >= 1
            assert search_result["results"][0]["id"] == "cons_2"
            
            # 新しいドキュメントを追加
            new_docs = [{"id": "cons_3", "content": "再起動後の追加"}]
            result = fts2.index(new_docs)
            assert result["ok"] is True
            
            # 全ドキュメントが検索可能
            search_result = fts2.search("ドキュメント")
            assert len(search_result["results"]) >= 1
            
            fts2.close()

            # Test 3: 重複IDの処理（上書き動作）
            fts3 = create_fts(db_path=db_path)
            
            # 既存IDで異なる内容をインデックス
            overwrite_doc = [{"id": "cons_1", "content": "上書きされた内容"}]
            result = fts3.index(overwrite_doc)
            assert result["ok"] is True
            
            # 新しい内容で検索可能
            search_result = fts3.search("上書きされた")
            assert len(search_result["results"]) == 1
            assert search_result["results"][0]["id"] == "cons_1"
            
            # 古い内容では見つからない
            search_result = fts3.search("一貫性テストドキュメント")
            assert not any(r["id"] == "cons_1" for r in search_result["results"])
            
            fts3.close()

    def test_concurrent_indexing_safety(self):
        """同時実行時の安全性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/concurrent_db"
            
            # 複数のFTSインスタンスで同時にインデックス
            def index_batch(batch_id, start_idx, count):
                fts = create_fts(db_path=db_path)
                docs = []
                for i in range(count):
                    docs.append({
                        "id": f"thread_{batch_id}_doc_{start_idx + i}",
                        "content": f"スレッド{batch_id}のドキュメント{i}"
                    })
                result = fts.index(docs)
                fts.close()
                return result["ok"], result.get("indexed_count", 0)

            # 5つのスレッドで同時に100件ずつインデックス
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i in range(5):
                    future = executor.submit(index_batch, i, i * 100, 100)
                    futures.append(future)
                
                # すべての結果を収集
                total_indexed = 0
                for future in as_completed(futures):
                    success, count = future.result()
                    assert success
                    total_indexed += count
                
                assert total_indexed == 500

            # 最終的にすべてのドキュメントが検索可能か確認
            fts_verify = create_fts(db_path=db_path)
            search_result = fts_verify.search("スレッド")
            assert len(search_result["results"]) == 500
            fts_verify.close()

    def test_index_performance_metrics(self):
        """インデックスのパフォーマンスメトリクス"""
        fts = create_fts(in_memory=True)

        # 様々なサイズのバッチでパフォーマンスを測定
        batch_configs = [
            {"size": 10, "max_time_ms": 100},
            {"size": 100, "max_time_ms": 500},
            {"size": 1000, "max_time_ms": 5000}
        ]

        for config in batch_configs:
            docs = []
            for i in range(config["size"]):
                docs.append({
                    "id": f"perf_{config['size']}_{i}",
                    "content": f"パフォーマンステスト {i}"
                })

            start_time = time.time()
            result = fts.index(docs)
            elapsed_ms = (time.time() - start_time) * 1000

            assert result["ok"] is True
            assert result["indexed_count"] == config["size"]
            assert "index_time_ms" in result
            
            # 実際の経過時間が許容範囲内
            assert elapsed_ms < config["max_time_ms"]
            
            # メトリクスの妥当性確認
            reported_time = result["index_time_ms"]
            assert reported_time > 0
            assert reported_time < config["max_time_ms"]

        fts.close()

    def test_index_error_recovery(self):
        """インデックスエラーからの回復"""
        fts = create_fts(in_memory=True)

        # Test 1: 不正なドキュメント形式
        invalid_docs = [
            {"id": "valid_1", "content": "正常なドキュメント"},
            {"content": "IDがないドキュメント"},  # IDなし
            {"id": "valid_2", "content": "別の正常なドキュメント"}
        ]

        result = fts.index(invalid_docs)
        assert result["ok"] is False
        assert "missing required 'id'" in result["error"].lower()

        # エラー後も正常に動作することを確認
        valid_docs = [
            {"id": "recovery_1", "content": "エラー後のドキュメント"}
        ]
        result = fts.index(valid_docs)
        assert result["ok"] is True

        # Test 2: 空のドキュメントリスト
        result = fts.index([])
        assert result["ok"] is False
        assert "No documents provided" in result["error"]

        # Test 3: 非常に大きなID
        large_id_doc = [{
            "id": "x" * 1000,  # 1000文字のID
            "content": "大きなIDのテスト"
        }]
        result = fts.index(large_id_doc)
        assert result["ok"] is True  # 大きなIDも受け入れる

        fts.close()

    def test_index_with_metadata(self):
        """メタデータを含むドキュメントのインデックス"""
        fts = create_fts(in_memory=True)

        # titleフィールドを含むドキュメント
        docs_with_metadata = [
            {
                "id": "meta_1",
                "title": "重要な仕様書",
                "content": "システムの詳細な仕様を記載"
            },
            {
                "id": "meta_2",
                "title": "API ドキュメント",
                "content": "REST APIのエンドポイント説明"
            },
            {
                "id": "meta_3",
                "title": "",  # 空のタイトル
                "content": "タイトルなしのドキュメント"
            },
            {
                "id": "meta_4",
                "content": "タイトルフィールドが存在しない"  # titleフィールドなし
            }
        ]

        result = fts.index(docs_with_metadata)
        assert result["ok"] is True
        assert result["indexed_count"] == 4

        # タイトルでの検索（タイトルも検索対象に含まれる場合）
        search_result = fts.search("仕様書")
        assert search_result["ok"] is True
        # タイトルまたはコンテンツに"仕様書"を含むドキュメントが見つかる

        # コンテンツでの検索
        search_result = fts.search("エンドポイント")
        assert search_result["ok"] is True
        assert len(search_result["results"]) >= 1

        fts.close()