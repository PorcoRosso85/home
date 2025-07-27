"""
End-to-end integration test for Reference Entity Guardrails POC
"""
import pytest
import tempfile
import json
from pathlib import Path

# Import all components
from migrate_ddl import migrate_to_v35
from asvs_loader import ASVSLoader
from reference_repository import create_reference_repository


class TestReferenceEntityIntegration:
    """統合テスト: DDL適用からギャップ分析まで"""
    
    @pytest.fixture
    def temp_db(self):
        """一時データベースを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield str(Path(tmpdir) / "test.db")
    
    def test_full_workflow(self, temp_db):
        """完全なワークフロー: DDL → データロード → 要件作成 → マッピング → ギャップ分析"""
        
        # Step 1: DDLマイグレーション適用
        print("\n=== Step 1: Applying DDL Migration ===")
        result = migrate_to_v35(temp_db)
        assert result["status"] == "success"
        print(f"✓ Migration applied: {result['message']}")
        
        # Step 2: リポジトリ作成
        print("\n=== Step 2: Creating Repository ===")
        repo = create_reference_repository(temp_db)
        assert "type" not in repo or "Error" not in repo.get("type", "")
        print("✓ Repository created successfully")
        
        # Step 3: ASVSデータロード
        print("\n=== Step 3: Loading ASVS Data ===")
        loader = ASVSLoader()
        cypher_queries = loader.load_and_generate("data/asvs_sample.yaml")
        
        # 各クエリを実行（簡易版: ReferenceEntity作成部分のみ）
        references_loaded = 0
        for line in cypher_queries.split('\n'):
            if line.strip().startswith('CREATE') and 'ReferenceEntity' in line:
                # 簡易的なパース（本来はより堅牢な実装が必要）
                if 'uri:' in line and 'title:' in line:
                    # Extract values between quotes
                    import re
                    uri_match = re.search(r'uri:\s*"([^"]+)"', line)
                    title_match = re.search(r'title:\s*"([^"]+)"', line)
                    
                    if uri_match and title_match:
                        ref_data = {
                            'uri': uri_match.group(1),
                            'title': title_match.group(1),
                            'entity_type': 'asvs_requirement',
                            'metadata': {
                                'standard': 'OWASP ASVS',
                                'version': '4.0.3',
                                'category': 'authentication',
                                'level': 1
                            }
                        }
                        
                        save_result = repo['save'](ref_data)
                        if save_result.get('uri'):
                            references_loaded += 1
        
        print(f"✓ Loaded {references_loaded} ASVS references")
        assert references_loaded >= 3  # V2.1.1, V2.1.2, V2.1.3
        
        # Step 4: 要件作成
        print("\n=== Step 4: Creating Requirements ===")
        requirements = [
            {
                'uri': 'req://app/security/password-policy',
                'title': 'Password Policy Implementation',
                'entity_type': 'requirement',
                'metadata': {
                    'status': 'implemented',
                    'description': 'Our application enforces a minimum password length of 12 characters'
                }
            },
            {
                'uri': 'req://app/security/password-storage',
                'title': 'Secure Password Storage',
                'entity_type': 'requirement',
                'metadata': {
                    'status': 'planned',
                    'description': 'Passwords will be hashed using bcrypt'
                }
            }
        ]
        
        for req in requirements:
            result = repo['save'](req)
            assert result.get('uri') == req['uri']
            print(f"✓ Created requirement: {req['uri']}")
        
        # Step 5: 要件とASVS参照のマッピング
        print("\n=== Step 5: Linking Requirements to ASVS ===")
        
        # パスワードポリシーをASVS V2.1.1にリンク
        impl_result = repo['add_implementation'](
            'req://app/security/password-policy',
            'asvs:4.0.3:V2.1.1',
            'full',
            'required',
            'Implemented with Django password validators'
        )
        assert 'implementations' in impl_result
        print("✓ Linked password policy to ASVS V2.1.1")
        
        # Step 6: ギャップ分析
        print("\n=== Step 6: Gap Analysis ===")
        
        # 実装済みの参照を確認
        impl_check = repo['find_implementations']('req://app/security/password-policy')
        assert len(impl_check.get('implementations', [])) > 0
        
        # 全ASVS参照を取得
        all_refs = repo['find_all']()
        asvs_refs = [r for r in all_refs.get('references', []) 
                     if r.get('entity_type') == 'asvs_requirement']
        
        # 実装済みの参照URIを収集
        implemented_uris = set()
        for req in requirements:
            impls = repo['find_implementations'](req['uri'])
            for impl in impls.get('implementations', []):
                if impl.get('reference_uri'):
                    implemented_uris.add(impl['reference_uri'])
        
        # ギャップ計算
        total_asvs = len(asvs_refs)
        implemented = len(implemented_uris)
        gaps = total_asvs - implemented
        coverage = (implemented / total_asvs * 100) if total_asvs > 0 else 0
        
        print(f"\nGap Analysis Results:")
        print(f"- Total ASVS requirements: {total_asvs}")
        print(f"- Implemented: {implemented}")
        print(f"- Gaps: {gaps}")
        print(f"- Coverage: {coverage:.1f}%")
        
        # 未実装の要件をリスト
        print(f"\nUnimplemented ASVS Requirements:")
        for ref in asvs_refs:
            if ref['uri'] not in implemented_uris:
                print(f"  - {ref['uri']}: {ref['title']}")
        
        # アサーション
        assert total_asvs >= 3
        assert implemented >= 1
        assert coverage > 0
        
        print("\n✓ Integration test completed successfully!")
    
    def test_migration_then_repository_operations(self, temp_db):
        """マイグレーション後のリポジトリ操作が正常に動作すること"""
        # マイグレーション適用
        migrate_result = migrate_to_v35(temp_db)
        assert migrate_result["status"] == "success"
        
        # リポジトリ作成
        repo = create_reference_repository(temp_db)
        
        # 基本的なCRUD操作
        ref_data = {
            'uri': 'iso:27001:A.9.4.1',
            'title': 'Information access restriction',
            'entity_type': 'iso_control',
            'metadata': {
                'standard': 'ISO 27001',
                'version': '2022',
                'category': 'access_control'
            }
        }
        
        # Create
        save_result = repo['save'](ref_data)
        assert save_result.get('uri') == ref_data['uri']
        
        # Read
        find_result = repo['find'](ref_data['uri'])
        assert find_result.get('uri') == ref_data['uri']
        assert find_result.get('title') == ref_data['title']
        
        # Search
        search_result = repo['search']('access')
        assert len(search_result.get('references', [])) >= 1
        
        print("✓ Repository operations work correctly after migration")
    
    def test_compliance_workflow(self):
        """コンプライアンス追跡ワークフロー"""
        # インメモリDBで高速テスト
        repo = create_reference_repository(":memory:")
        
        # ISO 27001コントロールを作成
        controls = [
            {
                'uri': 'iso:27001:A.9.1.1',
                'title': 'Access control policy',
                'entity_type': 'iso_control',
                'metadata': {'category': 'access_control', 'priority': 'high'}
            },
            {
                'uri': 'iso:27001:A.9.1.2', 
                'title': 'Access to networks and network services',
                'entity_type': 'iso_control',
                'metadata': {'category': 'access_control', 'priority': 'medium'}
            }
        ]
        
        for control in controls:
            repo['save'](control)
        
        # 実装要件を作成
        req = {
            'uri': 'req://security/access-control-policy',
            'title': 'Implement access control policy',
            'entity_type': 'requirement',
            'metadata': {'status': 'in_progress'}
        }
        repo['save'](req)
        
        # コンプライアンスマッピング
        repo['add_implementation'](
            req['uri'],
            controls[0]['uri'],
            'partial',
            'required',
            'Policy drafted, pending approval'
        )
        
        # コンプライアンス状況確認
        impls = repo['find_implementations'](req['uri'])
        assert len(impls['implementations']) == 1
        assert impls['implementations'][0]['implementation_type'] == 'partial'
        
        # 逆引き: ISOコントロールから実装要件を検索
        reverse = repo['find_implementations'](controls[0]['uri'])
        assert len(reverse['implementations']) == 1
        assert reverse['implementations'][0]['requirement_uri'] == req['uri']
        
        print("✓ Compliance workflow test passed")