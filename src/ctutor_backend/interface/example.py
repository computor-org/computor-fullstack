"""
Pydantic interfaces for Example Library models.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy_utils import Ltree

from .base import BaseEntityGet, EntityInterface, ListQuery
from ..model.example import ExampleRepository, Example, ExampleVersion, ExampleDependency


class ExampleRepositoryCreate(BaseModel):
    """Create a new example repository."""
    name: str = Field(..., description="Human-readable name of the repository")
    description: Optional[str] = Field(None, description="Description of the repository")
    source_type: str = Field("git", description="Type of source: git, minio, github, s3, gitlab")
    source_url: str = Field(..., description="Repository URL (Git URL, MinIO path, etc.)")
    access_credentials: Optional[str] = Field(None, description="Encrypted credentials")
    default_version: Optional[str] = Field(None, description="Default version to sync from")
    visibility: str = Field("private", description="public, private, or restricted")
    organization_id: Optional[UUID] = None


class ExampleRepositoryGet(BaseEntityGet, ExampleRepositoryCreate):
    """Get example repository details."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExampleRepositoryList(BaseModel):
    """List view of example repositories."""
    id: UUID
    name: str
    description: Optional[str] = None
    source_type: str
    source_url: str
    visibility: str
    organization_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExampleRepositoryUpdate(BaseModel):
    """Update example repository."""
    name: Optional[str] = None
    description: Optional[str] = None
    access_credentials: Optional[str] = None
    default_version: Optional[str] = None
    visibility: Optional[str] = None


class ExampleCreate(BaseModel):
    """Create a new example."""
    example_repository_id: UUID
    directory: str = Field(..., pattern="^[a-zA-Z0-9_-]+$")
    identifier: str = Field(..., description="Hierarchical identifier with dots as separators")
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version_identifier: Optional[str] = None


class ExampleGet(BaseEntityGet, ExampleCreate):
    """Get example details."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    # Relationships
    repository: Optional[ExampleRepositoryGet] = None
    versions: Optional[List['ExampleVersionGet']] = None
    dependencies: Optional[List['ExampleDependencyGet']] = None
    
    @field_validator('identifier', mode='before')
    @classmethod
    def cast_ltree_to_str(cls, value):
        return str(value)
    
    model_config = ConfigDict(from_attributes=True)


class ExampleList(BaseModel):
    """List view of examples."""
    id: UUID
    directory: str
    identifier: str
    title: str
    subject: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    version_identifier: Optional[str] = None
    example_repository_id: UUID
    
    @field_validator('identifier', mode='before')
    @classmethod
    def cast_ltree_to_str(cls, value):
        return str(value)
    
    model_config = ConfigDict(from_attributes=True)


class ExampleUpdate(BaseModel):
    """Update example."""
    identifier: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    version_identifier: Optional[str] = None


class ExampleVersionCreate(BaseModel):
    """Create a new example version."""
    example_id: UUID
    version_tag: str = Field(..., max_length=64)
    version_number: int = Field(..., ge=1)
    storage_path: str
    meta_yaml: str = Field(..., description="Content of meta.yaml")
    test_yaml: Optional[str] = Field(None, description="Content of test.yaml")


class ExampleVersionGet(BaseEntityGet):
    """Get example version details."""
    id: UUID
    example_id: UUID
    version_tag: str
    version_number: int
    storage_path: str
    meta_yaml: str
    test_yaml: Optional[str] = None
    created_at: datetime
    created_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExampleVersionList(BaseModel):
    """List view of example versions."""
    id: UUID
    version_tag: str
    version_number: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExampleDependencyCreate(BaseModel):
    """Create example dependency."""
    example_id: UUID
    depends_id: UUID


class ExampleDependencyGet(BaseModel):
    """Get example dependency details."""
    id: UUID
    example_id: UUID
    depends_id: UUID
    created_at: datetime
    
    # Relationship
    dependency: Optional[ExampleList] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExampleQuery(ListQuery):
    """Query parameters for listing examples."""
    repository_id: Optional[UUID] = None
    identifier: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None


class ExampleRepositoryQuery(ListQuery):
    """Query parameters for listing repositories."""
    name: Optional[str] = None
    source_type: Optional[str] = None
    visibility: Optional[str] = None
    organization_id: Optional[UUID] = None


# Search functions
def example_repository_search(db: Session, query, params: Optional[ExampleRepositoryQuery]):
    """Search function for example repositories."""
    if params is None:
        return query
    
    if params.name:
        query = query.filter(ExampleRepository.name.ilike(f"%{params.name}%"))
    if params.source_type:
        query = query.filter(ExampleRepository.source_type == params.source_type)
    if params.visibility:
        query = query.filter(ExampleRepository.visibility == params.visibility)
    if params.organization_id:
        query = query.filter(ExampleRepository.organization_id == params.organization_id)
    
    return query


def example_search(db: Session, query, params: Optional[ExampleQuery]):
    """Search function for examples."""
    if params is None:
        return query
    
    if params.repository_id:
        query = query.filter(Example.example_repository_id == params.repository_id)
    if params.identifier:
        query = query.filter(Example.identifier == Ltree(params.identifier))
    if params.title:
        query = query.filter(Example.title.ilike(f"%{params.title}%"))
    if params.subject:
        query = query.filter(Example.subject == params.subject)
    if params.category:
        query = query.filter(Example.category == params.category)
    if params.tags:
        # Filter by any of the provided tags
        query = query.filter(Example.tags.overlap(params.tags))
    if params.search:
        # Search in title, description, and identifier
        query = query.filter(
            or_(
                Example.title.ilike(f"%{params.search}%"),
                Example.description.ilike(f"%{params.search}%"),
                Example.identifier.op('~')(f"*{params.search}*"),  # Ltree contains
            )
        )
    
    return query


# EntityInterface classes
class ExampleRepositoryInterface(EntityInterface):
    """Interface for ExampleRepository entity."""
    create = ExampleRepositoryCreate
    get = ExampleRepositoryGet
    list = ExampleRepositoryList
    update = ExampleRepositoryUpdate
    query = ExampleRepositoryQuery
    search = example_repository_search
    endpoint = "example-repositories"
    model = ExampleRepository


class ExampleInterface(EntityInterface):
    """Interface for Example entity."""
    create = ExampleCreate
    get = ExampleGet
    list = ExampleList
    update = ExampleUpdate
    query = ExampleQuery
    search = example_search
    endpoint = "examples"
    model = Example


class ExampleUploadRequest(BaseModel):
    """Request to upload an example to storage."""
    repository_id: UUID
    directory: str = Field(..., pattern="^[a-zA-Z0-9_-]+$")
    version_tag: str
    files: Dict[str, str] = Field(..., description="Map of filename to content")
    meta_yaml: str
    test_yaml: Optional[str] = None


class ExampleDownloadResponse(BaseModel):
    """Response containing downloaded example files."""
    example_id: UUID
    version_id: UUID
    version_tag: str
    files: Dict[str, str] = Field(..., description="Map of filename to content")
    meta_yaml: str
    test_yaml: Optional[str] = None


# Fix forward references
ExampleGet.model_rebuild()