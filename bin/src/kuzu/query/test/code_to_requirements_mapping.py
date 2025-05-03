#!/usr/bin/env python
"""
階層型トレーサビリティモデル - コードエンティティから要件への逆引きサンプル

このスクリプトは「開発・実装支援」ユースケースの中から
「特定コードの対応要件群の確認（逆引き）」機能を実装するサンプルです。
開発者が特定のコードを変更する際に参照すべき要件を特定できます。
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
    
    # CodeEntity → CodeEntity 含有関係
    conn.execute("""
    CREATE REL TABLE CONTAINS (
        FROM CodeEntity TO CodeEntity
    )
    """)


def insert_sample_data(conn: kuzu.Connection) -> None:
    """サンプルデータを挿入します"""
    
    # LocationURIデータ
    conn.execute("CREATE (loc1:LocationURI {uri_id: 'loc1', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/service', fragment: '', query: ''})")
    conn.execute("CREATE (loc2:LocationURI {uri_id: 'loc2', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/controller', fragment: '', query: ''})")
    conn.execute("CREATE (loc3:LocationURI {uri_id: 'loc3', scheme: 'file', authority: 'project', path: '/src/test/java/com/example/service', fragment: '', query: ''})")
    conn.execute("CREATE (loc4:LocationURI {uri_id: 'loc4', scheme: 'requirement', authority: 'project', path: '/functional/user-management', fragment: '', query: ''})")
    conn.execute("CREATE (loc5:LocationURI {uri_id: 'loc5', scheme: 'requirement', authority: 'project', path: '/non-functional/security', fragment: '', query: ''})")
    
    # RequirementEntityデータ
    conn.execute("CREATE (req1:RequirementEntity {id: 'REQ-001', title: 'ユーザー登録機能', description: 'システムはユーザー情報を登録できること', priority: 'HIGH', requirement_type: 'functional'})")
    conn.execute("CREATE (req2:RequirementEntity {id: 'REQ-002', title: 'ユーザー認証機能', description: 'システムはユーザー認証を行えること', priority: 'HIGH', requirement_type: 'functional'})")
    conn.execute("CREATE (req3:RequirementEntity {id: 'REQ-003', title: 'パスワードポリシー', description: 'パスワードは8文字以上で、英数字と特殊文字を含むこと', priority: 'MEDIUM', requirement_type: 'security'})")
    conn.execute("CREATE (req4:RequirementEntity {id: 'REQ-004', title: 'アカウントロック機能', description: '連続5回の認証失敗でアカウントをロックすること', priority: 'MEDIUM', requirement_type: 'security'})")
    
    # CodeEntityデータ
    conn.execute("CREATE (code1:CodeEntity {persistent_id: 'CODE-001', name: 'UserService', type: 'class', signature: 'public class UserService', complexity: 5, start_position: 100, end_position: 500})")
    conn.execute("CREATE (code2:CodeEntity {persistent_id: 'CODE-002', name: 'registerUser', type: 'function', signature: 'public User registerUser(UserDTO userDTO)', complexity: 3, start_position: 150, end_position: 250})")
    conn.execute("CREATE (code3:CodeEntity {persistent_id: 'CODE-003', name: 'authenticateUser', type: 'function', signature: 'public boolean authenticateUser(String username, String password)', complexity: 4, start_position: 300, end_position: 400})")
    conn.execute("CREATE (code4:CodeEntity {persistent_id: 'CODE-004', name: 'UserController', type: 'class', signature: 'public class UserController', complexity: 2, start_position: 600, end_position: 900})")
    conn.execute("CREATE (code5:CodeEntity {persistent_id: 'CODE-005', name: 'UserServiceTest', type: 'test', signature: 'public class UserServiceTest', complexity: 1, start_position: 1000, end_position: 1200})")
    conn.execute("CREATE (code6:CodeEntity {persistent_id: 'CODE-006', name: 'validatePassword', type: 'function', signature: 'private boolean validatePassword(String password)', complexity: 2, start_position: 420, end_position: 480})")
    conn.execute("CREATE (code7:CodeEntity {persistent_id: 'CODE-007', name: 'lockAccount', type: 'function', signature: 'private void lockAccount(String username)', complexity: 3, start_position: 480, end_position: 520})")
    
    # HAS_LOCATION_URI関係データ
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-001'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-004'}), (l:LocationURI {uri_id: 'loc2'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (l:LocationURI {uri_id: 'loc3'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-007'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)")
    
    # REQUIREMENT_HAS_LOCATION_URI関係データ
    conn.execute("MATCH (r:RequirementEntity {id: 'REQ-001'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (r:RequirementEntity {id: 'REQ-002'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (r:RequirementEntity {id: 'REQ-003'}), (l:LocationURI {uri_id: 'loc5'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)")
    conn.execute("MATCH (r:RequirementEntity {id: 'REQ-004'}), (l:LocationURI {uri_id: 'loc5'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)")
    
    # IMPLEMENTS関係データ
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (r:RequirementEntity {id: 'REQ-003'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)")
    conn.execute("MATCH (c:CodeEntity {persistent_id: 'CODE-007'}), (r:RequirementEntity {id: 'REQ-004'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)")
    
    # 親子関係の例 - コードエンティティ間
    conn.execute("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-002'}) CREATE (c1)-[:CONTAINS]->(c2)")
    conn.execute("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-003'}) CREATE (c1)-[:CONTAINS]->(c2)")
    conn.execute("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-006'}) CREATE (c1)-[:CONTAINS]->(c2)")
    conn.execute("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-007'}) CREATE (c1)-[:CONTAINS]->(c2)")


def find_requirements_for_code(conn: kuzu.Connection, code_id: str) -> List[Dict[str, Any]]:
    """指定したコードIDに関連する要件を検索して結果を返します"""
    
    # 直接実装している要件を検索するクエリ
    query = """
    MATCH (c:CodeEntity)-[impl:IMPLEMENTS]->(r:RequirementEntity)
    WHERE c.persistent_id = $code_id
    OPTIONAL MATCH (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           r.priority as requirement_priority,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as requirement_location,
           'direct' as relation_type
    """
    
    response = conn.execute(query, {"code_id": code_id})
    
    results = []
    while response.has_next():
        row = response.get_next()
        results.append({
            "requirement_id": row[0],
            "requirement_title": row[1],
            "requirement_type": row[2],
            "requirement_priority": row[3],
            "implementation_type": row[4],
            "requirement_location": row[5],
            "relation_type": row[6]
        })
    
    # 親コードエンティティの場合、子コードが実装している要件も検索
    query_indirect = """
    MATCH (parent:CodeEntity)-[:CONTAINS]->(child:CodeEntity)-[impl:IMPLEMENTS]->(r:RequirementEntity)
    WHERE parent.persistent_id = $code_id
    OPTIONAL MATCH (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           r.priority as requirement_priority,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as requirement_location,
           'via_child_' + child.name as relation_type
    """
    
    response = conn.execute(query_indirect, {"code_id": code_id})
    
    while response.has_next():
        row = response.get_next()
        # 重複をチェック（既に直接関係で追加されている要件は除外）
        is_duplicate = False
        for existing in results:
            if existing["requirement_id"] == row[0]:
                is_duplicate = True
                break
        
        if not is_duplicate:
            results.append({
                "requirement_id": row[0],
                "requirement_title": row[1],
                "requirement_type": row[2],
                "requirement_priority": row[3],
                "implementation_type": row[4],
                "requirement_location": row[5],
                "relation_type": row[6]
            })
    
    return results


def format_requirements_for_code(results: List[Dict[str, Any]]) -> str:
    """コードに関連する要件の結果を整形して返します"""
    
    if not results:
        return "指定されたコードに関連する要件は見つかりませんでした。"
    
    output = []
    output.append("\n関連する要件:")
    output.append("=" * 80)
    output.append(f"{'要件ID':<10} {'タイトル':<30} {'タイプ':<10} {'優先度':<10} {'関連タイプ':<20} {'場所'}")
    output.append("-" * 80)
    
    # 優先度順にソート（HIGH、MEDIUM、LOW）
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sorted_results = sorted(results, key=lambda x: priority_order.get(x["requirement_priority"], 99))
    
    for result in sorted_results:
        output.append(f"{result['requirement_id']:<10} {result['requirement_title'][:30]:<30} "
                     f"{result['requirement_type']:<10} {result['requirement_priority']:<10} "
                     f"{result['relation_type'][:20]:<20} {result['requirement_location']}")
    
    return "\n".join(output)


def find_requirements_for_path(conn: kuzu.Connection, path: str) -> List[Dict[str, Any]]:
    """指定したパスのコードが実装している要件とその数を返します"""
    
    query = """
    MATCH (c:CodeEntity)-[:HAS_LOCATION_URI]->(loc:LocationURI)
    WHERE loc.path = $path
    MATCH (c)-[impl:IMPLEMENTS]->(r:RequirementEntity)
    RETURN r.id as requirement_id, COUNT(c) as implementation_count
    """
    
    response = conn.execute(query, {"path": path})
    
    results = []
    while response.has_next():
        row = response.get_next()
        results.append({
            "requirement_id": row[0],
            "implementation_count": row[1]
        })
    
    return results


def format_path_requirements(results: List[Dict[str, Any]], path: str) -> str:
    """パスに関連する要件結果を整形して返します"""
    
    output = []
    output.append(f"'{path}'パスに関連する要件:")
    
    if not results:
        output.append("関連する要件はありません。")
        return "\n".join(output)
    
    output.append(f"{'要件ID':<10} {'実装数'}")
    output.append("-" * 20)
    
    for result in results:
        output.append(f"{result['requirement_id']:<10} {result['implementation_count']}")
    
    return "\n".join(output)


def setup_database():
    """テスト用データベースをセットアップして接続を返します"""
    # データベースディレクトリ
    db_path = "./traceability_db_code_to_req"
    
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


def test_single_code_requirements(db_connection, capsys):
    """単一のコードエンティティに関連する要件を検索するテスト"""
    print("\n==== ユースケース: 特定コードの対応要件群の確認（逆引き） ====\n")
    
    # validatePassword関数のテスト
    code_id = 'CODE-006'
    print(f"コードID '{code_id}' (validatePassword関数) の関連要件:")
    results = find_requirements_for_code(db_connection, code_id)
    formatted_output = format_requirements_for_code(results)
    print(formatted_output)
    
    # 結果の検証
    assert len(results) == 1, "validatePassword関数は1つの要件と関連すべき"
    assert results[0]["requirement_id"] == "REQ-003", "validatePassword関数はREQ-003と関連すべき"
    assert "パスワードポリシー" in results[0]["requirement_title"], "要件タイトルが正しくない"
    assert results[0]["relation_type"] == "direct", "関連タイプが'direct'であるべき"


def test_parent_code_requirements(db_connection, capsys):
    """親コードエンティティに関連する要件を検索するテスト"""
    print("\nコードID 'CODE-001' (UserServiceクラス) の関連要件:")
    results = find_requirements_for_code(db_connection, 'CODE-001')
    formatted_output = format_requirements_for_code(results)
    print(formatted_output)
    
    # 結果の検証
    assert len(results) == 4, "UserServiceクラスは4つの要件と関連すべき"
    # 優先度の高い要件が含まれているか確認
    high_priority_reqs = [r for r in results if r["requirement_priority"] == "HIGH"]
    assert len(high_priority_reqs) == 2, "高優先度の要件が2つあるべき"
    # セキュリティ要件が含まれているか確認
    security_reqs = [r for r in results if r["requirement_type"] == "security"]
    assert len(security_reqs) == 2, "セキュリティ要件が2つあるべき"


def test_path_requirements(db_connection, capsys):
    """特定パス内のコードすべての関連要件を検索するテスト"""
    print("\n==== 追加機能: 特定パス内のコードすべての関連要件 ====\n")
    
    path = '/src/main/java/com/example/service'
    results = find_requirements_for_path(db_connection, path)
    formatted_output = format_path_requirements(results, path)
    print(formatted_output)
    
    # 結果の検証
    assert len(results) == 4, "Serviceパスには4つの要件の実装があるべき"
    # 要件IDの確認
    req_ids = [r["requirement_id"] for r in results]
    assert all(req_id in req_ids for req_id in ["REQ-001", "REQ-002", "REQ-003", "REQ-004"]), \
           "すべての要件IDが含まれているべき"


if __name__ == "__main__":
    # pytestで実行される場合はこのブロックは実行されない
    pytest.main(["-v", __file__])
