#!/usr/bin/env python3
"""
KuzuDB Native Client for TypeScript Integration
ネイティブKuzuDBをTypeScriptから使用するためのクライアント

This script acts as a bridge between TypeScript and native KuzuDB,
handling DML execution and state queries through JSON-RPC style communication.
"""

import sys
import json
import os

# Try importing kuzu, but fall back to mock if not available
try:
    import kuzu
    
    def create_database(path=None):
        """Create database using direct kuzu import"""
        if path is None or path == ":memory:":
            return kuzu.Database(":memory:")
        else:
            return kuzu.Database(str(path))
    
    def create_connection(database):
        """Create connection using direct kuzu import"""
        return kuzu.Connection(database)
except ImportError:
    # Mock implementation for testing architecture
    print("WARNING: Using mock KuzuDB implementation", file=sys.stderr)
    
    class MockDatabase:
        def __init__(self, path):
            self.path = path
            self.data = {}
    
    class MockConnection:
        def __init__(self, db):
            self.db = db
            self.executed_queries = []
        
        def query(self, cypher, params=None):
            self.executed_queries.append((cypher, params))
            # Mock result
            class MockResult:
                def getAllObjects(self):
                    return []
                def getAll(self):
                    return []
            return MockResult()
    
    def create_database(path=None):
        return MockDatabase(path or ":memory:")
    
    def create_connection(database):
        return MockConnection(database)

import traceback

def is_error(result):
    """Check if result is an error"""
    return isinstance(result, dict) and "type" in result and result["type"].endswith("Error")

