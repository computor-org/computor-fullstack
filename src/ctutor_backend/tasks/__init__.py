"""
Task execution framework for long-running operations.

This module provides a Redis Queue (RQ) based task execution system
that handles operations exceeding FastAPI's request-response cycle.
"""

from .executor import TaskExecutor, get_task_executor
from .base import BaseTask, TaskStatus, TaskResult, TaskSubmission, TaskInfo
from .registry import task_registry, register_task

# Import examples to auto-register tasks
from . import examples

__all__ = [
    'TaskExecutor',
    'get_task_executor', 
    'BaseTask',
    'TaskStatus',
    'TaskResult',
    'TaskSubmission',
    'TaskInfo',
    'task_registry',
    'register_task'
]