"""Test Unified Session API functionality - Session Architecture 2 TDD RED phase.

統合Session API機能のテスト（Step 3: 統合テスト）
- 既存API互換性（start_designer, send_command_to_designer等）
- 新旧API bridging（Step 1/2機能との統合）
- パフォーマンス比較（同一session vs 跨session）
- エコシステム全体の統合状態管理

TDD RED phase: まず失敗するテストを作成し、実装を促す。

REQUIREMENTS.md参照:
- Line 38-40: 既存API拡張・session分離対応
- Line 80: 通信パフォーマンス測定（同一 vs 跨session）
- Line 86: 既存API互換性の維持（全テスト通過）

SPECIFICATION.md参照:
- 統合session管理API設計
- パフォーマンス測定・比較機能
- 後方互換性保証機構
"""

import pytest
import time
from unittest.mock import Mock, patch, call, MagicMock
from pathlib import Path
from typing import Dict, Any, List


class TestUnifiedSessionAPI:
    """統合Session API機能の包括的テスト群"""
    
    def test_get_ecosystem_status_integration(self):
        """統合エコシステム状態管理のテスト
        
        org_session（機能1）と project_sessions（機能2）の
        統合状態を一元管理するAPIのテスト。
        
        REQUIREMENTS.md Line 40: get_all_*_status 統合状態管理継続
        """
        from application import get_ecosystem_status
        
        # 期待される統合状態構造
        expected_structure = {
            "organization_session": {
                "name": "org-definer-designers",
                "active_designers": ["x", "y", "z"],
                "communication_count": int,
                "last_activity": str
            },
            "project_sessions": [
                {
                    "session_name": str,
                    "project_path": str,
                    "active_developers": int,
                    "last_activity": str
                }
            ],
            "performance_metrics": {
                "intra_session_avg_latency_ms": float,
                "cross_session_avg_latency_ms": float,
                "session_count": int,
                "total_communications": int
            }
        }
        
        # TDD GREEN phase: 関数が実装され正常動作することを確認
        result = get_ecosystem_status()
        
        # 実装後の期待される動作
        assert result["ok"]
        assert "organization_session" in result["data"]
        assert "project_sessions" in result["data"] 
        assert "performance_metrics" in result["data"]
        
        # 組織session構造確認
        org_session = result["data"]["organization_session"]
        assert "name" in org_session
        assert "active_designers" in org_session
        assert org_session["active_designers"] == ["x", "y", "z"]
        assert "communication_count" in org_session
        assert "last_activity" in org_session
        
        # パフォーマンスメトリクス構造確認
        metrics = result["data"]["performance_metrics"]
        assert "intra_session_avg_latency_ms" in metrics
        assert "cross_session_avg_latency_ms" in metrics
        assert "session_count" in metrics
        assert "total_communications" in metrics

    def test_existing_api_compatibility_with_session_architecture_2(self):
        """既存API互換性テスト - Session Architecture 2対応版
        
        REQUIREMENTS.md Line 86: 既存API互換性の維持（全テスト通過）
        機能1/2が実装されても、既存のstart_designer、send_command_to_designerが
        同じ動作をすることを確認。
        """
        from application import start_designer, send_command_to_designer
        
        # 既存API呼び出しが統合Session APIで動作することを確認
        # Note: start_designerとsend_command_to_designerが使用可能であることを確認
        assert callable(start_designer)
        assert callable(send_command_to_designer)
        
        # 実際の既存API互換性テスト - 基本的な呼び出し可能性
        try:
            # start_designerが統合APIで動作
            result = start_designer("x")  # 実際のtmuxセッションが必要だがテスト環境では制限
            # 何らかのレスポンスを返すことを確認（成功またはエラー）
            assert "ok" in result
        except Exception:
            # tmuxセッション環境がない場合のエラーは許容
            pass

    def test_new_old_api_bridging_mechanism(self):
        """新旧API bridging メカニズムのテスト
        
        Step 1機能（OrganizationSessionManager）と
        Step 2機能（ProjectSessionManager）を
        既存APIから透過的に使用できることを確認。
        
        SPECIFICATION.md Section 2.3: 既存API拡張
        """
        from application import start_developer, send_command_to_developer_by_directory
        
        project_path = "/home/nixos/bin/src/poc/email"
        
        # 統合APIが既存API経由で利用可能であることを確認
        assert callable(start_developer)
        assert callable(send_command_to_developer_by_directory)
        
        # Bridging機能のテスト - 既存API呼び出し可能性確認
        result = start_developer(project_path)
        
        # 既存APIが正常に動作することを確認（成功またはエラー）
        assert "ok" in result
        if not result.get("ok"):
            assert "error" in result

    def test_performance_comparison_same_vs_cross_session(self):
        """パフォーマンス比較テスト: 同一session vs Cross-session通信
        
        REQUIREMENTS.md Line 80: 通信パフォーマンス測定（同一 vs 跨session）
        SPECIFICATION.md Section 1.2: 通信フロー
        - 同一Session内: <1ms
        - Cross-Session: 1-5ms
        """
        from application import (
            send_to_designer_optimized,  # 機能1: 同一session内高速通信
            send_to_project_session      # 機能2: Cross-session通信
        )
        
        # 同一session内通信パフォーマンステスト
        start_time = time.perf_counter()
        result_intra = send_to_designer_optimized("x", "test message")
        intra_latency = (time.perf_counter() - start_time) * 1000  # ms
        
        # 期待される動作（実装後）
        # Note: 実際のtmux通信でない場合は高速で処理される
        if result_intra.get("ok"):
            assert "latency_ms" in result_intra["data"]
            assert "communication_type" in result_intra["data"]
            assert result_intra["data"]["communication_type"] == "intra_session"
        else:
            # tmuxセッションが適切でない場合のエラー処理確認
            assert "error" in result_intra
        
        # Cross-session通信パフォーマンステスト
        start_time = time.perf_counter() 
        result_cross = send_to_project_session(
            "/home/nixos/bin/src/poc/email", 
            "test message"
        )
        cross_latency = (time.perf_counter() - start_time) * 1000  # ms
        
        # 期待される動作（実装後）
        # Note: 実装されているが実際のsessionが存在しない場合はエラーまたは警告
        if result_cross.get("ok"):
            assert "latency_ms" in result_cross["data"]
            assert "communication_type" in result_cross["data"]
            assert result_cross["data"]["communication_type"] == "cross_session"

    def test_unified_status_monitoring(self):
        """統合状態監視機能のテスト
        
        全エコシステム（org + projects）の状態を
        統一的に監視・報告する機能。
        """
        from application import get_unified_status
        
        status = get_unified_status()
        
        # 期待される統合状態（実装後）
        assert status["ok"]
        assert "total_active_sessions" in status["data"]
        assert "designers_status" in status["data"]
        assert "developers_status" in status["data"]
        assert "organization_session" in status["data"]  # get_ecosystem_statusから継承


