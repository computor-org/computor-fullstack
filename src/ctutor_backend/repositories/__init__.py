"""
Repository pattern implementation for direct database access.

This package provides repository classes that replace the API client
composite functions, enabling direct database operations.
"""

from .base import (
    BaseRepository,
    RepositoryError,
    NotFoundError,
    DuplicateError
)
from .organization import OrganizationRepository

__all__ = [
    "BaseRepository",
    "RepositoryError", 
    "NotFoundError",
    "DuplicateError",
    "OrganizationRepository"
]