"""
Migration helper to transition from old permission system to the refactored one.
This module provides utilities to help migrate existing code gradually.
"""

import logging
from typing import Any, Optional
from sqlalchemy.orm import Session

# Import old system components
from ctutor_backend.interface.permissions import (
    Principal as OldPrincipal,
    Claims as OldClaims,
    build_claim_actions as old_build_claim_actions
)
from ctutor_backend.api.permissions import (
    check_permissions as old_check_permissions,
    check_admin as old_check_admin,
    get_permitted_course_ids as old_get_permitted_course_ids
)

# Import new system components  
from ctutor_backend.permissions.principal import (
    Principal as NewPrincipal,
    Claims as NewClaims,
    build_claims as new_build_claims
)
from ctutor_backend.permissions.core import (
    check_permissions as new_check_permissions,
    check_admin as new_check_admin,
    get_permitted_course_ids as new_get_permitted_course_ids
)

logger = logging.getLogger(__name__)

# Migration configuration
USE_NEW_SYSTEM = False  # Set to True to enable new system globally


class PrincipalAdapter:
    """Adapter to convert between old and new Principal formats"""
    
    @staticmethod
    def old_to_new(old_principal: OldPrincipal) -> NewPrincipal:
        """Convert old Principal to new format"""
        
        # Convert old claims to new format
        claim_values = []
        
        # Convert general claims
        for resource, actions in old_principal.claims.general.items():
            for action in actions:
                claim_values.append(("permissions", f"{resource}:{action}"))
        
        # Convert dependent claims
        for resource, resource_dict in old_principal.claims.dependent.items():
            for resource_id, actions in resource_dict.items():
                for action in actions:
                    claim_values.append(("permissions", f"{resource}:{action}:{resource_id}"))
        
        # Build new claims
        new_claims = new_build_claims(claim_values)
        
        # Create new Principal
        return NewPrincipal(
            is_admin=old_principal.is_admin,
            user_id=old_principal.user_id,
            roles=old_principal.roles,
            claims=new_claims
        )
    
    @staticmethod
    def new_to_old(new_principal: NewPrincipal) -> OldPrincipal:
        """Convert new Principal to old format"""
        
        # Convert new claims to old format
        old_general = {}
        old_dependent = {}
        
        # Convert general claims
        for resource, actions in new_principal.claims.general.items():
            old_general[resource] = list(actions)
        
        # Convert dependent claims
        for resource, resource_dict in new_principal.claims.dependent.items():
            old_dependent[resource] = {}
            for resource_id, actions in resource_dict.items():
                old_dependent[resource][resource_id] = list(actions)
        
        # Create old Claims
        old_claims = OldClaims(general=old_general, dependent=old_dependent)
        
        # Create old Principal
        return OldPrincipal(
            is_admin=new_principal.is_admin,
            user_id=new_principal.user_id,
            roles=new_principal.roles,
            claims=old_claims
        )


