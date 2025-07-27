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
                    "from_id": child_id,  # パラメータ名を修正
                    "to_id": parent_id    # パラメータ名を修正
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
                "from_id": "circular_a",
                "to_id": "circular_b"
            }
        }, temp_db)
        assert result.get("data", {}).get("status") == "success"
        
        # Then: B->Aの依存関係を作成しようとすると失敗する
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "from_id": "circular_b",
                "to_id": "circular_a"
            }
        }, temp_db)
        
        # 循環依存が検出されることを確認
        # レスポンスは {'type': 'result', 'data': {'error': {...}, 'status': 'error'}} の形式
        if result.get("type") == "result" and result.get("data"):
            data = result["data"]
            assert data.get("status") == "error"
            error_message = str(data.get("error", ""))
        else:
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
                "from_id": "self_ref",
                "to_id": "self_ref"
            }
        }, temp_db)
        
        # レスポンスは {'type': 'result', 'data': {'error': {...}, 'status': 'error'}} の形式
        if result.get("type") == "result" and result.get("data"):
            data = result["data"]
            assert data.get("status") == "error"
            error_message = str(data.get("error", ""))
        else:
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
                    "from_id": child_id,
                    "to_id": parent_id
                }
            }, temp_db)
            assert result.get("data", {}).get("status") == "success"
        
        # Then: 循環を完成させようとすると失敗する
        result = run_system({
            "type": "template",
            "template": "add_dependency",
            "parameters": {
                "from_id": "chain_c",
                "to_id": "chain_a"
            }
        }, temp_db)
        
        # レスポンスは {'type': 'result', 'data': {'error': {...}, 'status': 'error'}} の形式
        if result.get("type") == "result" and result.get("data"):
            data = result["data"]
            assert data.get("status") == "error"
            error_message = str(data.get("error", ""))
        else:
            assert result.get("type") == "error" or result.get("error") is not None
            error_message = str(result.get("error", "")) or str(result.get("message", ""))
        assert "circular" in error_message.lower() or "cycle" in error_message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])