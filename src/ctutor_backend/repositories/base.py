"""
Base repository pattern implementation.

This module provides abstract base classes for the repository pattern,
enabling direct database access without going through the API layer.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import inspect

# Type variable for generic entity type
T = TypeVar('T')


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class NotFoundError(RepositoryError):
    """Exception raised when entity is not found."""
    
    def __init__(self, entity_type: str, entity_id: Any):
        super().__init__(f"{entity_type} with id {entity_id} not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateError(RepositoryError):
    """Exception raised when attempting to create duplicate entity."""
    
    def __init__(self, entity_type: str, criteria: Dict[str, Any]):
        super().__init__(f"{entity_type} already exists with criteria: {criteria}")
        self.entity_type = entity_type
        self.criteria = criteria


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository providing common database operations.
    
    This class implements the repository pattern, providing a clean
    abstraction over SQLAlchemy operations.
    """
    
    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize repository with database session and model class.
        
        Args:
            db: SQLAlchemy database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def get_by_id(self, entity_id: Any) -> T:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity instance
            
        Raises:
            NotFoundError: If entity not found
        """
        entity = self.get_by_id_optional(entity_id)
        if entity is None:
            raise NotFoundError(self.model.__name__, entity_id)
        return entity
    
    def get_by_id_optional(self, entity_id: Any) -> Optional[T]:
        """
        Get entity by ID, returning None if not found.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity instance or None
        """
        return self.db.query(self.model).filter(
            self.model.id == entity_id
        ).first()
    
    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **filters
    ) -> List[T]:
        """
        List entities with optional pagination and filters.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            **filters: Additional filter criteria
            
        Returns:
            List of entities
        """
        query = self.db.query(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        # Apply pagination
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()
    
    def create(self, entity: T) -> T:
        """
        Create a new entity.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            Created entity with updated fields (e.g., ID)
            
        Raises:
            DuplicateError: If entity violates unique constraints
            RepositoryError: If database operation fails
        """
        try:
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except IntegrityError as e:
            self.db.rollback()
            # Extract useful information from the error
            raise DuplicateError(
                self.model.__name__,
                self._extract_entity_dict(entity)
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to create {self.model.__name__}: {str(e)}")
    
    def update(self, entity_id: Any, updates: Dict[str, Any]) -> T:
        """
        Update an existing entity.
        
        Args:
            entity_id: Entity identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated entity
            
        Raises:
            NotFoundError: If entity not found
            RepositoryError: If update fails
        """
        entity = self.get_by_id(entity_id)
        
        try:
            # Apply updates
            for key, value in updates.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to update {self.model.__name__}: {str(e)}")
    
    def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if deletion successful
            
        Raises:
            NotFoundError: If entity not found
            RepositoryError: If deletion fails
        """
        entity = self.get_by_id(entity_id)
        
        try:
            self.db.delete(entity)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryError(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    def exists(self, entity_id: Any) -> bool:
        """
        Check if entity exists by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if entity exists
        """
        return self.db.query(self.model).filter(
            self.model.id == entity_id
        ).count() > 0
    
    def find_by(self, **criteria) -> List[T]:
        """
        Find entities by multiple criteria.
        
        Args:
            **criteria: Search criteria as keyword arguments
            
        Returns:
            List of matching entities
        """
        query = self.db.query(self.model)
        
        for key, value in criteria.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        return query.all()
    
    def find_one_by(self, **criteria) -> Optional[T]:
        """
        Find single entity by criteria.
        
        Args:
            **criteria: Search criteria as keyword arguments
            
        Returns:
            First matching entity or None
        """
        query = self.db.query(self.model)
        
        for key, value in criteria.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        return query.first()
    
    def count(self, **criteria) -> int:
        """
        Count entities matching criteria.
        
        Args:
            **criteria: Filter criteria as keyword arguments
            
        Returns:
            Number of matching entities
        """
        query = self.db.query(self.model)
        
        for key, value in criteria.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def flush(self) -> None:
        """Flush pending changes without committing."""
        self.db.flush()
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()
    
    def _extract_entity_dict(self, entity: T) -> Dict[str, Any]:
        """
        Extract entity attributes as dictionary.
        
        Args:
            entity: Entity instance
            
        Returns:
            Dictionary of entity attributes
        """
        # Use SQLAlchemy inspection if available
        try:
            mapper = inspect(entity)
            return {
                col.key: getattr(entity, col.key)
                for col in mapper.attrs
                if hasattr(entity, col.key)
            }
        except Exception:
            # Fallback to simple attribute extraction
            return {
                attr: getattr(entity, attr)
                for attr in dir(entity)
                if not attr.startswith('_') and not callable(getattr(entity, attr))
            }