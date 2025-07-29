"""
Tests for the minimal guardrail enforcer.
"""
import pytest
import tempfile
import shutil
from guardrail.minimal_enforcer import (
    detect_security_category,
    check_reference_compliance,
    enforce_basic_guardrails,
    create_exception_request
)
import kuzu


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for the database"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_conn(temp_db_dir):
    """Create a test database connection with schema"""
    db = kuzu.Database(str(temp_db_dir) + "/test.db")
    conn = kuzu.Connection(db)
    
    # Create RequirementEntity table
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            description STRING,
            status STRING DEFAULT 'pending',
            security_category STRING
        )
    """)
    
    # Create ReferenceEntity table
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
    
    # Create ExceptionRequest table
    conn.execute("""
        CREATE NODE TABLE ExceptionRequest (
            id STRING PRIMARY KEY,
            reason STRING,
            status STRING DEFAULT 'pending',
            requested_at STRING,
            approved_by STRING,
            approved_at STRING
        )
    """)
    
    # Create IMPLEMENTS relationship
    conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM RequirementEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'full',
            notes STRING
        )
    """)
    
    # Create HAS_EXCEPTION relationship
    conn.execute("""
        CREATE REL TABLE HAS_EXCEPTION (
            FROM RequirementEntity TO ExceptionRequest,
            exception_type STRING DEFAULT 'deviation',
            mitigation STRING
        )
    """)
    
    # Insert some test reference entities
    test_refs = [
        {
            "id": "ASVS-V2.1.1",
            "title": "Password Requirements",
            "description": "Verify that user set passwords are at least 12 characters in length.",
            "source": "OWASP ASVS 5.0",
            "category": "Authentication",
            "level": "L1"
        },
        {
            "id": "ASVS-V4.1.1",
            "title": "Access Control",
            "description": "Verify that the application enforces access control rules.",
            "source": "OWASP ASVS 5.0",
            "category": "Access Control",
            "level": "L1"
        },
        {
            "id": "NIST-AC-2",
            "title": "Account Management",
            "description": "The organization manages information system accounts.",
            "source": "NIST 800-53",
            "category": "Access Control",
            "level": "Moderate"
        },
        {
            "id": "NIST-IA-5",
            "title": "Authenticator Management",
            "description": "The organization manages information system authenticators.",
            "source": "NIST 800-53",
            "category": "Identification and Authentication",
            "level": "Moderate"
        }
    ]
    
    for ref in test_refs:
        # Add dummy embedding
        ref["embedding"] = [0.0] * 384
        ref["version"] = "5.0"
        ref["url"] = "https://example.com"
        
        conn.execute("""
            CREATE (r:ReferenceEntity {
                id: $id,
                title: $title,
                description: $description,
                source: $source,
                category: $category,
                level: $level,
                embedding: $embedding,
                version: $version,
                url: $url
            })
        """, ref)
    
    yield conn
    conn.close()


def test_detect_security_category():
    """Test security category detection"""
    # Authentication category
    assert detect_security_category("User login with password") == "authentication"
    assert detect_security_category("Implement OAuth authentication") == "authentication"
    
    # Authorization category
    assert detect_security_category("Check user permissions before access") == "authorization"
    assert detect_security_category("Implement role-based access control") == "authorization"
    
    # Session management
    assert detect_security_category("Generate secure session tokens") == "session_management"
    assert detect_security_category("Implement JWT token validation") == "session_management"
    
    # Cryptography
    assert detect_security_category("Encrypt sensitive data at rest") == "cryptography"
    assert detect_security_category("Use TLS for all communications") == "cryptography"
    
    # Input validation
    assert detect_security_category("Validate and sanitize user input") == "input_validation"
    assert detect_security_category("Prevent SQL injection attacks") == "input_validation"
    
    # General security
    assert detect_security_category("Implement security monitoring") == "general_security"
    
    # Non-security
    assert detect_security_category("Display user profile page") is None
    assert detect_security_category("Calculate order total") is None


def test_check_reference_compliance():
    """Test reference compliance checking"""
    # Authentication - requires ASVS-V2 or NIST-IA
    is_compliant, error = check_reference_compliance(
        "authentication",
        ["ASVS-V2.1.1"]
    )
    assert is_compliant is True
    assert error is None
    
    is_compliant, error = check_reference_compliance(
        "authentication",
        ["NIST-IA-5"]
    )
    assert is_compliant is True
    assert error is None
    
    is_compliant, error = check_reference_compliance(
        "authentication",
        ["ASVS-V4.1.1"]  # Wrong category
    )
    assert is_compliant is False
    assert "ASVS V2" in error
    
    # Authorization - requires ASVS-V4 or NIST-AC
    is_compliant, error = check_reference_compliance(
        "authorization",
        ["ASVS-V4.1.1"]
    )
    assert is_compliant is True
    
    is_compliant, error = check_reference_compliance(
        "authorization",
        ["NIST-AC-2"]
    )
    assert is_compliant is True
    
    # No references provided
    is_compliant, error = check_reference_compliance(
        "authentication",
        []
    )
    assert is_compliant is False
    assert error is not None


