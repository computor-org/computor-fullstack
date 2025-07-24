"""
System-level tasks - redirects to Temporal implementations.
"""

# Import workflows from temporal implementation
from .temporal_system import (
    ReleaseStudentsWorkflow,
    ReleaseCourseWorkflow,
    release_students_activity,
    release_course_activity
)

# For backwards compatibility
release_student_task = ReleaseStudentsWorkflow
release_course_task = ReleaseCourseWorkflow

__all__ = [
    'ReleaseStudentsWorkflow',
    'ReleaseCourseWorkflow',
    'release_student_task',
    'release_course_task'
]