"""
LocationURI階層自動生成テスト（TDD Red）

ファイルパスベースのLocationURIから、中間階層ノードを自動生成し、
要件の粒度を物理的な構造と連携させる。
"""
import pytest
import json
import sys
import io
import os

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()


class TestLocationURIHierarchy:
    """LocationURI階層構造の自動生成テスト"""
    
    @pytest.mark.skip(reason="TDD Red: LocationURI階層機能待ち")
    def test_ファイルパスから階層構造を自動生成(self):
        """
        /src/auth/login.py#L42 から以下を自動生成：
        - /src/auth/login.py#L42 (最も具体的)
        - /src/auth/login.py (ファイルレベル)
        - /src/auth (モジュールレベル)
        - /src (ソースルート)
        - / (プロジェクトルート)
        """
        from .main import main
        
        # ファイルパスベースの要件を作成
        test_input = json.dumps({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'REQ-AUTH-001',
                title: 'パスワード検証ロジック',
                location_uri: '/src/auth/login.py#L42'
            })
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(test_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 階層構造が生成されたことを確認
        verify_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (l:LocationURI)
            WHERE l.id IN [
                '/src/auth/login.py#L42',
                '/src/auth/login.py',
                '/src/auth',
                '/src',
                '/'
            ]
            RETURN l.id ORDER BY l.id
            """
        })
        
        output = io.StringIO()
        try:
            sys.stdin = io.StringIO(verify_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        locations = result_lines[0]["data"]
        assert len(locations) == 5
        assert "/" in locations
        assert "/src" in locations
        assert "/src/auth" in locations
        assert "/src/auth/login.py" in locations
        assert "/src/auth/login.py#L42" in locations
    
    @pytest.mark.skip(reason="TDD Red: LocationURI階層機能待ち")
    def test_階層間にCONTAINS_LOCATION関係が構築される(self):
        """親ディレクトリが子要素を含む関係が自動構築される"""
        from .main import main
        
        # CONTAINS_LOCATION関係を確認
        verify_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (parent:LocationURI {id: '/src/auth'})
            MATCH (parent)-[:CONTAINS_LOCATION]->(child:LocationURI)
            RETURN child.id ORDER BY child.id
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(verify_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        children = result_lines[0]["data"]
        assert "/src/auth/login.py" in children
    
    @pytest.mark.skip(reason="TDD Red: LocationURI階層機能待ち")
    def test_モジュール単位で要件を集約できる(self):
        """特定ディレクトリ配下の全要件を取得できる"""
        from .main import main
        
        # 複数の要件を異なるファイルに作成
        for file, req_id, title in [
            ("/src/auth/login.py#L42", "REQ-AUTH-001", "パスワード検証"),
            ("/src/auth/login.py#L108", "REQ-AUTH-002", "ログイン試行制限"),
            ("/src/auth/register.py#L15", "REQ-AUTH-003", "ユーザー登録"),
            ("/src/payment/checkout.py#L200", "REQ-PAY-001", "決済処理")
        ]:
            create_input = json.dumps({
                "type": "cypher",
                "query": f"""
                CREATE (r:RequirementEntity {{
                    id: '{req_id}',
                    title: '{title}',
                    location_uri: '{file}'
                }})
                """
            })
            
            output = io.StringIO()
            try:
                sys.stdin = io.StringIO(create_input)
                sys.stdout = output
                main()
            finally:
                sys.stdin = original_stdin
                sys.stdout = original_stdout
        
        # /src/auth配下の要件を集約
        aggregate_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (module:LocationURI {id: '/src/auth'})
            MATCH (module)-[:CONTAINS_LOCATION*]->(file:LocationURI)
            MATCH (file)-[:LOCATES]->(r:RequirementEntity)
            RETURN r.id, r.title ORDER BY r.id
            """
        })
        
        output = io.StringIO()
        try:
            sys.stdin = io.StringIO(aggregate_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        auth_reqs = result_lines[0]["data"]
        assert len(auth_reqs) == 3
        assert all(req[0].startswith("REQ-AUTH-") for req in auth_reqs)
    
    @pytest.mark.skip(reason="TDD Red: LocationURI階層機能待ち")
    def test_要件移動時に階層構造が更新される(self):
        """要件のlocation_uriを変更すると階層構造も更新される"""
        from .main import main
        
        # 要件を別のモジュールに移動
        move_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (r:RequirementEntity {id: 'REQ-AUTH-001'})
            SET r.location_uri = '/src/security/auth/password.py#L10'
            RETURN r
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(move_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 新しい階層が生成されたことを確認
        verify_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (l:LocationURI)
            WHERE l.id IN ['/src/security', '/src/security/auth']
            RETURN l.id
            """
        })
        
        output = io.StringIO()
        try:
            sys.stdin = io.StringIO(verify_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        new_locations = result_lines[0]["data"]
        assert "/src/security" in new_locations
        assert "/src/security/auth" in new_locations
    
    @pytest.mark.skip(reason="TDD Red: LocationURI階層機能待ち")
    def test_階層レベルに応じた要件の粒度分析(self):
        """階層の深さから要件の粒度を自動判定"""
        from .main import main
        
        # 粒度分析クエリ
        granularity_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (l:LocationURI)-[:LOCATES]->(r:RequirementEntity)
            WITH l, r, size(split(l.id, '/')) - 1 as depth
            RETURN r.id, r.title, depth, 
                   CASE 
                     WHEN depth = 0 THEN 'project'
                     WHEN depth = 1 THEN 'module'
                     WHEN depth = 2 THEN 'submodule'
                     WHEN depth >= 3 AND l.id CONTAINS '#' THEN 'implementation'
                     WHEN depth >= 3 THEN 'file'
                     ELSE 'unknown'
                   END as granularity
            ORDER BY depth, r.id
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(granularity_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        granularities = result_lines[0]["data"]
        assert any(g[3] == "implementation" for g in granularities)
        assert any(g[3] == "submodule" for g in granularities)