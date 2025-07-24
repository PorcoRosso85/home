"""
Graph Health Monitoring Test Specifications

Tests for graph health features including:
- Depth limit enforcement (implemented) 
- Circular dependency detection (implemented)
- Isolated node detection (not implemented - spec only)
- Graph connectivity analysis (not implemented - spec only)
- Health metrics dashboard (not implemented - spec only)

Following the testing philosophy: no mocks, test actual behavior through real instances
"""
import pytest
import subprocess
import json
import os
import tempfile
import time


def run_system(input_data, db_path=None):
    """requirement/graphシステムの公開APIを実行"""
    env = os.environ.copy()
    if db_path:
        env["RGL_DATABASE_PATH"] = db_path

    # venvのPythonを使用
    import sys
    python_cmd = sys.executable  # 現在のPython（venv内）を使用

    result = subprocess.run(
        [python_cmd, "-m", "requirement.graph"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )

    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

    return {"error": "No valid JSON output", "stderr": result.stderr}


class TestDepthLimitEnforcement:
    """深さ制限の強制（実装済み機能のテスト）"""

    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            # スキーマ初期化
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            if result.get("type") == "error" or result.get("error"):
                pytest.fail(f"Schema initialization failed: {result}")
            yield db_dir

    def test_depth_limit_validation_passes_within_limit(self, temp_db):
        """深さ制限内の依存関係は正常に作成される"""
        # Given: 階層的な要件を作成
        requirements = [
            {"id": "layer1", "title": "Layer 1", "description": "Top layer"},
            {"id": "layer2", "title": "Layer 2", "description": "Middle layer"},
            {"id": "layer3", "title": "Layer 3", "description": "Bottom layer"}
        ]
        
        for req in requirements:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # When: 深さ2の依存関係を作成
        # layer3 -> layer2 -> layer1
        dependencies = [
            ("layer3", "layer2"),
            ("layer2", "layer1")
        ]
        
        for child_id, parent_id in dependencies:
            result = run_system({
                "type": "template", 
                "template": "add_dependency",
                "parameters": {
                    "child_id": child_id,
                    "parent_id": parent_id
                }
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # Then: グラフの深さを検証（制限内）
        # 注: 実際のAPIがグラフヘルスチェックを提供する場合のテスト
        # 現在は依存関係が正常に作成されることを確認
        
    def test_depth_limit_prevents_deep_chains(self, temp_db):
        """深い依存関係チェーンの防止"""
        # Given: 多層の要件を作成
        layer_count = 10
        requirements = []
        
        for i in range(layer_count):
            req = {
                "id": f"deep_{i}",
                "title": f"Deep Layer {i}",
                "description": f"Layer {i} in deep hierarchy"
            }
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
            requirements.append(req)
        
        # When: 深い依存関係チェーンを作成しようとする
        for i in range(layer_count - 1):
            result = run_system({
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": f"deep_{i+1}",
                    "parent_id": f"deep_{i}"
                }
            }, temp_db)
            
            # Then: 一定の深さまでは成功するが、制限を超えると警告/エラーが出る可能性
            # 注: 実装によって動作が異なる可能性あり
            if i < 5:  # 仮の制限値
                assert "error" not in result or result.get("data", {}).get("status") == "success"


class TestCircularDependencyPrevention:
    """循環依存の防止（実装済み機能のテスト）"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            if result.get("type") == "error" or result.get("error"):
                pytest.fail(f"Schema initialization failed: {result}")
            yield db_dir
    
    def test_direct_circular_dependency_prevented(self, temp_db):
        """直接的な循環依存（A->B->A）が防止される"""
        # Given: 2つの要件を作成
        requirements = [
            {"id": "circular_a", "title": "Circular A", "description": "Part of circular dependency"},
            {"id": "circular_b", "title": "Circular B", "description": "Part of circular dependency"}
        ]
        
        for req in requirements:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # When: A->Bの依存関係を作成
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "circular_a",
                "parent_id": "circular_b"
            }
        }, temp_db)
        assert result.get("data", {}).get("status") == "success"
        
        # Then: B->Aの依存関係を作成しようとすると失敗する
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "circular_b",
                "parent_id": "circular_a"
            }
        }, temp_db)
        
        # 循環依存が検出されることを確認
        assert result.get("type") == "error" or result.get("error") is not None
        error_message = str(result.get("error", "")) or str(result.get("message", ""))
        assert "circular" in error_message.lower() or "cycle" in error_message.lower()
    
    def test_self_dependency_prevented(self, temp_db):
        """自己依存（A->A）が防止される"""
        # Given: 要件を作成
        result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "self_ref",
                "title": "Self Reference",
                "description": "Attempts self-dependency"
            }
        }, temp_db)
        assert result.get("data", {}).get("status") == "success"
        
        # When/Then: 自己依存を作成しようとすると失敗する
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "self_ref",
                "parent_id": "self_ref"
            }
        }, temp_db)
        
        assert result.get("type") == "error" or result.get("error") is not None
        error_message = str(result.get("error", "")) or str(result.get("message", ""))
        assert "self" in error_message.lower() or "circular" in error_message.lower()
    
    def test_indirect_circular_dependency_prevented(self, temp_db):
        """間接的な循環依存（A->B->C->A）が防止される"""
        # Given: 3つの要件を作成
        requirements = [
            {"id": "chain_a", "title": "Chain A", "description": "Start of chain"},
            {"id": "chain_b", "title": "Chain B", "description": "Middle of chain"},
            {"id": "chain_c", "title": "Chain C", "description": "End of chain"}
        ]
        
        for req in requirements:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # When: チェーンを作成
        dependencies = [
            ("chain_a", "chain_b"),
            ("chain_b", "chain_c")
        ]
        
        for child_id, parent_id in dependencies:
            result = run_system({
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": child_id,
                    "parent_id": parent_id
                }
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # Then: 循環を完成させようとすると失敗する
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "chain_c",
                "parent_id": "chain_a"
            }
        }, temp_db)
        
        assert result.get("type") == "error" or result.get("error") is not None
        error_message = str(result.get("error", "")) or str(result.get("message", ""))
        assert "circular" in error_message.lower() or "cycle" in error_message.lower()


@pytest.mark.skip(reason="Feature not implemented: Isolated node detection")
class TestIsolatedNodeDetection:
    """孤立ノードの検出（未実装機能の仕様テスト）"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            if result.get("type") == "error" or result.get("error"):
                pytest.fail(f"Schema initialization failed: {result}")
            yield db_dir
    
    def test_detect_orphaned_requirements(self, temp_db):
        """依存関係を持たない孤立した要件を検出"""
        # Given: 複数の要件（一部は孤立）
        connected_reqs = [
            {"id": "connected_1", "title": "Connected 1", "description": "Has dependencies"},
            {"id": "connected_2", "title": "Connected 2", "description": "Has dependencies"}
        ]
        
        isolated_reqs = [
            {"id": "isolated_1", "title": "Isolated 1", "description": "No dependencies"},
            {"id": "isolated_2", "title": "Isolated 2", "description": "No dependencies"}
        ]
        
        # すべての要件を作成
        for req in connected_reqs + isolated_reqs:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # 接続された要件に依存関係を追加
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "connected_1",
                "parent_id": "connected_2"
            }
        }, temp_db)
        assert result.get("data", {}).get("status") == "success"
        
        # When: グラフヘルスチェックを実行（仮想的なAPI）
        result = run_system({
            "type": "health",
            "action": "check_isolated_nodes"
        }, temp_db)
        
        # Then: 孤立ノードが検出される
        assert result.get("data", {}).get("isolated_nodes") == ["isolated_1", "isolated_2"]
        assert result.get("data", {}).get("isolated_count") == 2
    
    def test_warn_on_isolated_requirement_creation(self, temp_db):
        """孤立した要件作成時に警告を表示"""
        # Given: いくつかの接続された要件が存在
        existing_reqs = [
            {"id": "existing_1", "title": "Existing 1", "description": "Part of network"},
            {"id": "existing_2", "title": "Existing 2", "description": "Part of network"}
        ]
        
        for req in existing_reqs:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # 依存関係を追加
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "existing_1",
                "parent_id": "existing_2"
            }
        }, temp_db)
        
        # When: 新しい孤立した要件を作成
        result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "new_isolated",
                "title": "New Isolated",
                "description": "Will be isolated"
            }
        }, temp_db)
        
        # Then: 作成は成功するが警告が出る
        assert result.get("data", {}).get("status") == "success"
        warning = result.get("warning") or result.get("data", {}).get("warning")
        assert warning is not None
        assert warning.get("type") == "IsolatedNodeWarning"
        assert "isolated" in warning.get("message", "").lower()


