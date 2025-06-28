"""KuzuDB UDF Test Suite

Tests for KuzuDB User Defined Functions (UDF) functionality.
Run with: uv run pytest test_kuzu_udf.py -v
"""

import re
import time
import pytest
import kuzu


class TestKuzuUDF:
    """Test suite for KuzuDB UDF functionality"""
    
    @pytest.fixture
    def db_conn(self):
        """Create in-memory KuzuDB connection for each test"""
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        yield conn
        # Cleanup happens automatically when connection is closed
    
    def test_extract_scheme_udf_registration_succeeds(self, db_conn):
        """Test UDF registration for scheme extraction"""
        # Arrange
        def extract_scheme(uri: str) -> str:
            match = re.match(r'^([^:]+)://', uri)
            return match.group(1) if match else ""
        
        # Act
        db_conn.create_function("extract_scheme", extract_scheme)
        
        # Assert - function is registered (no exception thrown)
        assert True  # If we got here, registration succeeded
    
    def test_extract_scheme_udf_in_cypher_query(self, db_conn):
        """Test using extract_scheme UDF in Cypher queries"""
        # Arrange
        db_conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
        
        # Insert test data
        test_data = [
            "req://system/auth",
            "file:///src/main.py",
            "test://unit/login"
        ]
        for uri in test_data:
            db_conn.execute(f"CREATE (:LocationURI {{id: '{uri}'}})")
        
        # Register UDF
        def extract_scheme(uri: str) -> str:
            match = re.match(r'^([^:]+)://', uri)
            return match.group(1) if match else ""
        
        db_conn.create_function("extract_scheme", extract_scheme)
        
        # Act
        result = db_conn.execute("""
            MATCH (n:LocationURI)
            RETURN n.id, extract_scheme(n.id) as scheme
            ORDER BY n.id
        """)
        
        # Assert
        rows = list(result)
        assert len(rows) == 3
        assert rows[0] == {"n.id": "file:///src/main.py", "scheme": "file"}
        assert rows[1] == {"n.id": "req://system/auth", "scheme": "req"}
        assert rows[2] == {"n.id": "test://unit/login", "scheme": "test"}
    
    def test_validate_hierarchy_udf_in_where_clause(self, db_conn):
        """Test hierarchy validation UDF used in WHERE clause"""
        # Arrange
        db_conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
        db_conn.execute("CREATE REL TABLE CONTAINS_LOCATION (FROM LocationURI TO LocationURI)")
        
        # Create nodes
        nodes = ["req://system", "req://system/auth", "req://system/auth/login", "req://invalid"]
        for node in nodes:
            db_conn.execute(f"CREATE (:LocationURI {{id: '{node}'}})")
        
        # Create relationships (some valid, some invalid)
        relationships = [
            ("req://system", "req://system/auth"),  # Valid
            ("req://system/auth", "req://system/auth/login"),  # Valid
            ("req://invalid", "req://system"),  # Invalid
        ]
        for parent, child in relationships:
            db_conn.execute(f"""
                MATCH (p:LocationURI {{id: '{parent}'}}), 
                      (c:LocationURI {{id: '{child}'}})
                CREATE (p)-[:CONTAINS_LOCATION]->(c)
            """)
        
        # Register validation UDF
        def validate_hierarchy(parent_uri: str, child_uri: str) -> bool:
            return child_uri.startswith(parent_uri + "/")
        
        db_conn.create_function("validate_hierarchy", validate_hierarchy)
        
        # Act - Find valid hierarchies
        result = db_conn.execute("""
            MATCH (p:LocationURI)-[:CONTAINS_LOCATION]->(c:LocationURI)
            WHERE validate_hierarchy(p.id, c.id)
            RETURN p.id as parent, c.id as child
            ORDER BY parent
        """)
        
        # Assert
        valid_rows = list(result)
        assert len(valid_rows) == 2
        assert valid_rows[0] == {"parent": "req://system", "child": "req://system/auth"}
        assert valid_rows[1] == {"parent": "req://system/auth", "child": "req://system/auth/login"}
    
    def test_udf_with_aggregation_and_grouping(self, db_conn):
        """Test UDF combined with GROUP BY and aggregation functions"""
        # Arrange
        db_conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
        
        # Insert diverse test data
        test_uris = [
            "req://vision/goal1",
            "req://architecture/module1",
            "req://architecture/module2", 
            "file:///src/main.py",
            "file:///src/utils.py",
            "file:///tests/test_main.py",
            "test://unit/test1",
            "test://integration/test2"
        ]
        
        for uri in test_uris:
            db_conn.execute(f"CREATE (:LocationURI {{id: '{uri}'}})")
        
        # Register UDF
        def extract_scheme(uri: str) -> str:
            match = re.match(r'^([^:]+)://', uri)
            return match.group(1) if match else "unknown"
        
        db_conn.create_function("extract_scheme", extract_scheme)
        
        # Act - Aggregate by scheme
        result = db_conn.execute("""
            MATCH (n:LocationURI)
            WITH extract_scheme(n.id) as scheme, count(*) as cnt
            RETURN scheme, cnt
            ORDER BY cnt DESC, scheme
        """)
        
        # Assert
        rows = list(result)
        assert len(rows) == 3
        assert rows[0] == {"scheme": "file", "cnt": 3}
        assert rows[1] == {"scheme": "req", "cnt": 3}
        assert rows[2] == {"scheme": "test", "cnt": 2}
    
    def test_udf_performance_comparison(self, db_conn):
        """Compare performance: UDF filtering vs application-side filtering"""
        # Arrange
        db_conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
        
        # Create many nodes for performance testing
        num_nodes = 1000
        schemes = ["req", "file", "test", "doc", "config"]
        
        for i in range(num_nodes):
            scheme = schemes[i % len(schemes)]
            db_conn.execute(f"CREATE (:LocationURI {{id: '{scheme}://path/to/item{i}'}})")
        
        # Register UDF
        def extract_scheme(uri: str) -> str:
            match = re.match(r'^([^:]+)://', uri)
            return match.group(1) if match else ""
        
        db_conn.create_function("extract_scheme", extract_scheme)
        
        # Act 1: Filter using UDF (database-side)
        start_udf = time.time()
        result_udf = db_conn.execute("""
            MATCH (n:LocationURI)
            WHERE extract_scheme(n.id) = 'req'
            RETURN count(*) as cnt
        """)
        udf_count = list(result_udf)[0]["cnt"]
        udf_time = time.time() - start_udf
        
        # Act 2: Fetch all and filter in Python (application-side)
        start_python = time.time()
        all_nodes = db_conn.execute("MATCH (n:LocationURI) RETURN n.id")
        python_count = 0
        for row in all_nodes:
            match = re.match(r'^([^:]+)://', row["n.id"])
            if match and match.group(1) == "req":
                python_count += 1
        python_time = time.time() - start_python
        
        # Assert
        assert udf_count == python_count == 200  # 1000 nodes / 5 schemes
        assert udf_time < python_time  # UDF should be faster
        
        # Log performance metrics
        print(f"\nPerformance comparison (n={num_nodes}):")
        print(f"  UDF filtering: {udf_time:.4f}s")
        print(f"  Python filtering: {python_time:.4f}s")
        print(f"  UDF is {python_time/udf_time:.1f}x faster")
    
    def test_complex_udf_with_path_analysis(self, db_conn):
        """Test more complex UDF analyzing URI paths"""
        # Arrange
        db_conn.execute("CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY)")
        
        # Insert hierarchical URIs
        uris = [
            "req://system",
            "req://system/auth",
            "req://system/auth/login",
            "req://system/auth/logout",
            "req://system/db",
            "req://system/db/connection"
        ]
        
        for uri in uris:
            db_conn.execute(f"CREATE (:LocationURI {{id: '{uri}'}})")
        
        # Register UDF to count path depth
        def count_path_depth(uri: str) -> int:
            # Remove scheme
            path = re.sub(r'^[^:]+://', '', uri)
            # Count path segments
            return len([s for s in path.split('/') if s])
        
        db_conn.create_function("count_path_depth", count_path_depth)
        
        # Act - Group by depth
        result = db_conn.execute("""
            MATCH (n:LocationURI)
            WITH count_path_depth(n.id) as depth, collect(n.id) as uris
            RETURN depth, size(uris) as count, uris
            ORDER BY depth
        """)
        
        # Assert
        rows = list(result)
        assert len(rows) == 3
        assert rows[0]["depth"] == 1  # system
        assert rows[0]["count"] == 1
        assert rows[1]["depth"] == 2  # auth, db
        assert rows[1]["count"] == 2
        assert rows[2]["depth"] == 3  # login, logout, connection
        assert rows[2]["count"] == 3


