from .base import Base, metadata
from .auth import User, Account, Profile, StudentProfile, Session
from .organization import Organization
from .course import (
    CourseContentKind,
    CourseRole,
    CourseFamily,
    Course,
    CourseContentType,
    CourseExecutionBackend,
    CourseGroup,
    CourseContent,
    CourseMember,
    CourseSubmissionGroup,
    CourseSubmissionGroupMember,
    CourseMemberComment
)
from .execution import ExecutionBackend
from .result import Result
from .role import Role, RoleClaim, UserRole
from .group import Group, GroupClaim, UserGroup
from .message import Message, MessageRead
from .example import Example, ExampleRepository, ExampleVersion, ExampleDependency
from .example_deployment import ExampleDeployment

# Import all models to ensure relationships are properly set up
from . import auth, organization, role, group, execution, course, result, message, example, example_deployment

__all__ = [
    'Base',
    'metadata',
    # Auth models
    'User',
    'Account',
    'Profile',
    'StudentProfile',
    'Session',
    # Organization
    'Organization',
    # Course models
    'CourseContentKind',
    'CourseRole',
    'CourseFamily',
    'Course',
    'CourseContentType',
    'CourseExecutionBackend',
    'CourseGroup',
    'CourseContent',
    'CourseMember',
    'CourseSubmissionGroup',
    'CourseSubmissionGroupMember',
    'CourseMemberComment',
    # Execution
    'ExecutionBackend',
    # Result
    'Result',
    # Role/Permission models
    'Role',
    'RoleClaim',
    'UserRole',
    # Group models
    'Group',
    'GroupClaim',
    'UserGroup',
    # Message models
    'Message',
    'MessageRead',
    # Example models
    'ExampleRepository',
    'Example',
    'ExampleVersion',
    'ExampleDependency',
    'ExampleDeployment'
]