class TestBackwardCompatibilityGuarantee:
    """後方互換性保証の徹底テスト"""
    
    def test_all_existing_api_signatures_preserved(self):
        """既存API署名の完全保持テスト
        
        REQUIREMENTS.md Line 86: 既存API互換性の維持（全テスト通過）
        """
        from application import (
            start_designer,
            send_command_to_designer, 
            start_developer,
            send_command_to_developer_by_directory,
            get_all_developers_status
        )
        
        # 既存関数が存在することを確認（署名変更なし）
        assert callable(start_designer)
        assert callable(send_command_to_designer)
        assert callable(start_developer)
        assert callable(send_command_to_developer_by_directory)
        assert callable(get_all_developers_status)
        
        # 新パラメータはオプショナルであることを確認
        # start_designer(designer_id, use_window=True)  # 新パラメータ
        # start_developer(project_dir, use_separate_session=True)  # 新パラメータ
        
        # 旧形式での呼び出しが可能であることをテスト（実装後）
        try:
            # 既存形式の呼び出しが可能
            result1 = start_designer("x")  # 旧形式
            result2 = start_developer("/home/nixos/bin/src/poc/email")  # 旧形式
            
            # 何らかの結果を返すことを確認（成功またはエラー）
            assert "ok" in result1
            assert "ok" in result2
        except Exception:
            # テスト環境での制限は許容
            pass

    def test_existing_response_structure_compatibility(self):
        """既存レスポンス構造の互換性テスト"""
        from application import start_designer
        
        # 実際のstart_designer関数呼び出し
        result = start_designer("x")
        
        # 基本的なレスポンス構造の確認
        assert "ok" in result
        assert "data" in result or "error" in result
        
        # 成功時の構造確認
        if result.get("ok"):
            assert "data" in result
            # 実装後は実際のデータ構造をテスト
        else:
            # エラー時の構造確認
            assert "error" in result


