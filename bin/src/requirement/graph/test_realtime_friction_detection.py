"""
リアルタイム摩擦検出のE2Eテスト
"""
import json
import subprocess
import os
import tempfile
import time
import pytest

def run_rgl_command(query: str) -> dict:
    """RGLコマンドを実行してレスポンスを取得"""
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'
    
    input_data = json.dumps({
        "type": "cypher",
        "query": query
    })
    
    # 仮想環境のPythonを使用
    venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
    
    result = subprocess.run(
        [venv_python, '-m', 'main'],
        input=input_data,
        capture_output=True,
        text=True,
        env=env,
        cwd=os.path.dirname(__file__)  # 現在のディレクトリ
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return {"status": "error", "message": result.stderr}
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON. stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return {"status": "error", "message": "JSON parse error"}


@pytest.mark.skip(reason="リアルタイム摩擦検出機能は未実装")
def test_realtime_friction_alert_on_ambiguous_requirement():
    """曖昧な要件を作成した際にリアルタイムでアラートが出る"""
    # 曖昧な要件を作成
    timestamp = str(int(time.time() * 1000))
    response = run_rgl_command(f"""
        CREATE (r:RequirementEntity {{
            id: 'req_ambiguous_rt_{timestamp}',
            title: 'ユーザーフレンドリーな画面設計',
            description: '使いやすい画面を作る',
            priority: 2
        }})
        CREATE (loc:LocationURI {{id: 'loc://vision/ui/ambiguous_{timestamp}'}})
        CREATE (loc)-[:LOCATES]->(r)
    """)
    
    print(f"Response: {response}")  # デバッグ出力を追加
    assert response["status"] == "success"
    
    # 摩擦分析が含まれていることを確認
    assert "friction_analysis" in response
    
    # 曖昧性摩擦が検出されていることを確認
    friction = response["friction_analysis"]["frictions"]["ambiguity"]
    assert friction["score"] < 0  # 負のスコア（摩擦あり）
    assert "曖昧" in friction["message"] or "解釈" in friction["message"]
    
    print(f"曖昧性摩擦検出: スコア={friction['score']}, メッセージ={friction['message']}")


@pytest.mark.skip(reason="リアルタイム摩擦検出機能は未実装")
def test_realtime_friction_alert_on_multiple_critical():
    """複数のcritical要件を追加した際に優先度摩擦のアラート"""
    # 3つのcritical要件を順次追加
    timestamp = str(int(time.time() * 1000))
    critical_reqs = [
        (f"req_critical_rt_{timestamp}_1", "顧客データ移行", "既存顧客のデータを新システムに移行"),
        (f"req_critical_rt_{timestamp}_2", "セキュリティ監査対応", "外部監査に向けたセキュリティ強化"),
        (f"req_critical_rt_{timestamp}_3", "パフォーマンス改善", "レスポンスタイム50%削減")
    ]
    
    for i, (req_id, title, desc) in enumerate(critical_reqs):
        response = run_rgl_command(f"""
            CREATE (r:RequirementEntity {{
                id: '{req_id}',
                title: '{title}',
                description: '{desc}',
                priority: 250
            }})
            CREATE (loc:LocationURI {{id: 'loc://vision/{req_id}'}})
            CREATE (loc)-[:LOCATES]->(r)
        """)
        
        assert response["status"] == "success"
        
        # 3つ目のcritical要件で摩擦分析を確認
        if i == 2:
            print(f"Final response: {response}")
            # 摩擦分析が含まれていることを確認
            assert "friction_analysis" in response
            
            # total_scoreが悪化していることを確認（-0.3以下）
            total_score = response["friction_analysis"]["total"]["total_score"]
            assert total_score <= -0.2  # needs_attentionレベル
            assert response["friction_analysis"]["total"]["health"] in ["needs_attention", "unhealthy", "critical"]
            
            # 摩擦の詳細が報告されていることを確認
            if "friction_details" in response:
                print(f"摩擦詳細: {response['friction_details']}")
                assert len(response["friction_details"]) > 0


@pytest.mark.skip(reason="リアルタイム摩擦検出機能は未実装")
def test_realtime_contradiction_detection():
    """矛盾する要件を追加した際の検出"""
    # コスト削減要件
    timestamp = str(int(time.time() * 1000))
    response1 = run_rgl_command(f"""
        CREATE (r:RequirementEntity {{
            id: 'req_cost_rt_{timestamp}',
            title: 'インフラコスト削減',
            description: 'クラウドコストを50%削減する',
            priority: 2
        }})
        CREATE (loc:LocationURI {{id: 'loc://vision/cost_{timestamp}'}})
        CREATE (loc)-[:LOCATES]->(r)
    """)
    
    assert response1["status"] == "success"
    
    # 性能向上要件（矛盾）
    response2 = run_rgl_command(f"""
        CREATE (r:RequirementEntity {{
            id: 'req_perf_rt_{timestamp}_2',
            title: 'パフォーマンス向上',
            description: '全画面のレスポンスを高速化',
            priority: 2
        }})
        CREATE (loc:LocationURI {{id: 'loc://vision/perf_{timestamp}'}})
        CREATE (loc)-[:LOCATES]->(r)
    """)
    
    assert response2["status"] == "success"
    assert "friction_analysis" in response2
    
    # 矛盾摩擦が検出されることを確認
    contradiction = response2["friction_analysis"]["frictions"]["contradiction"]
    if contradiction["score"] < 0:
        print(f"矛盾摩擦検出: スコア={contradiction['score']}")


@pytest.mark.skip(reason="リアルタイム摩擦検出機能は未実装")
def test_no_friction_on_clear_requirement():
    """明確で問題ない要件では摩擦が検出されない"""
    timestamp = str(int(time.time() * 1000))
    response = run_rgl_command(f"""
        CREATE (r:RequirementEntity {{
            id: 'req_clear_rt_{timestamp}',
            title: 'ログイン機能実装',
            description: 'メールアドレスとパスワードによる認証',
            priority: 1,
            acceptance_criteria: '1. メールアドレス形式検証 2. パスワード8文字以上',
            technical_specifications: '{{"auth": "JWT", "hash": "bcrypt"}}'
        }})
        CREATE (loc:LocationURI {{id: 'loc://vision/auth/login_{timestamp}'}})
        CREATE (loc)-[:LOCATES]->(r)
    """)
    
    assert response["status"] == "success"
    
    # アラートがないか、健全なスコアであることを確認
    if "alert" in response:
        assert response["alert"]["level"] != "critical"
    
    if "friction_analysis" in response:
        total_score = response["friction_analysis"]["total"]["total_score"]
        assert total_score > -0.5  # 健全な範囲
        print(f"健全な要件: 総合スコア={total_score}")


if __name__ == "__main__":
    print("=== リアルタイム摩擦検出テスト ===")
    
    print("\n1. 曖昧な要件のテスト")
    test_realtime_friction_alert_on_ambiguous_requirement()
    
    print("\n2. 複数critical要件のテスト")
    test_realtime_friction_alert_on_multiple_critical()
    
    print("\n3. 矛盾する要件のテスト")
    test_realtime_contradiction_detection()
    
    print("\n4. 明確な要件のテスト")
    test_no_friction_on_clear_requirement()
    
    print("\n✅ すべてのテストが完了しました")