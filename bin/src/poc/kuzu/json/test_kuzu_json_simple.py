#!/usr/bin/env python3
import kuzu
import tempfile
import shutil


def test_json_functionality():
    """Test KuzuDB JSON functionality without pytest"""
    temp_dir = tempfile.mkdtemp()
    try:
        db = kuzu.Database(temp_dir)
        conn = kuzu.Connection(db)
        
        print("Test 1: Installing JSON extension...")
        conn.execute("INSTALL json;")
        conn.execute("LOAD json;")
        print("✓ JSON extension loaded")
        
        print("\nTest 2: Creating table with JSON column...")
        conn.execute("CREATE NODE TABLE Person (id INT64, description JSON, primary key(id));")
        print("✓ Table created")
        
        print("\nTest 3: Inserting JSON data...")
        conn.execute("CREATE (p:Person {id: 20, description: to_json({height: 52, age: 32, scores: [1,2,5]})});")
        conn.execute("CREATE (p:Person {id: 40, description: to_json({age: 55, scores: [1,32,5,null], name: 'dan'})});")
        print("✓ JSON data inserted")
        
        print("\nTest 4: Querying JSON data...")
        result = conn.execute("MATCH (p:Person) RETURN p.* ORDER BY p.id;")
        df = result.get_as_df()
        print(f"✓ Found {len(df)} records")
        print(df)
        
        print("\nTest 5: Using json_extract...")
        result = conn.execute("""
            MATCH (p:Person)
            WHERE json_extract(p.description, 'age') < 50
            RETURN p.id AS id, json_extract(p.description, 'age') AS age;
        """)
        df = result.get_as_df()
        print(f"✓ Filtered {len(df)} records with age < 50")
        print(df)
        
        print("\nTest 6: Testing JSON functions...")
        
        # to_json
        result = conn.execute("RETURN to_json('{\"name\": \"Gregory\"}') AS person;")
        print(f"✓ to_json: {result.get_as_df().iloc[0]['person']}")
        
        # json_object
        result = conn.execute("RETURN json_object('name', 'Alicia', 'age', 28) AS obj;")
        print(f"✓ json_object: {result.get_as_df().iloc[0]['obj']}")
        
        # json_array
        result = conn.execute("RETURN json_array('Alicia', '25', NULL) AS arr;")
        print(f"✓ json_array: {result.get_as_df().iloc[0]['arr']}")
        
        # json_merge_patch
        result = conn.execute("RETURN json_merge_patch('{\"name\": \"Alicia\"}', '{\"age\": 28}') AS merged;")
        print(f"✓ json_merge_patch: {result.get_as_df().iloc[0]['merged']}")
        
        # json_array_length
        result = conn.execute("RETURN json_array_length('[\"1\", \"1\", \"4\", null]') AS len;")
        print(f"✓ json_array_length: {result.get_as_df().iloc[0]['len']}")
        
        # json_contains
        result = conn.execute("RETURN json_contains('{\"name\": \"Alicia\"}', '\"Alicia\"') AS found;")
        print(f"✓ json_contains: {result.get_as_df().iloc[0]['found']}")
        
        # json_keys
        result = conn.execute("RETURN json_keys('{ \"family\": \"anatidae\", \"species\": [ \"duck\", \"goose\", \"swan\", null ] }') AS keys;")
        print(f"✓ json_keys: {result.get_as_df().iloc[0]['keys']}")
        
        # json_valid
        result = conn.execute("RETURN json_valid('{\"name\": \"Alicia\", \"age\": 28}') AS is_valid;")
        print(f"✓ json_valid: {result.get_as_df().iloc[0]['is_valid']}")
        
        conn.close()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_json_functionality()