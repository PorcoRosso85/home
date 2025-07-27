#!/usr/bin/env python3
"""E2E test for URI POC workflow."""

import tempfile
from pathlib import Path

import kuzu
import pytest

from enforced_workflow import EnforcedWorkflow
from reference_repository import ReferenceRepository


class TestE2EWorkflow:
    """End-to-end workflow tests."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_complete_workflow(self, temp_db):
        """Test complete URI workflow from creation to validation."""
        # Initialize database
        db = kuzu.Database(str(temp_db))
        conn = db.get_connection()
        
        # Create schema
        conn.execute("CREATE NODE TABLE ISOStandard(id STRING, PRIMARY KEY(id))")
        conn.execute("CREATE NODE TABLE URI(uri STRING, PRIMARY KEY(uri))")
        conn.execute("CREATE REL TABLE HAS_CLAUSE(FROM ISOStandard TO URI)")
        
        # Initialize repositories
        ref_repo = ReferenceRepository(conn)
        workflow = EnforcedWorkflow(conn)
        
        # Add standard
        conn.execute("CREATE (:ISOStandard {id: 'ISO-27001'})")
        
        # Create URI with reference
        uri = "uri:iso:27001:a.5.1"
        result = workflow.create_uri_with_reference(uri, "ISO-27001", "Test URI")
        
        # Verify creation
        assert result["success"] is True
        assert result["uri"] == uri
        
        # Query verification
        query = "MATCH (u:URI {uri: $uri}) RETURN u"
        result = conn.execute(query, {"uri": uri})
        assert result.has_next()