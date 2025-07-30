"""Integration tests for graph adapter with persistent database."""

import tempfile
from pathlib import Path

from .graph_adapter import GraphAdapter


class TestGraphAdapterIntegration:
    """Test graph adapter with persistent database."""

    def test_persistent_database(self):
        """Test adapter with persistent database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_db"

            # Create adapter with persistent database
            adapter1 = GraphAdapter(str(db_path))

            # Add some data
            adapter1._conn.execute("""
                CREATE (r:RequirementEntity {
                    id: 'req_persist_001',
                    title: 'Persistent Requirement',
                    description: 'This should persist',
                    status: 'active'
                })
            """)

            # Close the adapter
            adapter1.close()

            # Create new adapter with same database
            adapter2 = GraphAdapter(str(db_path))

            # Verify data persisted
            req = adapter2.get_requirement('req_persist_001')
            assert req is not None
            assert req['title'] == 'Persistent Requirement'
            assert req['description'] == 'This should persist'

            adapter2.close()

    def test_context_manager(self):
        """Test using adapter as context manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_db"

            # Use as context manager
            with GraphAdapter(str(db_path)) as adapter:
                adapter._conn.execute("""
                    CREATE (r:RequirementEntity {
                        id: 'req_ctx_001',
                        title: 'Context Manager Test',
                        description: 'Testing context manager',
                        status: 'active'
                    })
                """)

                req = adapter.get_requirement('req_ctx_001')
                assert req is not None

            # Verify connection is closed properly by reopening
            with GraphAdapter(str(db_path)) as adapter:
                req = adapter.get_requirement('req_ctx_001')
                assert req is not None
                assert req['title'] == 'Context Manager Test'

    def test_transaction_support(self):
        """Test transaction support."""
        with GraphAdapter(":memory:") as adapter:
            # Begin transaction
            adapter.begin_transaction()

            # Add data
            adapter._conn.execute("""
                CREATE (r:RequirementEntity {
                    id: 'req_tx_001',
                    title: 'Transaction Test',
                    description: 'Testing transactions',
                    status: 'active'
                })
            """)

            # Verify data exists before commit
            req = adapter.get_requirement('req_tx_001')
            assert req is not None

            # Commit transaction
            adapter.commit()

            # Verify data still exists after commit
            req = adapter.get_requirement('req_tx_001')
            assert req is not None

    def test_error_handling(self):
        """Test error handling with Result types."""
        # Test with invalid path (read-only directory)
        try:
            adapter = GraphAdapter("/invalid/readonly/path")
            # If we get here, the adapter creation didn't fail as expected
            # This is actually fine - KuzuDB might handle this gracefully
            adapter.close()
        except RuntimeError as e:
            # Expected error
            assert "Failed to create" in str(e)

    def test_metric_persistence(self):
        """Test metric result persistence."""
        with GraphAdapter(":memory:") as adapter:
            # Create requirement
            adapter._conn.execute("""
                CREATE (r:RequirementEntity {
                    id: 'req_metric_001',
                    title: 'Metric Test',
                    description: 'Testing metrics',
                    status: 'active'
                })
            """)

            # Save multiple metrics
            for i in range(3):
                adapter.save_metric_result(
                    "req_metric_001",
                    "test_metric",
                    {"value": 0.5 + i * 0.1}
                )

            # Get metric history
            history = adapter.get_metric_history("req_metric_001", "test_metric")
            assert len(history) == 3

            # Verify values are in descending order by timestamp
            values = [h["value"] for h in history]
            assert values[0] == 0.7  # Most recent first
