"""
Tests for DDL migration functionality.
"""
import pytest
import kuzu
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for the database."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def db(temp_db_dir):
    """Create an in-memory KuzuDB instance."""
    db = kuzu.Database(temp_db_dir + "/test.db")
    yield db
    del db


@pytest.fixture
def conn(db):
    """Create a connection to the database."""
    conn = kuzu.Connection(db)
    yield conn
    conn.close()


@pytest.fixture
def ddl_path():
    """Get the path to the DDL migration file."""
    return Path(__file__).parent.parent / "ddl" / "migrations" / "3.5.0_reference_guardrails.cypher"


def test_apply_migration(conn, ddl_path):
    """Test that DDL can be applied successfully."""
    # Read the DDL file
    with open(ddl_path, 'r') as f:
        ddl_content = f.read()
    
    # Split DDL content by semicolons and execute each statement
    statements = [stmt.strip() for stmt in ddl_content.split(';') if stmt.strip()]
    
    # First, we need to create RequirementEntity table since IMPLEMENTS relationship depends on it
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING
        )
    """)
    
    # Execute each DDL statement
    for statement in statements:
        # Skip comments and empty lines
        if statement.startswith('//') or not statement:
            continue
        
        # Extract only CREATE statements
        lines = statement.split('\n')
        create_statement = []
        in_create = False
        
        for line in lines:
            if line.strip().startswith('CREATE'):
                in_create = True
            if in_create:
                if not line.strip().startswith('//'):
                    create_statement.append(line)
        
        if create_statement:
            sql = '\n'.join(create_statement)
            conn.execute(sql)
    
    # Verify tables were created
    result = conn.execute("CALL table_info('ReferenceEntity') RETURN *")
    assert result.has_next()
    
    result = conn.execute("CALL table_info('ExceptionRequest') RETURN *")
    assert result.has_next()
    
    result = conn.execute("CALL table_info('IMPLEMENTS') RETURN *")
    assert result.has_next()
    
    result = conn.execute("CALL table_info('HAS_EXCEPTION') RETURN *")
    assert result.has_next()


def test_reference_entity_schema(conn):
    """Test that ReferenceEntity table is created with correct schema."""
    # Create the ReferenceEntity table
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            source STRING,
            category STRING,
            level STRING,
            embedding DOUBLE[384],
            version STRING,
            url STRING
        )
    """)
    
    # Get table info
    result = conn.execute("CALL table_info('ReferenceEntity') RETURN *")
    
    # Collect column information
    columns = {}
    while result.has_next():
        row = result.get_next()
        col_name = row[1]  # column name is at index 1
        col_type = row[2]  # column type is at index 2
        columns[col_name] = col_type
    
    # Verify all expected columns exist
    expected_columns = {
        'id': 'STRING',
        'title': 'STRING', 
        'description': 'STRING',
        'source': 'STRING',
        'category': 'STRING',
        'level': 'STRING',
        'embedding': 'DOUBLE[384]',
        'version': 'STRING',
        'url': 'STRING'
    }
    
    for col_name, expected_type in expected_columns.items():
        assert col_name in columns, f"Column {col_name} not found in ReferenceEntity table"
        assert columns[col_name] == expected_type, f"Column {col_name} has type {columns[col_name]}, expected {expected_type}"
    
    # Insert a test record
    conn.execute("""
        CREATE (:ReferenceEntity {
            id: 'ASVS-V1.1.1',
            title: 'Secure Software Development Lifecycle',
            description: 'Verify the use of a secure software development lifecycle',
            source: 'OWASP ASVS 5.0',
            category: 'Architecture',
            level: 'L1',
            version: '5.0',
            url: 'https://owasp.org/asvs'
        })
    """)
    
    # Query the record back
    result = conn.execute("MATCH (r:ReferenceEntity {id: 'ASVS-V1.1.1'}) RETURN r.title")
    assert result.has_next()
    row = result.get_next()
    assert row[0] == 'Secure Software Development Lifecycle'


def test_implements_relationship(conn):
    """Test that IMPLEMENTS relationship can be created between RequirementEntity and ReferenceEntity."""
    # Create both node tables
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            source STRING,
            category STRING,
            level STRING,
            embedding DOUBLE[384],
            version STRING,
            url STRING
        )
    """)
    
    # Create the IMPLEMENTS relationship table
    conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM RequirementEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'full',
            notes STRING
        )
    """)
    
    # Create test nodes
    conn.execute("""
        CREATE (:RequirementEntity {
            id: 'REQ-001',
            title: 'User Authentication',
            description: 'System must authenticate users before granting access'
        })
    """)
    
    conn.execute("""
        CREATE (:ReferenceEntity {
            id: 'ASVS-V2.1.1',
            title: 'Authentication Verification',
            description: 'Verify that user authentication is properly implemented',
            source: 'OWASP ASVS 5.0',
            category: 'Authentication',
            level: 'L1',
            version: '5.0',
            url: 'https://owasp.org/asvs'
        })
    """)
    
    # Create relationship
    conn.execute("""
        MATCH (req:RequirementEntity {id: 'REQ-001'}), 
              (ref:ReferenceEntity {id: 'ASVS-V2.1.1'})
        CREATE (req)-[:IMPLEMENTS {
            implementation_type: 'full',
            notes: 'Implements OWASP ASVS authentication requirements'
        }]->(ref)
    """)
    
    # Query the relationship
    result = conn.execute("""
        MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
        WHERE req.id = 'REQ-001' AND ref.id = 'ASVS-V2.1.1'
        RETURN impl.implementation_type, impl.notes
    """)
    
    assert result.has_next()
    row = result.get_next()
    assert row[0] == 'full'
    assert row[1] == 'Implements OWASP ASVS authentication requirements'