"""
Task execution framework for long-running operations.

This module provides a Temporal-based task execution system
that handles operations exceeding FastAPI's request-response cycle.
"""

from .temporal_executor import TemporalTaskExecutor as TaskExecutor, get_task_executor
from .base import BaseTask, TaskStatus, TaskResult, TaskSubmission, TaskInfo
from .registry import task_registry, register_task
from .temporal_client import (
    get_temporal_client, 
    close_temporal_client,
    get_task_queue_name,
    DEFAULT_TASK_QUEUE
)
from .temporal_base import BaseWorkflow, BaseActivity, WorkflowResult, WorkflowProgress

# Note: Temporal workflow modules are imported lazily to avoid circular dependencies
# They will be imported when the worker starts or when specific tasks are needed
# The modules that would normally be imported here are:
# - temporal_examples
# - temporal_hierarchy_management
# - temporal_system
# - temporal_student_testing
# - temporal_student_template_v2
# - temporal_student_repository

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
    'get_task_queue_name',
    'DEFAULT_TASK_QUEUE',
    'BaseWorkflow',
    'BaseActivity',
    'WorkflowResult',
    'WorkflowProgress'
]