"""
Requirement Graph - LLM専用エントリーポイント

使い方:
    echo '{"type": "cypher", "query": "CREATE ..."}' | LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ python -m requirement.graph.main
    
戻り値:
    {"status": "success|error", "score": -1.0~1.0, "message": "..."}
"""
import sys
import json
import os

# 相対インポートのみ使用
from .infrastructure.llm_hooks_api import create_llm_hooks_api
from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.hierarchy_validator import HierarchyValidator
from .infrastructure.variables import get_db_path

def main():
    """LLMからのCypherクエリを受け取り、検証・実行・フィードバックを返す"""
    try:
        # 標準入力からJSONを読む
        input_data = json.loads(sys.stdin.read())
        
        # 階層検証は最初に実行（DBアクセス前）
        hierarchy_validator = HierarchyValidator()
        
        # Cypherクエリの場合は階層検証を実行
        if input_data.get("type") == "cypher":
            query = input_data.get("query", "")
            
            # 階層検証
            hierarchy_result = hierarchy_validator.validate_hierarchy_constraints(query)
            
            if not hierarchy_result["is_valid"]:
                # 階層違反 - 負のフィードバック
                response = {
                    "status": "error",
                    "score": hierarchy_result["score"],
                    "message": hierarchy_result["error"],
                    "details": hierarchy_result["details"],
                    "suggestion": "階層ルールに従ってください。親は子より上位の階層である必要があります。"
                }
                print(json.dumps(response, ensure_ascii=False))
                return
            
            # 警告がある場合
            if hierarchy_result["warning"]:
                # クエリは実行するが、警告を含める
                input_data["_hierarchy_warning"] = hierarchy_result["warning"]
                input_data["_hierarchy_score"] = hierarchy_result["score"]
        
        # 階層検証を通過した場合のみDBアクセス
        # KuzuDBリポジトリを作成
        repository = create_kuzu_repository()
        
        # 階層検証機能を統合したAPIを作成
        api = create_llm_hooks_api(repository)
        
        # APIを実行
        result = api["query"](input_data)
        
        # 階層警告を結果に含める
        if "_hierarchy_warning" in input_data:
            result["warning"] = input_data["_hierarchy_warning"]
            result["score"] = max(result.get("score", 0.0), input_data["_hierarchy_score"])
        
        print(json.dumps(result, ensure_ascii=False))
        
    except json.JSONDecodeError:
        error_response = {
            "status": "error",
            "score": -0.5,
            "message": "Invalid JSON input",
            "suggestion": "正しいJSON形式で入力してください"
        }
        print(json.dumps(error_response, ensure_ascii=False))
    except Exception as e:
        error_response = {
            "status": "error",
            "score": -0.5,
            "message": str(e),
            "suggestion": "エラーが発生しました。クエリを確認してください"
        }
        print(json.dumps(error_response, ensure_ascii=False))

def test_main_階層違反クエリ_エラーレスポンスとスコアマイナス1():
    """main_階層違反Cypherクエリ_適切なJSONエラーレスポンス"""
    import io
    import contextlib
    
    # 標準入力をモック
    test_input = json.dumps({
        "type": "cypher",
        "query": """
        CREATE (task:RequirementEntity {
            id: 'test_task',
            title: 'タスク実装'
        }),
        (vision:RequirementEntity {
            id: 'test_vision',
            title: 'ビジョン'
        }),
        (task)-[:DEPENDS_ON]->(vision)
        """
    })
    
    # 標準出力をキャプチャ
    output = io.StringIO()
    
    # mainを実行（標準入出力を置き換え）
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    try:
        sys.stdin = io.StringIO(test_input)
        sys.stdout = output
        main()
    finally:
        sys.stdin = original_stdin
        sys.stdout = original_stdout
    
    # レスポンスを検証
    response = json.loads(output.getvalue())
    assert response["status"] == "error"
    assert response["score"] == -1.0
    assert "階層違反" in response["message"]
    assert "階層ルールに従ってください" in response["suggestion"]


def test_main_正常クエリ_KuzuDB実行へ進む():
    """main_正常なCypherクエリ_階層検証を通過してDB実行へ"""
    import io
    
    test_input = json.dumps({
        "type": "cypher",
        "query": """
        CREATE (arch:RequirementEntity {
            id: 'test_arch',
            title: 'アーキテクチャ設計'
        }),
        (module:RequirementEntity {
            id: 'test_module',
            title: 'モジュール実装'
        }),
        (arch)-[:DEPENDS_ON]->(module)
        """
    })
    
    output = io.StringIO()
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    
    try:
        sys.stdin = io.StringIO(test_input)
        sys.stdout = output
        # 環境変数が未設定の場合のエラーハンドリングも含む
        try:
            main()
        except EnvironmentError:
            # 環境変数未設定は想定内
            pass
    finally:
        sys.stdin = original_stdin
        sys.stdout = original_stdout
    
    # 階層違反エラーが出ていないことを確認
    output_str = output.getvalue()
    if output_str:
        response = json.loads(output_str)
        # 階層違反以外のエラー（環境変数など）は許容
        if response.get("message"):
            assert "階層違反" not in response["message"]


def test_実DB統合_要件作成からクエリまで():
    """実DB統合_要件作成と取得_エンドツーエンドで動作確認"""
    import tempfile
    import subprocess
    
    # テスト用の一時DBディレクトリ
    with tempfile.TemporaryDirectory() as temp_db:
        # 環境変数設定
        env = os.environ.copy()
        env['RGL_DB_PATH'] = temp_db
        env['LD_LIBRARY_PATH'] = os.environ.get('LD_LIBRARY_PATH', '')
        
        # 1. スキーマ初期化
        schema_cmd = [
            sys.executable, '-m', 
            'requirement.graph.infrastructure.apply_ddl_schema'
        ]
        result = subprocess.run(
            schema_cmd, 
            env=env, 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        assert result.returncode == 0, f"Schema init failed: {result.stderr}"
        
        # 2. 要件を作成
        create_input = json.dumps({
            "type": "cypher",
            "query": """
                CREATE (vision:RequirementEntity {
                    id: 'test_vision_db',
                    title: 'システムビジョン',
                    description: 'テスト用ビジョン',
                    priority: 'high',
                    requirement_type: 'functional',
                    verification_required: true
                })
            """
        })
        
        main_cmd = [sys.executable, '-m', 'requirement.graph.main']
        result = subprocess.run(
            main_cmd,
            input=create_input,
            env=env,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        assert result.returncode == 0, f"Create failed: {result.stderr}"
        
        create_response = json.loads(result.stdout)
        assert create_response["status"] == "success", f"Create failed: {create_response}"
        
        # 3. 作成した要件を取得
        query_input = json.dumps({
            "type": "cypher",
            "query": "MATCH (r:RequirementEntity {id: 'test_vision_db'}) RETURN r.title"
        })
        
        result = subprocess.run(
            main_cmd,
            input=query_input,
            env=env,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        assert result.returncode == 0, f"Query failed: {result.stderr}"
        
        query_response = json.loads(result.stdout)
        assert query_response["status"] == "success"
        assert query_response["data"][0][0] == "システムビジョン"
