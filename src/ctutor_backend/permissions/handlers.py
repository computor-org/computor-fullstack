from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from sqlalchemy.orm import Session, Query, aliased
from sqlalchemy import and_, or_, select
from ctutor_backend.permissions.principal import Principal
from ctutor_backend.api.exceptions import ForbiddenException


class PermissionHandler(ABC):
    """Base class for entity-specific permission handlers"""
    
    def __init__(self, entity: Type[Any]):
        self.entity = entity
        self.resource_name = entity.__tablename__
    
    @abstractmethod
    def can_perform_action(self, principal: Principal, action: str, resource_id: Optional[str] = None) -> bool:
        """Check if principal can perform an action on a resource"""
        pass
    
    @abstractmethod
    def build_query(self, principal: Principal, action: str, db: Session) -> Query:
        """Build a filtered query based on permissions"""
        pass
    
    def check_admin(self, principal: Principal) -> bool:
        """Check if principal has admin privileges"""
        return principal.is_admin
    
    def check_general_permission(self, principal: Principal, action: str) -> bool:
        """Check if principal has general permission for action on this resource"""
        return principal.permitted(self.resource_name, action)
    
    def check_dependent_permission(self, principal: Principal, action: str, resource_id: str) -> bool:
        """Check if principal has specific permission for action on a specific resource"""
        return principal.permitted(self.resource_name, action, resource_id)


class PermissionRegistry:
    """Registry for managing entity permission handlers"""
    
    _instance = None
    _handlers: Dict[Type[Any], PermissionHandler] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, entity: Type[Any], handler: PermissionHandler):
        """Register a permission handler for an entity"""
        self._handlers[entity] = handler
    
    def get_handler(self, entity: Type[Any]) -> Optional[PermissionHandler]:
        """Get the permission handler for an entity"""
        return self._handlers.get(entity)
    
    def check_permissions(self, principal: Principal, entity: Type[Any], action: str, db: Session) -> Query:
        """Check permissions and return filtered query"""
        handler = self.get_handler(entity)
        if not handler:
            # Fallback to admin-only if no handler registered
            if not principal.is_admin:
                raise ForbiddenException(detail={"entity": entity.__tablename__})
            return db.query(entity)
        
        return handler.build_query(principal, action, db)


# Global registry instance
permission_registry = PermissionRegistry()
