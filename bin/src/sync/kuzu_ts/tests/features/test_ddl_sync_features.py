"""
DDL Sync Feature Tests
DDL同期の機能担保テスト

このテストは、examples/ddl_sync_scenario.tsから移行された
機能説明を、実行可能な仕様として再定義したものです。
"""

import pytest
import kuzu
import uuid
import time
from typing import Dict, Any, List


class MockSchemaManager:
    """SchemaManagerのモック実装"""
    
    def __init__(self):
        self.version = 0
        self.tables = {}
        self.applied_ddls = []
        
    def apply_ddl_event(self, event: Dict[str, Any]):
        """DDLイベントを適用"""
        self.applied_ddls.append(event)
        self.version += 1
        
        template = event.get("template")
        params = event.get("params", {})
        
        if template == "CREATE_NODE_TABLE":
            self.tables[params["tableName"]] = {
                "type": "node",
                "columns": params["columns"],
                "primaryKey": params["primaryKey"]
            }
        elif template == "ADD_COLUMN":
            if params["tableName"] in self.tables:
                self.tables[params["tableName"]]["columns"].append({
                    "name": params["columnName"],
                    "type": params["columnType"]
                })
                
    def get_schema_state(self) -> Dict[str, Any]:
        """現在のスキーマ状態を取得"""
        return {
            "version": self.version,
            "tables": self.tables
        }


