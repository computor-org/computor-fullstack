"""
Task registry for managing and discovering task implementations.
"""

from typing import Dict, Type
from .base import BaseTask


class TaskRegistry:
    """Registry for managing task implementations."""
    
    def __init__(self):
        self._tasks: Dict[str, Type[BaseTask]] = {}
    
    def register(self, task_class: Type[BaseTask]) -> Type[BaseTask]:
        """
        Register a task implementation.
        
        Args:
            task_class: Task class to register
            
        Returns:
            The registered task class (for decorator usage)
        """
        task_instance = task_class()
        task_name = task_instance.name
        
        if task_name in self._tasks:
            raise ValueError(f"Task '{task_name}' is already registered")
        
        self._tasks[task_name] = task_class
        return task_class
    
    def get_task(self, task_name: str) -> Type[BaseTask]:
        """
        Get a task implementation by name.
        
        Args:
            task_name: Name of the task
            
        Returns:
            Task class
            
        Raises:
            KeyError: If task is not registered
        """
        if task_name not in self._tasks:
            raise KeyError(f"Task '{task_name}' is not registered")
        
        return self._tasks[task_name]
    
    def list_tasks(self) -> Dict[str, Type[BaseTask]]:
        """
        Get all registered tasks.
        
        Returns:
            Dictionary mapping task names to task classes
        """
        return self._tasks.copy()
    
    def is_registered(self, task_name: str) -> bool:
        """
        Check if a task is registered.
        
        Args:
            task_name: Name of the task
            
        Returns:
            True if task is registered, False otherwise
        """
        return task_name in self._tasks


# Global task registry instance
task_registry = TaskRegistry()


def register_task(task_class: Type[BaseTask]) -> Type[BaseTask]:
    """
    Decorator for registering task implementations.
    
    Usage:
        @register_task
        class MyTask(BaseTask):
            name = "my_task"
            
            async def execute(self, **kwargs):
                # Implementation here
                pass
    
    Args:
        task_class: Task class to register
        
    Returns:
        The registered task class
    """
    return task_registry.register(task_class)