# ===== EXAMPLE USAGE =====

def print_udf_examples():
    """Print example UDF usage patterns"""
    examples = """
=== KuzuDB UDF Usage Examples ===

1. Simple extraction UDF:
   ```cypher
   MATCH (n:LocationURI)
   WHERE extract_scheme(n.id) = 'req'
   RETURN n.id
   ```

2. Validation UDF in relationships:
   ```cypher
   MATCH (p:LocationURI)-[:CONTAINS_LOCATION]->(c:LocationURI)
   WHERE NOT validate_hierarchy(p.id, c.id)
   RETURN p.id as parent, c.id as invalid_child
   ```

3. Complex aggregation with UDF:
   ```cypher
   MATCH (n:LocationURI)
   WITH extract_scheme(n.id) as scheme, 
        count_path_depth(n.id) as depth,
        count(*) as cnt
   RETURN scheme, avg(depth) as avg_depth, cnt
   ORDER BY avg_depth DESC
   ```

4. UDF in CASE expressions:
   ```cypher
   MATCH (n:LocationURI)
   RETURN n.id,
          CASE 
            WHEN extract_scheme(n.id) = 'req' THEN 'requirement'
            WHEN extract_scheme(n.id) = 'file' THEN 'source code'
            ELSE 'other'
          END as type
   ```
"""
    print(examples)


if __name__ == "__main__":
    print_udf_examples()
    pytest.main([__file__, "-v"])