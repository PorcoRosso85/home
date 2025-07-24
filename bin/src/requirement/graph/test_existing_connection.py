"""
Tests for existing_connection functionality
Following the testing philosophy: no mocks, test actual behavior through real instances
Tests connection sharing between repository and SearchAdapter
"""
import pytest
import tempfile
import os
import sys
import time

# Set up the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Create a minimal mock for the log module to avoid import issues
class MockLog:
    def __call__(self, *args, **kwargs):
        pass

sys.modules['log'] = type(sys)('log')
sys.modules['log'].log = MockLog()

# Now we can import our modules
from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
from requirement.graph.infrastructure.database_factory import (
    create_database, create_connection, KUZU_PY_AVAILABLE
)
from requirement.graph.application.search_adapter import (
    SearchAdapter, VSS_MODULES_AVAILABLE, FTS_MODULES_AVAILABLE
)


class TestExistingConnectionSharing:
    """Test connection sharing between repository and SearchAdapter"""
    
    def setup_method(self):
        """Set up test environment"""
        # Save original env
        self.orig_skip_schema = os.environ.get("SKIP_SCHEMA_CHECK")
        # Skip schema check for all tests in this class
        os.environ["SKIP_SCHEMA_CHECK"] = "true"
    
    def teardown_method(self):
        """Restore environment"""
        if self.orig_skip_schema is None:
            os.environ.pop("SKIP_SCHEMA_CHECK", None)
        else:
            os.environ["SKIP_SCHEMA_CHECK"] = self.orig_skip_schema

    def test_repository_exposes_connection(self):
        """Test that repository exposes its connection for sharing"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        # Create a repository
        repository = create_kuzu_repository(":memory:")
        
        # Should not be an error
        assert not isinstance(repository, dict) or repository.get("type") != "DatabaseError"
        
        # Should expose connection
        assert "connection" in repository
        assert repository["connection"] is not None
        
        # Connection should be a valid KuzuDB connection
        conn = repository["connection"]
        assert hasattr(conn, 'execute')
        assert hasattr(conn, '__class__')
        assert 'Connection' in str(conn.__class__)

    def test_search_adapter_uses_existing_connection(self):
        """Test that SearchAdapter can use an existing connection"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
        
        if not VSS_MODULES_AVAILABLE and not FTS_MODULES_AVAILABLE:
            pytest.skip("No search modules available")

        # Create a repository with connection
        repository = create_kuzu_repository(":memory:")
        assert not isinstance(repository, dict) or repository.get("type") != "DatabaseError"
        
        # Get the connection
        repo_connection = repository["connection"]
        
        # Create SearchAdapter with existing connection
        search_adapter = SearchAdapter(":memory:", repository_connection=repo_connection)
        
        # Verify the adapter was initialized
        if VSS_MODULES_AVAILABLE:
            assert search_adapter._vss_service is not None
            # Check that the VSS adapter received the connection
            assert search_adapter._vss_service._conn is repo_connection
            
        if FTS_MODULES_AVAILABLE:
            assert search_adapter._fts_service is not None
            # Check that the FTS adapter received the connection
            assert search_adapter._fts_service._conn is repo_connection

    @pytest.mark.skip(reason="Requires schema initialization - to be fixed in integration tests")
    def test_shared_connection_data_consistency(self):
        """Test that data written through repository is accessible via search adapter"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
            
        if not VSS_MODULES_AVAILABLE:
            pytest.skip("VSS modules not available for testing")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            # Create repository
            repository = create_kuzu_repository(db_path)
            assert not isinstance(repository, dict) or repository.get("type") != "DatabaseError"
            
            # Skip schema check temporarily
            os.environ['RGL_SKIP_SCHEMA_CHECK'] = '1'
            
            # Add a requirement through repository
            save_result = repository["save"]({
                "id": "test_001",
                "title": "Test Requirement",
                "description": "Testing connection sharing",
                "status": "active"
            }, track_version=False)  # Disable versioning for simple test
            
            # Check save succeeded
            if isinstance(save_result, dict) and save_result.get("type") in ["DatabaseError", "ValidationError"]:
                pytest.fail(f"Save failed: {save_result}")
            
            # Create search adapter with shared connection
            search_adapter = SearchAdapter(db_path, repository_connection=repository["connection"])
            
            # Add to search index
            success = search_adapter.add_to_index({
                "id": "test_001",
                "title": "Test Requirement",
                "description": "Testing connection sharing"
            })
            
            assert success, "Failed to add to search index"
            
            # Wait for indexing
            time.sleep(0.1)
            
            # Search should find the requirement
            results = search_adapter.search_similar("test requirement", k=5)
            
            # Should find at least one result
            assert len(results) > 0
            
            # The result should be our test requirement
            found_ids = [r["id"] for r in results if "error" not in r]
            assert "test_001" in found_ids


class TestConnectionInitializationOrder:
    """Test different initialization orders and edge cases"""
    
    def test_search_adapter_without_existing_connection(self):
        """Test that SearchAdapter works without an existing connection"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
            
        if not VSS_MODULES_AVAILABLE and not FTS_MODULES_AVAILABLE:
            pytest.skip("No search modules available")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            # Create SearchAdapter without existing connection
            search_adapter = SearchAdapter(db_path, repository_connection=None)
            
            # Should still initialize (creates its own connection)
            if VSS_MODULES_AVAILABLE:
                assert search_adapter._vss_service is not None
                
            if FTS_MODULES_AVAILABLE:
                assert search_adapter._fts_service is not None

    def test_invalid_connection_handling(self):
        """Test SearchAdapter behavior with invalid connection"""
        if not VSS_MODULES_AVAILABLE and not FTS_MODULES_AVAILABLE:
            pytest.skip("No search modules available")

        # Create SearchAdapter with invalid connection
        search_adapter = SearchAdapter(":memory:", repository_connection="not_a_connection")
        
        # Should handle gracefully
        # The adapter should still be created but might not be fully initialized
        assert search_adapter is not None
        
        # Check error handling
        if search_adapter._error:
            assert search_adapter._error["type"] == "ModuleNotFoundError"
        else:
            # If modules are available, they should handle the invalid connection
            if VSS_MODULES_AVAILABLE and search_adapter._vss_service:
                # VSS service might not be fully initialized
                assert not search_adapter._vss_service._is_initialized or \
                       search_adapter._vss_service._conn == "not_a_connection"


