"""
Integration module to enable the new permission system in the existing codebase.
This provides a gradual migration path from the old to new system.
"""

import os
from typing import Any
from sqlalchemy.orm import Session
import logging

# Environment variable to control which system to use
USE_NEW_PERMISSION_SYSTEM = os.getenv("USE_NEW_PERMISSION_SYSTEM", "true").lower() == "true"

logger = logging.getLogger(__name__)

# Import old system
from ctutor_backend.api.permissions import (
    check_permissions as old_check_permissions,
    check_admin as old_check_admin,
    check_course_permissions as old_check_course_permissions,
    get_permitted_course_ids as old_get_permitted_course_ids,
    db_get_claims as old_db_get_claims,
    db_get_course_claims as old_db_get_course_claims,
)
# Note: get_current_permissions remains in api.auth to avoid circular imports
from ctutor_backend.interface.permissions import (
    Principal as OldPrincipal,
    build_claim_actions as old_build_claim_actions,
)

# Import new system
from ctutor_backend.permissions.core import (
    check_permissions as new_check_permissions,
    check_admin as new_check_admin,
    check_course_permissions as new_check_course_permissions,
    get_permitted_course_ids as new_get_permitted_course_ids,
    db_get_claims as new_db_get_claims,
    db_get_course_claims as new_db_get_course_claims,
    initialize_permission_handlers,
)
# Auth functions remain in their original modules to avoid circular imports
from ctutor_backend.permissions.principal import (
    Principal as NewPrincipal,
    build_claims as new_build_claim_actions,
)
from ctutor_backend.permissions.migration import PrincipalAdapter

# Initialize the new system handlers if enabled
if USE_NEW_PERMISSION_SYSTEM:
    logger.info("🚀 NEW PERMISSION SYSTEM ENABLED")
    initialize_permission_handlers()
else:
    logger.info("Using old permission system (set USE_NEW_PERMISSION_SYSTEM=true to enable new system)")


def adaptive_check_permissions(permissions: Any, entity: Any, action: str, db: Session):
    """
    Adaptive permission check that routes to the appropriate system.
    Automatically converts Principal types if needed.
    """
    if USE_NEW_PERMISSION_SYSTEM:
        # Convert old Principal to new if needed
        if isinstance(permissions, OldPrincipal):
            permissions = PrincipalAdapter.old_to_new(permissions)
        return new_check_permissions(permissions, entity, action, db)
    else:
        # Use old system
        if isinstance(permissions, NewPrincipal):
            permissions = PrincipalAdapter.new_to_old(permissions)
        return old_check_permissions(permissions, entity, action, db)


def adaptive_check_admin(permissions: Any) -> bool:
    """Adaptive admin check"""
    if USE_NEW_PERMISSION_SYSTEM:
        if isinstance(permissions, OldPrincipal):
            permissions = PrincipalAdapter.old_to_new(permissions)
        return new_check_admin(permissions)
    else:
        if isinstance(permissions, NewPrincipal):
            permissions = PrincipalAdapter.new_to_old(permissions)
        return old_check_admin(permissions)


def adaptive_check_course_permissions(permissions: Any, entity: Any, course_role_id: str, db: Session):
    """Adaptive course permission check"""
    if USE_NEW_PERMISSION_SYSTEM:
        if isinstance(permissions, OldPrincipal):
            permissions = PrincipalAdapter.old_to_new(permissions)
        return new_check_course_permissions(permissions, entity, course_role_id, db)
    else:
        if isinstance(permissions, NewPrincipal):
            permissions = PrincipalAdapter.new_to_old(permissions)
        return old_check_course_permissions(permissions, entity, course_role_id, db)


def adaptive_get_permitted_course_ids(permissions: Any, course_role_id: str, db: Session):
    """Adaptive get permitted course IDs"""
    if USE_NEW_PERMISSION_SYSTEM:
        if isinstance(permissions, OldPrincipal):
            permissions = PrincipalAdapter.old_to_new(permissions)
        return new_get_permitted_course_ids(permissions, course_role_id, db)
    else:
        if isinstance(permissions, NewPrincipal):
            permissions = PrincipalAdapter.new_to_old(permissions)
        return old_get_permitted_course_ids(permissions, course_role_id, db)


# Export the appropriate functions based on configuration
if USE_NEW_PERMISSION_SYSTEM:
    # Use new system
    check_permissions = new_check_permissions
    check_admin = new_check_admin
    check_course_permissions = new_check_course_permissions
    get_permitted_course_ids = new_get_permitted_course_ids
    db_get_claims = new_db_get_claims
    db_get_course_claims = new_db_get_course_claims
    Principal = NewPrincipal
    build_claim_actions = new_build_claim_actions
    
    # Log which system is being used
    logger.info("Exported NEW permission system functions")
else:
    # Use old system (default)
    check_permissions = old_check_permissions
    check_admin = old_check_admin
    check_course_permissions = old_check_course_permissions
    get_permitted_course_ids = old_get_permitted_course_ids
    db_get_claims = old_db_get_claims
    db_get_course_claims = old_db_get_course_claims
    Principal = OldPrincipal
    build_claim_actions = old_build_claim_actions
    
    # Log which system is being used
    logger.info("Exported OLD permission system functions")


# Utility function to check which system is active
def get_active_system() -> str:
    """Return which permission system is currently active"""
    return "NEW" if USE_NEW_PERMISSION_SYSTEM else "OLD"


def toggle_system(use_new: bool = None) -> str:
    """
    Toggle between old and new permission systems at runtime.
    Note: This only affects new imports, not already imported modules.
    
    Args:
        use_new: If provided, set the system to use. If None, toggle current.
    
    Returns:
        The active system after toggle
    """
    global USE_NEW_PERMISSION_SYSTEM
    
    if use_new is None:
        USE_NEW_PERMISSION_SYSTEM = not USE_NEW_PERMISSION_SYSTEM
    else:
        USE_NEW_PERMISSION_SYSTEM = use_new
    
    if USE_NEW_PERMISSION_SYSTEM:
        initialize_permission_handlers()
        logger.info("Switched to NEW permission system")
    else:
        logger.info("Switched to OLD permission system")
    
    return get_active_system()


# Export adaptive functions for gradual migration
__all__ = [
    # Main functions
    "check_permissions",
    "check_admin", 
    "check_course_permissions",
    "get_permitted_course_ids",
    "db_get_claims",
    "db_get_course_claims",
    "Principal",
    "build_claim_actions",
    
    # Adaptive functions for mixed usage
    "adaptive_check_permissions",
    "adaptive_check_admin",
    "adaptive_check_course_permissions",
    "adaptive_get_permitted_course_ids",
    
    # Utility functions
    "get_active_system",
    "toggle_system",
    "USE_NEW_PERMISSION_SYSTEM",
]