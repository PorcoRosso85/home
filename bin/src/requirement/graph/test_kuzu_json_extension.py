#!/usr/bin/env python3
"""
KuzuDB JSON拡張機能の実際の動作確認テスト
"""
import tempfile
import shutil
import os


import pytest

@pytest.mark.skip(reason="Direct JSON extension loading causes segfault in pytest - use subprocess wrapper instead")
def test_json_extension_availability():
    """JSON拡張機能が実際に使えるか確認"""
    import kuzu
    
    temp_dir = tempfile.mkdtemp()
    try:
        # データベース作成
        db = kuzu.Database(temp_dir)
        conn = kuzu.Connection(db)
        
        # JSON拡張機能のインストールと読み込みを試行
        try:
            conn.execute("INSTALL json;")
            print("✓ JSON extension installed")
        except Exception as e:
            print(f"✗ Failed to install JSON extension: {e}")
            return False
            
        try:
            conn.execute("LOAD EXTENSION json;")
            print("✓ JSON extension loaded")
        except Exception as e:
            print(f"✗ Failed to load JSON extension: {e}")
            return False
        
        # JSON型を使ったテーブル作成を試行
        try:
            conn.execute("""
                CREATE NODE TABLE TestJSON (
                    id INT64, 
                    data JSON,
                    PRIMARY KEY(id)
                );
            """)
            print("✓ Table with JSON column created")
        except Exception as e:
            print(f"✗ Failed to create table with JSON column: {e}")
            return False
        
        # to_json関数を使ったデータ挿入を試行
        try:
            conn.execute("""
                CREATE (n:TestJSON {
                    id: 1, 
                    data: to_json({
                        'name': 'Test',
                        'values': [1, 2, 3]
                    })
                });
            """)
            print("✓ Data inserted using to_json")
        except Exception as e:
            print(f"✗ Failed to insert data with to_json: {e}")
            return False
        
        # json_extract関数を使ったクエリを試行
        try:
            result = conn.execute("""
                MATCH (n:TestJSON)
                RETURN n.id, json_extract(n.data, 'name') as name
            """)
            
            if result.has_next():
                row = result.get_next()
                print(f"✓ json_extract works: id={row[0]}, name={row[1]}")
                return True
            else:
                print("✗ No results from json_extract query")
                return False
                
        except Exception as e:
            print(f"✗ Failed to use json_extract: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_requirement_graph_json_integration():
    """要件グラフシステムでJSON型を使う場合の例"""
    from infrastructure.kuzu_subprocess_wrapper import KuzuJSONSubprocess, is_pytest_running
    import kuzu
    
    temp_dir = tempfile.mkdtemp()
    try:
        if is_pytest_running():
            # pytest環境ではサブプロセスラッパーを使用
            wrapper = KuzuJSONSubprocess(temp_dir)
            
            # スキーマとデータを一度に実行
            queries = [
                # JSON拡張機能は自動的にロードされるため不要
                # "INSTALL json;",
                # "LOAD EXTENSION json;",
                """CREATE NODE TABLE RequirementEntity (
                    id STRING PRIMARY KEY,
                    title STRING,
                    description STRING,
                    priority UINT8,
                    technical_specifications JSON
                );""",
                """CREATE NODE TABLE LocationURI (
                    id STRING PRIMARY KEY
                );""",
                """CREATE REL TABLE LOCATES (
                    FROM LocationURI TO RequirementEntity
                );""",
                """CREATE (req:RequirementEntity {
                    id: 'REQ-001',
                    title: 'API実装',
                    description: 'REST APIの実装',
                    priority: 100,
                    technical_specifications: to_json(map(['framework', 'auth', 'database', 'budget'], ['FastAPI', 'OAuth2', 'PostgreSQL', '10000']))
                })""",
                """CREATE (uri:LocationURI {id: '/api/v1/endpoints.py'})""",
                """MATCH (uri:LocationURI {id: '/api/v1/endpoints.py'}), (req:RequirementEntity {id: 'REQ-001'})
                   CREATE (uri)-[:LOCATES]->(req)""",
                """CREATE (constraint:RequirementEntity {
                    id: 'CONSTRAINT-001',
                    title: '予算制約',
                    description: '開発予算の上限',
                    priority: 200,
                    technical_specifications: to_json(map(['type', 'max_amount'], ['budget_limit', '5000']))
                })"""
            ]
            
            try:
                results = wrapper.execute_with_json(queries)
                
                # すべてのクエリが成功したか確認
                for i, result in enumerate(results):
                    if not result["success"]:
                        print(f"Query {i} failed: {result.get('error')}")
                        assert False, f"Query {i} failed: {result.get('error')}"
            except Exception as e:
                print(f"Subprocess execution failed: {e}")
                assert False, f"Subprocess execution failed: {e}"
            
            print("✓ All schema and data creation queries succeeded")
            
            # JSON関数を使ったクエリ
            test_queries = [
                "MATCH (req:RequirementEntity) RETURN req.id, req.technical_specifications",
                """MATCH (req:RequirementEntity) 
                   WHERE json_extract(req.technical_specifications, '$.framework') = 'FastAPI'
                   RETURN req.id, req.title, json_extract(req.technical_specifications, '$.budget') as budget""",
                """MATCH (constraint:RequirementEntity)
                   WHERE json_extract(constraint.technical_specifications, '$.type') = 'budget_limit'
                   WITH constraint, json_extract(constraint.technical_specifications, '$.max_amount') as budget_limit
                   MATCH (req:RequirementEntity)
                   WHERE req.id <> constraint.id
                   AND CAST(json_extract(req.technical_specifications, '$.budget') AS INT64) > CAST(budget_limit AS INT64)
                   RETURN req.id as requirement,
                          CAST(json_extract(req.technical_specifications, '$.budget') AS INT64) as requested_budget,
                          CAST(budget_limit AS INT64) as limit,
                          CAST(json_extract(req.technical_specifications, '$.budget') AS INT64) - CAST(budget_limit AS INT64) as overage"""
            ]
            
            for query in test_queries:
                result = wrapper.execute_single(query)
                if not result["success"]:
                    print(f"Test query failed: {result.get('error')}")
                    assert False, f"Test query failed: {result.get('error')}"
                if result.get("rows"):
                    print(f"✓ Query returned {len(result['rows'])} rows")
            
            print("✓ JSON extension works correctly in pytest environment")
            
        else:
            # 通常環境では既存のコードを使用
            db = kuzu.Database(temp_dir)
            conn = kuzu.Connection(db)
            
            # JSON拡張機能の設定
            conn.execute("INSTALL json;")
            conn.execute("LOAD EXTENSION json;")
            
            # RequirementEntityテーブルをJSON型で作成
            conn.execute("""
                CREATE NODE TABLE RequirementEntity (
                    id STRING PRIMARY KEY,
                    title STRING,
                    description STRING,
                    priority UINT8,
                    technical_specifications JSON
                );
            """)
            
            # LocationURIテーブル
            conn.execute("""
                CREATE NODE TABLE LocationURI (
                    id STRING PRIMARY KEY
                );
            """)
            
            # LOCATES関係
            conn.execute("""
                CREATE REL TABLE LOCATES (
                    FROM LocationURI TO RequirementEntity
                );
            """)
            
            # JSON型でデータを挿入
            conn.execute("""
                CREATE (req:RequirementEntity {
                    id: 'REQ-001',
                    title: 'API実装',
                    description: 'REST APIの実装',
                    priority: 100,
                    technical_specifications: to_json({
                        'framework': 'FastAPI',
                        'auth': 'OAuth2',
                        'endpoints': ['/users', '/products'],
                        'budget': 500000
                    })
                })
                CREATE (loc:LocationURI {id: 'req://REQ-001'})
                CREATE (loc)-[:LOCATES]->(req);
            """)
            
            # まずデータが挿入されているか確認
            check_result = conn.execute("MATCH (req:RequirementEntity) RETURN req.id, req.technical_specifications")
            if check_result.has_next():
                row = check_result.get_next()
                print(f"✓ Data exists: id={row[0]}, specs={row[1]}")
            else:
                print("✗ No data found in RequirementEntity table")
                assert False, "No data found in RequirementEntity table"
            
            # JSON内のデータでクエリ
            result = conn.execute("""
                MATCH (req:RequirementEntity)
                WHERE json_extract(req.technical_specifications, 'framework') = '"FastAPI"'
                RETURN req.id, req.title, json_extract(req.technical_specifications, 'budget') as budget
            """)
            
            if result.has_next():
                row = result.get_next()
                print(f"\n✓ JSON query successful:")
                print(f"  ID: {row[0]}")
                print(f"  Title: {row[1]}")
                print(f"  Budget: {row[2]}")
                
                # 予算矛盾検出の例
                conn.execute("""
                    CREATE (constraint:RequirementEntity {
                        id: 'REQ-CONSTRAINT-001',
                        title: '予算上限',
                        priority: 200,
                        technical_specifications: to_json({
                            'type': 'budget_limit',
                            'max_amount': 300000
                        })
                    });
                """)
                
                # 矛盾検出クエリ
                conflict_result = conn.execute("""
                    MATCH (constraint:RequirementEntity)
                    WHERE json_extract(constraint.technical_specifications, 'type') = 'budget_limit'
                    WITH constraint, json_extract(constraint.technical_specifications, 'max_amount') as budget_limit
                    
                    MATCH (req:RequirementEntity)
                    WHERE req.id <> constraint.id
                      AND json_extract(req.technical_specifications, 'budget') > budget_limit
                    
                    RETURN req.id as conflicting_requirement,
                           json_extract(req.technical_specifications, 'budget') as requested_budget,
                           budget_limit,
                           CAST(json_extract(req.technical_specifications, 'budget') AS INT64) - CAST(budget_limit AS INT64) as overage
                """)
                
                if conflict_result.has_next():
                    conflict = conflict_result.get_next()
                    print(f"\n✓ Conflict detected:")
                    print(f"  Requirement: {conflict[0]}")
                    print(f"  Requested: {conflict[1]}")
                    print(f"  Limit: {conflict[2]}")
                    print(f"  Overage: {conflict[3]}")
                    
            else:
                print("✗ No results from JSON query")
                assert False, "No results from JSON query"
            
    except Exception as e:
        print(f"✗ Error in requirement graph test: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Error in requirement graph test: {e}"
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=== KuzuDB JSON Extension Test ===\n")
    
    print("1. Testing JSON extension availability:")
    json_works = test_json_extension_availability()
    
    if json_works:
        print("\n2. Testing requirement graph JSON integration:")
        test_requirement_graph_json_integration()
    else:
        print("\n⚠️  JSON extension not available - cannot test integration")
        print("\nNote: The POC at /home/nixos/bin/src/poc/kuzu/json uses STRING type")
        print("      instead of JSON type to avoid segfault issues.")