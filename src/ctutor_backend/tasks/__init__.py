"""
Task execution framework for long-running operations.

This module provides a Temporal-based task execution system
that handles operations exceeding FastAPI's request-response cycle.
"""

from .executor import TaskExecutor, get_task_executor
from .base import BaseTask, TaskStatus, TaskResult, TaskSubmission, TaskInfo
from .registry import task_registry, register_task
from .temporal_client import get_temporal_client, close_temporal_client
from .temporal_base import BaseWorkflow, BaseActivity, WorkflowResult, WorkflowProgress

# Import examples to auto-register tasks
from . import examples

# Import hierarchy management tasks to auto-register
from . import hierarchy_management

__all__ = [
    'TaskExecutor',
    'get_task_executor', 
    'BaseTask',
    'TaskStatus',
    'TaskResult',
    'TaskSubmission',
    'TaskInfo',
    'task_registry',
    'register_task',
    'get_temporal_client',
    'close_temporal_client',
    'BaseWorkflow',
    'BaseActivity',
    'WorkflowResult',
    'WorkflowProgress'
]