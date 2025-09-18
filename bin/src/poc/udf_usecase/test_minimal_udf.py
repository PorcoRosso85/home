"""Minimal KuzuDB UDF Test
最小限のUDFテスト環境
"""

import kuzu
import pytest


def test_simple_udf():
    """Test the simplest possible UDF"""
    # Create in-memory database
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Define a simple UDF that adds 10 to a number
    def add_ten(x: int) -> int:
        return x + 10
    
    # Register the UDF
    conn.create_function("add_ten", add_ten)
    
    # Create a simple table
    conn.execute("CREATE NODE TABLE Numbers (value INT64, PRIMARY KEY(value))")
    conn.execute("CREATE (:Numbers {value: 5})")
    conn.execute("CREATE (:Numbers {value: 15})")
    conn.execute("CREATE (:Numbers {value: 25})")
    
    # Use the UDF in a query
    result = conn.execute("""
        MATCH (n:Numbers)
        RETURN n.value, add_ten(n.value) as plus_ten
        ORDER BY n.value
    """)
    
    # Verify results
    rows = []
    while result.has_next():
        rows.append(result.get_next())
    
    assert len(rows) == 3
    assert rows[0] == [5, 15]
    assert rows[1] == [15, 25]
    assert rows[2] == [25, 35]
    
    print("✅ Simple UDF test passed!")


def test_string_udf():
    """Test a UDF that works with strings"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Define a string UDF
    def make_uppercase(text: str) -> str:
        return text.upper()
    
    # Register the UDF
    conn.create_function("make_uppercase", make_uppercase)
    
    # Create table with string data
    conn.execute("CREATE NODE TABLE Words (word STRING, PRIMARY KEY(word))")
    conn.execute("CREATE (:Words {word: 'hello'})")
    conn.execute("CREATE (:Words {word: 'world'})")
    
    # Use the UDF
    result = conn.execute("""
        MATCH (w:Words)
        RETURN w.word, make_uppercase(w.word) as upper
        ORDER BY w.word
    """)
    
    # Verify results
    rows = []
    while result.has_next():
        rows.append(result.get_next())
    
    assert len(rows) == 2
    assert rows[0] == ["hello", "HELLO"]
    assert rows[1] == ["world", "WORLD"]
    
    print("✅ String UDF test passed!")


def test_udf_with_types():
    """Test UDF with explicit type declarations"""
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Define a UDF with explicit types
    def multiply(a, b):
        return a * b
    
    # Register with explicit types
    parameters = [kuzu.Type.INT64, kuzu.Type.INT64]
    return_type = kuzu.Type.INT64
    conn.create_function("multiply", multiply, parameters, return_type)
    
    # Create test data
    conn.execute("CREATE NODE TABLE Values (id INT64, a INT64, b INT64, PRIMARY KEY(id))")
    conn.execute("CREATE (:Values {id: 1, a: 2, b: 3})")
    conn.execute("CREATE (:Values {id: 2, a: 4, b: 5})")
    
    # Use the UDF
    result = conn.execute("""
        MATCH (v:Values)
        RETURN v.a, v.b, multiply(v.a, v.b) as product
        ORDER BY v.a
    """)
    
    # Verify
    rows = []
    while result.has_next():
        rows.append(result.get_next())
    
    assert len(rows) == 2
    assert rows[0] == [2, 3, 6]
    assert rows[1] == [4, 5, 20]
    
    print("✅ UDF with types test passed!")


if __name__ == "__main__":
    # Run individual tests
    test_simple_udf()
    test_string_udf()
    test_udf_with_types()
    
    print("\n🎉 All minimal UDF tests passed!")
    
    # Run with pytest for more detailed output
    # pytest.main([__file__, "-v"])