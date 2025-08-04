"""
Organization repository for direct database access.

This module provides the OrganizationRepository class that handles
all database operations for Organization entities, replacing API
client composite functions.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from ..types import Ltree

from .base import BaseRepository
from ..model.organization import Organization


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization entity database operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Organization)
    
    def find_by_path(self, path: str) -> Optional[Organization]:
        """
        Find organization by hierarchical path.
        
        Args:
            path: The ltree path to search for
            
        Returns:
            Organization if found, None otherwise
        """
        return self.find_one_by(path=Ltree(path))
    
    def find_by_organization_type(self, org_type: str) -> List[Organization]:
        """
        Find organizations by type.
        
        Args:
            org_type: Organization type ('user', 'community', 'organization')
            
        Returns:
            List of organizations of the specified type
        """
        return self.find_by(organization_type=org_type)
    
    def find_by_user_id(self, user_id: str) -> Optional[Organization]:
        """
        Find user organization by user ID.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Organization if found, None otherwise
        """
        return self.find_one_by(user_id=user_id)
    
    def find_children(self, parent_path: str) -> List[Organization]:
        """
        Find all child organizations under a parent path.
        
        Args:
            parent_path: The parent path to search under
            
        Returns:
            List of child organizations
        """
        # Use ltree path matching to find children
        query = self.db.query(Organization).filter(
            Organization.path.descendant_of(Ltree(parent_path))
        )
        return query.all()
    
    def find_direct_children(self, parent_path: str) -> List[Organization]:
        """
        Find direct child organizations (immediate children only).
        
        Args:
            parent_path: The parent path to search under
            
        Returns:
            List of direct child organizations
        """
        # Use computed parent_path to find direct children
        query = self.db.query(Organization).filter(
            Organization.parent_path == Ltree(parent_path)
        )
        return query.all()
    
    def find_by_path_pattern(self, pattern: str) -> List[Organization]:
        """
        Find organizations matching a path pattern.
        
        Args:
            pattern: Ltree pattern to match (e.g., '*.university.*')
            
        Returns:
            List of organizations matching the pattern
        """
        query = self.db.query(Organization).filter(
            Organization.path.lquery(pattern)
        )
        return query.all()
    
    def find_active_organizations(self) -> List[Organization]:
        """
        Find all non-archived organizations.
        
        Returns:
            List of active (non-archived) organizations
        """
        return self.find_by(archived_at=None)
    
    def find_by_number(self, number: str) -> Optional[Organization]:
        """
        Find organization by number/identifier.
        
        Args:
            number: Organization number to search for
            
        Returns:
            Organization if found, None otherwise
        """
        return self.find_one_by(number=number)
    
    def search_by_title(self, title_pattern: str) -> List[Organization]:
        """
        Search organizations by title pattern (case-insensitive).
        
        Args:
            title_pattern: Pattern to search for in titles
            
        Returns:
            List of organizations with matching titles
        """
        query = self.db.query(Organization).filter(
            Organization.title.ilike(f"%{title_pattern}%")
        )
        return query.all()
    
    def get_root_organizations(self) -> List[Organization]:
        """
        Get all root organizations (no parent).
        
        Returns:
            List of root organizations
        """
        query = self.db.query(Organization).filter(
            Organization.parent_path.is_(None)
        )
        return query.all()