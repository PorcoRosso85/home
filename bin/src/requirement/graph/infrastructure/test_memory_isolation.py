#!/usr/bin/env python3
"""
Test to prove that KuzuDB :memory: databases are naturally isolated without UUID.

This is a RED test that should initially fail if UUID is truly needed for isolation.
The test creates two separate :memory: databases without any UUID and verifies
that tables created in one database don't exist in the other.
"""

import pytest
import kuzu


class TestMemoryIsolation:
    """Test suite to verify KuzuDB :memory: database isolation without UUID."""
    
    def test_memory_databases_are_isolated_without_uuid(self):
        """
        RED Test: Verify that two :memory: databases are isolated without UUID.
        
        This test should fail if UUID is required for isolation, proving that
        the current assumption about needing UUID for isolation is correct.
        """
        # Create two separate :memory: databases without any UUID
        db1 = kuzu.Database(":memory:")
        db2 = kuzu.Database(":memory:")
        
        # Create connections
        conn1 = kuzu.Connection(db1)
        conn2 = kuzu.Connection(db2)
        
        try:
            # Create a table in the first database
            create_table_query = """
            CREATE NODE TABLE IsolationTestTable(
                id INT64,
                data STRING,
                PRIMARY KEY(id)
            )
            """
            conn1.execute(create_table_query)
            
            # Insert test data in database 1
            conn1.execute("CREATE (:IsolationTestTable {id: 1, data: 'DB1_DATA'})")
            
            # Verify table exists and has data in database 1
            result1 = conn1.execute("MATCH (t:IsolationTestTable) RETURN count(t) as count")
            count_db1 = result1.get_next()[0]
            assert count_db1 == 1, f"Expected 1 record in DB1, got {count_db1}"
            
            # Now check if the table exists in database 2
            # This should fail if databases are properly isolated
            with pytest.raises(Exception) as exc_info:
                conn2.execute("MATCH (t:IsolationTestTable) RETURN count(t) as count")
            
            # Verify the error indicates the table doesn't exist
            error_message = str(exc_info.value).lower()
            assert "isolationtesttable" in error_message or "table" in error_message, \
                f"Expected table not found error, got: {exc_info.value}"
            
        finally:
            # Clean up connections
            conn1.close()
            conn2.close()
    
    def test_table_creation_isolation(self):
        """
        RED Test: Verify table creation in one :memory: DB doesn't affect another.
        
        This test creates different tables in two databases and verifies
        they remain completely separate.
        """
        # Create two separate :memory: databases
        db1 = kuzu.Database(":memory:")
        db2 = kuzu.Database(":memory:")
        
        conn1 = kuzu.Connection(db1)
        conn2 = kuzu.Connection(db2)
        
        try:
            # Create different tables in each database
            conn1.execute("""
                CREATE NODE TABLE Database1Table(
                    id INT64,
                    name STRING,
                    PRIMARY KEY(id)
                )
            """)
            
            conn2.execute("""
                CREATE NODE TABLE Database2Table(
                    id INT64,
                    value DOUBLE,
                    PRIMARY KEY(id)
                )
            """)
            
            # Verify DB1 only has its table
            with pytest.raises(Exception):
                conn1.execute("MATCH (t:Database2Table) RETURN t")
            
            # Verify DB2 only has its table  
            with pytest.raises(Exception):
                conn2.execute("MATCH (t:Database1Table) RETURN t")
            
            # Verify each can query its own table
            conn1.execute("CREATE (:Database1Table {id: 1, name: 'test'})")
            result1 = conn1.execute("MATCH (t:Database1Table) RETURN count(t) as count")
            assert result1.get_next()[0] == 1
            
            conn2.execute("CREATE (:Database2Table {id: 1, value: 3.14})")
            result2 = conn2.execute("MATCH (t:Database2Table) RETURN count(t) as count")
            assert result2.get_next()[0] == 1
            
        finally:
            conn1.close()
            conn2.close()
    
    def test_schema_isolation(self):
        """
        RED Test: Verify schema changes in one DB don't affect another.
        
        This test modifies schema in one database and ensures the other
        database remains unaffected.
        """
        db1 = kuzu.Database(":memory:")
        db2 = kuzu.Database(":memory:")
        
        conn1 = kuzu.Connection(db1)
        conn2 = kuzu.Connection(db2)
        
        try:
            # Create a table in both databases with same name but different schema
            conn1.execute("""
                CREATE NODE TABLE SharedName(
                    id INT64,
                    field1 STRING,
                    PRIMARY KEY(id)
                )
            """)
            
            conn2.execute("""
                CREATE NODE TABLE SharedName(
                    id INT64,
                    field2 INT64,
                    field3 BOOLEAN,
                    PRIMARY KEY(id)
                )
            """)
            
            # Insert data with respective schemas
            conn1.execute("CREATE (:SharedName {id: 1, field1: 'test'})")
            conn2.execute("CREATE (:SharedName {id: 1, field2: 100, field3: true})")
            
            # Verify each database has its own schema
            result1 = conn1.execute("MATCH (t:SharedName) RETURN t.field1")
            assert result1.get_next()[0] == 'test'
            
            result2 = conn2.execute("MATCH (t:SharedName) RETURN t.field2, t.field3")
            row = result2.get_next()
            assert row[0] == 100
            assert row[1] == True
            
            # Verify accessing wrong fields fails
            with pytest.raises(Exception):
                conn1.execute("MATCH (t:SharedName) RETURN t.field2")
                
            with pytest.raises(Exception):
                conn2.execute("MATCH (t:SharedName) RETURN t.field1")
                
        finally:
            conn1.close()
            conn2.close()


if __name__ == "__main__":
    # Run the tests
    test = TestMemoryIsolation()
    
    print("Running Test 1: Memory databases are isolated without UUID...")
    try:
        test.test_memory_databases_are_isolated_without_uuid()
        print("✓ Test 1 PASSED: Databases are isolated without UUID")
    except AssertionError as e:
        print(f"✗ Test 1 FAILED: {e}")
    except Exception as e:
        print(f"✗ Test 1 ERROR: {e}")
    
    print("\nRunning Test 2: Table creation isolation...")
    try:
        test.test_table_creation_isolation()
        print("✓ Test 2 PASSED: Table creation is isolated")
    except AssertionError as e:
        print(f"✗ Test 2 FAILED: {e}")
    except Exception as e:
        print(f"✗ Test 2 ERROR: {e}")
    
    print("\nRunning Test 3: Schema isolation...")
    try:
        test.test_schema_isolation()
        print("✓ Test 3 PASSED: Schemas are isolated")
    except AssertionError as e:
        print(f"✗ Test 3 FAILED: {e}")
    except Exception as e:
        print(f"✗ Test 3 ERROR: {e}")
    
    print("\n" + "="*60)
    print("CONCLUSION: Testing KuzuDB :memory: isolation without UUID")
    print("If tests pass: UUID is NOT needed for isolation")
    print("If tests fail: UUID IS needed for isolation")
    print("="*60)