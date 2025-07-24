"""
Task executor - redirects to Temporal implementation.
"""

# Import everything from temporal executor
from .temporal_executor import (
    TemporalTaskExecutor as TaskExecutor,
    get_task_executor
)

# Export for backwards compatibility
__all__ = ['TaskExecutor', 'get_task_executor']