"""Tests for graph adapter."""

import tempfile
from pathlib import Path

from .graph_adapter import GraphAdapter


class TestGraphAdapter:
    """Test graph database adapter."""

    def setup_method(self):
        """Set up test fixture with in-memory database."""
        # Use in-memory database for tests
        self.adapter = GraphAdapter(":memory:")
        self._setup_test_data()

    def teardown_method(self):
        """Clean up resources."""
        # Connection cleanup happens automatically
        pass

    def _setup_test_data(self):
        """Set up test data in the database."""
        # Create test requirements
        self.adapter._conn.execute("""
            CREATE (r:RequirementEntity {
                id: 'req_001',
                title: 'User Login',
                description: 'Users should be able to log in',
                status: 'active'
            })
        """)

        self.adapter._conn.execute("""
            CREATE (r:RequirementEntity {
                id: 'req_002',
                title: 'User Logout',
                description: 'Users should be able to log out',
                status: 'active'
            })
        """)

        # Create test specifications
        self.adapter._conn.execute("""
            CREATE (t:TestSpecification {
                id: 'test_001',
                test_type: 'unit'
            })
        """)

        self.adapter._conn.execute("""
            CREATE (t:TestSpecification {
                id: 'test_002',
                test_type: 'e2e'
            })
        """)

        # Create relationships
        self.adapter._conn.execute("""
            MATCH (r:RequirementEntity {id: 'req_001'})
            MATCH (t:TestSpecification {id: 'test_001'})
            CREATE (r)-[:VERIFIED_BY]->(t)
        """)

        self.adapter._conn.execute("""
            MATCH (r:RequirementEntity {id: 'req_001'})
            MATCH (t:TestSpecification {id: 'test_002'})
            CREATE (r)-[:VERIFIED_BY]->(t)
        """)

    def test_initialization(self):
        """Test adapter initialization."""
        assert self.adapter._db is not None
        assert self.adapter._conn is not None

        # Verify schema exists by querying
        result = self.adapter._conn.execute("""
            MATCH (r:RequirementEntity) RETURN count(r) as count
        """)

        assert result.has_next()
        row = result.get_next()
        assert row[0] >= 2  # We created 2 requirements in setup

    def test_get_requirement(self):
        """Test retrieving requirements."""
        # Get existing requirement
        req = self.adapter.get_requirement("req_001")
        assert req is not None
        assert req["id"] == "req_001"
        assert req["title"] == "User Login"
        assert req["description"] == "Users should be able to log in"
        assert req["status"] == "active"

        # Get non-existent requirement
        assert self.adapter.get_requirement("req_999") is None

    def test_get_tests_for_requirement(self):
        """Test retrieving tests for a requirement."""
        # Get tests for req_001 (should have 2)
        tests = self.adapter.get_tests_for_requirement("req_001")
        assert len(tests) == 2

        test_ids = [t["id"] for t in tests]
        assert "test_001" in test_ids
        assert "test_002" in test_ids

        # Check test types
        test_types = [t["test_type"] for t in tests]
        assert "unit" in test_types
        assert "e2e" in test_types

        # Get tests for req_002 (should have 0)
        tests = self.adapter.get_tests_for_requirement("req_002")
        assert len(tests) == 0

    def test_save_metric_result(self):
        """Test saving metric results."""
        result = {
            "value": 0.85,
            "details": {"coverage": 10, "total": 12}
        }

        # Save metric
        self.adapter.save_metric_result("req_001", "existence", result)

        # Verify by querying
        history = self.adapter.get_metric_history("req_001", "existence")
        assert len(history) > 0
        assert history[0]["value"] == 0.85

    def test_export_to_cypher(self):
        """Test exporting to Cypher format."""
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cypher', delete=False) as f:
            output_file = f.name

        try:
            self.adapter.export_to_cypher(output_file)

            # Verify export
            output_path = Path(output_file)
            assert output_path.exists()

            content = output_path.read_text()
            # Check for requirements
            assert "CREATE (r:RequirementEntity {id: 'req_001'" in content
            assert "CREATE (r:RequirementEntity {id: 'req_002'" in content

            # Check for tests
            assert "CREATE (t:TestSpecification {id: 'test_001'" in content
            assert "CREATE (t:TestSpecification {id: 'test_002'" in content

            # Check for relationships
            assert "CREATE (r)-[:VERIFIED_BY]->(t);" in content

        finally:
            # Clean up
            Path(output_file).unlink(missing_ok=True)

    def test_execute_cypher(self):
        """Test executing arbitrary Cypher queries."""
        # Execute a count query
        results = self.adapter.execute_cypher(
            "MATCH (r:RequirementEntity) RETURN count(r) as count"
        )

        assert len(results) == 1
        assert results[0]["col0"] >= 2

        # Execute with parameters
        results = self.adapter.execute_cypher(
            "MATCH (r:RequirementEntity {id: $id}) RETURN r.title as title",
            {"id": "req_001"}
        )

        assert len(results) == 1
        assert results[0]["col0"] == "User Login"

    def test_get_dependencies(self):
        """Test getting test dependencies."""
        # Create dependency relationship
        self.adapter._conn.execute("""
            CREATE (t:TestSpecification {id: 'test_003', test_type: 'integration'})
        """)

        self.adapter._conn.execute("""
            MATCH (t1:TestSpecification {id: 'test_001'})
            MATCH (t2:TestSpecification {id: 'test_003'})
            CREATE (t1)-[:DEPENDS_ON]->(t2)
        """)

        # Get dependencies
        deps = self.adapter.get_dependencies("test_001")
        assert "test_001" in deps
        assert "test_003" in deps["test_001"]

        # Test with no dependencies
        deps = self.adapter.get_dependencies("test_002")
        assert deps == {"test_002": []}
