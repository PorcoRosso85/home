"""
ReferenceEntity Query and Search Tests

Tests for searching and querying ReferenceEntity data
using the reference_repository.py
"""
import pytest
import kuzu
import os
from reference_repository import create_reference_repository


class TestReferenceEntityQuery:
    """Test query and search functionality for ReferenceEntity"""

    @pytest.fixture
    def repo_with_data(self):
        """Create repository with schema and sample data"""
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        
        # Create schema matching reference_repository.py
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
        
        # Insert sample ASVS data using repository
        sample_data = [
            # Authentication requirements
            {
                "uri": "asvs:4.0.3/v2.1.1",
                "title": "Password Length Requirement",
                "description": "Verify that user set passwords are at least 12 characters in length",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "authentication", "section": "V2.1.1"}'
            },
            {
                "uri": "asvs:4.0.3/v2.1.2",
                "title": "Password Spaces Allowed",
                "description": "Verify that passwords can contain spaces",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "authentication", "section": "V2.1.2"}'
            },
            {
                "uri": "asvs:4.0.3/v2.1.3",
                "title": "Password No Truncation",
                "description": "Verify that password truncation is not performed",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "authentication", "section": "V2.1.3"}'
            },
            {
                "uri": "asvs:4.0.3/v2.2.1",
                "title": "Anti-automation Controls",
                "description": "Verify that anti-automation controls are effective",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "authentication", "section": "V2.2.1"}'
            },
            # Session management requirements
            {
                "uri": "asvs:4.0.3/v3.1.1",
                "title": "Session Token Protection",
                "description": "Verify the application never reveals session tokens in URL parameters",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "session", "section": "V3.1.1"}'
            },
            {
                "uri": "asvs:4.0.3/v3.2.1",
                "title": "Session Token Generation",
                "description": "Verify the application generates a new session token on user authentication",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "session", "section": "V3.2.1"}'
            },
            # Access control requirements
            {
                "uri": "asvs:4.0.3/v4.1.1",
                "title": "Access Control Enforcement",
                "description": "Verify that the application enforces access control rules",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "access_control", "section": "V4.1.1"}'
            },
            {
                "uri": "asvs:4.0.3/v4.1.2",
                "title": "Access Control Attributes Protection",
                "description": "Verify that all user and data attributes used by access controls are protected",
                "entity_type": "security_requirement",
                "metadata": '{"level": 2, "category": "access_control", "section": "V4.1.2"}'
            },
            # Cryptography requirements
            {
                "uri": "asvs:4.0.3/v6.2.1",
                "title": "Cryptographic Module Failure",
                "description": "Verify that all cryptographic modules fail securely",
                "entity_type": "security_requirement",
                "metadata": '{"level": 1, "category": "cryptography", "section": "V6.2.1"}'
            },
            {
                "uri": "asvs:4.0.3/v6.2.2",
                "title": "Industry Proven Cryptographic Modules",
                "description": "Verify that industry proven cryptographic modules are used",
                "entity_type": "security_requirement",
                "metadata": '{"level": 2, "category": "cryptography", "section": "V6.2.2"}'
            }
        ]
        
        for ref in sample_data:
            repo["save"](ref)
        
        yield repo
        conn.close()

    def test_search_by_category(self, repo_with_data):
        """カテゴリによる検索が正しく動作すること"""
        # Search for authentication requirements using execute
        result = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            WHERE r.metadata CONTAINS '"category": "authentication"'
            RETURN r.uri, r.metadata, r.description
            ORDER BY r.uri
        """)
        
        assert result["status"] == "success"
        assert len(result["data"]) == 4
        # Check all are authentication category by parsing metadata
        for row in result["data"]:
            assert 'authentication' in row[1]  # metadata contains authentication

    def test_search_by_level(self, repo_with_data):
        """レベルによる検索が正しく動作すること"""
        # Search for Level 1 requirements
        result = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            WHERE r.metadata CONTAINS '"level": 1'
            RETURN r.uri, r.metadata
            ORDER BY r.uri
        """)
        
        assert result["status"] == "success"
        assert len(result["data"]) == 8  # Most are Level 1
        
        # Search for Level 2 requirements
        result_l2 = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            WHERE r.metadata CONTAINS '"level": 2'
            RETURN r.uri, r.metadata
            ORDER BY r.uri
        """)
        
        assert result_l2["status"] == "success"
        assert len(result_l2["data"]) == 2  # Only 2 Level 2 requirements

    def test_search_by_standard_and_version(self, repo_with_data):
        """標準とバージョンによる検索が正しく動作すること"""
        # Search for ASVS 4.0.3 by URI pattern
        result = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            WHERE r.uri STARTS WITH 'asvs:4.0.3/'
            RETURN count(r) as count
        """)
        
        assert result["status"] == "success"
        assert result["data"][0][0] == 10  # All our sample data

    def test_search_by_keyword_in_description(self, repo_with_data):
        """説明文のキーワード検索が正しく動作すること"""
        # Use repository search function
        results = repo_with_data["search"]("password")
        
        assert len(results) == 3
        assert all('password' in ref["description"].lower() for ref in results)

    def test_category_statistics(self, repo_with_data):
        """カテゴリ別の統計情報取得が正しく動作すること"""
        # Get all references and count by category
        all_refs = repo_with_data["find_all"]()
        
        # Parse metadata to count categories
        category_counts = {}
        for ref in all_refs:
            # Simple parsing of JSON metadata
            if '"category": "authentication"' in ref["metadata"]:
                category_counts['authentication'] = category_counts.get('authentication', 0) + 1
            elif '"category": "access_control"' in ref["metadata"]:
                category_counts['access_control'] = category_counts.get('access_control', 0) + 1
            elif '"category": "cryptography"' in ref["metadata"]:
                category_counts['cryptography'] = category_counts.get('cryptography', 0) + 1
            elif '"category": "session"' in ref["metadata"]:
                category_counts['session'] = category_counts.get('session', 0) + 1
        
        assert category_counts['authentication'] == 4
        assert category_counts['access_control'] == 2
        assert category_counts['cryptography'] == 2
        assert category_counts['session'] == 2

    def test_section_prefix_search(self, repo_with_data):
        """セクション番号のプレフィックス検索が正しく動作すること"""
        # Search for all V2 requirements by metadata
        result = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            WHERE r.metadata CONTAINS '"section": "V2.'
            RETURN r.uri, r.metadata
            ORDER BY r.uri
        """)
        
        assert result["status"] == "success"
        assert len(result["data"]) == 4
        # Verify all are authentication category
        for row in result["data"]:
            assert '"category": "authentication"' in row[1]

    def test_combined_filter_search(self, repo_with_data):
        """複合条件での検索が正しく動作すること"""
        # Search for Level 1 authentication requirements
        result = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            WHERE r.metadata CONTAINS '"category": "authentication"' 
              AND r.metadata CONTAINS '"level": 1'
            RETURN r.uri, r.metadata
            ORDER BY r.uri
        """)
        
        assert result["status"] == "success"
        assert len(result["data"]) == 4

    def test_get_all_categories(self, repo_with_data):
        """全カテゴリの一覧取得が正しく動作すること"""
        # Get all references and extract unique categories
        all_refs = repo_with_data["find_all"]()
        
        categories = set()
        for ref in all_refs:
            if '"category": "authentication"' in ref["metadata"]:
                categories.add('authentication')
            elif '"category": "access_control"' in ref["metadata"]:
                categories.add('access_control')
            elif '"category": "cryptography"' in ref["metadata"]:
                categories.add('cryptography')
            elif '"category": "session"' in ref["metadata"]:
                categories.add('session')
        
        expected_categories = {'access_control', 'authentication', 'cryptography', 'session'}
        assert categories == expected_categories

    def test_paginated_search(self, repo_with_data):
        """ページネーション付き検索が正しく動作すること"""
        # Get first page (5 items)
        page1 = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            RETURN r.uri
            ORDER BY r.uri
            LIMIT 5
        """)
        
        assert page1["status"] == "success"
        assert len(page1["data"]) == 5
        
        # Get second page (skip 5, take 5)
        page2 = repo_with_data["execute"]("""
            MATCH (r:ReferenceEntity)
            RETURN r.uri
            ORDER BY r.uri
            SKIP 5
            LIMIT 5
        """)
        
        assert page2["status"] == "success"
        assert len(page2["data"]) == 5
        
        # Verify no overlap
        page1_uris = {row[0] for row in page1["data"]}
        page2_uris = {row[0] for row in page2["data"]}
        assert len(page1_uris.intersection(page2_uris)) == 0