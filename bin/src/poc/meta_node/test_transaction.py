#!/usr/bin/env python3
"""
トランザクション管理機能のテストスクリプト

このスクリプトは、ガードレールルールのトランザクション管理が
正しく動作することを確認します。
"""

import os
import kuzu
from meta_node import MetaNode


def test_transaction_management():
    """トランザクション管理の動作を確認"""
    
    # テスト用のデータベースを作成
    test_db_path = "/tmp/test_transaction_db"
    if os.path.exists(test_db_path):
        # 既存のDBがある場合は削除
        import shutil
        try:
            if os.path.isdir(test_db_path):
                shutil.rmtree(test_db_path)
            else:
                os.remove(test_db_path)
        except:
            pass  # エラーは無視
    
    db = kuzu.Database(test_db_path)
    meta_node = MetaNode(db)
    
    # テスト用のノードテーブルを作成
    conn = kuzu.Connection(db)
    conn.execute("""
        CREATE NODE TABLE TestNode(
            id INT64,
            value STRING,
            PRIMARY KEY(id)
        )
    """)
    
    # 初期データを投入
    conn.execute("CREATE (:TestNode {id: 1, value: 'initial'})")
    
    print("=== トランザクション管理テスト開始 ===\n")
    
    # テスト1: 成功するルールのみの場合（コミットされるはず）
    print("テスト1: 成功するルールのみ")
    
    # transformationルールを作成（データを更新）
    meta_node.create_guardrail_rule(
        rule_type="transformation",
        name="update_value",
        description="値を更新するルール",
        priority=1,
        active=True,
        cypher_query="""
            MATCH (n:TestNode {id: 1})
            SET n.value = 'updated'
            RETURN true, 'Value updated successfully'
        """
    )
    
    # validationルールを作成（成功する）
    meta_node.create_guardrail_rule(
        rule_type="validation",
        name="check_not_empty",
        description="値が空でないことを確認",
        priority=2,
        active=True,
        cypher_query="""
            MATCH (n:TestNode {id: 1})
            RETURN n.value <> '', 'Value is not empty'
        """
    )
    
    # ルール実行
    result = meta_node.execute_guardrail_rules({})
    
    print(f"実行結果: {result['passed']}")
    print(f"トランザクション状態: {result['transaction_status']}")
    print("ログ:")
    for log in result['logs']:
        print(f"  - {log}")
    
    # データの確認
    check_result = conn.execute("MATCH (n:TestNode {id: 1}) RETURN n.value").get_next()
    print(f"データの値: {check_result[0]}")
    print()
    
    # テスト2: validationルールが失敗する場合（ロールバックされるはず）
    print("\nテスト2: validationルールが失敗する場合")
    
    # 失敗するvalidationルールを追加
    meta_node.create_guardrail_rule(
        rule_type="validation",
        name="check_specific_value",
        description="特定の値であることを確認",
        priority=3,
        active=True,
        cypher_query="""
            MATCH (n:TestNode {id: 1})
            RETURN n.value = 'specific_value', 'Value must be specific_value'
        """
    )
    
    # 別のtransformationルールを追加
    meta_node.create_guardrail_rule(
        rule_type="transformation",
        name="update_to_another",
        description="別の値に更新",
        priority=0,  # 最初に実行される
        active=True,
        cypher_query="""
            MATCH (n:TestNode {id: 1})
            SET n.value = 'another_value'
            RETURN true, 'Updated to another_value'
        """
    )
    
    # ルール実行
    result = meta_node.execute_guardrail_rules({})
    
    print(f"実行結果: {result['passed']}")
    print(f"トランザクション状態: {result['transaction_status']}")
    print("ログ:")
    for log in result['logs']:
        print(f"  - {log}")
    
    print("失敗したルール:")
    for failed in result['failed_rules']:
        print(f"  - {failed['name']} ({failed['rule_type']}): {failed.get('reason', failed.get('error', 'Unknown'))}")
    
    # データの確認（ロールバックされているはず）
    check_result = conn.execute("MATCH (n:TestNode {id: 1}) RETURN n.value").get_next()
    print(f"データの値（ロールバック後）: {check_result[0]}")
    
    # テスト3: エラーが発生する場合
    print("\n\nテスト3: クエリエラーが発生する場合")
    
    # エラーを起こすルールを作成
    meta_node.create_guardrail_rule(
        rule_type="validation",
        name="error_rule",
        description="エラーを起こすルール",
        priority=0,
        active=True,
        cypher_query="""
            MATCH (n:NonExistentTable)
            RETURN true
        """
    )
    
    # ルール実行
    result = meta_node.execute_guardrail_rules({})
    
    print(f"実行結果: {result['passed']}")
    print(f"トランザクション状態: {result['transaction_status']}")
    print("ログ:")
    for log in result['logs']:
        print(f"  - {log}")
    
    print("\n=== テスト完了 ===")
    print("\n注意: KuzuDBは現在、明示的なトランザクション管理をサポートしていないため、")
    print("各クエリは自動的にコミットされます。実際のロールバック機能は")
    print("アプリケーション層で実装する必要があります。")


if __name__ == "__main__":
    test_transaction_management()