#!/usr/bin/env python3
"""
Reference Entity Guardrails Demo - 新リポジトリパターン版

reference_repository.pyを使用した統合デモ
"""
from pathlib import Path
import tempfile

# 新しいリポジトリをインポート
from reference_repository import create_reference_repository
from migrate_ddl import migrate_to_v35
from asvs_loader import ASVSLoader


def demo_reference_guardrails():
    """Reference Guardrailsの統合デモンストレーション"""
    
    print("=" * 70)
    print("Reference Entity Guardrails Demo - New Repository Pattern")
    print("=" * 70)
    print()
    
    # 一時DBを使用（実環境では永続化DBを使用）
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "demo.db")
        
        # Step 1: DDLマイグレーション
        print("1. Applying DDL Migration (v3.5.0)...")
        migration_result = migrate_to_v35(db_path)
        if migration_result["status"] != "success":
            print(f"Error: {migration_result}")
            return
        print("✓ DDL migration applied successfully\n")
        
        # Step 2: リポジトリ作成
        print("2. Creating reference repository...")
        repo = create_reference_repository(db_path)
        
        if "type" in repo and "Error" in repo.get("type", ""):
            print(f"Error: {repo}")
            return
        
        print("✓ Repository created with new schema\n")
        
        # Step 3: ASVSデータロード（実際のローダーを使用）
        print("3. Loading ASVS data using template engine...")
        loader = ASVSLoader()
        
        # サンプルASVSデータを手動で追加（簡易版）
        asvs_refs = [
            {
                'uri': 'asvs:4.0.3:V2.1.1',
                'title': 'Password minimum length - 12 characters',
                'entity_type': 'asvs_requirement',
                'metadata': {
                    'standard': 'OWASP ASVS',
                    'version': '4.0.3',
                    'section': 'V2.1.1',
                    'description': 'Verify that user set passwords are at least 12 characters in length',
                    'level': 1,
                    'category': 'authentication'
                }
            },
            {
                'uri': 'asvs:4.0.3:V2.1.2',
                'title': 'Password maximum length - 128 characters',
                'entity_type': 'asvs_requirement',
                'metadata': {
                    'standard': 'OWASP ASVS',
                    'version': '4.0.3',
                    'section': 'V2.1.2',
                    'description': 'Verify that passwords of at least 128 characters are permitted',
                    'level': 2,
                    'category': 'authentication'
                }
            },
            {
                'uri': 'asvs:4.0.3:V2.1.3',
                'title': 'No password truncation',
                'entity_type': 'asvs_requirement',
                'metadata': {
                    'standard': 'OWASP ASVS',
                    'version': '4.0.3',
                    'section': 'V2.1.3',
                    'description': 'Verify that password truncation is not performed',
                    'level': 2,
                    'category': 'authentication'
                }
            }
        ]
        
        for ref in asvs_refs:
            result = repo['save'](ref)
            if 'uri' in result:
                print(f"  ✓ Loaded: {ref['uri']}")
        
        print(f"\n✓ Loaded {len(asvs_refs)} ASVS references\n")
        
        # Step 4: カテゴリ検索（新リポジトリのsearch機能を使用）
        print("4. Searching for authentication references...")
        search_result = repo['search']('authentication')
        
        if 'references' in search_result:
            refs = search_result['references']
            print(f"Found {len(refs)} references:")
            for ref in refs:
                metadata = ref.get('metadata', {})
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)
                print(f"  - {ref['uri']}: {ref['title']}")
                print(f"    Level: {metadata.get('level', 'N/A')}, Category: {metadata.get('category', 'N/A')}")
        print()
        
        # Step 5: 要件作成
        print("5. Creating application requirements...")
        
        requirements = [
            {
                'uri': 'req://app/auth/password-policy',
                'title': 'Application Password Policy',
                'entity_type': 'requirement',
                'metadata': {
                    'description': 'Our app enforces minimum 12 character passwords',
                    'status': 'implemented',
                    'component': 'authentication'
                }
            },
            {
                'uri': 'req://app/auth/password-storage',
                'title': 'Secure Password Storage',
                'entity_type': 'requirement', 
                'metadata': {
                    'description': 'Passwords are hashed using bcrypt with cost factor 12',
                    'status': 'implemented',
                    'component': 'authentication'
                }
            },
            {
                'uri': 'req://app/auth/password-history',
                'title': 'Password History Check',
                'entity_type': 'requirement',
                'metadata': {
                    'description': 'System prevents reuse of last 5 passwords',
                    'status': 'planned',
                    'component': 'authentication'
                }
            }
        ]
        
        for req in requirements:
            result = repo['save'](req)
            if 'uri' in result:
                print(f"  ✓ Created: {req['uri']}")
        print()
        
        # Step 6: コンプライアンスマッピング
        print("6. Creating compliance mappings...")
        
        # パスワードポリシーをASVS V2.1.1にマップ
        impl1 = repo['add_implementation'](
            'req://app/auth/password-policy',
            'asvs:4.0.3:V2.1.1',
            'full',
            'required',
            'Implemented with Django password validators, min length = 12'
        )
        
        if 'implementations' in impl1:
            print("  ✓ Mapped password policy -> ASVS V2.1.1")
        
        # パスワード保存をASVS V2.1.2に部分的にマップ
        impl2 = repo['add_implementation'](
            'req://app/auth/password-storage',
            'asvs:4.0.3:V2.1.2',
            'partial',
            'required',
            'We support up to 128 chars but UI limits to 64 for UX'
        )
        
        if 'implementations' in impl2:
            print("  ✓ Mapped password storage -> ASVS V2.1.2 (partial)")
        print()
        
        # Step 7: ギャップ分析
        print("7. Gap Analysis...")
        
        # すべてのASVS要件を取得
        all_refs = repo['find_all']()
        asvs_requirements = [
            r for r in all_refs.get('references', [])
            if r.get('entity_type') == 'asvs_requirement'
        ]
        
        # 実装済みのASVS要件を特定
        implemented_refs = set()
        for req in requirements:
            impls = repo['find_implementations'](req['uri'])
            for impl in impls.get('implementations', []):
                if impl.get('reference_uri'):
                    implemented_refs.add(impl['reference_uri'])
        
        # 統計を計算
        total = len(asvs_requirements)
        implemented = len(implemented_refs)
        gaps = total - implemented
        coverage = (implemented / total * 100) if total > 0 else 0
        
        print(f"  Total ASVS requirements: {total}")
        print(f"  Implemented: {implemented}")
        print(f"  Gaps: {gaps}")
        print(f"  Coverage: {coverage:.1f}%")
        print()
        
        # 未実装の要件を表示
        print("  Unimplemented ASVS requirements:")
        for ref in asvs_requirements:
            if ref['uri'] not in implemented_refs:
                print(f"    - {ref['uri']}: {ref['title']}")
        print()
        
        # Step 8: 実装の詳細確認
        print("8. Implementation Details...")
        
        for req_uri in ['req://app/auth/password-policy', 'req://app/auth/password-storage']:
            impls = repo['find_implementations'](req_uri)
            if impls.get('implementations'):
                print(f"\n  {req_uri}:")
                for impl in impls['implementations']:
                    print(f"    -> {impl.get('reference_uri')}")
                    print(f"       Type: {impl.get('implementation_type')}")
                    print(f"       Level: {impl.get('compliance_level')}")
                    print(f"       Notes: {impl.get('notes', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
        
        # 統計サマリー
        print("\nSummary:")
        print(f"- Database: {db_path}")
        print(f"- References loaded: {len(asvs_refs)}")
        print(f"- Requirements created: {len(requirements)}") 
        print(f"- Compliance mappings: {implemented}")
        print(f"- Coverage: {coverage:.1f}%")
        
        return {
            'db_path': db_path,
            'references': len(asvs_refs),
            'requirements': len(requirements),
            'mappings': implemented,
            'coverage': coverage
        }


if __name__ == "__main__":
    demo_reference_guardrails()