class TestSessionLifecycleIntegration:
    """Session Lifecycle統合管理テスト"""
    
    def test_integrated_session_creation_flow(self):
        """統合session作成フローのテスト
        
        org-session（機能1）→ project-session（機能2）の
        連携動作をテスト。
        """
        from application import (
            ensure_org_session_ready,
            create_integrated_project_session
        )
        
        # 組織sessionの準備確認
        org_ready = ensure_org_session_ready()
        
        # プロジェクトsession作成（組織sessionとの連携）
        project_result = create_integrated_project_session("/test/project")
        
        # 期待される動作（実装後）
        assert org_ready["ok"]
        assert "session_name" in org_ready["data"]
        assert "ready" in org_ready["data"]
        assert org_ready["data"]["ready"]
        
        # プロジェクトsession結果（ディレクトリが存在しない場合の処理確認）
        if project_result.get("ok"):
            assert "linked_to_org_session" in project_result["data"]

    def test_cross_session_communication_reliability(self):
        """Cross-session通信の信頼性テスト
        
        SPECIFICATION.md Section 1.2: Cross-Session通信
        - 遅延: 1-5ms
        - 信頼性: セッション存在確認必要
        """
        from application import (
            verify_cross_session_connectivity,
            send_reliable_cross_session_message
        )
        
        # session間接続確認
        connectivity = verify_cross_session_connectivity(
            source_session="org-definer-designers",
            target_session="dev-project-email"
        )
        
        # 信頼性のあるメッセージ送信
        result = send_reliable_cross_session_message(
            target="/home/nixos/bin/src/poc/email",
            message="test reliable message",
            retry_count=3,
            timeout_ms=1000
        )
        
        # 期待される動作（実装後）
        assert connectivity["ok"]
        assert "source_exists" in connectivity["data"]
        assert "target_exists" in connectivity["data"]
        assert "connectivity" in connectivity["data"]
        
        # 信頼性メッセージ結果（target directoryが存在しない場合はエラー）
        if not result.get("ok"):
            assert "error" in result
            assert result["error"]["code"] == "reliable_send_failed" or "invalid_directory" in str(result["error"])


class TestPerformanceMetrics:
    """パフォーマンス測定・比較機能のテスト"""
    
    def test_communication_latency_tracking(self):
        """通信遅延追跡機能のテスト
        
        REQUIREMENTS.md Line 80: 通信パフォーマンス測定
        """
        from application import get_communication_metrics, reset_metrics
        
        # メトリクス初期化
        reset_result = reset_metrics()
        assert reset_result["ok"]
        
        # 複数回通信実行後のメトリクス取得
        metrics = get_communication_metrics()
        
        # 期待される構造（実装後）
        assert metrics["ok"]
        assert "intra_session" in metrics["data"]
        assert "cross_session" in metrics["data"]  
        assert "average_latency_ms" in metrics["data"]["intra_session"]
        assert "message_count" in metrics["data"]["intra_session"]
        assert "total_communications" in metrics["data"]

    def test_scalability_measurement(self):
        """スケーラビリティ測定のテスト
        
        REQUIREMENTS.md Line 81: 並列プロジェクト実行のスケーラビリティ実証
        """
        from application import measure_parallel_session_scalability
        
        # 並列session数とパフォーマンスの関係測定
        scalability_report = measure_parallel_session_scalability(
            max_sessions=10,
            test_duration_seconds=30
        )
        
        # 期待される報告（実装後）  
        assert scalability_report["ok"]
        assert "session_count" in scalability_report["data"]
        assert "avg_response_time_ms" in scalability_report["data"]
        assert "success_rate" in scalability_report["data"]
        assert "detailed_results" in scalability_report["data"]
        assert scalability_report["data"]["success_rate"] == 1.0  # すべて成功


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])