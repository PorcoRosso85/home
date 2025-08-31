"""Test domain logic for org project - worker existence checking.

Following TDD principles: these tests are written first to describe desired behavior.
They should fail initially and guide implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from domain import WorkerRegistry, Worker, WorkerNotFoundError, WorkerValidationError


class TestWorker:
    """Test suite for Worker entity."""

    def test_worker_creation_with_valid_data(self):
        """Test that Worker can be created with valid data."""
        # This test should fail initially - Worker doesn't exist yet
        worker = Worker(
            name="test_worker",
            path="/home/nixos/bin/src/test",
            description="Test worker for testing"
        )
        
        assert worker.name == "test_worker"
        assert worker.path == Path("/home/nixos/bin/src/test")
        assert worker.description == "Test worker for testing"
        assert worker.is_active is False  # Default state

    def test_worker_creation_requires_name(self):
        """Test that Worker creation requires a name."""
        with pytest.raises(WorkerValidationError, match="Worker name is required"):
            Worker(name="", path="/some/path")
        
        with pytest.raises(WorkerValidationError, match="Worker name is required"):
            Worker(name=None, path="/some/path")

    def test_worker_creation_requires_path(self):
        """Test that Worker creation requires a valid path."""
        with pytest.raises(WorkerValidationError, match="Worker path is required"):
            Worker(name="test", path="")
        
        with pytest.raises(WorkerValidationError, match="Worker path is required"):
            Worker(name="test", path=None)

    def test_worker_path_is_converted_to_pathlib_path(self):
        """Test that worker path is converted to pathlib.Path."""
        worker = Worker(name="test", path="/home/test")
        assert isinstance(worker.path, Path)
        assert str(worker.path) == "/home/test"

    @patch('domain.Path.exists')
    def test_worker_exists_returns_true_when_path_exists(self, mock_exists):
        """Test that exists() returns True when worker path exists."""
        mock_exists.return_value = True
        
        worker = Worker(name="test", path="/existing/path")
        assert worker.exists() is True
        mock_exists.assert_called_once()

    @patch('domain.Path.exists')
    def test_worker_exists_returns_false_when_path_missing(self, mock_exists):
        """Test that exists() returns False when worker path doesn't exist."""
        mock_exists.return_value = False
        
        worker = Worker(name="test", path="/missing/path")
        assert worker.exists() is False
        mock_exists.assert_called_once()

    def test_worker_activate_changes_state(self):
        """Test that activate() changes worker state to active."""
        worker = Worker(name="test", path="/some/path")
        assert worker.is_active is False
        
        worker.activate()
        assert worker.is_active is True

    def test_worker_deactivate_changes_state(self):
        """Test that deactivate() changes worker state to inactive."""
        worker = Worker(name="test", path="/some/path")
        worker.activate()  # First activate
        assert worker.is_active is True
        
        worker.deactivate()
        assert worker.is_active is False


