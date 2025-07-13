"""
POC Search完全統合の仕様テスト
このテストは現在失敗するべき（TDD RED状態）
"""
import subprocess
import json
import os
import sys
import tempfile
import pytest


def run_system(input_data, db_path=None):
    """requirement/graphシステムの公開APIを実行"""
    env = os.environ.copy()
    if db_path:
        env["RGL_DATABASE_PATH"] = db_path
    
    # venvのPythonを使用
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
    if os.path.exists(venv_python):
        python_cmd = venv_python
    else:
        python_cmd = sys.executable
    
    # プロジェクトルートから実行
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = subprocess.run(
        [python_cmd, "-m", "requirement.graph"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
        cwd=project_root
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


class TestPOCSearchCompleteIntegration:
    """POC Search完全統合の仕様
    
    要求仕様:
    1. POC searchのAPIを直接使用（一切の独自実装禁止）
    2. ハイブリッド検索（VSS + FTS）を実行
    3. エンベディングの生成と保存
    4. 同一DBインスタンスの共有
    """
    
    @pytest.fixture
    def temp_db(self):
        """一時的なデータベース環境"""
        with tempfile.TemporaryDirectory() as db_dir:
            # スキーマ初期化
            result = run_system({"type": "schema", "action": "apply"}, db_dir)
            yield db_dir
    
    def test_hybrid_search_integration(self, temp_db):
        """ハイブリッド検索（VSS + FTS）が動作する"""
        # Given: 要件を作成
        create_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_001",
                "title": "ユーザー認証システム",
                "description": "ログイン機能の実装"
            }
        }, temp_db)
        
        assert "error" not in create_result
        
        # When: 類似要件を作成しようとする
        duplicate_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_002",
                "title": "認証システム",
                "description": "ユーザーログイン機能"
            }
        }, temp_db)
        
        # Then: ハイブリッド検索により重複が検出される
        assert "warning" in duplicate_result or "warning" in duplicate_result.get("data", {})
        
        # 警告の詳細を確認
        warning = duplicate_result.get("warning") or duplicate_result.get("data", {}).get("warning")
        assert warning is not None
        assert warning.get("type") == "DuplicateWarning"
        assert len(warning.get("duplicates", [])) > 0
        
        # ハイブリッド検索の結果であることを確認
        duplicate = warning["duplicates"][0]
        assert duplicate.get("type") == "hybrid"  # VSS + FTSの結果
        assert duplicate.get("score") > 0.5  # 類似度スコア
    
    def test_embedding_generation_and_storage(self, temp_db):
        """エンベディングが生成され保存される"""
        # Given: 要件を作成
        create_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "req_emb_001",
                "title": "テスト要件",
                "description": "エンベディング生成テスト"
            }
        }, temp_db)
        
        assert "error" not in create_result
        
        # When: 作成した要件を検索
        find_result = run_system({
            "type": "template",
            "template": "find_requirement",
            "parameters": {"id": "req_emb_001"}
        }, temp_db)
        
        # Then: エンベディングが保存されている
        assert "error" not in find_result
        data = find_result.get("data", [])
        assert len(data) > 0
        
        requirement = data[0][0] if isinstance(data[0], list) else data[0]
        assert "embedding" in requirement
        # エンベディングは256次元のベクトル
        assert requirement["embedding"] is not None
        assert len(requirement["embedding"]) == 256
    
    def test_poc_search_api_usage(self, temp_db):
        """POC searchのAPIが正しく使用される"""
        # このテストは実装の詳細ではなく、振る舞いを検証
        # POC searchが動作していることを間接的に確認
        
        # Given: 複数の要件を作成
        requirements = [
            {"id": "api_001", "title": "ユーザー管理", "description": "ユーザー情報の管理"},
            {"id": "api_002", "title": "認証機能", "description": "ログイン認証の実装"},
            {"id": "api_003", "title": "データベース設計", "description": "RDBMSの設計"}
        ]
        
        for req in requirements:
            result = run_system({
                "type": "template",
                "template": "create_requirement",
                "parameters": req
            }, temp_db)
            assert "error" not in result
        
        # When: 類似検索を実行（新しい要件作成時）
        search_result = run_system({
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "api_004",
                "title": "ユーザー認証管理",
                "description": "ユーザーのログイン管理機能"
            }
        }, temp_db)
        
        # Then: 複数の類似要件が検出される
        warning = search_result.get("warning") or search_result.get("data", {}).get("warning")
        assert warning is not None
        duplicates = warning.get("duplicates", [])
        
        # 複数の関連要件が見つかる（ハイブリッド検索の特徴）
        assert len(duplicates) >= 2
        
        # スコア順にソートされている
        scores = [d["score"] for d in duplicates]
        assert scores == sorted(scores, reverse=True)


# このテストファイルを実行すると、現在は全て失敗するはず（TDD RED）
# POC search統合が正しく実装されたら、これらのテストが通るようになる