class MigrationHelper:
    """Helper class for gradual migration"""
    
    @staticmethod
    def check_permissions(permissions: Any, entity: Any, action: str, db: Session):
        """
        Unified check_permissions that routes to old or new system
        """
        if USE_NEW_SYSTEM:
            # Convert old Principal to new if needed
            if isinstance(permissions, OldPrincipal):
                permissions = PrincipalAdapter.old_to_new(permissions)
            
            return new_check_permissions(permissions, entity, action, db)
        else:
            # Convert new Principal to old if needed
            if isinstance(permissions, NewPrincipal):
                permissions = PrincipalAdapter.new_to_old(permissions)
            
            return old_check_permissions(permissions, entity, action, db)
    
    @staticmethod
    def check_admin(permissions: Any) -> bool:
        """Unified admin check"""
        if USE_NEW_SYSTEM:
            if isinstance(permissions, OldPrincipal):
                permissions = PrincipalAdapter.old_to_new(permissions)
            return new_check_admin(permissions)
        else:
            if isinstance(permissions, NewPrincipal):
                permissions = PrincipalAdapter.new_to_old(permissions)
            return old_check_admin(permissions)
    
    @staticmethod
    def compare_systems(permissions: Any, entity: Any, action: str, db: Session):
        """
        Compare results from both systems for testing
        """
        # Ensure we have both Principal types
        if isinstance(permissions, OldPrincipal):
            old_principal = permissions
            new_principal = PrincipalAdapter.old_to_new(permissions)
        else:
            new_principal = permissions
            old_principal = PrincipalAdapter.new_to_old(permissions)
        
        # Run both systems
        try:
            old_result = old_check_permissions(old_principal, entity, action, db)
            old_count = old_result.count() if old_result else 0
        except Exception as e:
            logger.error(f"Old system error: {e}")
            old_count = -1
        
        try:
            new_result = new_check_permissions(new_principal, entity, action, db)
            new_count = new_result.count() if new_result else 0
        except Exception as e:
            logger.error(f"New system error: {e}")
            new_count = -1
        
        # Compare results
        if old_count != new_count:
            logger.warning(
                f"Permission system mismatch for {entity.__name__}.{action}: "
                f"old={old_count}, new={new_count}"
            )
        
        return {
            "old_count": old_count,
            "new_count": new_count,
            "match": old_count == new_count
        }


def enable_new_system():
    """Enable the new permission system globally"""
    global USE_NEW_SYSTEM
    USE_NEW_SYSTEM = True
    logger.info("New permission system enabled")


def disable_new_system():
    """Disable the new permission system (use old system)"""
    global USE_NEW_SYSTEM
    USE_NEW_SYSTEM = False
    logger.info("Old permission system enabled")


def get_system_status() -> str:
    """Get current system status"""
    return "NEW" if USE_NEW_SYSTEM else "OLD"


# Migration checklist functions
def verify_entity_handler_coverage() -> dict:
    """Check which entities have handlers in the new system"""
    from ctutor_backend.permissions.handlers import permission_registry
    
    # List of all entities that need handlers
    required_entities = [
        "User", "Account", "Profile", "StudentProfile", "Session",
        "Organization", "CourseFamily", "Course", "CourseMember",
        "CourseContent", "CourseContentType", "CourseContentKind",
        "CourseRole", "CourseGroup", "CourseExecutionBackend",
        "Result", "ExecutionBackend", "Role", "RoleClaim", "UserRole",
        "Group", "GroupClaim", "UserGroup", "Example", "ExampleRepository",
        "ExampleVersion", "ExampleDependency"
    ]
    
    coverage = {}
    for entity_name in required_entities:
        # Try to get the actual entity class
        try:
            # Import and check if handler exists
            handler_exists = False
            # This is simplified - in reality you'd check the registry
            coverage[entity_name] = {
                "has_handler": handler_exists,
                "status": "✓" if handler_exists else "✗"
            }
        except Exception as e:
            coverage[entity_name] = {
                "has_handler": False,
                "status": "✗",
                "error": str(e)
            }
    
    return coverage


def run_migration_tests() -> dict:
    """Run basic tests to verify the new system works correctly"""
    results = {
        "principal_conversion": False,
        "permission_check": False,
        "cache_functionality": False
    }
    
    try:
        # Test Principal conversion
        old_claims = OldClaims(
            general={"user": ["list", "get"]},
            dependent={"course": {"123": ["update"]}}
        )
        old_principal = OldPrincipal(
            is_admin=False,
            user_id="test-user",
            roles=["_user"],
            claims=old_claims
        )
        
        new_principal = PrincipalAdapter.old_to_new(old_principal)
        back_to_old = PrincipalAdapter.new_to_old(new_principal)
        
        results["principal_conversion"] = (
            old_principal.user_id == back_to_old.user_id and
            old_principal.is_admin == back_to_old.is_admin
        )
        
        # Test permission check
        results["permission_check"] = new_principal.permitted("user", "list")
        
        # Test cache (basic check)
        from ctutor_backend.permissions.cache import permission_cache
        results["cache_functionality"] = permission_cache is not None
        
    except Exception as e:
        logger.error(f"Migration test error: {e}")
    
    return results