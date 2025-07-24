"""
Hierarchy management tasks - redirects to Temporal implementations.
"""

# Import workflows from temporal implementation
from .temporal_hierarchy_management import (
    CreateOrganizationWorkflow,
    CreateCourseFamilyWorkflow,
    CreateCourseWorkflow,
    create_organization_activity,
    create_course_family_activity,
    create_course_activity
)

# For backwards compatibility
create_organization_task = CreateOrganizationWorkflow
create_course_family_task = CreateCourseFamilyWorkflow
create_course_task = CreateCourseWorkflow

__all__ = [
    'CreateOrganizationWorkflow',
    'CreateCourseFamilyWorkflow',
    'CreateCourseWorkflow',
    'create_organization_task',
    'create_course_family_task',
    'create_course_task'
]