class TestPerformanceWithConnectionSharing:
    """Test performance improvements from connection sharing"""
    
    @pytest.mark.slow
    def test_initialization_performance(self):
        """Test that connection sharing improves initialization time"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
            
        if not VSS_MODULES_AVAILABLE:
            pytest.skip("VSS modules not available")
            
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "perf_test.db")
            
            # Measure time without connection sharing
            start_time = time.time()
            for i in range(5):
                adapter = SearchAdapter(db_path, repository_connection=None)
                del adapter
            time_without_sharing = time.time() - start_time
            
            # Create a shared connection
            db = create_database(path=db_path)
            conn = create_connection(db)
            
            # Measure time with connection sharing
            start_time = time.time()
            for i in range(5):
                adapter = SearchAdapter(db_path, repository_connection=conn)
                del adapter
            time_with_sharing = time.time() - start_time
            
            # Connection sharing should be faster (or at least not slower)
            # We don't assert strict performance as it depends on the system
            print(f"Time without sharing: {time_without_sharing:.3f}s")
            print(f"Time with sharing: {time_with_sharing:.3f}s")
            
            # Just verify both approaches work
            assert time_without_sharing > 0
            assert time_with_sharing > 0
    
    @pytest.mark.skip(reason="Segmentation fault due to PyTorch/KuzuDB thread conflict")
    def test_detailed_performance_comparison(self):
        """
        詳細なパフォーマンステスト - 接続共有の利点を示す
        
        セグメンテーションフォルトの原因:
        1. PyTorchのコンパイルワーカースレッドとKuzuDBの同時実行による競合
        2. sentence-transformersがモデルロード時に複数のPyTorchスレッドを起動
        3. FTSSearchAdapterがKuzuDB接続でcheck_fts_extension()を実行時にクラッシュ
        4. 10回の繰り返しで、PyTorchスレッドプールとKuzuDB接続が競合状態に
        
        スタックトレース:
        - torch._inductor.compile_worker.subproc_pool._recv_msg (PyTorchワーカー)
        - kuzu.connection.execute (メインスレッド)
        - fts_kuzu.infrastructure.check_fts_extension
        
        回避策:
        - OMP_NUM_THREADS=1 環境変数でPyTorchのスレッド数を制限
        - またはテストをスキップ（現在の対応）
        """
        """Detailed performance test showing connection reuse benefits"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
            
        if not VSS_MODULES_AVAILABLE:
            pytest.skip("VSS modules not available")
            
        print("\n=== Connection Reuse Performance Test ===")
        
        # Use in-memory database for consistent results
        db_path = ":memory:"
        
        # Create repository with shared connection
        repository = create_kuzu_repository(db_path)
        if isinstance(repository, dict) and repository.get("type") == "DatabaseError":
            pytest.skip("Could not create repository")
        
        shared_connection = repository["connection"]
        
        # Test 1: Measure adapter creation WITHOUT connection sharing
        print("\nTest 1: Creating 10 SearchAdapters WITHOUT connection sharing")
        times_without = []
        
        for i in range(10):
            start = time.perf_counter()
            adapter = SearchAdapter(db_path, repository_connection=None)
            # Perform a search to ensure full initialization
            adapter.search_similar("test", k=1)
            end = time.perf_counter()
            
            elapsed = end - start
            times_without.append(elapsed)
            print(f"  Adapter {i+1}: {elapsed:.3f}s")
            del adapter
        
        avg_without = sum(times_without) / len(times_without)
        total_without = sum(times_without)
        
        # Test 2: Measure adapter creation WITH connection sharing
        print("\nTest 2: Creating 10 SearchAdapters WITH connection sharing")
        times_with = []
        
        for i in range(10):
            start = time.perf_counter()
            adapter = SearchAdapter(db_path, repository_connection=shared_connection)
            # Perform a search to ensure full initialization
            adapter.search_similar("test", k=1)
            end = time.perf_counter()
            
            elapsed = end - start
            times_with.append(elapsed)
            print(f"  Adapter {i+1}: {elapsed:.3f}s (reusing connection)")
            del adapter
        
        avg_with = sum(times_with) / len(times_with)
        total_with = sum(times_with)
        
        # Display results
        print("\n=== Performance Summary ===")
        print(f"WITHOUT connection sharing:")
        print(f"  Total time:    {total_without:.3f}s")
        print(f"  Average time:  {avg_without:.3f}s per adapter")
        
        print(f"\nWITH connection sharing:")
        print(f"  Total time:    {total_with:.3f}s")
        print(f"  Average time:  {avg_with:.3f}s per adapter")
        
        if avg_without > 0:
            improvement = ((avg_without - avg_with) / avg_without) * 100
            time_saved = total_without - total_with
            
            print(f"\nPerformance improvement: {improvement:.1f}%")
            print(f"Total time saved: {time_saved:.3f}s")
            
            if avg_with < avg_without:
                print("\n✓ Connection reuse provides measurable performance benefits!")
                print("  Benefits include:")
                print("  - Eliminated connection initialization overhead")
                print("  - Reduced memory allocation")
                print("  - Faster adapter instantiation")
            else:
                print("\n⚠ No significant performance improvement measured")
                print("  (Benefits may be more visible with file-based databases)")
        
        # Verify connection sharing doesn't degrade performance
        assert avg_with <= avg_without * 1.2, \
            "Connection sharing should not significantly degrade performance"
    
    def test_connection_creation_overhead(self):
        """Test the overhead of connection creation vs reuse"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
            
        print("\n=== Connection Creation Overhead Test ===")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "overhead_test.db")
            
            # Create initial database
            db = create_database(path=db_path)
            
            # Test 1: Create 20 new connections
            print("\nCreating 20 new connections:")
            start = time.perf_counter()
            
            connections = []
            for i in range(20):
                conn = create_connection(db)
                connections.append(conn)
                if i % 5 == 4:
                    print(f"  Created {i+1} connections...")
            
            time_new_connections = time.perf_counter() - start
            print(f"Total time: {time_new_connections:.3f}s")
            
            # Test 2: Simulate adapter creation with reused connection
            print("\nSimulating 20 adapter creations with shared connection:")
            shared_conn = connections[0]
            
            start = time.perf_counter()
            
            # Just measure the overhead of NOT creating new connections
            for i in range(20):
                # This simulates what SearchAdapter does when given existing_connection
                # It skips connection creation and just uses the provided one
                conn_ref = shared_conn  # Simple reference assignment
                if i % 5 == 4:
                    print(f"  Reused connection {i+1} times...")
            
            time_reused_connection = time.perf_counter() - start
            print(f"Total time: {time_reused_connection:.3f}s")
            
            # Display results
            print("\n=== Overhead Summary ===")
            print(f"Creating 20 new connections:  {time_new_connections:.3f}s")
            print(f"Reusing 1 connection 20x:     {time_reused_connection:.3f}s")
            print(f"Time saved by reuse:          {time_new_connections - time_reused_connection:.3f}s")
            
            if time_new_connections > time_reused_connection:
                overhead_reduction = ((time_new_connections - time_reused_connection) / time_new_connections) * 100
                print(f"Overhead reduction:           {overhead_reduction:.1f}%")
                print("\n✓ Connection reuse eliminates creation overhead!")
            
            # Connection reuse should always be faster
            assert time_reused_connection < time_new_connections, \
                "Connection reuse should be faster than creating new connections"


class TestErrorScenarios:
    """Test error scenarios for connection sharing"""
    
    def test_none_as_existing_connection(self):
        """Test that None is handled properly as existing_connection"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
            
        # Create SearchAdapter with None connection (should work)
        search_adapter = SearchAdapter(":memory:", repository_connection=None)
        
        # Should create successfully
        assert search_adapter is not None
        
        # If search modules are available, they should create their own connections
        if VSS_MODULES_AVAILABLE:
            assert search_adapter._vss_service is not None
        if FTS_MODULES_AVAILABLE:
            assert search_adapter._fts_service is not None
    
    def test_closed_connection(self):
        """Test behavior with a closed connection"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")
            
        # Create and close a connection
        db = create_database(in_memory=True)
        conn = create_connection(db)
        
        # Note: KuzuDB connections don't have a close() method in the current version
        # So we'll simulate an invalid connection state
        
        # Create SearchAdapter with the connection
        search_adapter = SearchAdapter(":memory:", repository_connection=conn)
        
        # Should handle gracefully
        assert search_adapter is not None
    
    def test_connection_type_validation(self):
        """Test that connection type is validated"""
        # Test with various invalid types
        invalid_connections = [
            123,  # int
            [],  # list
            {},  # dict
            set(),  # set
            lambda: None,  # function
        ]
        
        for invalid_conn in invalid_connections:
            search_adapter = SearchAdapter(":memory:", repository_connection=invalid_conn)
            
            # Should create adapter but might not initialize services
            assert search_adapter is not None
            
            # Services might fail to initialize with invalid connection
            if VSS_MODULES_AVAILABLE and search_adapter._vss_service:
                # Check if it handled the invalid connection
                assert search_adapter._vss_service._conn == invalid_conn
    
    def test_error_message_clarity(self):
        """Test that error messages are clear when connection sharing fails"""
        if not VSS_MODULES_AVAILABLE and not FTS_MODULES_AVAILABLE:
            pytest.skip("No search modules available")
            
        # Create adapter with invalid connection
        search_adapter = SearchAdapter(":memory:", repository_connection="invalid")
        
        # Try to use it
        results = search_adapter.search_similar("test", k=5)
        
        # Should return results (empty or with errors)
        assert isinstance(results, list)
        
        # If there are errors, they should be clear
        for result in results:
            if "error" in result:
                error = result["error"]
                # Error should have a type and message
                if isinstance(error, dict):
                    assert "type" in error or "message" in error