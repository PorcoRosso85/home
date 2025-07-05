#!/usr/bin/env python3
import pytest
import kuzu
import tempfile
import shutil
import os


class TestKuzuJsonDataType:
    """Tests for KuzuDB JSON data type functionality"""
    
    @pytest.fixture
    def db(self):
        """Create a temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db = kuzu.Database(temp_dir)
        conn = kuzu.Connection(db)
        yield conn
        conn.close()
        shutil.rmtree(temp_dir)
    
    def test_create_table_with_json_column(self, db):
        """Test creating a node table with JSON column"""
        db.execute("INSTALL json;")
        db.execute("LOAD json;")
        db.execute("CREATE NODE TABLE Person (id INT64, description JSON, primary key(id));")
        
        result = db.execute("CALL table_info('Person') RETURN *;")
        columns = result.get_as_df()
        assert 'description' in columns['name'].values
        assert columns[columns['name'] == 'description']['type'].values[0] == 'JSON'
    
    def test_insert_json_data_with_to_json(self, db):
        """Test inserting JSON data using to_json function"""
        db.execute("INSTALL json;")
        db.execute("LOAD json;")
        db.execute("CREATE NODE TABLE Person (id INT64, description JSON, primary key(id));")
        
        db.execute("CREATE (p:Person {id: 20, description: to_json({height: 52, age: 32, scores: [1,2,5]})});")
        db.execute("CREATE (p:Person {id: 40, description: to_json({age: 55, scores: [1,32,5,null], name: 'dan'})});")
        
        result = db.execute("MATCH (p:Person) RETURN p.* ORDER BY p.id;")
        df = result.get_as_df()
        
        assert len(df) == 2
        assert df.iloc[0]['p.id'] == 20
        assert df.iloc[0]['p.description'] == '{"height":52,"age":32,"scores":[1,2,5]}'
        assert df.iloc[1]['p.id'] == 40
        assert df.iloc[1]['p.description'] == '{"age":55,"scores":[1,32,5,null],"name":"dan"}'
    
    def test_query_json_with_json_extract(self, db):
        """Test querying JSON data using json_extract"""
        db.execute("INSTALL json;")
        db.execute("LOAD json;")
        db.execute("CREATE NODE TABLE Person (id INT64, description JSON, primary key(id));")
        db.execute("CREATE (p:Person {id: 20, description: to_json({height: 52, age: 32, scores: [1,2,5]})});")
        db.execute("CREATE (p:Person {id: 40, description: to_json({age: 55, scores: [1,32,5,null], name: 'dan'})});")
        
        result = db.execute("""
            MATCH (p:Person)
            WHERE json_extract(p.description, 'age') < 50
            RETURN p.id AS id, json_extract(p.description, 'age') AS age;
        """)
        df = result.get_as_df()
        
        assert len(df) == 1
        assert df.iloc[0]['id'] == 20
        assert df.iloc[0]['age'] == 32


class TestKuzuJsonFunctions:
    """Tests for KuzuDB JSON functions"""
    
    @pytest.fixture
    def db(self):
        """Create a temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db = kuzu.Database(temp_dir)
        conn = kuzu.Connection(db)
        conn.execute("INSTALL json;")
        conn.execute("LOAD json;")
        yield conn
        conn.close()
        shutil.rmtree(temp_dir)
    
    def test_to_json_function(self, db):
        """Test to_json function with various inputs"""
        # String to JSON
        result = db.execute("RETURN to_json('{\"name\": \"Gregory\"}') AS person;")
        assert result.get_as_df().iloc[0]['person'] == '{"name":"Gregory"}'
        
        # Array to JSON
        result = db.execute("RETURN to_json([1,2,3]) AS json_array;")
        assert result.get_as_df().iloc[0]['json_array'] == '[1,2,3]'
        
        # Simple string to JSON
        result = db.execute("RETURN to_json('Alicia') AS simple_string;")
        assert result.get_as_df().iloc[0]['simple_string'] == '"Alicia"'
    
    def test_cast_to_json(self, db):
        """Test CAST to JSON"""
        result = db.execute("RETURN cast('{\"name\": \"Alicia\", \"age\": 28}' AS JSON) AS json_data;")
        assert result.get_as_df().iloc[0]['json_data'] == '{"name":"Alicia","age":28}'
    
    def test_json_object_function(self, db):
        """Test json_object function"""
        # Single key-value pair
        result = db.execute("RETURN json_object('name', 'Alicia') AS obj;")
        assert result.get_as_df().iloc[0]['obj'] == '{"name":"Alicia"}'
        
        # Multiple key-value pairs
        result = db.execute("RETURN json_object('name', 'Alicia', 'age', 28) AS obj;")
        assert result.get_as_df().iloc[0]['obj'] == '{"name":"Alicia","age":28}'
    
    def test_json_array_function(self, db):
        """Test json_array function"""
        result = db.execute("RETURN json_array('Alicia', '25', NULL) AS arr;")
        assert result.get_as_df().iloc[0]['arr'] == '["Alicia","25",null]'
    
    def test_json_merge_patch(self, db):
        """Test json_merge_patch function"""
        # Merge two objects
        result = db.execute("RETURN json_merge_patch('{\"name\": \"Alicia\"}', '{\"age\": 28}') AS merged;")
        assert result.get_as_df().iloc[0]['merged'] == '{"name":"Alicia","age":28}'
        
        # Merge with NULL
        result = db.execute("RETURN json_merge_patch('3', NULL) AS merged;")
        assert result.get_as_df().iloc[0]['merged'] is None
    
    def test_json_extract_function(self, db):
        """Test json_extract function"""
        # Extract with path
        result = db.execute("RETURN json_extract('{\"Software\": {\"Database\": [\"duck\", \"kuzu\"]}}', 'Software/Database/1') AS extracted;")
        assert result.get_as_df().iloc[0]['extracted'] == '"kuzu"'
        
        # Extract with list of paths
        result = db.execute("RETURN json_extract('{\"Software\": {\"Database\": [\"duck\", \"kuzu\"]}}', ['Software/Database/1', 'Software/Database/0']) AS extracted;")
        assert result.get_as_df().iloc[0]['extracted'] == '["kuzu","duck"]'
        
        # Extract with integer index
        result = db.execute("RETURN json_extract('[1, 2, 42]', 2) AS nums;")
        assert result.get_as_df().iloc[0]['nums'] == '42'
    
    def test_json_array_length(self, db):
        """Test json_array_length function"""
        # Valid array
        result = db.execute("RETURN json_array_length('[\"1\", \"1\", \"4\", null]') AS len;")
        assert result.get_as_df().iloc[0]['len'] == 4
        
        # Non-array JSON
        result = db.execute("RETURN json_array_length('{\"kuzu\": [\"1\", \"1\", \"4\", null]}') AS len;")
        assert result.get_as_df().iloc[0]['len'] == 0
    
    def test_json_contains(self, db):
        """Test json_contains function"""
        # String in object
        result = db.execute("RETURN json_contains('{\"name\": \"Alicia\"}', '\"Alicia\"') AS found_name;")
        assert result.get_as_df().iloc[0]['found_name'] == True
        
        # Number in object
        result = db.execute("RETURN json_contains('{\"age\": 28}', '28') AS found_age;")
        assert result.get_as_df().iloc[0]['found_age'] == True
    
    def test_json_keys(self, db):
        """Test json_keys function"""
        result = db.execute("RETURN json_keys('{ \"family\": \"anatidae\", \"species\": [ \"duck\", \"goose\", \"swan\", null ] }') AS keys;")
        keys = result.get_as_df().iloc[0]['keys']
        assert set(keys) == {'family', 'species'}
    
    def test_json_structure(self, db):
        """Test json_structure function"""
        result = db.execute("RETURN json_structure('[{\"a\": -1, \"b\": [1000, 2000, 3000]}, {\"a\": 2, \"c\": \"hi\"}]') AS structure;")
        assert 'STRUCT' in result.get_as_df().iloc[0]['structure']
    
    def test_json_valid(self, db):
        """Test json_valid function"""
        # Valid JSON
        result = db.execute("RETURN json_valid('{\"name\": \"Alicia\", \"age\": 28}') AS is_valid;")
        assert result.get_as_df().iloc[0]['is_valid'] == True
        
        # Invalid JSON
        result = db.execute("RETURN json_valid('\"name\": \"Alicia\", \"age\": 28') AS is_valid;")
        assert result.get_as_df().iloc[0]['is_valid'] == False
    
    def test_json_function(self, db):
        """Test json minification function"""
        result = db.execute("RETURN json('[        {\"a\":  [1],     \"b\": 2,\"c\": 1}, 1,    5, 9]') AS minified;")
        assert result.get_as_df().iloc[0]['minified'] == '[{"a":[1],"b":2,"c":1},1,5,9]'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])