class TestWorkerRegistry:
    """Test suite for WorkerRegistry."""

    def test_worker_registry_initialization(self):
        """Test that WorkerRegistry can be initialized."""
        # This test should fail initially - WorkerRegistry doesn't exist yet
        registry = WorkerRegistry()
        assert registry is not None
        assert len(registry.get_all_workers()) == 0

    def test_register_worker_adds_worker_to_registry(self):
        """Test that register_worker adds a worker to the registry."""
        registry = WorkerRegistry()
        worker = Worker(name="test_worker", path="/test/path")
        
        registry.register_worker(worker)
        
        workers = registry.get_all_workers()
        assert len(workers) == 1
        assert workers[0] == worker

    def test_register_worker_prevents_duplicate_names(self):
        """Test that register_worker prevents duplicate worker names."""
        registry = WorkerRegistry()
        worker1 = Worker(name="duplicate", path="/path1")
        worker2 = Worker(name="duplicate", path="/path2")
        
        registry.register_worker(worker1)
        
        with pytest.raises(WorkerValidationError, match="Worker with name 'duplicate' already exists"):
            registry.register_worker(worker2)

    def test_get_worker_by_name_returns_existing_worker(self):
        """Test that get_worker_by_name returns the correct worker."""
        registry = WorkerRegistry()
        worker = Worker(name="findable", path="/find/me")
        registry.register_worker(worker)
        
        found_worker = registry.get_worker_by_name("findable")
        assert found_worker == worker

    def test_get_worker_by_name_raises_error_for_missing_worker(self):
        """Test that get_worker_by_name raises error for non-existent worker."""
        registry = WorkerRegistry()
        
        with pytest.raises(WorkerNotFoundError, match="Worker 'missing' not found"):
            registry.get_worker_by_name("missing")

    def test_worker_exists_by_name_returns_true_for_existing(self):
        """Test that worker_exists_by_name returns True for existing worker."""
        registry = WorkerRegistry()
        worker = Worker(name="exists", path="/exists")
        registry.register_worker(worker)
        
        assert registry.worker_exists_by_name("exists") is True

    def test_worker_exists_by_name_returns_false_for_missing(self):
        """Test that worker_exists_by_name returns False for missing worker."""
        registry = WorkerRegistry()
        
        assert registry.worker_exists_by_name("missing") is False

    @patch('domain.Path.exists')
    def test_get_active_workers_returns_only_active_existing_workers(self, mock_exists):
        """Test that get_active_workers returns only active workers that exist."""
        mock_exists.return_value = True
        
        registry = WorkerRegistry()
        
        worker1 = Worker(name="active1", path="/path1")
        worker2 = Worker(name="active2", path="/path2")
        worker3 = Worker(name="inactive", path="/path3")
        
        worker1.activate()
        worker2.activate()
        # worker3 stays inactive
        
        registry.register_worker(worker1)
        registry.register_worker(worker2)
        registry.register_worker(worker3)
        
        active_workers = registry.get_active_workers()
        assert len(active_workers) == 2
        assert worker1 in active_workers
        assert worker2 in active_workers
        assert worker3 not in active_workers

    @patch('domain.Path.exists')
    def test_get_existing_workers_returns_only_workers_with_existing_paths(self, mock_exists):
        """Test that get_existing_workers returns only workers whose paths exist."""
        def mock_exists_side_effect(path_instance):
            return str(path_instance) in ["/existing1", "/existing2"]
        
        mock_exists.side_effect = mock_exists_side_effect
        
        registry = WorkerRegistry()
        
        worker1 = Worker(name="existing1", path="/existing1")
        worker2 = Worker(name="existing2", path="/existing2") 
        worker3 = Worker(name="missing", path="/missing")
        
        registry.register_worker(worker1)
        registry.register_worker(worker2)
        registry.register_worker(worker3)
        
        existing_workers = registry.get_existing_workers()
        assert len(existing_workers) == 2
        assert worker1 in existing_workers
        assert worker2 in existing_workers
        assert worker3 not in existing_workers

    def test_remove_worker_removes_from_registry(self):
        """Test that remove_worker removes worker from registry."""
        registry = WorkerRegistry()
        worker = Worker(name="removeme", path="/remove")
        registry.register_worker(worker)
        
        assert registry.worker_exists_by_name("removeme") is True
        
        registry.remove_worker("removeme")
        
        assert registry.worker_exists_by_name("removeme") is False

    def test_remove_worker_raises_error_for_missing_worker(self):
        """Test that remove_worker raises error for non-existent worker."""
        registry = WorkerRegistry()
        
        with pytest.raises(WorkerNotFoundError, match="Worker 'missing' not found"):
            registry.remove_worker("missing")


class TestWorkerExceptions:
    """Test suite for worker-related exceptions."""

    def test_worker_not_found_error_is_exception(self):
        """Test that WorkerNotFoundError is a proper exception."""
        error = WorkerNotFoundError("Test not found")
        assert isinstance(error, Exception)
        assert str(error) == "Test not found"

    def test_worker_validation_error_is_exception(self):
        """Test that WorkerValidationError is a proper exception."""
        error = WorkerValidationError("Test validation error")
        assert isinstance(error, Exception)
        assert str(error) == "Test validation error"