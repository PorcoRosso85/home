"""Domain layer for org project - worker entities and business logic."""

from pathlib import Path
from typing import List, Optional, Union


class WorkerNotFoundError(Exception):
    """Exception raised when worker is not found."""
    pass


class WorkerValidationError(Exception):
    """Exception raised when worker validation fails."""
    pass


class Worker:
    """Represents a worker entity with path and state management."""
    
    def __init__(self, name: str, path: Union[str, Path], description: Optional[str] = None):
        """Initialize Worker with name and path.
        
        Args:
            name: Worker name
            path: Worker path (string or Path object)
            description: Optional worker description
            
        Raises:
            WorkerValidationError: If name or path is invalid
        """
        if not name:
            raise WorkerValidationError("Worker name is required")
        if not path:
            raise WorkerValidationError("Worker path is required")
            
        self.name = name
        self.path = Path(path)
        self.description = description
        self.is_active = False
    
    def exists(self) -> bool:
        """Check if worker path exists on filesystem.
        
        Returns:
            bool: True if path exists
        """
        return self.path.exists()
    
    def activate(self) -> None:
        """Activate this worker."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate this worker."""
        self.is_active = False


class WorkerRegistry:
    """Registry for managing workers."""
    
    def __init__(self):
        """Initialize empty worker registry."""
        self._workers: List[Worker] = []
    
    def register_worker(self, worker: Worker) -> None:
        """Register a worker in the registry.
        
        Args:
            worker: Worker to register
            
        Raises:
            WorkerValidationError: If worker with same name already exists
        """
        if self.worker_exists_by_name(worker.name):
            raise WorkerValidationError(f"Worker with name '{worker.name}' already exists")
        
        self._workers.append(worker)
    
    def get_all_workers(self) -> List[Worker]:
        """Get all registered workers.
        
        Returns:
            List[Worker]: All workers
        """
        return self._workers.copy()
    
    def get_worker_by_name(self, name: str) -> Worker:
        """Get worker by name.
        
        Args:
            name: Worker name to find
            
        Returns:
            Worker: The found worker
            
        Raises:
            WorkerNotFoundError: If worker not found
        """
        for worker in self._workers:
            if worker.name == name:
                return worker
        
        raise WorkerNotFoundError(f"Worker '{name}' not found")
    
    def worker_exists_by_name(self, name: str) -> bool:
        """Check if worker exists by name.
        
        Args:
            name: Worker name to check
            
        Returns:
            bool: True if worker exists
        """
        try:
            self.get_worker_by_name(name)
            return True
        except WorkerNotFoundError:
            return False
    
    def get_active_workers(self) -> List[Worker]:
        """Get all active workers that exist on filesystem.
        
        Returns:
            List[Worker]: Active workers with existing paths
        """
        return [worker for worker in self._workers 
                if worker.is_active and worker.exists()]
    
    def get_existing_workers(self) -> List[Worker]:
        """Get all workers whose paths exist on filesystem.
        
        Returns:
            List[Worker]: Workers with existing paths
        """
        return [worker for worker in self._workers if worker.exists()]
    
    def remove_worker(self, name: str) -> None:
        """Remove worker from registry.
        
        Args:
            name: Name of worker to remove
            
        Raises:
            WorkerNotFoundError: If worker not found
        """
        worker = self.get_worker_by_name(name)  # This will raise if not found
        self._workers.remove(worker)