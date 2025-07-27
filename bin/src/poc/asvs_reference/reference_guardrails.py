"""
Reference Entity Guardrails Module

外部標準（ASVS等）を参照基盤として活用し、
要件作成時の品質と網羅性を向上させる
"""
from typing import List, Dict, Optional, Set, Union, Any
from pathlib import Path
import json


def create_reference_repository(db_path: str = ":memory:") -> Dict[str, Any]:
    """
    Reference Entity機能を持つリポジトリを作成
    
    Args:
        db_path: データベースパス（デフォルト: インメモリ）
    
    Returns:
        リポジトリ関数の辞書またはエラー
    """
    # kuzu_pyを使用
    import sys
    persistence_path = Path(__file__).parent.parent.parent / "persistence" / "kuzu_py"
    if str(persistence_path) not in sys.path:
        sys.path.insert(0, str(persistence_path))
    
    from database import create_database, create_connection
    
    # データベース作成
    db_result = create_database(db_path)
    if hasattr(db_result, "get") and db_result.get("ok") is False:
        return {
            "type": "DatabaseError",
            "message": "Failed to create database",
            "details": db_result
        }
    
    # コネクション作成
    conn_result = create_connection(db_result)
    if hasattr(conn_result, "get") and conn_result.get("ok") is False:
        return {
            "type": "ConnectionError", 
            "message": "Failed to create connection",
            "details": conn_result
        }
    
    db = db_result
    conn = conn_result
    
    # スキーマ初期化
    try:
        # ReferenceEntityテーブル
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS ReferenceEntity (
                id STRING PRIMARY KEY,
                standard STRING,
                version STRING,
                section STRING,
                description STRING,
                level INT,
                category STRING
            )
        """)
        
        # RequirementEntityテーブル（簡易版）
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                status STRING DEFAULT 'draft'
            )
        """)
        
        # IMPLEMENTS関係
        conn.execute("""
            CREATE REL TABLE IF NOT EXISTS IMPLEMENTS (
                FROM RequirementEntity TO ReferenceEntity,
                status STRING DEFAULT 'planned',
                justification STRING,
                verified_date STRING,
                evidence_uri STRING
            )
        """)
        
    except Exception as e:
        return {
            "type": "SchemaError",
            "message": f"Failed to initialize schema: {str(e)}"
        }
    
    def load_asvs_samples() -> Dict[str, Any]:
        """ASVS V2認証要件のサンプルをロード"""
        try:
            samples = [
                {
                    "id": "ASVS_V2.1.1", 
                    "standard": "OWASP ASVS",
                    "version": "4.0.3",
                    "section": "V2.1.1",
                    "description": "Verify that user set passwords are at least 12 characters in length",
                    "level": 1,
                    "category": "authentication"
                },
                {
                    "id": "ASVS_V2.1.2",
                    "standard": "OWASP ASVS", 
                    "version": "4.0.3",
                    "section": "V2.1.2",
                    "description": "Verify that passwords of at least 128 characters are permitted",
                    "level": 2,
                    "category": "authentication"
                },
                {
                    "id": "ASVS_V2.1.3",
                    "standard": "OWASP ASVS",
                    "version": "4.0.3", 
                    "section": "V2.1.3",
                    "description": "Verify that password truncation is not performed",
                    "level": 2,
                    "category": "authentication"
                }
            ]
            
            for sample in samples:
                conn.execute("""
                    CREATE (r:ReferenceEntity {
                        id: $id,
                        standard: $standard,
                        version: $version,
                        section: $section,
                        description: $description,
                        level: $level,
                        category: $category
                    })
                """, sample)
                
            return {
                "type": "Success",
                "message": f"Loaded {len(samples)} ASVS samples"
            }
            
        except Exception as e:
            return {
                "type": "LoadError",
                "message": f"Failed to load samples: {str(e)}"
            }
    
    def find_references_by_category(category: str) -> Dict[str, Any]:
        """カテゴリで参照要件を検索"""
        try:
            result = conn.execute("""
                MATCH (ref:ReferenceEntity {category: $category})
                RETURN ref.id as id, 
                       ref.section as section,
                       ref.description as description,
                       ref.level as level
                ORDER BY ref.section
            """, {"category": category})
            
            references = []
            while result.has_next():
                row = result.get_next()
                references.append({
                    "id": row[0],
                    "section": row[1],
                    "description": row[2],
                    "level": row[3]
                })
            
            return {
                "type": "Success",
                "references": references,
                "count": len(references)
            }
            
        except Exception as e:
            return {
                "type": "QueryError",
                "message": f"Failed to search references: {str(e)}"
            }
    
    def create_compliance_mapping(requirement_id: str, reference_id: str, 
                                status: str = "planned", justification: str = None) -> Dict[str, Any]:
        """要件と参照標準のマッピングを作成"""
        try:
            # 両ノードの存在確認
            req_check = conn.execute("""
                MATCH (r:RequirementEntity {id: $id})
                RETURN r
            """, {"id": requirement_id})
            
            if not req_check.has_next():
                return {
                    "type": "NotFoundError",
                    "message": f"Requirement {requirement_id} not found"
                }
            
            ref_check = conn.execute("""
                MATCH (r:ReferenceEntity {id: $id})
                RETURN r
            """, {"id": reference_id})
            
            if not ref_check.has_next():
                return {
                    "type": "NotFoundError",
                    "message": f"Reference {reference_id} not found"
                }
            
            # マッピング作成
            params = {
                "req_id": requirement_id,
                "ref_id": reference_id,
                "status": status,
                "justification": justification or ""
            }
            
            conn.execute("""
                MATCH (req:RequirementEntity {id: $req_id})
                MATCH (ref:ReferenceEntity {id: $ref_id})
                CREATE (req)-[:IMPLEMENTS {
                    status: $status,
                    justification: $justification
                }]->(ref)
            """, params)
            
            return {
                "type": "Success",
                "mapping": {
                    "requirement": requirement_id,
                    "reference": reference_id,
                    "status": status
                }
            }
            
        except Exception as e:
            return {
                "type": "MappingError",
                "message": f"Failed to create mapping: {str(e)}"
            }
    
    def gap_analysis(standard: str = "OWASP ASVS", level: Optional[int] = None) -> Dict[str, Any]:
        """未実装の参照要件を分析"""
        try:
            # 条件構築
            where_clause = "WHERE ref.standard = $standard"
            params = {"standard": standard}
            
            if level is not None:
                where_clause += " AND ref.level <= $level"
                params["level"] = level
            
            # 全参照要件を取得
            all_refs = conn.execute(f"""
                MATCH (ref:ReferenceEntity)
                {where_clause}
                RETURN ref.id, ref.section, ref.description, ref.level, ref.category
                ORDER BY ref.section
            """, params)
            
            all_references = []
            while all_refs.has_next():
                row = all_refs.get_next()
                all_references.append({
                    "id": row[0],
                    "section": row[1], 
                    "description": row[2],
                    "level": row[3],
                    "category": row[4]
                })
            
            # 実装済み要件を取得
            implemented = conn.execute(f"""
                MATCH (ref:ReferenceEntity)
                {where_clause}
                WHERE EXISTS {{
                    MATCH (req:RequirementEntity)-[:IMPLEMENTS {{status: 'completed'}}]->(ref)
                }}
                RETURN ref.id
            """, params)
            
            implemented_ids = set()
            while implemented.has_next():
                row = implemented.get_next()
                implemented_ids.add(row[0])
            
            # ギャップ計算
            gaps = [ref for ref in all_references if ref["id"] not in implemented_ids]
            total = len(all_references)
            implemented_count = len(implemented_ids)
            coverage = (implemented_count / total * 100) if total > 0 else 0
            
            # カテゴリ別集計
            gaps_by_category = {}
            for gap in gaps:
                cat = gap["category"]
                if cat not in gaps_by_category:
                    gaps_by_category[cat] = []
                gaps_by_category[cat].append(gap)
            
            return {
                "type": "Success",
                "analysis": {
                    "standard": standard,
                    "level": level,
                    "total_requirements": total,
                    "implemented": implemented_count,
                    "gaps": len(gaps),
                    "coverage_percentage": round(coverage, 1),
                    "gaps_by_category": gaps_by_category,
                    "gap_details": gaps
                }
            }
            
        except Exception as e:
            return {
                "type": "AnalysisError",
                "message": f"Failed to analyze gaps: {str(e)}"
            }
    
    # リポジトリインターフェース
    return {
        "load_asvs_samples": load_asvs_samples,
        "find_references_by_category": find_references_by_category,
        "create_compliance_mapping": create_compliance_mapping,
        "gap_analysis": gap_analysis,
        "connection": conn,
        "database": db
    }


