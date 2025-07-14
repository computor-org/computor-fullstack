"""
Base classes and interfaces for task execution framework.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TaskStatus(str, Enum):
    """Task execution status enumeration."""
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class TaskResult(BaseModel):
    """Task execution result container."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(use_enum_values=True)


class BaseTask(ABC):
    """
    Abstract base class for all task implementations.
    
    Tasks should inherit from this class and implement the execute method.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name identifier for this task type."""
        pass
    
    @property
    def timeout(self) -> Optional[int]:
        """Task timeout in seconds. None for no timeout."""
        return 3600  # 1 hour default
    
    @property
    def retry_limit(self) -> int:
        """Maximum number of retry attempts."""
        return 3
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the task with given parameters.
        
        Args:
            **kwargs: Task parameters
            
        Returns:
            Task execution result
            
        Raises:
            Exception: If task execution fails
        """
        pass
    
    async def on_success(self, result: Any, **kwargs) -> None:
        """
        Hook called when task completes successfully.
        
        Args:
            result: Task execution result
            **kwargs: Original task parameters
        """
        pass
    
    async def on_failure(self, error: Exception, **kwargs) -> None:
        """
        Hook called when task fails.
        
        Args:
            error: Exception that caused the failure
            **kwargs: Original task parameters
        """
        pass
    
    async def update_progress(self, percentage: int, metadata: Dict[str, Any] = None) -> None:
        """
        Update task progress.
        
        This method should be called during task execution to report progress.
        The implementation depends on how the task is being executed (Celery, etc.).
        
        Args:
            percentage: Progress percentage (0-100)
            metadata: Additional progress metadata
        """
        # Default implementation does nothing
        # This will be overridden by the Celery wrapper in executor.py
        pass


class TaskSubmission(BaseModel):
    """Task submission request."""
    task_name: str
    parameters: Dict[str, Any] = {}
    priority: int = 0  # Higher values = higher priority
    delay: Optional[int] = None  # Delay in seconds before execution
    
    
class TaskInfo(BaseModel):
    """Task information for status queries."""
    task_id: str
    task_name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)