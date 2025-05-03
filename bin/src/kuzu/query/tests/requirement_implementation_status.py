#!/usr/bin/env python
"""
階層型トレーサビリティモデル - 要件実装状況確認サンプル

このスクリプトは「開発・実装支援」ユースケースの中から
「特定要件の実装状況の追跡」機能を実装するサンプルです。
特定の要件に対する実装状況を確認できます。
"""

import os
import kuzu
import pytest
from typing import List, Dict, Any, Tuple

def create_schema(conn: kuzu.Connection) -> None:
    """データベーススキーマを作成します"""
    
    # LocationURIノード
    conn.execute("""
    CREATE NODE TABLE LocationURI (
        uri_id STRING PRIMARY KEY,
        scheme STRING,
        authority STRING,
        path STRING,
        fragment STRING,
        query STRING
    )
    """)
    
    # CodeEntityノード
    conn.execute("""
    CREATE NODE TABLE CodeEntity (
        persistent_id STRING PRIMARY KEY,
        name STRING,
        type STRING,
        signature STRING,
        complexity INT64,
        start_position INT64,
        end_position INT64
    )
    """)
    
    # RequirementEntityノード
    conn.execute("""
    CREATE NODE TABLE RequirementEntity (
        id STRING PRIMARY KEY,
        title STRING,
        description STRING,
        priority STRING,
        requirement_type STRING
    )
    """)
    
    # CodeEntity → LocationURI 関係
    conn.execute("""
    CREATE REL TABLE HAS_LOCATION_URI (
        FROM CodeEntity TO LocationURI
    )
    """)
    
    # RequirementEntity → LocationURI 関係
    conn.execute("""
    CREATE REL TABLE REQUIREMENT_HAS_LOCATION_URI (
        FROM RequirementEntity TO LocationURI
    )
    """)
    
    # CodeEntity → RequirementEntity 実装関係
    conn.execute("""
    CREATE REL TABLE IMPLEMENTS (
        FROM CodeEntity TO RequirementEntity,
        implementation_type STRING
    )
    """)