def demo_reference_guardrails():
    """Reference Guardrailsのデモンストレーション"""
    
    print("=" * 60)
    print("Reference Entity Guardrails Demo")
    print("=" * 60)
    print()
    
    # リポジトリ作成
    print("1. Creating reference repository...")
    repo = create_reference_repository(":memory:")
    
    if "type" in repo and "Error" in repo.get("type", ""):
        print(f"Error: {repo}")
        return
    
    print("✓ Repository created\n")
    
    # サンプルデータロード
    print("2. Loading ASVS samples...")
    load_result = repo["load_asvs_samples"]()
    print(f"✓ {load_result['message']}\n")
    
    # カテゴリ検索
    print("3. Finding authentication references...")
    search_result = repo["find_references_by_category"]("authentication")
    
    if search_result["type"] == "Success":
        print(f"Found {search_result['count']} references:")
        for ref in search_result["references"]:
            print(f"  - {ref['section']}: {ref['description'][:60]}...")
            print(f"    (Level {ref['level']})")
    print()
    
    # 要件作成とマッピング
    print("4. Creating sample requirements and mappings...")
    
    # サンプル要件を作成
    conn = repo["connection"]
    conn.execute("""
        CREATE (r:RequirementEntity {
            id: 'REQ-AUTH-001',
            title: 'Password minimum length',
            description: 'Passwords must be at least 12 characters long',
            status: 'implemented'
        })
    """)
    
    # マッピング作成
    mapping_result = repo["create_compliance_mapping"](
        "REQ-AUTH-001", 
        "ASVS_V2.1.1",
        "completed",
        "Implemented using Django auth validators"
    )
    
    if mapping_result["type"] == "Success":
        print(f"✓ Mapped {mapping_result['mapping']['requirement']} -> {mapping_result['mapping']['reference']}")
    print()
    
    # ギャップ分析
    print("5. Gap Analysis for ASVS Level 1...")
    gap_result = repo["gap_analysis"]("OWASP ASVS", 1)
    
    if gap_result["type"] == "Success":
        analysis = gap_result["analysis"]
        print(f"Coverage: {analysis['coverage_percentage']}%")
        print(f"Implemented: {analysis['implemented']}/{analysis['total_requirements']}")
        
        if analysis['gaps'] > 0:
            print(f"\nGaps found ({analysis['gaps']} items):")
            for category, gaps in analysis['gaps_by_category'].items():
                print(f"\n  {category.upper()}:")
                for gap in gaps:
                    print(f"    - {gap['section']}: {gap['description'][:50]}...")
    
    print("\n" + "=" * 60)
    print("Demo completed!")


if __name__ == "__main__":
    demo_reference_guardrails()