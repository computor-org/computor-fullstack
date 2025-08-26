# Backend Implementation Guide for Computor

This guide provides comprehensive instructions for implementing new features and extending existing functionality in the Computor backend.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Database Models (SQLAlchemy)](#database-models-sqlalchemy)
3. [DTOs/Interfaces (Pydantic)](#dtosinterfaces-pydantic)
4. [API Implementation](#api-implementation)
5. [Database Connection & Sessions](#database-connection--sessions)
6. [Redis Caching](#redis-caching)
7. [Complete Implementation Example](#complete-implementation-example)

## Architecture Overview

The backend follows a layered architecture:
- **Models** (`src/ctutor_backend/model/`): SQLAlchemy ORM models (single source of truth)
- **Interfaces/DTOs** (`src/ctutor_backend/interface/`): Pydantic schemas for API validation
- **API** (`src/ctutor_backend/api/`): FastAPI endpoints with automatic CRUD generation
- **Database** (`src/ctutor_backend/database.py`): PostgreSQL connection management
- **Cache** (`src/ctutor_backend/redis_cache.py`): Redis caching with aiocache

## Database Models (SQLAlchemy)

### Creating a New Model

1. Create a new file in `src/ctutor_backend/model/` (e.g., `example.py`):

```python
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, 
    ForeignKey, String, text, Integer
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base

class Example(Base):
    __tablename__ = 'example'
    
    # Standard fields (always include these)
    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)  # For flexible additional data
    
    # Optional archive support
    archived_at = Column(DateTime(True))
    
    # Your custom fields
    name = Column(String(255), nullable=False)
    description = Column(String(4096))
    is_active = Column(Boolean, server_default=text("true"))
    
    # Foreign keys
    organization_id = Column(ForeignKey('organization.id', ondelete='CASCADE'))
    
    # Relationships
    organization = relationship('Organization', back_populates='examples')
```

### Model Best Practices

- Always inherit from `Base`
- Include standard metadata fields (id, version, timestamps, created/updated_by)
- Use `UUID` for primary keys with `uuid_generate_v4()`
- Add `properties` JSONB field for extensibility
- Define relationships with proper `back_populates`
- Use appropriate constraints and indexes
- Support soft deletes with `archived_at` when needed

## DTOs/Interfaces (Pydantic)

### Creating DTOs for Your Model

Create a new file in `src/ctutor_backend/interface/` (e.g., `examples.py`):

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional
from sqlalchemy.orm import Session

from ctutor_backend.interface.base import (
    BaseEntityGet, BaseEntityList, EntityInterface, ListQuery
)
from ctutor_backend.model.example import Example

# Create DTO - for POST requests
class ExampleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Example name")
    description: Optional[str] = Field(None, max_length=4096)
    is_active: Optional[bool] = Field(True, description="Active status")
    organization_id: Optional[str] = Field(None, description="Organization UUID")
    properties: Optional[dict] = Field(None, description="Additional properties")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    model_config = ConfigDict(use_enum_values=True)

# Get DTO - for single entity responses
class ExampleGet(BaseEntityGet):
    id: str = Field(description="Example unique identifier")
    name: str = Field(description="Example name")
    description: Optional[str] = Field(None, description="Description")
    is_active: bool = Field(description="Active status")
    organization_id: Optional[str] = Field(None, description="Organization UUID")
    properties: Optional[dict] = Field(None, description="Additional properties")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    
    # Add computed properties if needed
    @property
    def display_name(self) -> str:
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

# List DTO - for list responses (lighter weight)
class ExampleList(BaseEntityList):
    id: str = Field(description="Example unique identifier")
    name: str = Field(description="Example name")
    is_active: bool = Field(description="Active status")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

# Update DTO - for PATCH requests
class ExampleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=4096)
    is_active: Optional[bool] = Field(None)
    properties: Optional[dict] = Field(None)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v

# Query DTO - for filtering
class ExampleQuery(ListQuery):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    organization_id: Optional[str] = None
    archived: Optional[bool] = None

# Search function for database queries
def example_search(db: Session, query, params: Optional[ExampleQuery]):
    if params.name is not None:
        query = query.filter(Example.name.ilike(f"%{params.name}%"))
    
    if params.is_active is not None:
        query = query.filter(Example.is_active == params.is_active)
    
    if params.organization_id is not None:
        query = query.filter(Example.organization_id == params.organization_id)
    
    # Handle archived filter
    if params.archived is not None and params.archived:
        query = query.filter(Example.archived_at.isnot(None))
    else:
        query = query.filter(Example.archived_at.is_(None))
    
    return query

# Interface class that ties everything together
class ExampleInterface(EntityInterface):
    create = ExampleCreate
    get = ExampleGet
    list = ExampleList
    update = ExampleUpdate
    query = ExampleQuery
    search = example_search
    endpoint = "examples"
    model = Example
    cache_ttl = 300  # Cache for 5 minutes
```

### DTO Best Practices

- Inherit from `BaseEntityGet` and `BaseEntityList` for standard fields
- Use Pydantic v2 decorators (`@field_validator`)
- Add comprehensive field descriptions
- Implement validation for business rules
- Keep List DTOs lightweight (fewer fields)
- Use `ConfigDict` for proper model configuration
- Set appropriate cache TTL based on data volatility

## API Implementation

### Automatic CRUD API Generation

Add to `src/ctutor_backend/server.py`:

```python
from ctutor_backend.interface.examples import ExampleInterface

# In the startup_logic function:
CrudRouter(ExampleInterface()).register_routes(app)
```

This automatically creates:
- `POST /examples` - Create example
- `GET /examples/{id}` - Get example by ID
- `GET /examples` - List examples with pagination
- `PATCH /examples/{id}` - Update example
- `DELETE /examples/{id}` - Delete example
- `PATCH /examples/{id}/archive` - Archive example (if model has archived_at)

### Custom API Endpoints

For custom business logic, create `src/ctutor_backend/api/examples.py`:

```python
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.crud import create_db, get_id_db
from ctutor_backend.database import get_db
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.examples import ExampleInterface, ExampleGet
from ctutor_backend.model.example import Example
from ctutor_backend.redis_cache import get_redis_client
from aiocache import BaseCache

example_router = APIRouter(prefix="/examples", tags=["examples"])

@example_router.post("/bulk", response_model=List[ExampleGet])
async def create_bulk_examples(
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    examples: List[ExampleInterface.create],
    cache: Annotated[BaseCache, Depends(get_redis_client)],
    db: Session = Depends(get_db)
):
    """Create multiple examples in one request"""
    created_examples = []
    
    for example_data in examples:
        created = await create_db(
            permissions, db, example_data, 
            Example, ExampleGet
        )
        created_examples.append(created)
    
    # Clear cache after bulk creation
    pattern = f"example:*"
    if hasattr(cache, '_client'):
        await cache._client.delete(*await cache._client.keys(pattern))
    
    return created_examples

@example_router.get("/active", response_model=List[ExampleGet])
async def get_active_examples(
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    cache: Annotated[BaseCache, Depends(get_redis_client)],
    db: Session = Depends(get_db)
):
    """Get all active examples"""
    # Check cache first
    cache_key = f"examples:active:{permissions.user_id}"
    cached = await cache.get(cache_key)
    
    if cached:
        return [ExampleGet.model_validate_json(item) for item in cached]
    
    # Query database
    examples = db.query(Example).filter(
        Example.is_active == True,
        Example.archived_at.is_(None)
    ).all()
    
    result = [ExampleGet.model_validate(e, from_attributes=True) for e in examples]
    
    # Cache results
    await cache.set(
        cache_key, 
        [r.model_dump_json() for r in result], 
        ttl=300
    )
    
    return result
```

Register in `server.py`:
```python
app.include_router(example_router)
```

## Database Connection & Sessions

### Using Database Sessions

```python
from ctutor_backend.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

# In your API endpoint:
def your_endpoint(db: Session = Depends(get_db)):
    # db is automatically managed (opened/closed)
    result = db.query(YourModel).filter(...).first()
    
    # For writes:
    new_item = YourModel(field="value")
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
```

### Database Configuration

- Connection pooling is pre-configured with optimal settings
- Sessions are automatically rolled back on errors
- Use environment variables: `POSTGRES_HOST`, `POSTGRES_USER`, etc.

## Redis Caching

### Using Redis Cache

```python
from ctutor_backend.redis_cache import get_redis_client
from aiocache import BaseCache
from typing import Annotated
from fastapi import Depends

async def cached_endpoint(
    cache: Annotated[BaseCache, Depends(get_redis_client)]
):
    # Check cache
    cache_key = "your:cache:key"
    cached_value = await cache.get(cache_key)
    
    if cached_value:
        return cached_value
    
    # Compute value
    result = expensive_operation()
    
    # Store in cache
    await cache.set(cache_key, result, ttl=300)  # 5 minutes
    
    return result
```

### Cache Patterns

1. **Entity Caching**: `{table_name}:get:{user_id}:{entity_id}`
2. **List Caching**: `{table_name}:list:{user_id}:{params_hash}`
3. **Custom Caching**: Define your own patterns

### Cache Invalidation

```python
# Clear all cache entries for a table
pattern = f"{table_name}:*"
if hasattr(cache, '_client'):
    redis_client = cache._client
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)
```

## Complete Implementation Example

Let's implement a "Project" feature:

### 1. Create Model (`src/ctutor_backend/model/project.py`)

```python
from sqlalchemy import Column, String, Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base

class Project(Base):
    __tablename__ = 'project'
    
    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    # ... standard fields ...
    
    name = Column(String(255), nullable=False)
    description = Column(String(4096))
    is_public = Column(Boolean, server_default=text("false"))
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE'))
    
    course = relationship('Course', back_populates='projects')
```

### 2. Create Interface (`src/ctutor_backend/interface/projects.py`)

```python
from ctutor_backend.interface.base import BaseEntityGet, BaseEntityList, EntityInterface, ListQuery
from ctutor_backend.model.project import Project

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False
    course_id: str

class ProjectGet(BaseEntityGet):
    id: str
    name: str
    description: Optional[str]
    is_public: bool
    course_id: str

class ProjectList(BaseEntityList):
    id: str
    name: str
    is_public: bool

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class ProjectQuery(ListQuery):
    name: Optional[str] = None
    is_public: Optional[bool] = None
    course_id: Optional[str] = None

def project_search(db: Session, query, params: ProjectQuery):
    if params.name:
        query = query.filter(Project.name.ilike(f"%{params.name}%"))
    if params.is_public is not None:
        query = query.filter(Project.is_public == params.is_public)
    if params.course_id:
        query = query.filter(Project.course_id == params.course_id)
    return query

class ProjectInterface(EntityInterface):
    create = ProjectCreate
    get = ProjectGet
    list = ProjectList
    update = ProjectUpdate
    query = ProjectQuery
    search = project_search
    endpoint = "projects"
    model = Project
    cache_ttl = 600  # 10 minutes
```

### 3. Generate Migration

```bash
cd src
alembic revision --autogenerate -m "Add project model"
alembic upgrade head
```

### 4. Register API (`src/ctutor_backend/server.py`)

```python
from ctutor_backend.interface.projects import ProjectInterface

# In startup_logic:
CrudRouter(ProjectInterface()).register_routes(app)
```

### 5. Test Your Implementation

```bash
# Start the server
bash api.sh

# Test endpoints
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "course_id": "..."}'
```

## Key Principles

1. **Models are the source of truth** - Define structure in SQLAlchemy
2. **DTOs validate and shape data** - Use Pydantic for validation
3. **APIs are auto-generated** - Use CrudRouter for standard CRUD
4. **Cache aggressively** - Use Redis to improve performance
5. **Handle permissions** - Always check user permissions
6. **Soft delete when possible** - Use archived_at instead of hard deletes
7. **Test everything** - Write tests for models, DTOs, and APIs