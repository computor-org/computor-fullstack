"""
Example tasks - redirects to Temporal implementations.
"""

# Import all example workflows from temporal_examples
from .temporal_examples import (
    ExampleLongRunningWorkflow,
    ExampleDataProcessingWorkflow,
    ExampleErrorHandlingWorkflow,
)

# For backwards compatibility, create aliases with old names
ExampleLongRunningTask = ExampleLongRunningWorkflow
ExampleDataProcessingTask = ExampleDataProcessingWorkflow

__all__ = [
    'ExampleLongRunningWorkflow',
    'ExampleDataProcessingWorkflow', 
    'ExampleErrorHandlingWorkflow',
    'ExampleLongRunningTask',
    'ExampleDataProcessingTask',
]