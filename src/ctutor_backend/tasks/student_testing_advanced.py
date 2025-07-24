"""
Advanced student testing tasks - redirects to Temporal implementations.
"""

# Import everything from temporal student testing
from .temporal_student_testing import *

# For backwards compatibility
StudentTestingTask = StudentTestingWorkflow

__all__ = [
    'StudentTestingWorkflow',
    'SubmissionProcessingWorkflow',
    'StudentTestingTask'
]