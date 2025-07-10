"""
経営者とエンジニアのCypherクエリによる真のE2Eテスト（改良版）

実際のシステムを通じて：
1. 経営者がCypherで要件を登録
2. エンジニアがCypherで要件を登録  
3. システムが矛盾を検出してスコアリング
"""
import json
import subprocess
import os
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


def test_executive_vs_engineer_budget_conflict_real_e2e():
    """経営者とエンジニアの予算要件の矛盾を真のE2Eで検出"""
    # 一時ディレクトリとデータベースを作成
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test.db")

    try:
        # 環境変数設定
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'
        env['RGL_DB_PATH'] = test_db_path
        env['RGL_SKIP_SCHEMA_CHECK'] = 'true'

        # 1. スキーマ適用
        print("\n=== Step 1: スキーマ適用 ===")
        schema_result = run_command_with_env({
            "type": "schema",
            "action": "apply",
            "create_test_data": False
        }, env)

        assert schema_result["status"] == "success"
        print("スキーマ適用成功")

        timestamp = str(int(time.time() * 1000))

        # 2. 経営者: インフラ予算5万円制限をCypherで登録
        print("\n=== Step 2: 経営者の要件登録 ===")
        exec_result = run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (exec:RequirementEntity {{
                id: 'EXEC_BUDGET_{timestamp}',
                title: 'インフラ予算制限',
                description: '年間インフラ予算を5万円以内に抑える',
                priority: 250,
                status: 'approved',
                requirement_type: 'constraint'
            }})
            CREATE (loc:LocationURI {{id: 'req://EXEC_BUDGET_{timestamp}'}})
            CREATE (loc)-[:LOCATES]->(exec)
            """
        }, env)

        assert exec_result["status"] == "success"

        # 摩擦スコアを確認
        score_response = next((r for r in exec_result["responses"] if r.get("type") == "score"), None)
        if score_response:
            print(f"経営者要件のスコア: {score_response['data']['total']}")

        # 3. エンジニア: 高可用性インフラ（12万円）をCypherで要求
        print("\n=== Step 3: エンジニアの要件登録 ===")
        eng_result = run_command_with_env({
            "type": "cypher",
            "query": f"""
            CREATE (eng:RequirementEntity {{
                id: 'ENG_INFRA_{timestamp}',
                title: '高可用性インフラ構築',
                description: '99.99%の可用性を実現するインフラ（12万円必要）',
                priority: 200,
                status: 'proposed',
                requirement_type: 'infrastructure'
            }})
            CREATE (loc:LocationURI {{id: 'req://ENG_INFRA_{timestamp}'}})
            CREATE (loc)-[:LOCATES]->(eng)
            """
        }, env)

        assert eng_result["status"] == "success"

        # 摩擦スコアを確認
        score_response = next((r for r in eng_result["responses"] if r.get("type") == "score"), None)
        if score_response:
            print(f"エンジニア要件のスコア: {score_response['data']['total']}")
            frictions = score_response['data']['frictions']

            # 各摩擦の詳細を表示
            print("\n=== 摩擦分析詳細 ===")
            for friction_type, friction_data in frictions.items():
                if friction_data.get('score', 0) != 0:
                    print(f"{friction_type}: {friction_data}")

            # 矛盾検出を確認
            if 'contradiction' in frictions:
                contradiction = frictions['contradiction']
                print("\n=== 矛盾検出結果 ===")
                print(f"矛盾数: {contradiction['contradiction_count']}")
                print(f"スコア: {contradiction['score']}")
                print(f"メッセージ: {contradiction['message']}")

                # 矛盾の詳細があれば表示
                details = score_response['data'].get('details', {})
                if 'contradictions' in details:
                    contradictions_detail = details['contradictions']
                    if 'contradictions' in contradictions_detail:
                        for c in contradictions_detail['contradictions']:
                            print(f"矛盾詳細: {c}")

        # 4. 明示的な矛盾検出クエリ
        print("\n=== Step 4: 矛盾検出クエリ ===")
        analysis_result = run_command_with_env({
            "type": "cypher",
            "query": """
            MATCH (exec:RequirementEntity)
            WHERE exec.requirement_type = 'constraint' 
              AND exec.description CONTAINS '5万円'
            WITH exec
            
            MATCH (eng:RequirementEntity)
            WHERE eng.requirement_type = 'infrastructure'
              AND eng.description CONTAINS '12万円'
            
            RETURN {
                constraint: {
                    id: exec.id,
                    title: exec.title,
                    description: exec.description
                },
                requirement: {
                    id: eng.id,
                    title: eng.title,
                    description: eng.description
                },
                conflict_type: '予算超過',
                message: 'インフラ要求（12万円）が予算制限（5万円）を超過しています'
            } as conflict_analysis
            """
        }, env)

        assert analysis_result["status"] == "success"

        # 結果を確認
        result_response = next((r for r in analysis_result["responses"] if r.get("type") == "result"), None)
        if result_response and result_response.get("data"):
            conflict_data = result_response["data"][0][0]
            print("\n=== 矛盾分析結果 ===")
            print(f"制約: {conflict_data['constraint']['title']}")
            print(f"要求: {conflict_data['requirement']['title']}")
            print(f"矛盾タイプ: {conflict_data['conflict_type']}")
            print(f"メッセージ: {conflict_data['message']}")

            # テスト成功条件
            assert conflict_data['conflict_type'] == '予算超過'
            assert '12万円' in conflict_data['requirement']['description']
            assert '5万円' in conflict_data['constraint']['description']

        print("\n=== E2Eテスト成功 ===")

    finally:
        # クリーンアップ
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # 直接実行してデバッグ
    test_executive_vs_engineer_budget_conflict_real_e2e()