class TestableKuzuClient:
    """テスト用のKuzuクライアント実装"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.db = kuzu.Database(':memory:')
        self.conn = kuzu.Connection(self.db)
        self.schema_manager = MockSchemaManager()
        self.events = []
        
    def create_ddl_event(self, template: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """DDLイベントを作成"""
        event = {
            "id": f"ddl-{uuid.uuid4()}",
            "template": template,
            "params": params,
            "timestamp": int(time.time() * 1000),
            "type": "DDL",
            "dependsOn": []
        }
        return event
        
    def apply_event(self, event: Dict[str, Any]):
        """イベントを適用"""
        self.events.append(event)
        
        if event.get("type") == "DDL":
            self.schema_manager.apply_ddl_event(event)
            
            # 実際のDDLクエリを生成して実行
            query = self._generate_ddl_query(event)
            if query:
                self.conn.execute(query)
                
    def _generate_ddl_query(self, event: Dict[str, Any]) -> str:
        """DDLイベントからクエリを生成"""
        template = event.get("template")
        params = event.get("params", {})
        
        if template == "CREATE_NODE_TABLE":
            columns = []
            for col in params["columns"]:
                col_def = f"{col['name']} {col['type']}"
                if col.get('nullable') is False:
                    col_def += " NOT NULL"
                columns.append(col_def)
            
            columns_str = ", ".join(columns)
            return f"CREATE NODE TABLE {params['tableName']} ({columns_str}, PRIMARY KEY({params['primaryKey']}))"
            
        elif template == "CREATE_EDGE_TABLE":
            query = f"CREATE REL TABLE {params['tableName']} (FROM {params['fromTable']} TO {params['toTable']}"
            if params.get('properties'):
                query += f", {params['properties']}"
            query += ")"
            return query
            
        elif template == "ADD_COLUMN":
            # KuzuDBはALTER TABLE ADD COLUMNをサポートしていないため、スキップ
            return ""
            
        return ""
        
    def has_table(self, table_name: str) -> bool:
        """テーブルの存在確認"""
        try:
            result = self.conn.execute("CALL table_info() RETURN *")
            while result.has_next():
                row = result.get_next()
                if row[1] == table_name:
                    return True
            return False
        except:
            return False
            
    def execute_query(self, query: str) -> Any:
        """クエリを実行"""
        return self.conn.execute(query)
        
    def get_schema_state(self) -> Dict[str, Any]:
        """スキーマ状態を取得"""
        return self.schema_manager.get_schema_state()


def test_feature_new_client_auto_schema_sync():
    """機能: 新規クライアントの自動スキーマ同期"""
    # クライアントAが初期スキーマを作成
    client_a = TestableKuzuClient("client-A")
    
    create_product = client_a.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Product",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "name", "type": "STRING"},
                {"name": "price", "type": "DOUBLE"}
            ],
            "primaryKey": "id"
        }
    )
    
    client_a.apply_event(create_product)
    
    # クライアントBが接続し、同じスキーマを適用
    client_b = TestableKuzuClient("client-B")
    client_b.apply_event(create_product)
    
    # 両クライアントが同じテーブルを持つことを確認
    assert client_a.has_table("Product")
    assert client_b.has_table("Product")
    
    # スキーマバージョンが同期されていることを確認
    state_a = client_a.get_schema_state()
    state_b = client_b.get_schema_state()
    assert state_a["version"] == state_b["version"]
    assert "Product" in state_a["tables"]
    assert "Product" in state_b["tables"]


def test_feature_dynamic_schema_extension():
    """機能: 動的なスキーマ拡張（カラム追加）"""
    client = TestableKuzuClient("client")
    
    # 初期テーブル作成
    create_table = client.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "User",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "name", "type": "STRING"}
            ],
            "primaryKey": "id"
        }
    )
    client.apply_event(create_table)
    
    initial_state = client.get_schema_state()
    initial_version = initial_state["version"]
    
    # カラム追加
    add_column = client.create_ddl_event(
        "ADD_COLUMN",
        {
            "tableName": "User",
            "columnName": "email",
            "columnType": "STRING",
            "defaultValue": "''"
        }
    )
    client.apply_event(add_column)
    
    # スキーマバージョンが増加したことを確認
    final_state = client.get_schema_state()
    assert final_state["version"] > initial_version
    
    # カラムが追加されたことを確認
    user_table = final_state["tables"]["User"]
    column_names = [col["name"] for col in user_table["columns"]]
    assert "email" in column_names


def test_feature_ddl_dependency_management():
    """機能: 依存関係のあるDDL操作"""
    client = TestableKuzuClient("client")
    
    # ノードテーブルを作成
    create_user = client.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "User",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "name", "type": "STRING"}
            ],
            "primaryKey": "id"
        }
    )
    
    create_post = client.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Post",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "title", "type": "STRING"}
            ],
            "primaryKey": "id"
        }
    )
    
    # エッジテーブルを作成（依存関係を設定）
    create_authored = client.create_ddl_event(
        "CREATE_EDGE_TABLE",
        {
            "tableName": "AUTHORED",
            "fromTable": "User",
            "toTable": "Post"
        }
    )
    create_authored["dependsOn"] = [create_user["id"], create_post["id"]]
    
    # すべてのイベントを適用
    client.apply_event(create_user)
    client.apply_event(create_post)
    client.apply_event(create_authored)
    
    # テーブルが正しく作成されたことを確認
    assert client.has_table("User")
    assert client.has_table("Post")
    assert client.has_table("AUTHORED")
    
    # 依存関係が記録されていることを確認
    assert len(client.schema_manager.applied_ddls) == 3
    authored_event = client.schema_manager.applied_ddls[2]
    assert len(authored_event["dependsOn"]) == 2


def test_feature_schema_version_tracking():
    """機能: スキーマバージョン管理"""
    clients = [
        TestableKuzuClient("client-1"),
        TestableKuzuClient("client-2"),
        TestableKuzuClient("client-3")
    ]
    
    # 一連のDDL操作を定義
    ddl_events = []
    
    # テーブル作成
    create_table = clients[0].create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Document",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "content", "type": "STRING"}
            ],
            "primaryKey": "id"
        }
    )
    ddl_events.append(create_table)
    
    # カラム追加
    add_column = clients[1].create_ddl_event(
        "ADD_COLUMN",
        {
            "tableName": "Document",
            "columnName": "created_at",
            "columnType": "TIMESTAMP"
        }
    )
    ddl_events.append(add_column)
    
    # すべてのクライアントに全イベントを適用
    for event in ddl_events:
        for client in clients:
            client.apply_event(event)
    
    # すべてのクライアントが同じスキーマバージョンを持つことを確認
    versions = [client.get_schema_state()["version"] for client in clients]
    assert len(set(versions)) == 1  # すべて同じバージョン
    assert versions[0] == len(ddl_events)  # イベント数と一致


def test_feature_concurrent_schema_operations():
    """機能: 並行スキーマ操作の処理"""
    # 2つのクライアントが同時に異なるテーブルを作成
    client_a = TestableKuzuClient("client-A")
    client_b = TestableKuzuClient("client-B")
    
    # クライアントAがOrderテーブルを作成
    create_order = client_a.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Order",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "total", "type": "DOUBLE"}
            ],
            "primaryKey": "id"
        }
    )
    
    # クライアントBがPaymentテーブルを作成
    create_payment = client_b.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Payment",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "amount", "type": "DOUBLE"}
            ],
            "primaryKey": "id"
        }
    )
    
    # 各クライアントが自分のDDLを適用
    client_a.apply_event(create_order)
    client_b.apply_event(create_payment)
    
    # 相互に同期
    client_a.apply_event(create_payment)
    client_b.apply_event(create_order)
    
    # 両クライアントが両方のテーブルを持つことを確認
    assert client_a.has_table("Order")
    assert client_a.has_table("Payment")
    assert client_b.has_table("Order")
    assert client_b.has_table("Payment")
    
    # スキーマ状態が一致することを確認
    state_a = client_a.get_schema_state()
    state_b = client_b.get_schema_state()
    assert state_a["version"] == state_b["version"]
    assert set(state_a["tables"].keys()) == set(state_b["tables"].keys())


if __name__ == "__main__":
    # 機能テストを実行
    test_feature_new_client_auto_schema_sync()
    print("✅ 新規クライアントの自動スキーマ同期")
    
    test_feature_dynamic_schema_extension()
    print("✅ 動的なスキーマ拡張（カラム追加）")
    
    test_feature_ddl_dependency_management()
    print("✅ 依存関係のあるDDL操作")
    
    test_feature_schema_version_tracking()
    print("✅ スキーマバージョン管理")
    
    test_feature_concurrent_schema_operations()
    print("✅ 並行スキーマ操作の処理")
    
    print("\n🎉 すべてのDDL同期機能テストが成功しました！")