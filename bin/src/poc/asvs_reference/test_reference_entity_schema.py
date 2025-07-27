"""
ReferenceEntity Schema Creation and CRUD Tests

Tests for ReferenceEntity node table creation and basic CRUD operations
using the reference_repository.py
"""
import pytest
import kuzu
import tempfile
import shutil
import os
from reference_repository import create_reference_repository


class TestReferenceEntitySchema:
    """Test ReferenceEntity schema creation and structure"""

    @pytest.fixture
    def db_path(self):
        """Create temporary database directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def db_with_schema(self):
        """Create in-memory database with schema"""
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        
        # Apply the new schema that matches reference_repository.py
        conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """)
        
        conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM ReferenceEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'implements',
            confidence DOUBLE DEFAULT 1.0,
            created_at TIMESTAMP
        )
        """)
        
        yield db
        conn.close()

    def test_create_reference_entity_table(self):
        """ReferenceEntityテーブルが正しく作成されること"""
        # Test that repository creation fails without schema
        repo = create_reference_repository(":memory:")
        assert isinstance(repo, dict)
        assert repo.get("type") == "DatabaseError"
        assert "SCHEMA_NOT_INITIALIZED" in str(repo)

    def test_repository_with_schema(self, db_with_schema):
        """スキーマ初期化後のリポジトリ作成が正しく動作すること"""
        # Skip schema check since we manually created it
        os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
        repo = create_reference_repository(existing_db=db_with_schema)
        del os.environ["URI_SKIP_SCHEMA_CHECK"]
        
        # Verify repository has all expected functions
        assert "save" in repo
        assert "find" in repo
        assert "find_all" in repo
        assert "add_implementation" in repo
        assert "find_implementations" in repo
        assert "search" in repo
        assert "execute" in repo
        assert "db" in repo
        assert "connection" in repo

    def test_create_implements_relationship(self, db_with_schema):
        """IMPLEMENTS関係が正しく作成されること"""
        os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
        repo = create_reference_repository(existing_db=db_with_schema)
        del os.environ["URI_SKIP_SCHEMA_CHECK"]
        
        # Create two reference entities
        spec_ref = {
            "uri": "iso:9001:2015/clause/4.1",
            "title": "Understanding the organization and its context",
            "entity_type": "standard_clause"
        }
        
        impl_ref = {
            "uri": "company:acme/procedure/context-analysis",
            "title": "Context Analysis Procedure",
            "entity_type": "procedure"
        }
        
        # Save references
        repo["save"](spec_ref)
        repo["save"](impl_ref)
        
        # Create IMPLEMENTS relationship
        result = repo["add_implementation"](
            impl_ref["uri"],
            spec_ref["uri"],
            "procedural",
            0.95
        )
        
        assert result.get("success") == True
        assert result.get("source") == impl_ref["uri"]
        assert result.get("target") == spec_ref["uri"]
        assert result.get("relationship") == "IMPLEMENTS"


class TestReferenceEntityCRUD:
    """Test CRUD operations on ReferenceEntity using repository"""

    @pytest.fixture
    def repository(self):
        """Create repository with in-memory database"""
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        
        # Create schema
        conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """)
        
        conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM ReferenceEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'implements',
            confidence DOUBLE DEFAULT 1.0,
            created_at TIMESTAMP
        )
        """)
        
        os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
        repo = create_reference_repository(existing_db=db)
        del os.environ["URI_SKIP_SCHEMA_CHECK"]
        
        yield repo
        conn.close()

    def test_insert_reference_entity(self, repository):
        """ReferenceEntityの挿入が正しく動作すること"""
        # Insert ASVS reference with new schema
        reference = {
            "uri": "asvs:4.0.3/v2.1.1",
            "title": "Password Length Requirement",
            "description": "Verify that user set passwords are at least 12 characters in length",
            "entity_type": "security_requirement",
            "metadata": '{"level": 1, "category": "authentication"}'
        }
        
        result = repository["save"](reference)
        
        # Should not be an error
        assert not isinstance(result, dict) or result.get("type") not in ["DatabaseError", "ValidationError"]
        assert result == reference
        
        # Verify insertion using find
        found = repository["find"]("asvs:4.0.3/v2.1.1")
        assert found["uri"] == reference["uri"]
        assert found["title"] == reference["title"]
        assert found["entity_type"] == reference["entity_type"]

    def test_bulk_insert_reference_entities(self, repository):
        """複数のReferenceEntityの一括挿入が正しく動作すること"""
        # Insert multiple ASVS references
        references = [
            {
                "uri": "asvs:4.0.3/v2.1.1",
                "title": "Password Length Requirement",
                "description": "Verify that user set passwords are at least 12 characters in length",
                "entity_type": "security_requirement"
            },
            {
                "uri": "asvs:4.0.3/v2.1.2",
                "title": "Password Spaces Allowed",
                "description": "Verify that passwords can contain spaces",
                "entity_type": "security_requirement"
            },
            {
                "uri": "asvs:4.0.3/v2.1.3",
                "title": "Password No Truncation",
                "description": "Verify that password truncation is not performed",
                "entity_type": "security_requirement"
            }
        ]
        
        for ref in references:
            result = repository["save"](ref)
            assert result == ref
        
        # Verify all inserted
        all_refs = repository["find_all"]()
        assert len(all_refs) == 3
        
        # Verify URIs
        uris = {ref["uri"] for ref in all_refs}
        expected_uris = {ref["uri"] for ref in references}
        assert uris == expected_uris

    def test_update_reference_entity(self, repository):
        """ReferenceEntityの更新が正しく動作すること"""
        # Insert initial data
        reference = {
            "uri": "asvs:4.0.3/v2.1.1",
            "title": "Old Title",
            "description": "Old description",
            "entity_type": "security_requirement"
        }
        repository["save"](reference)
        
        # Update the reference
        reference["title"] = "Password Length Requirement (Updated)"
        reference["description"] = "Verify that user set passwords are at least 12 characters in length (Updated)"
        
        result = repository["save"](reference)
        assert result == reference
        
        # Verify update
        found = repository["find"]("asvs:4.0.3/v2.1.1")
        assert "Updated" in found["title"]
        assert "Updated" in found["description"]

    def test_delete_reference_entity(self, repository):
        """ReferenceEntityの削除が正しく動作すること（execute経由）"""
        # Insert data
        reference = {
            "uri": "asvs:4.0.3/v2.1.1",
            "title": "Test Reference",
            "description": "Test description",
            "entity_type": "security_requirement"
        }
        repository["save"](reference)
        
        # Delete using execute
        result = repository["execute"](
            "MATCH (r:ReferenceEntity {uri: $uri}) DELETE r",
            {"uri": "asvs:4.0.3/v2.1.1"}
        )
        assert result["status"] == "success"
        
        # Verify deletion
        not_found = repository["find"]("asvs:4.0.3/v2.1.1")
        assert not_found["type"] == "NotFoundError"

    def test_unique_constraint_on_uri(self, repository):
        """URIの一意制約が機能すること"""
        # Insert first entity
        reference = {
            "uri": "asvs:4.0.3/v2.1.1",
            "title": "First Entity",
            "description": "First entity",
            "entity_type": "security_requirement"
        }
        repository["save"](reference)
        
        # Update with same URI should work (it's an update, not a new insert)
        reference["title"] = "Updated Title"
        result = repository["save"](reference)
        assert result == reference
        
        # Verify only one entity exists
        all_refs = repository["find_all"]()
        assert len(all_refs) == 1
        assert all_refs[0]["title"] == "Updated Title"