def test_enforce_basic_guardrails_non_security(test_conn):
    """Test enforcement for non-security requirements"""
    result = enforce_basic_guardrails(
        test_conn,
        "REQ-001",
        "Display user profile information",
        []
    )
    
    assert result["success"] is True
    assert result["requirement_created"] is True
    assert result["references_linked"] == []
    assert result["error"] is None
    
    # Verify requirement was created
    query_result = test_conn.execute("""
        MATCH (r:RequirementEntity {id: 'REQ-001'})
        RETURN r.description, r.status
    """)
    assert query_result.has_next()
    row = query_result.get_next()
    assert row[0] == "Display user profile information"
    assert row[1] == "pending"


def test_enforce_basic_guardrails_security_compliant(test_conn):
    """Test enforcement for compliant security requirements"""
    result = enforce_basic_guardrails(
        test_conn,
        "REQ-002",
        "Implement user authentication with secure password storage",
        ["ASVS-V2.1.1"]
    )
    
    assert result["success"] is True
    assert result["requirement_created"] is True
    assert "ASVS-V2.1.1" in result["references_linked"]
    assert result["error"] is None
    
    # Verify requirement and relationship were created
    query_result = test_conn.execute("""
        MATCH (r:RequirementEntity {id: 'REQ-002'})-[:IMPLEMENTS]->(ref:ReferenceEntity)
        RETURN r.security_category, ref.id
    """)
    assert query_result.has_next()
    row = query_result.get_next()
    assert row[0] == "authentication"
    assert row[1] == "ASVS-V2.1.1"


def test_enforce_basic_guardrails_security_non_compliant(test_conn):
    """Test enforcement for non-compliant security requirements"""
    result = enforce_basic_guardrails(
        test_conn,
        "REQ-003",
        "Implement user authentication system",
        ["ASVS-V4.1.1"]  # Wrong reference for authentication
    )
    
    assert result["success"] is False
    assert result["requirement_created"] is False
    assert result["references_linked"] == []
    assert "ASVS V2" in result["error"]
    
    # Verify requirement was not created
    query_result = test_conn.execute("""
        MATCH (r:RequirementEntity {id: 'REQ-003'})
        RETURN r
    """)
    assert not query_result.has_next()


def test_enforce_basic_guardrails_multiple_references(test_conn):
    """Test enforcement with multiple references"""
    result = enforce_basic_guardrails(
        test_conn,
        "REQ-004",
        "Implement comprehensive access control system",
        ["ASVS-V4.1.1", "NIST-AC-2", "ASVS-V2.1.1"]  # Mix of correct and incorrect
    )
    
    assert result["success"] is True
    assert result["requirement_created"] is True
    assert "ASVS-V4.1.1" in result["references_linked"]
    assert "NIST-AC-2" in result["references_linked"]
    # ASVS-V2.1.1 might not be linked as it's not the right category


def test_enforce_basic_guardrails_transaction_rollback(test_conn):
    """Test that transactions are rolled back on error"""
    # Create a requirement that will fail during relationship creation
    result = enforce_basic_guardrails(
        test_conn,
        "REQ-005",
        "Implement secure authentication",
        ["NONEXISTENT-REF"]  # Reference that doesn't exist
    )
    
    assert result["success"] is False
    assert "Failed to link any references" in result["error"]
    
    # Verify requirement was not created (rolled back)
    query_result = test_conn.execute("""
        MATCH (r:RequirementEntity {id: 'REQ-005'})
        RETURN r
    """)
    assert not query_result.has_next()


def test_create_exception_request(test_conn):
    """Test exception request creation"""
    # First create a requirement
    test_conn.execute("""
        CREATE (r:RequirementEntity {
            id: 'REQ-006',
            description: 'Legacy system integration',
            status: 'pending'
        })
    """)
    
    result = create_exception_request(
        test_conn,
        "REQ-006",
        "Legacy system cannot support modern authentication standards",
        "Additional network segmentation and monitoring"
    )
    
    assert result["success"] is True
    assert result["exception_id"] is not None
    assert result["status"] == "pending"
    assert result["error"] is None
    
    # Verify exception and relationship were created
    query_result = test_conn.execute("""
        MATCH (r:RequirementEntity {id: 'REQ-006'})-[he:HAS_EXCEPTION]->(e:ExceptionRequest)
        RETURN e.id, e.reason, e.status, he.mitigation
    """)
    assert query_result.has_next()
    row = query_result.get_next()
    assert row[0] == result["exception_id"]
    assert "Legacy system" in row[1]
    assert row[2] == "pending"
    assert "network segmentation" in row[3]


def test_create_exception_request_no_mitigation(test_conn):
    """Test exception request creation without mitigation"""
    # First create a requirement
    test_conn.execute("""
        CREATE (r:RequirementEntity {
            id: 'REQ-007',
            description: 'Temporary workaround',
            status: 'pending'
        })
    """)
    
    result = create_exception_request(
        test_conn,
        "REQ-007",
        "Temporary implementation pending full solution"
    )
    
    assert result["success"] is True
    assert result["exception_id"] is not None
    
    # Verify default mitigation was set
    query_result = test_conn.execute("""
        MATCH (r:RequirementEntity {id: 'REQ-007'})-[he:HAS_EXCEPTION]->(e:ExceptionRequest)
        RETURN he.mitigation
    """)
    assert query_result.has_next()
    row = query_result.get_next()
    assert row[0] == "No specific mitigation provided"