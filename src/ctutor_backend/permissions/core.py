"""
Refactored permissions module using the handler registry pattern.
This module provides a cleaner, more maintainable approach to permission management.
"""

from typing import Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from ctutor_backend.api.exceptions import ForbiddenException
from ctutor_backend.permissions.handlers import permission_registry
from ctutor_backend.permissions.handlers_impl import (
    UserPermissionHandler,
    AccountPermissionHandler,
    ProfilePermissionHandler,
    CoursePermissionHandler,
    OrganizationPermissionHandler,
    CourseFamilyPermissionHandler,
    CourseContentTypePermissionHandler,
    CourseContentPermissionHandler,
    CourseMemberPermissionHandler,
    ReadOnlyPermissionHandler
)

# Import refactored Principal and related classes
from ctutor_backend.permissions.principal import (
    Principal,
    Claims,
    build_claims,
    course_role_hierarchy
)

# Import models for registration
from ctutor_backend.model.auth import User, Account, Profile, StudentProfile, Session as UserSession
from ctutor_backend.model.course import (
    Course, CourseFamily, CourseMember, CourseContent,
    CourseContentType, CourseContentKind, CourseRole, CourseGroup,
    CourseExecutionBackend, CourseMemberComment,
    CourseSubmissionGroup, CourseSubmissionGroupMember
)
from ctutor_backend.model.organization import Organization
from ctutor_backend.model.result import Result
from ctutor_backend.model.execution import ExecutionBackend
from ctutor_backend.model.role import Role, RoleClaim, UserRole
from ctutor_backend.model.group import Group, GroupClaim, UserGroup
from ctutor_backend.model.example import Example, ExampleRepository, ExampleVersion, ExampleDependency


def initialize_permission_handlers():
    """Initialize and register all permission handlers"""
    
    # User-related entities
    permission_registry.register(User, UserPermissionHandler(User))
    permission_registry.register(Account, AccountPermissionHandler(Account))
    permission_registry.register(Profile, ProfilePermissionHandler(Profile))
    permission_registry.register(StudentProfile, ProfilePermissionHandler(StudentProfile))
    permission_registry.register(UserSession, ProfilePermissionHandler(UserSession))
    
    # Organization and Course hierarchy
    permission_registry.register(Organization, OrganizationPermissionHandler(Organization))
    permission_registry.register(CourseFamily, CourseFamilyPermissionHandler(CourseFamily))
    permission_registry.register(Course, CoursePermissionHandler(Course))
    
    # Course-related entities
    permission_registry.register(CourseContentType, CourseContentTypePermissionHandler(CourseContentType))
    permission_registry.register(CourseContent, CourseContentPermissionHandler(CourseContent))
    permission_registry.register(CourseMember, CourseMemberPermissionHandler(CourseMember))
    permission_registry.register(CourseGroup, CourseMemberPermissionHandler(CourseGroup))
    permission_registry.register(CourseExecutionBackend, CourseContentPermissionHandler(CourseExecutionBackend))
    permission_registry.register(CourseMemberComment, CourseMemberPermissionHandler(CourseMemberComment))
    permission_registry.register(CourseSubmissionGroup, CourseMemberPermissionHandler(CourseSubmissionGroup))
    permission_registry.register(CourseSubmissionGroupMember, CourseMemberPermissionHandler(CourseSubmissionGroupMember))
    
    # Read-only entities
    permission_registry.register(CourseRole, ReadOnlyPermissionHandler(CourseRole))
    permission_registry.register(CourseContentKind, ReadOnlyPermissionHandler(CourseContentKind))
    
    # Example entities (read-only for most users)
    permission_registry.register(Example, ReadOnlyPermissionHandler(Example))
    permission_registry.register(ExampleRepository, ReadOnlyPermissionHandler(ExampleRepository))
    permission_registry.register(ExampleVersion, ReadOnlyPermissionHandler(ExampleVersion))
    permission_registry.register(ExampleDependency, ReadOnlyPermissionHandler(ExampleDependency))
    
    # System entities - admin only by default
    permission_registry.register(Role, UserPermissionHandler(Role))  # Can be customized
    permission_registry.register(RoleClaim, UserPermissionHandler(RoleClaim))
    permission_registry.register(UserRole, UserPermissionHandler(UserRole))
    permission_registry.register(Group, UserPermissionHandler(Group))
    permission_registry.register(GroupClaim, UserPermissionHandler(GroupClaim))
    permission_registry.register(UserGroup, UserPermissionHandler(UserGroup))
    permission_registry.register(ExecutionBackend, ReadOnlyPermissionHandler(ExecutionBackend))
    permission_registry.register(Result, CourseMemberPermissionHandler(Result))