class KuzuNativeClient:
    def __init__(self):
        self.db = None
        self.conn = None
        self.initialized = False
        
    def initialize(self, path=None):
        """Initialize KuzuDB database and connection"""
        try:
            # Create in-memory database by default
            db_path = path if path else ":memory:"
            self.db = create_database(db_path)
            
            if is_error(self.db):
                return {"error": self.db}
            
            self.conn = create_connection(self.db)
            
            if is_error(self.conn):
                return {"error": self.conn}
            
            # Create default schema
            self._create_default_schema()
            
            self.initialized = True
            return {"success": True, "message": "Database initialized"}
            
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def _create_default_schema(self):
        """Create default schema for sync application"""
        queries = [
            # User node table
            """CREATE NODE TABLE IF NOT EXISTS User(
                id STRING, 
                name STRING, 
                email STRING, 
                PRIMARY KEY(id)
            )""",
            
            # Post node table
            """CREATE NODE TABLE IF NOT EXISTS Post(
                id STRING,
                content STRING,
                authorId STRING,
                PRIMARY KEY(id)
            )""",
            
            # FOLLOWS relationship table
            """CREATE REL TABLE IF NOT EXISTS FOLLOWS(FROM User TO User)""",
            
            # Counter node table
            """CREATE NODE TABLE IF NOT EXISTS Counter(
                id STRING,
                value INT64,
                PRIMARY KEY(id)
            )"""
        ]
        
        for query in queries:
            result = self.conn.query(query)
            # Log creation
            self.log("INFO", {
                "message": "Schema created",
                "query": query.replace('\n', ' ').strip()
            })
    
    def execute_template(self, template, params):
        """Execute a DML template with parameters"""
        if not self.initialized:
            return {"error": "Client not initialized"}
        
        templates = {
            "CREATE_USER": """
                CREATE (u:User {
                    id: $id,
                    name: $name,
                    email: $email
                })
            """,
            "UPDATE_USER": """
                MATCH (u:User {id: $id})
                SET u.name = $name
            """,
            "CREATE_POST": """
                CREATE (p:Post {
                    id: $id,
                    content: $content,
                    authorId: $authorId
                })
            """,
            "FOLLOW_USER": """
                MATCH (follower:User {id: $followerId})
                MATCH (target:User {id: $targetId})
                CREATE (follower)-[:FOLLOWS]->(target)
            """,
            "INCREMENT_COUNTER": """
                MERGE (c:Counter {id: $counterId})
                ON CREATE SET c.value = COALESCE($amount, 1)
                ON MATCH SET c.value = c.value + COALESCE($amount, 1)
            """,
            "QUERY_COUNTER": """
                MATCH (c:Counter {id: $counterId})
                RETURN c.value as value
            """
        }
        
        query = templates.get(template)
        if not query:
            return {"error": f"Unknown template: {template}"}
        
        try:
            # Execute query
            result = self.conn.query(query, params)
            
            # Log execution
            self.log("INFO", {
                "message": "DML executed",
                "template": template,
                "params": params
            })
            
            # Handle query results
            if template == "QUERY_COUNTER":
                result_set = result.getAllObjects()
                if result_set:
                    return {"success": True, "result": result_set[0].get("value", 0)}
                else:
                    return {"success": True, "result": 0}
            
            return {"success": True}
            
        except Exception as e:
            self.log("ERROR", {
                "message": "DML execution failed",
                "template": template,
                "params": params,
                "error": str(e)
            })
            return {"error": str(e)}
    
    def get_local_state(self):
        """Get current database state"""
        if not self.initialized:
            return {"error": "Client not initialized"}
        
        try:
            # Get users
            user_result = self.conn.query("""
                MATCH (u:User)
                RETURN u.id as id, u.name as name, u.email as email
                ORDER BY u.id
            """)
            users = user_result.getAllObjects() if hasattr(user_result, 'getAllObjects') else []
            
            # Get posts
            post_result = self.conn.query("""
                MATCH (p:Post)
                RETURN p.id as id, p.content as content, p.authorId as authorId
                ORDER BY p.id
            """)
            posts = post_result.getAllObjects() if hasattr(post_result, 'getAllObjects') else []
            
            # Get follows
            follow_result = self.conn.query("""
                MATCH (follower:User)-[:FOLLOWS]->(target:User)
                RETURN follower.id as followerId, target.id as targetId
            """)
            follows = follow_result.getAllObjects() if hasattr(follow_result, 'getAllObjects') else []
            
            return {
                "success": True,
                "state": {
                    "users": users,
                    "posts": posts,
                    "follows": follows
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def log(self, level, data):
        """Log to stderr for TypeScript telemetry"""
        log_entry = {
            "level": level,
            "timestamp": self._get_timestamp(),
            "uri": "sync/kuzu_ts/native_client",
            **data
        }
        print(json.dumps(log_entry), file=sys.stderr)
    
    def _get_timestamp(self):
        """Get ISO timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def execute_query(self, query, params=None):
        """Execute raw Cypher query"""
        if not self.initialized:
            return {"error": "Client not initialized"}
        
        try:
            result = self.conn.query(query, params or {})
            
            # Log execution
            self.log("DEBUG", {
                "message": "Raw query executed",
                "query": query.replace('\n', ' ').strip()
            })
            
            # Try to get results if available
            if hasattr(result, 'getAllObjects'):
                return {"success": True, "result": result.getAllObjects()}
            else:
                return {"success": True, "result": None}
            
        except Exception as e:
            self.log("ERROR", {
                "message": "Query execution failed",
                "query": query,
                "error": str(e)
            })
            return {"error": str(e)}
    
    def handle_request(self, request):
        """Handle JSON-RPC style request"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return self.initialize(params.get("path"))
        elif method == "executeTemplate":
            return self.execute_template(params["template"], params["params"])
        elif method == "getLocalState":
            return self.get_local_state()
        elif method == "executeQuery":
            return self.execute_query(params["query"], params.get("params"))
        else:
            return {"error": f"Unknown method: {method}"}


def main():
    """Main entry point - reads JSON requests from stdin, writes responses to stdout"""
    client = KuzuNativeClient()
    
    # Log startup
    client.log("INFO", {"message": "Native KuzuDB client started"})
    
    # Read line by line from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = client.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            error_response = {"error": f"Invalid JSON: {str(e)}"}
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {"error": str(e), "traceback": traceback.format_exc()}
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()