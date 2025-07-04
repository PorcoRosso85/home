"""
予算矛盾検出のE2Eテスト（TDD Red）

現在のシステムに不足している機能：
- 要件の内容（金額など）を解析して矛盾を検出する機能
- CypherクエリからPythonの矛盾検出器へのブリッジ
"""
import json
import subprocess
import os
import pytest
import time
import tempfile
import shutil


def run_command_with_env(input_data: dict, env: dict) -> dict:
    """環境変数を指定してコマンドを実行"""
    venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
    run_py = os.path.join(os.path.dirname(__file__), 'run.py')
    
    result = subprocess.run(
        [venv_python, run_py],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.returncode != 0:
        return {
            "status": "error", 
            "message": result.stderr,
            "stdout": result.stdout
        }
    
    # JSONLを1行ずつパース
    lines = result.stdout.strip().split('\n')
    responses = []
    for line in lines:
        if line:
            try:
                responses.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    return {"status": "success", "responses": responses}


@pytest.mark.skip(reason="TDD Red: 予算矛盾検出機能は未実装")
def test_budget_conflict_detection_e2e():
    """予算制約と要求の矛盾を自動検出"""
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 環境変数設定
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'
        env['RGL_DB_PATH'] = test_db_path
        env['RGL_SKIP_SCHEMA_CHECK'] = 'true'
        
        # スキーマ適用
        schema_result = run_command_with_env({
            "type": "schema",
            "action": "apply",
            "create_test_data": False
        }, env)
        assert schema_result["status"] == "success"
        
        timestamp = str(int(time.time() * 1000))
        
        # 1. 経営者: 予算制約を登録
        exec_result = run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (exec:RequirementEntity {{
                id: 'EXEC_BUDGET_{timestamp}',
                title: 'インフラ予算上限',
                description: '年間インフラ予算は5万円以内',
                priority: 250,
                requirement_type: 'constraint',
                // 構造化データとして予算情報を格納
                constraint_data: '{{
                    "type": "budget_limit",
                    "resource": "infrastructure",
                    "amount": 50000,
                    "currency": "JPY"
                }}'
            }})
            """
        }, env)
        assert exec_result["status"] == "success"
        
        # 2. エンジニア: 予算超過の要求
        eng_result = run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (eng:RequirementEntity {{
                id: 'ENG_INFRA_{timestamp}',
                title: '高可用性インフラ',
                description: 'AWS上に冗長構成を構築',
                priority: 200,
                requirement_type: 'infrastructure',
                // 構造化データとして必要リソースを格納
                resource_data: '{{
                    "type": "budget_requirement",
                    "resource": "infrastructure",
                    "amount": 120000,
                    "currency": "JPY",
                    "justification": "冗長構成のため"
                }}'
            }})
            """
        }, env)
        assert eng_result["status"] == "success"
        
        # 期待される動作：自動的に予算矛盾が検出される
        score_response = next((r for r in eng_result["responses"] if r.get("type") == "score"), None)
        assert score_response is not None
        
        frictions = score_response['data']['frictions']
        
        # 予算矛盾が検出されていることを確認
        assert 'budget' in frictions or 'resource' in frictions
        
        # 矛盾の詳細に予算超過が含まれる
        details = score_response['data'].get('details', {})
        budget_conflicts = details.get('budget_conflicts', [])
        
        assert len(budget_conflicts) > 0
        conflict = budget_conflicts[0]
        assert conflict['constraint_amount'] == 50000
        assert conflict['required_amount'] == 120000
        assert conflict['shortage'] == 70000
        assert conflict['conflict_type'] == 'budget_overrun'
        
        # 健全性スコアが低下している
        total_score = score_response['data']['total']['total_score']
        assert total_score < -0.5  # 予算2倍以上なので大幅減点
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@pytest.mark.skip(reason="TDD Red: リソース競合検出機能は未実装")
def test_resource_allocation_conflict_e2e():
    """複数要件のリソース合計が制約を超過することを検出"""
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test.db")
    
    try:
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'
        env['RGL_DB_PATH'] = test_db_path
        env['RGL_SKIP_SCHEMA_CHECK'] = 'true'
        
        # スキーマ適用
        schema_result = run_command_with_env({
            "type": "schema",
            "action": "apply",
            "create_test_data": False
        }, env)
        assert schema_result["status"] == "success"
        
        timestamp = str(int(time.time() * 1000))
        
        # 1. DB接続プール上限を設定
        run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (constraint:RequirementEntity {{
                id: 'CONSTRAINT_DB_{timestamp}',
                title: 'DB接続プール上限',
                description: '最大100接続まで',
                priority: 255,
                requirement_type: 'constraint',
                constraint_data: '{{
                    "type": "resource_limit",
                    "resource": "db_connections",
                    "max": 100
                }}'
            }})
            """
        }, env)
        
        # 2. サービスA: 60接続必要
        run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (service_a:RequirementEntity {{
                id: 'SERVICE_A_{timestamp}',
                title: 'サービスA',
                description: 'ユーザー管理サービス',
                priority: 200,
                requirement_type: 'service',
                resource_data: '{{
                    "type": "resource_requirement",
                    "resource": "db_connections",
                    "required": 60
                }}'
            }})
            """
        }, env)
        
        # 3. サービスB: 50接続必要（合計110で超過）
        result = run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (service_b:RequirementEntity {{
                id: 'SERVICE_B_{timestamp}',
                title: 'サービスB',
                description: '注文処理サービス',
                priority: 200,
                requirement_type: 'service',
                resource_data: '{{
                    "type": "resource_requirement",
                    "resource": "db_connections",
                    "required": 50
                }}'
            }})
            """
        }, env)
        
        # リソース競合が検出される
        score_response = next((r for r in result["responses"] if r.get("type") == "score"), None)
        assert score_response is not None
        
        details = score_response['data'].get('details', {})
        resource_conflicts = details.get('resource_conflicts', [])
        
        assert len(resource_conflicts) > 0
        conflict = resource_conflicts[0]
        assert conflict['resource'] == 'db_connections'
        assert conflict['total_required'] == 110
        assert conflict['available'] == 100
        assert conflict['shortage'] == 10
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@pytest.mark.skip(reason="TDD Red: MVP vs 品質要求の矛盾検出は未実装")
def test_mvp_vs_quality_conflict_e2e():
    """MVP要求と品質要求の矛盾を検出"""
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test.db")
    
    try:
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'
        env['RGL_DB_PATH'] = test_db_path
        env['RGL_SKIP_SCHEMA_CHECK'] = 'true'
        
        # スキーマ適用
        schema_result = run_command_with_env({
            "type": "schema",
            "action": "apply",
            "create_test_data": False
        }, env)
        assert schema_result["status"] == "success"
        
        timestamp = str(int(time.time() * 1000))
        
        # 1. 経営者: MVP要求（機能40%、技術的負債許容）
        run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (mvp:RequirementEntity {{
                id: 'EXEC_MVP_{timestamp}',
                title: 'MVP早期リリース',
                description: '3ヶ月以内にMVPリリース',
                priority: 255,
                requirement_type: 'milestone',
                milestone_data: '{{
                    "type": "mvp",
                    "feature_coverage": 40,
                    "deadline": "2024-03-01",
                    "allow_technical_debt": true
                }}'
            }})
            """
        }, env)
        
        # 2. QA: 品質要求（テストカバレッジ90%、技術的負債拒否）
        result = run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (quality:RequirementEntity {{
                id: 'QA_QUALITY_{timestamp}',
                title: '品質基準',
                description: 'プロダクション品質の確保',
                priority: 200,
                requirement_type: 'quality',
                quality_data: '{{
                    "type": "quality_standard",
                    "test_coverage": 90,
                    "code_review": "mandatory",
                    "allow_technical_debt": false
                }}'
            }})
            """
        }, env)
        
        # MVP vs 品質の矛盾が検出される
        score_response = next((r for r in result["responses"] if r.get("type") == "score"), None)
        assert score_response is not None
        
        frictions = score_response['data']['frictions']
        
        # 品質矛盾が検出されている
        assert 'quality' in frictions or 'policy' in frictions
        
        details = score_response['data'].get('details', {})
        policy_conflicts = details.get('policy_conflicts', [])
        
        assert len(policy_conflicts) > 0
        conflict = policy_conflicts[0]
        assert conflict['conflict_type'] == 'mvp_vs_quality'
        assert conflict['mvp_coverage'] == 40
        assert conflict['required_coverage'] == 90
        assert conflict['technical_debt_mismatch'] == True
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=== 予算矛盾検出E2Eテスト（TDD Red）===")
    print("現在のシステムに不足している機能:")
    print("1. 要件の構造化データ（constraint_data, resource_data）の解析")
    print("2. Cypher実行時の自動矛盾検出")
    print("3. 予算、リソース、ポリシーレベルの矛盾検出")
    print("\nこれらの機能が実装されれば、経営者とエンジニアの要件矛盾が")
    print("Cypherクエリ実行時に自動的に検出されるようになります。")