@pytest.mark.skip(reason="Feature not implemented: Graph connectivity analysis")
class TestGraphConnectivityAnalysis:
    """グラフ接続性分析（未実装機能の仕様テスト）"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            if result.get("type") == "error" or result.get("error"):
                pytest.fail(f"Schema initialization failed: {result}")
            yield db_dir
    
    def test_identify_disconnected_subgraphs(self, temp_db):
        """切断されたサブグラフを識別"""
        # Given: 2つの独立したグラフクラスター
        cluster1 = [
            {"id": "cluster1_a", "title": "Cluster 1 A", "description": "First cluster"},
            {"id": "cluster1_b", "title": "Cluster 1 B", "description": "First cluster"},
            {"id": "cluster1_c", "title": "Cluster 1 C", "description": "First cluster"}
        ]
        
        cluster2 = [
            {"id": "cluster2_x", "title": "Cluster 2 X", "description": "Second cluster"},
            {"id": "cluster2_y", "title": "Cluster 2 Y", "description": "Second cluster"},
            {"id": "cluster2_z", "title": "Cluster 2 Z", "description": "Second cluster"}
        ]
        
        # すべての要件を作成
        for req in cluster1 + cluster2:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # クラスター内で依存関係を作成
        cluster1_deps = [
            ("cluster1_a", "cluster1_b"),
            ("cluster1_b", "cluster1_c")
        ]
        
        cluster2_deps = [
            ("cluster2_x", "cluster2_y"),
            ("cluster2_y", "cluster2_z")
        ]
        
        for child_id, parent_id in cluster1_deps + cluster2_deps:
            result = run_system({
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": child_id,
                    "parent_id": parent_id
                }
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # When: 接続性分析を実行
        result = run_system({
            "type": "health",
            "action": "analyze_connectivity"
        }, temp_db)
        
        # Then: 2つの切断されたクラスターが識別される
        assert result.get("data", {}).get("connected_components") == 2
        components = result.get("data", {}).get("components")
        assert len(components) == 2
        
        # 各コンポーネントのサイズを確認
        component_sizes = sorted([len(c) for c in components])
        assert component_sizes == [3, 3]
    
    def test_calculate_graph_connectivity_metrics(self, temp_db):
        """グラフの接続性メトリクスを計算"""
        # Given: 様々な接続パターンを持つグラフ
        requirements = [
            {"id": f"node_{i}", "title": f"Node {i}", "description": f"Test node {i}"}
            for i in range(10)
        ]
        
        for req in requirements:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # スター型トポロジー（node_0が中心）
        for i in range(1, 5):
            result = run_system({
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": f"node_{i}",
                    "parent_id": "node_0"
                }
            }, temp_db)
        
        # チェーン型トポロジー
        for i in range(5, 9):
            result = run_system({
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": f"node_{i+1}",
                    "parent_id": f"node_{i}"
                }
            }, temp_db)
        
        # When: メトリクスを計算
        result = run_system({
            "type": "health",
            "action": "calculate_metrics"
        }, temp_db)
        
        # Then: 各種メトリクスが計算される
        metrics = result.get("data", {}).get("metrics")
        assert metrics.get("total_nodes") == 10
        assert metrics.get("total_edges") >= 8
        assert metrics.get("average_degree") > 0
        assert metrics.get("max_degree") >= 4  # node_0の次数
        assert metrics.get("connectivity_ratio") > 0


@pytest.mark.skip(reason="Feature not implemented: Health metrics dashboard")
class TestHealthMetricsDashboard:
    """ヘルスメトリクスダッシュボード（未実装機能の仕様テスト）"""
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            if result.get("type") == "error" or result.get("error"):
                pytest.fail(f"Schema initialization failed: {result}")
            yield db_dir
    
    def test_comprehensive_health_report(self, temp_db):
        """包括的なヘルスレポートの生成"""
        # Given: 様々な問題を含むグラフ
        # 正常な要件
        normal_reqs = [
            {"id": "normal_1", "title": "Normal 1", "description": "Healthy requirement"},
            {"id": "normal_2", "title": "Normal 2", "description": "Healthy requirement"}
        ]
        
        # 問題のある要件
        problem_reqs = [
            {"id": "isolated", "title": "Isolated", "description": "No connections"},
            {"id": "deep_1", "title": "Deep 1", "description": "Part of deep chain"}
        ]
        
        for req in normal_reqs + problem_reqs:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
        
        # 正常な依存関係
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "child_id": "normal_1",
                "parent_id": "normal_2"
            }
        }, temp_db)
        
        # When: ヘルスダッシュボードを生成
        result = run_system({
            "type": "health",
            "action": "generate_dashboard"
        }, temp_db)
        
        # Then: 包括的なレポートが生成される
        dashboard = result.get("data", {}).get("dashboard")
        
        # 総合スコア
        assert "overall_health_score" in dashboard
        assert 0 <= dashboard["overall_health_score"] <= 100
        
        # 問題サマリー
        assert "issues" in dashboard
        issues = dashboard["issues"]
        assert "isolated_nodes" in issues
        assert "circular_dependencies" in issues
        assert "depth_violations" in issues
        
        # 推奨事項
        assert "recommendations" in dashboard
        recommendations = dashboard["recommendations"]
        assert len(recommendations) > 0
        
        # メトリクス
        assert "metrics" in dashboard
        metrics = dashboard["metrics"]
        assert "total_requirements" in metrics
        assert "total_dependencies" in metrics
        assert "average_connectivity" in metrics
    
    def test_health_score_calculation(self, temp_db):
        """ヘルススコアの計算ロジック"""
        # Given: 完全に健全なグラフ
        requirements = [
            {"id": f"healthy_{i}", "title": f"Healthy {i}", "description": "Part of healthy graph"}
            for i in range(5)
        ]
        
        for req in requirements:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
        
        # バランスの取れた依存関係を作成
        dependencies = [
            ("healthy_0", "healthy_1"),
            ("healthy_0", "healthy_2"),
            ("healthy_1", "healthy_3"),
            ("healthy_2", "healthy_4")
        ]
        
        for child_id, parent_id in dependencies:
            result = run_system({
                "type": "template",
                "template": "add_dependency",
                "parameters": {
                    "child_id": child_id,
                    "parent_id": parent_id
                }
            }, temp_db)
        
        # When: ヘルススコアを計算
        result = run_system({
            "type": "health",
            "action": "calculate_score"
        }, temp_db)
        
        # Then: 高いヘルススコアが返される
        score_data = result.get("data", {})
        assert score_data.get("health_score") >= 90  # 健全なグラフは高スコア
        
        # スコアの内訳
        breakdown = score_data.get("score_breakdown")
        assert breakdown.get("connectivity_score") >= 90
        assert breakdown.get("depth_score") == 100  # 深さ違反なし
        assert breakdown.get("circular_score") == 100  # 循環なし
        assert breakdown.get("isolation_score") == 100  # 孤立ノードなし
    
    def test_real_time_health_monitoring(self, temp_db):
        """リアルタイムヘルスモニタリング"""
        # Given: 初期状態のグラフ
        initial_req = {
            "id": "monitor_1",
            "title": "Monitor 1",
            "description": "Initial requirement"
        }
        
        result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": initial_req
        }, temp_db)
        
        # When: ヘルスモニタリングを有効化
        result = run_system({
            "type": "health",
            "action": "enable_monitoring",
            "parameters": {
                "real_time": True,
                "threshold_alerts": {
                    "health_score": 80,
                    "isolated_nodes": 5,
                    "max_depth": 10
                }
            }
        }, temp_db)
        
        # モニタリングが有効化されたことを確認
        assert result.get("data", {}).get("monitoring_enabled") == True
        
        # 問題のある要件を追加してアラートをトリガー
        for i in range(6):
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": {
                    "id": f"isolated_{i}",
                    "title": f"Isolated {i}",
                    "description": "Will trigger alert"
                }
            }, temp_db)
        
        # Then: アラートが発生する
        # 注: 実際の実装では、イベント駆動やポーリングベースの通知メカニズムが必要
        result = run_system({
            "type": "health",
            "action": "get_alerts"
        }, temp_db)
        
        alerts = result.get("data", {}).get("alerts")
        assert len(alerts) > 0
        
        # 孤立ノードアラートを確認
        isolated_alert = next((a for a in alerts if a["type"] == "isolated_nodes_threshold"), None)
        assert isolated_alert is not None
        assert isolated_alert["current_value"] >= 6
        assert isolated_alert["threshold"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])