def check_admin(permissions: Principal) -> bool:
    """Check if principal has admin privileges"""
    return permissions.is_admin


def check_permissions(permissions: Principal, entity: Any, action: str, db: Session):
    """
    Main entry point for permission checking.
    Uses the registry pattern to delegate to appropriate handlers.
    """
    return permission_registry.check_permissions(permissions, entity, action, db)


def get_permitted_course_ids(permissions: Principal, minimum_role: str, db: Session) -> List[str]:
    """Get list of course IDs where user has at least the minimum role"""
    if permissions.is_admin:
        # Admin has access to all courses
        return db.query(Course.id).all()
    
    return list(permissions.get_courses_with_role(minimum_role))


def check_course_permissions(permissions: Principal, entity: Any, course_role_id: str, db: Session):
    """Check permissions for course-related entities"""
    from ctutor_backend.permissions.query_builders import CoursePermissionQueryBuilder
    
    if permissions.is_admin:
        return db.query(entity)
    
    # Filter by course membership
    return CoursePermissionQueryBuilder.filter_by_course_membership(
        db.query(entity), entity, permissions.user_id, course_role_id, db
    )


# Database helper functions (keep existing implementations)
def db_get_claims(user_id: str, db: Session) -> List[tuple]:
    """Get claims for a user from database"""
    from ctutor_backend.model.role import RoleClaim
    from ctutor_backend.model.auth import User
    
    values = (
        db.query(RoleClaim.claim_type, RoleClaim.claim_value)
        .select_from(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(RoleClaim, RoleClaim.role_id == Role.id)
        .filter(User.id == user_id)
        .distinct(RoleClaim.claim_type, RoleClaim.claim_value)
        .all()
    )
    
    # Convert to list and add default permissions
    values = list(values)
    
    # Add default permissions for read-only entities
    values.extend([
        ("permissions", f"{CourseContentKind.__tablename__}:get"),
        ("permissions", f"{CourseContentKind.__tablename__}:list"),
        ("permissions", f"{CourseRole.__tablename__}:get"),
        ("permissions", f"{CourseRole.__tablename__}:list"),
    ])
    
    return values


def db_get_course_claims(user_id: str, db: Session) -> List[tuple]: #TODO: PERMISSIONS
    """Get course-specific claims for a user"""
    from ctutor_backend.model.auth import User
    
    course_members = (
        db.query(
            CourseMember.course_id,
            CourseMember.course_role_id
        )
        .select_from(User)
        .join(CourseMember, CourseMember.user_id == User.id)
        .filter(User.id == user_id)
        .all()
    )
    
    course_claims = []
    is_lecturer = False
    
    for course_id, course_role_id in course_members:
        # Store course role as a claim
        course_claims.append(("permissions", f"course:{course_role_id}:{course_id}"))
        
        # Check if user is a lecturer in any course
        if course_role_id in course_role_hierarchy.get_allowed_roles("_lecturer"):
            is_lecturer = True
    
    # Add general permissions for lecturers
    if is_lecturer:
        course_claims.extend([
            ("permissions", f"{CourseContent.__tablename__}:create"),
            ("permissions", f"{CourseContent.__tablename__}:update"),
            ("permissions", f"{Example.__tablename__}:upload"),
            ("permissions", f"{Example.__tablename__}:download"),
        ])
    
    return course_claims


def db_get_roles_claims(user_id: str, db: Session) -> tuple:
    """Get roles and claims for a user"""
    from ctutor_backend.model.auth import User
    
    values = (
        db.query(RoleClaim.role_id, RoleClaim.claim_type, RoleClaim.claim_value)
        .select_from(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(RoleClaim, RoleClaim.role_id == Role.id)
        .filter(User.id == user_id)
        .all()
    )
    
    role_ids = list({row.role_id for row in values})
    claim_values = [(row.claim_type, row.claim_value) for row in values]
    
    return role_ids, claim_values


def db_apply_roles(role_id: str, claims: List[str], db: Session):
    """Apply claims to a role in the database"""
    from sqlalchemy.dialects.postgresql import insert
    
    stmt = insert(RoleClaim).values([
        {"role_id": role_id, "claim_type": ct, "claim_value": cv}
        for ct, cv in claims
    ])
    
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["role_id", "claim_type", "claim_value"]
    )
    db.execute(stmt)
    db.commit()


# Initialize handlers on module import
initialize_permission_handlers()