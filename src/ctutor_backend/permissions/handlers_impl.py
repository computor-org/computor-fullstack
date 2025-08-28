from typing import Optional
from sqlalchemy.orm import Session, Query
from ctutor_backend.permissions.handlers import PermissionHandler
from ctutor_backend.permissions.query_builders import (
    CoursePermissionQueryBuilder, 
    OrganizationPermissionQueryBuilder,
    UserPermissionQueryBuilder
)
from ctutor_backend.permissions.principal import Principal
from ctutor_backend.api.exceptions import ForbiddenException
from ctutor_backend.model.auth import User
from ctutor_backend.model.course import Course, CourseMember


class UserPermissionHandler(PermissionHandler):
    """Permission handler for User entity"""
    
    ACTION_PERMISSIONS = {
        "list": ["list", "get"],  # Actions that allow listing
        "get": ["get"],
        "create": ["create"],
        "update": ["update"],
        "delete": ["delete"]
    }
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        # Admin can do anything
        if self.check_admin(principal):
            return True
        
        # Check general permission
        if self.check_general_permission(principal, action):
            return True
        
        # Users can view themselves
        if action in ["list", "get"] and resource_id == principal.user_id:
            return True
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        # Admin gets everything
        if self.check_admin(principal):
            return db.query(self.entity)
        
        # Check general permission
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        # For list/get, users can see themselves and users in their courses (as tutor+)
        if action in ["list", "get"]:
            return UserPermissionQueryBuilder.filter_visible_users(principal.user_id, db)
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class AccountPermissionHandler(PermissionHandler):
    """Permission handler for Account entity"""
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        if self.check_general_permission(principal, action):
            return True
        
        # Users can view their own accounts
        if action in ["list", "get"]:
            return True
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        # Users can only see their own accounts
        if action in ["list", "get"]:
            return (
                db.query(self.entity)
                .join(User, User.id == self.entity.user_id)
                .filter(User.id == principal.user_id)
            )
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class ProfilePermissionHandler(PermissionHandler):
    """Permission handler for Profile entity"""
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        if self.check_general_permission(principal, action):
            return True
        
        # Users can view and update their own profile
        if action in ["list", "get", "update"]:
            return True
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        if action in ["list", "get", "update"]:
            return db.query(self.entity).filter(self.entity.user_id == principal.user_id)
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class CoursePermissionHandler(PermissionHandler):
    """Permission handler for Course entity"""
    
    ACTION_ROLE_MAP = {
        "get": "_student",
        "list": "_student",
        "update": "_maintainer",
        "create": None,  # Only through general permission
        "delete": None   # Only through general permission
    }
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        if self.check_general_permission(principal, action):
            return True
        
        # Check course-specific permissions
        if resource_id and action in self.ACTION_ROLE_MAP:
            min_role = self.ACTION_ROLE_MAP[action]
            if min_role:
                # Check if user has required role in this course
                return principal.permitted(self.resource_name, action, resource_id)
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        min_role = self.ACTION_ROLE_MAP.get(action)
        if min_role:
            return CoursePermissionQueryBuilder.build_course_filtered_query(
                self.entity, principal.user_id, min_role, db
            )
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class OrganizationPermissionHandler(PermissionHandler):
    """Permission handler for Organization entity"""
    
    ACTION_ROLE_MAP = {
        "get": "_student",
        "list": "_student",
        "update": None,  # Only through general permission
        "create": None,  # Only through general permission
        "delete": None   # Only through general permission
    }
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        if self.check_general_permission(principal, action):
            return True
        
        # Users can view organizations of courses they're in
        if action in ["get", "list"]:
            return True  # Will be filtered by query
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        min_role = self.ACTION_ROLE_MAP.get(action)
        if min_role:
            return OrganizationPermissionQueryBuilder.filter_by_course_organization(
                self.entity, principal.user_id, min_role, db
            )
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class CourseFamilyPermissionHandler(PermissionHandler):
    """Permission handler for CourseFamily entity"""
    
    ACTION_ROLE_MAP = {
        "get": "_student",
        "list": "_student",
        "update": None,  # Only through general permission
        "create": None,  # Only through general permission
        "delete": None   # Only through general permission
    }
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        if self.check_general_permission(principal, action):
            return True
        
        if action in ["get", "list"]:
            return True  # Will be filtered by query
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        min_role = self.ACTION_ROLE_MAP.get(action)
        if min_role:
            from sqlalchemy.orm import aliased
            from sqlalchemy import select
            
            cm_other = aliased(CourseMember)
            
            query = (
                db.query(self.entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(Course, cm_other.course_id == Course.id)
                .outerjoin(self.entity, self.entity.id == Course.course_family_id)
                .filter(
                    cm_other.course_id.in_(
                        select(CoursePermissionQueryBuilder.user_courses_subquery(
                            principal.user_id, min_role, db
                        ))
                    )
                )
            )
            
            return query
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class CourseContentPermissionHandler(PermissionHandler):
    """Permission handler for CourseContent entity"""
    
    ACTION_ROLE_MAP = {
        "get": "_student",
        "list": "_student",
        "create": "_lecturer",
        "update": "_lecturer",
        "delete": "_lecturer"
    }
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        if self.check_general_permission(principal, action):
            return True
        
        # Check course-based permissions
        if action in self.ACTION_ROLE_MAP:
            return True  # Will be filtered by query
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        min_role = self.ACTION_ROLE_MAP.get(action)
        if min_role:
            from sqlalchemy.orm import aliased
            from sqlalchemy import select
            
            cm_other = aliased(CourseMember)
            
            query = (
                db.query(self.entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(self.entity, self.entity.course_id == cm_other.course_id)
                .filter(
                    cm_other.course_id.in_(
                        select(CoursePermissionQueryBuilder.user_courses_subquery(
                            principal.user_id, min_role, db
                        ))
                    )
                )
            )
            
            return query
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class CourseMemberPermissionHandler(PermissionHandler):
    """Permission handler for CourseMember entity"""
    
    ACTION_ROLE_MAP = {
        "get": "_tutor",
        "list": "_tutor", 
        "update": "_maintainer",
        "create": "_maintainer",
        "delete": "_maintainer"
    }
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        if self.check_general_permission(principal, action):
            return True
        
        # Students can view their own membership
        if action in ["get", "list"] and resource_id == principal.user_id:
            return True
        
        return False
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        min_role = self.ACTION_ROLE_MAP.get(action)
        if min_role:
            from sqlalchemy.orm import aliased
            from sqlalchemy import or_, and_, select
            
            cm_other = aliased(CourseMember)
            
            query = (
                db.query(self.entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(self.entity, self.entity.course_id == cm_other.course_id)
                .filter(
                    or_(
                        cm_other.course_id.in_(
                            select(CoursePermissionQueryBuilder.user_courses_subquery(
                                principal.user_id, min_role, db
                            ))
                        ),
                        and_(
                            User.id == principal.user_id,
                            cm_other.course_role_id == "_student",
                            action in ["get", "list"],
                            self.entity.id == cm_other.id
                        )
                    )
                )
            )
            
            return query
        
        raise ForbiddenException(detail={"entity": self.resource_name})


class ReadOnlyPermissionHandler(PermissionHandler):
    """Permission handler for read-only entities like CourseRole, CourseContentKind"""
    
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        if self.check_admin(principal):
            return True
        
        # Everyone can read these entities
        if action in ["list", "get"]:
            return True
        
        # Only admin can modify
        return self.check_general_permission(principal, action)
    
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        if self.check_admin(principal):
            return db.query(self.entity)
        
        if action in ["list", "get"]:
            return db.query(self.entity)
        
        if self.check_general_permission(principal, action):
            return db.query(self.entity)
        
        raise ForbiddenException(detail={"entity": self.resource_name})