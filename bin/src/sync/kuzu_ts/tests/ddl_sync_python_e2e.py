"""
DDL Sync End-to-End Tests using Python
DDL同期のエンドツーエンドテスト（Python版）
"""

import asyncio
import json
import pytest
import uuid
import time
import kuzu

class DDLEnabledSyncClient:
    """WebSocket同期クライアント with DDL support"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.db = kuzu.Database(':memory:')
        self.conn = kuzu.Connection(self.db)
        self.schema_version = 0
        self.applied_ddls = []
        self.pending_ddls = []
        
    def create_ddl_event(self, template: str, params: dict, depends_on=None):
        """Create a DDL event"""
        event = {
            "id": f"ddl-{uuid.uuid4()}",
            "template": template,
            "type": "DDL",
            "params": params,
            "clientId": self.client_id,
            "timestamp": int(time.time() * 1000)
        }
        if depends_on:
            event["dependsOn"] = depends_on
        return event
        
    def apply_ddl_event(self, event: dict):
        """Apply a DDL event"""
        template = event["template"]
        params = event["params"]
        
        if template == "CREATE_NODE_TABLE":
            columns = ", ".join([
                f"{col['name']} {col['type']}" for col in params["columns"]
            ])
            query = f"""
                CREATE NODE TABLE {params['tableName']} (
                    {columns},
                    PRIMARY KEY({params['primaryKey']})
                )
            """
            print(f"Executing DDL: {query}")
        elif template == "CREATE_EDGE_TABLE":
            properties = params.get("properties", "")
            if properties:
                query = f"""
                    CREATE REL TABLE IF NOT EXISTS {params['tableName']} (
                        FROM {params['fromTable']} TO {params['toTable']},
                        {properties}
                    )
                """
            else:
                query = f"""
                    CREATE REL TABLE IF NOT EXISTS {params['tableName']} (
                        FROM {params['fromTable']} TO {params['toTable']}
                    )
                """
        elif template == "ADD_COLUMN":
            # KuzuDB doesn't support NULL/NOT NULL in ALTER TABLE ADD
            default = f" DEFAULT {params['defaultValue']}" if "defaultValue" in params else ""
            query = f"""
                ALTER TABLE {params['tableName']} 
                ADD {params['columnName']} {params['columnType']}{default}
            """
        else:
            raise ValueError(f"Unknown DDL template: {template}")
            
        # Execute DDL
        try:
            self.conn.execute(query)
            self.schema_version += 1
            self.applied_ddls.append(event["id"])
            print(f"✅ DDL executed successfully")
        except Exception as e:
            print(f"❌ DDL execution failed: {e}")
            raise
        
    def has_table(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            # Use SHOW_TABLES to check if table exists
            result = self.conn.execute("CALL show_tables() RETURN *")
            while result.has_next():
                table_info = result.get_next()
                if table_info[1] == table_name:  # Table name is at index 1
                    print(f"✅ Table '{table_name}' found")
                    return True
            print(f"❌ Table '{table_name}' not found")
            return False
        except Exception as e:
            print(f"Error checking table '{table_name}': {e}")
            return False
            
    def has_column(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            result = self.conn.execute(f"CALL table_info('{table_name}') RETURN *")
            while result.has_next():
                col_info = result.get_next()
                # col_info structure: (id, property_name, type, ...)
                if col_info[1] == column_name:  # column name is at index 1
                    print(f"✅ Column '{column_name}' found in table '{table_name}'")
                    return True
            print(f"❌ Column '{column_name}' not found in table '{table_name}'")
            return False
        except Exception as e:
            print(f"Error checking column: {e}")
            return False
            
    def get_schema_version(self) -> int:
        """Get current schema version"""
        return self.schema_version


@pytest.mark.asyncio
async def test_ddl_sync_basic():
    """Test basic DDL synchronization"""
    # Create two clients
    client1 = DDLEnabledSyncClient("client-1")
    client2 = DDLEnabledSyncClient("client-2") 
    
    print("Testing basic DDL synchronization...")
    
    # Client1 creates a table
    create_table_event = client1.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Customer",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "name", "type": "STRING"},
                {"name": "email", "type": "STRING"}
            ],
            "primaryKey": "id"
        }
    )
    
    client1.apply_ddl_event(create_table_event)
    assert client1.has_table("Customer")
    assert client1.get_schema_version() == 1
    
    # Simulate event propagation to client2
    client2.apply_ddl_event(create_table_event)
    assert client2.has_table("Customer")
    assert client2.get_schema_version() == 1
    
    # Client2 adds a column
    add_column_event = client2.create_ddl_event(
        "ADD_COLUMN",
        {
            "tableName": "Customer",
            "columnName": "phone",
            "columnType": "STRING",
            "nullable": True
        },
        depends_on=[create_table_event["id"]]
    )
    
    client2.apply_ddl_event(add_column_event)
    assert client2.has_column("Customer", "phone")
    assert client2.get_schema_version() == 2
    
    # Propagate to client1
    client1.apply_ddl_event(add_column_event)
    assert client1.has_column("Customer", "phone")
    assert client1.get_schema_version() == 2
    
    # Test DML on new schema
    client1.conn.execute("""
        CREATE (c:Customer {
            id: 'c1',
            name: 'Alice',
            email: 'alice@example.com',
            phone: '+1234567890'
        })
    """)
    
    result = client1.conn.execute("""
        MATCH (c:Customer {id: 'c1'})
        RETURN c.name as name, c.phone as phone
    """)
    
    row = result.get_next()
    assert row[0] == "Alice"
    assert row[1] == "+1234567890"
    
    print("✅ Basic DDL synchronization test passed!")


@pytest.mark.asyncio
async def test_ddl_dependency_management():
    """Test DDL dependency management"""
    client = DDLEnabledSyncClient("test-client")
    
    print("Testing DDL dependency management...")
    
    # Create table events
    user_table_event = client.create_ddl_event(
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
    
    post_table_event = client.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Post",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "content", "type": "STRING"},
                {"name": "authorId", "type": "STRING"}
            ],
            "primaryKey": "id"
        }
    )
    
    # Create relationship with dependencies
    relation_event = client.create_ddl_event(
        "CREATE_EDGE_TABLE",
        {
            "tableName": "AUTHORED",
            "fromTable": "User",
            "toTable": "Post"
        },
        depends_on=[user_table_event["id"], post_table_event["id"]]
    )
    
    # Apply in correct order
    client.apply_ddl_event(user_table_event)
    client.apply_ddl_event(post_table_event)
    client.apply_ddl_event(relation_event)
    
    assert client.has_table("User")
    assert client.has_table("Post")
    assert client.get_schema_version() == 3
    
    # Test relationship works
    client.conn.execute("""
        CREATE (u:User {id: 'u1', name: 'Bob'})
    """)
    client.conn.execute("""
        CREATE (p:Post {id: 'p1', content: 'Hello World', authorId: 'u1'})
    """)
    client.conn.execute("""
        MATCH (u:User {id: 'u1'})
        MATCH (p:Post {id: 'p1'})
        CREATE (u)-[:AUTHORED]->(p)
    """)
    
    # Verify relationship
    result = client.conn.execute("""
        MATCH (u:User)-[:AUTHORED]->(p:Post)
        RETURN u.name as author, p.content as content
    """)
    
    row = result.get_next()
    assert row[0] == "Bob"
    assert row[1] == "Hello World"
    
    print("✅ DDL dependency management test passed!")


@pytest.mark.asyncio
async def test_concurrent_ddl_operations():
    """Test concurrent DDL operations from multiple clients"""
    client1 = DDLEnabledSyncClient("client-1")
    client2 = DDLEnabledSyncClient("client-2")
    
    print("Testing concurrent DDL operations...")
    
    # Both clients create different tables
    orders_event = client1.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Orders",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "total", "type": "DOUBLE"}
            ],
            "primaryKey": "id"
        }
    )
    
    products_event = client2.create_ddl_event(
        "CREATE_NODE_TABLE",
        {
            "tableName": "Products",
            "columns": [
                {"name": "id", "type": "STRING"},
                {"name": "price", "type": "DOUBLE"}
            ],
            "primaryKey": "id"
        }
    )
    
    # Apply locally
    client1.apply_ddl_event(orders_event)
    client2.apply_ddl_event(products_event)
    
    # Cross-sync
    client1.apply_ddl_event(products_event)
    client2.apply_ddl_event(orders_event)
    
    # Verify both have both tables
    assert client1.has_table("Orders")
    assert client1.has_table("Products")
    assert client2.has_table("Orders")
    assert client2.has_table("Products")
    
    # Verify schema versions
    assert client1.get_schema_version() == 2
    assert client2.get_schema_version() == 2
    
    print("✅ Concurrent DDL operations test passed!")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_ddl_sync_basic())
    asyncio.run(test_ddl_dependency_management())
    asyncio.run(test_concurrent_ddl_operations())
    print("\n🎉 All DDL sync tests passed!")