"""
Student test execution tasks - redirects to Temporal implementations.
"""

# Import workflows from temporal implementation
from .temporal_student_testing import (
    StudentTestingWorkflow,
    SubmissionProcessingWorkflow
)

# For backwards compatibility
StudentTestExecutionTask = StudentTestingWorkflow

__all__ = [
    'StudentTestingWorkflow',
    'SubmissionProcessingWorkflow',
    'StudentTestExecutionTask'
]