def insert_sample_data(conn: kuzu.Connection) -> None:
    """サンプルデータを挿入します"""
    
    # LocationURIデータ
    conn.execute("CREATE (loc1:LocationURI {uri_id: 'loc1', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/service', fragment: '', query: ''})")
    conn.execute("CREATE (loc2:LocationURI {uri_id: 'loc2', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/controller', fragment: '', query: ''})")
    conn.execute("CREATE (loc3:LocationURI {uri_id: 'loc3', scheme: 'file', authority: 'project', path: '/src/test/java/com/example/service', fragment: '', query: ''})")
    conn.execute("CREATE (loc4:LocationURI {uri_id: 'loc4', scheme: 'requirement', authority: 'project', path: '/functional/user-management', fragment: '', query: ''})")
    
    # RequirementEntityデータ
    conn.execute("CREATE (req1:RequirementEntity {id: 'REQ-001', title: 'ユーザー登録機能', description: 'システムはユーザー情報を登録できること', priority: 'HIGH', requirement_type: 'functional'})")
    conn.execute("CREATE (req2:RequirementEntity {id: 'REQ-002', title: 'ユーザー認証機能', description: 'システムはユーザー認証を行えること', priority: 'HIGH', requirement_type: 'functional'})")
    conn.execute("CREATE (req3:RequirementEntity {id: 'REQ-003', title: 'パスワードポリシー', description: 'パスワードは8文字以上で、英数字と特殊文字を含むこと', priority: 'MEDIUM', requirement_type: 'security'})")
    
    # CodeEntityデータ
    conn.execute("CREATE (code1:CodeEntity {persistent_id: 'CODE-001', name: 'UserService', type: 'class', signature: 'public class UserService', complexity: 5, start_position: 100, end_position: 500})")
    conn.execute("CREATE (code2:CodeEntity {persistent_id: 'CODE-002', name: 'registerUser', type: 'function', signature: 'public User registerUser(UserDTO userDTO)', complexity: 3, start_position: 150, end_position: 250})")
    conn.execute("CREATE (code3:CodeEntity {persistent_id: 'CODE-003', name: 'authenticateUser', type: 'function', signature: 'public boolean authenticateUser(String username, String password)', complexity: 4, start_position: 300, end_position: 400})")
    conn.execute("CREATE (code4:CodeEntity {persistent_id: 'CODE-004', name: 'UserController', type: 'class', signature: 'public class UserController', complexity: 2, start_position: 600, end_position: 900})")
    conn.execute("CREATE (code5:CodeEntity {persistent_id: 'CODE-005', name: 'UserServiceTest', type: 'test', signature: 'public class UserServiceTest', complexity: 1, start_position: 1000, end_position: 1200})")
    conn.execute("CREATE (code6:CodeEntity {persistent_id: 'CODE-006', name: 'validatePassword', type: 'function', signature: 'private boolean validatePassword(String password)', complexity: 2, start_position: 420, end_position: 480})")
    
    # HAS_LOCATION_URI関係データ
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-001'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-004'}), (l:LocationURI {uri_id: 'loc2'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (l:LocationURI {uri_id: 'loc3'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    
    # REQUIREMENT_HAS_LOCATION_URI関係データ
    conn.execute("MATCH (r:RequirementEntity {id: 'REQ-001'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (r:RequirementEntity {id: 'REQ-002'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (r:RequirementEntity {id: 'REQ-003'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)")
    
    # IMPLEMENTS関係データ
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (r:RequirementEntity {id: 'REQ-003'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)")

def track_requirement_implementation(conn: kuzu.Connection, requirement_id: str) -> List[Dict[str, Any]]:
    """指定した要件IDの実装状況を追跡して結果を返します"""
    
    query = """
    MATCH (r:RequirementEntity)<-[impl:IMPLEMENTS]-(c:CodeEntity)
    WHERE r.id = $req_id
    OPTIONAL MATCH (c)-[:HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           c.persistent_id as code_id, 
           c.name as code_name,
           c.type as code_type,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as code_location
    """
    
    response = conn.execute(query, {"req_id": requirement_id})
    
    results = []
    while response.has_next():
        row = response.get_next()
        results.append({
            "requirement_id": row[0],
            "requirement_title": row[1],
            "requirement_type": row[2],
            "code_id": row[3],
            "code_name": row[4],
            "code_type": row[5],
            "implementation_type": row[6],
            "code_location": row[7]
        })
    
    return results

def format_implementation_status(results: List[Dict[str, Any]]) -> str:
    """実装状況結果を整形して文字列として返します"""
    
    if not results:
        return "指定された要件の実装は見つかりませんでした。"
    
    output = []
    # 要件情報を取得（すべての結果で同じ）
    req_info = results[0]
    output.append(f"要件ID: {req_info['requirement_id']}")
    output.append(f"タイトル: {req_info['requirement_title']}")
    output.append(f"タイプ: {req_info['requirement_type']}")
    output.append("\n実装状況:")
    output.append("=" * 80)
    output.append(f"{'コードID':<10} {'名前':<20} {'種類':<10} {'実装タイプ':<20} {'場所'}")
    output.append("-" * 80)
    
    for result in results:
        output.append(f"{result['code_id']:<10} {result['code_name']:<20} {result['code_type']:<10} "
              f"{result['implementation_type']:<20} {result['code_location']}")
    
    return "\n".join(output)

def find_unimplemented_requirements(conn: kuzu.Connection) -> List[Dict[str, Any]]:
    """未実装の要件を検索して結果を返します"""
    
    query = """
    MATCH (r:RequirementEntity)
    WHERE NOT EXISTS {
        MATCH (r)<-[:IMPLEMENTS]-(c:CodeEntity)
        WHERE c.type <> 'test'
    }
    RETURN r.id as requirement_id, r.title as title
    """
    
    response = conn.execute(query)
    
    results = []
    while response.has_next():
        row = response.get_next()
        results.append({
            "requirement_id": row[0],
            "title": row[1]
        })
    
    return results

def format_unimplemented_requirements(results: List[Dict[str, Any]]) -> str:
    """未実装要件の結果を整形して文字列として返します"""
    
    output = []
    output.append("未実装の要件:")
    
    if not results:
        output.append("すべての要件が実装されています。")
    else:
        for result in results:
            output.append(f"- {result['requirement_id']}: {result['title']}")
    
    return "\n".join(output)

def setup_database():
    """テスト用データベースをセットアップして接続を返します"""
    # データベースディレクトリ
    db_path = "./traceability_db"
    
    # 既存のDBを削除（テスト用）
    if os.path.exists(db_path):
        import shutil
        shutil.rmtree(db_path)
    
    # データベース作成・接続
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # スキーマ作成
    create_schema(conn)
    
    # サンプルデータ挿入
    insert_sample_data(conn)
    
    return conn

@pytest.fixture
def db_connection():
    """pytestフィクスチャ: データベース接続を提供"""
    return setup_database()

def test_requirement_implementation_tracking(db_connection, capsys):
    """要件の実装状況追跡のテスト"""
    print("\n==== ユースケース: 特定要件の実装状況の追跡 ====\n")
    
    # REQ-001の実装状況を確認
    print("REQ-001の実装状況:")
    results = track_requirement_implementation(db_connection, "REQ-001")
    formatted_output = format_implementation_status(results)
    print(formatted_output)
    
    # 結果の検証
    assert len(results) == 2, "REQ-001は2つのコードエンティティによって実装されるべき"
    code_ids = [r["code_id"] for r in results]
    assert "CODE-002" in code_ids, "CODE-002がREQ-001を実装すべき"
    assert "CODE-005" in code_ids, "CODE-005がREQ-001をテストすべき"
    
    implementation_types = {r["code_id"]: r["implementation_type"] for r in results}
    assert implementation_types["CODE-002"] == "IMPLEMENTS", "CODE-002の実装タイプはIMPLEMENTSであるべき"
    assert implementation_types["CODE-005"] == "TESTS", "CODE-005の実装タイプはTESTSであるべき"

def test_requirement_implementation_tracking_security(db_connection, capsys):
    """セキュリティ要件の実装状況追跡のテスト"""
    # REQ-003の実装状況を確認
    print("\nREQ-003の実装状況:")
    results = track_requirement_implementation(db_connection, "REQ-003")
    formatted_output = format_implementation_status(results)
    print(formatted_output)
    
    # 結果の検証
    assert len(results) == 1, "REQ-003は1つのコードエンティティによって実装されるべき"
    assert results[0]["code_id"] == "CODE-006", "CODE-006がREQ-003を実装すべき"
    assert results[0]["implementation_type"] == "IMPLEMENTS", "実装タイプはIMPLEMENTSであるべき"
    assert "validatePassword" in results[0]["code_name"], "実装はvalidatePassword関数であるべき"

def test_unimplemented_requirements(db_connection, capsys):
    """未実装要件の特定のテスト"""
    print("\n==== 追加機能: 未実装要件の特定 ====\n")
    
    results = find_unimplemented_requirements(db_connection)
    formatted_output = format_unimplemented_requirements(results)
    print(formatted_output)
    
    # 結果の検証 - このサンプルデータではすべての要件が実装されている
    assert len(results) == 0, "すべての要件が実装されているべき"

if __name__ == "__main__":
    # pytestで実行される場合はこのブロックは実行されない
    pytest.main(["-v", __file__])
