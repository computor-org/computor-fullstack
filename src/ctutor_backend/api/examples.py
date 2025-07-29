"""
FastAPI endpoints for Example Library management.
"""

import io
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..interface.permissions import Principal
from ..interface.example import (
    ExampleVersionCreate,
    ExampleVersionGet,
    ExampleVersionList,
    ExampleDependencyCreate,
    ExampleDependencyGet,
    ExampleUploadRequest,
    ExampleDownloadResponse,
)
from ..model.example import ExampleRepository, Example, ExampleVersion, ExampleDependency
from ..api.auth import get_current_permissions
from ..api.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    NotImplementedException,
)
from ..redis_cache import get_redis_client, get_cached, set_cached, delete_cached
from ..services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

examples_router = APIRouter(prefix="/examples", tags=["examples"])

# Cache TTL values
CACHE_TTL_LIST = 300  # 5 minutes
CACHE_TTL_GET = 600   # 10 minutes

# Note: Basic CRUD operations are handled by CrudRouter in server.py


# ==============================================================================
# Example Version Endpoints
# ==============================================================================

@examples_router.post("/{example_id}/versions", response_model=ExampleVersionGet)
async def create_version(
    example_id: UUID,
    version: ExampleVersionCreate,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
):
    """Create a new version for an example."""
    # Check permissions
    if not permissions.permitted("example", "create"):
        raise ForbiddenException("You don't have permission to create versions")
    
    # Verify example exists
    example = db.query(Example).filter(Example.id == example_id).first()
    if not example:
        raise NotFoundException(f"Example {example_id} not found")
    
    # Ensure example_id matches
    if version.example_id != example_id:
        raise BadRequestException("Example ID mismatch")
    
    # Create version
    db_version = ExampleVersion(
        **version.model_dump(),
        created_by=permissions.user_id,
    )
    
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    
    # Invalidate cache
    await delete_cached(f"example:{example_id}")
    await delete_cached(f"example_versions:{example_id}")
    
    return db_version


@examples_router.get("/{example_id}/versions", response_model=List[ExampleVersionList])
async def list_versions(
    example_id: UUID,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
    redis_client=Depends(get_redis_client),
):
    """List all versions of an example."""
    # Check permissions
    if not permissions.permitted("example", "read"):
        raise ForbiddenException("You don't have permission to view versions")
    
    # Try cache first
    cache_key = f"example_versions:{example_id}"
    cached_result = await get_cached(redis_client, cache_key)
    if cached_result:
        return cached_result
    
    # Get versions
    versions = db.query(ExampleVersion).filter(
        ExampleVersion.example_id == example_id
    ).order_by(ExampleVersion.version_number.desc()).all()
    
    # Cache result
    result = [ExampleVersionList.model_validate(v) for v in versions]
    await set_cached(redis_client, cache_key, result, CACHE_TTL_LIST)
    
    return result


@examples_router.get("/versions/{version_id}", response_model=ExampleVersionGet)
async def get_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
    redis_client=Depends(get_redis_client),
):
    """Get a specific version."""
    # Check permissions
    if not permissions.permitted("example", "read"):
        raise ForbiddenException("You don't have permission to view versions")
    
    # Try cache first
    cache_key = f"example_version:{version_id}"
    cached_result = await get_cached(redis_client, cache_key)
    if cached_result:
        return cached_result
    
    # Get version
    version = db.query(ExampleVersion).filter(
        ExampleVersion.id == version_id
    ).first()
    
    if not version:
        raise NotFoundException(f"Version {version_id} not found")
    
    # Cache result
    result = ExampleVersionGet.model_validate(version)
    await set_cached(redis_client, cache_key, result, CACHE_TTL_GET)
    
    return result


# ==============================================================================
# Example Dependencies Endpoints
# ==============================================================================

@examples_router.post("/{example_id}/dependencies", response_model=ExampleDependencyGet)
async def add_dependency(
    example_id: UUID,
    dependency: ExampleDependencyCreate,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
):
    """Add a dependency to an example."""
    # Check permissions
    if not permissions.permitted("example", "update"):
        raise ForbiddenException("You don't have permission to modify dependencies")
    
    # Verify example exists
    example = db.query(Example).filter(Example.id == example_id).first()
    if not example:
        raise NotFoundException(f"Example {example_id} not found")
    
    # Verify dependency exists
    depends_on = db.query(Example).filter(Example.id == dependency.depends_id).first()
    if not depends_on:
        raise NotFoundException(f"Dependency example {dependency.depends_id} not found")
    
    # Ensure example_id matches
    if dependency.example_id != example_id:
        raise BadRequestException("Example ID mismatch")
    
    # Check for circular dependencies
    if dependency.depends_id == example_id:
        raise BadRequestException("An example cannot depend on itself")
    
    # Create dependency
    db_dependency = ExampleDependency(**dependency.model_dump())
    
    db.add(db_dependency)
    db.commit()
    db.refresh(db_dependency)
    
    # Invalidate cache
    await delete_cached(f"example:{example_id}")
    
    return db_dependency


@examples_router.get("/{example_id}/dependencies", response_model=List[ExampleDependencyGet])
async def list_dependencies(
    example_id: UUID,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
):
    """List all dependencies of an example."""
    # Check permissions
    if not permissions.permitted("example", "read"):
        raise ForbiddenException("You don't have permission to view dependencies")
    
    # Get dependencies
    dependencies = db.query(ExampleDependency).filter(
        ExampleDependency.example_id == example_id
    ).all()
    
    return [ExampleDependencyGet.model_validate(d) for d in dependencies]


@examples_router.delete("/dependencies/{dependency_id}")
async def remove_dependency(
    dependency_id: UUID,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
):
    """Remove a dependency."""
    # Check permissions
    if not permissions.permitted("example", "update"):
        raise ForbiddenException("You don't have permission to modify dependencies")
    
    # Get dependency
    dependency = db.query(ExampleDependency).filter(
        ExampleDependency.id == dependency_id
    ).first()
    
    if not dependency:
        raise NotFoundException(f"Dependency {dependency_id} not found")
    
    example_id = dependency.example_id
    
    # Delete dependency
    db.delete(dependency)
    db.commit()
    
    # Invalidate cache
    await delete_cached(f"example:{example_id}")
    
    return {"message": "Dependency removed successfully"}


# ==============================================================================
# Upload/Download Endpoints
# ==============================================================================

@examples_router.post("/upload", response_model=ExampleVersionGet)
async def upload_example(
    request: ExampleUploadRequest,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
    storage_service=Depends(get_storage_service),
):
    """Upload an example to storage (MinIO)."""
    # Check permissions
    if not permissions.permitted("example", "create"):
        raise ForbiddenException("You don't have permission to upload examples")
    
    # Verify repository exists and is MinIO type
    repository = db.query(ExampleRepository).filter(
        ExampleRepository.id == request.repository_id
    ).first()
    
    if not repository:
        raise NotFoundException(f"Repository {request.repository_id} not found")
    
    if repository.source_type == "git":
        raise NotImplementedException("Git upload not implemented - use git push instead")
    
    if repository.source_type not in ["minio", "s3"]:
        raise BadRequestException(f"Upload not supported for {repository.source_type} repositories")
    
    # Check if example exists
    example = db.query(Example).filter(
        Example.example_repository_id == request.repository_id,
        Example.directory == request.directory
    ).first()
    
    # Create example if it doesn't exist
    if not example:
        example = Example(
            example_repository_id=request.repository_id,
            directory=request.directory,
            title=request.directory,  # Default title
            tags=[],
            created_by=permissions.user_id,
            updated_by=permissions.user_id,
        )
        db.add(example)
        db.flush()
    
    # Get next version number
    last_version = db.query(ExampleVersion).filter(
        ExampleVersion.example_id == example.id
    ).order_by(ExampleVersion.version_number.desc()).first()
    
    next_version_number = (last_version.version_number + 1) if last_version else 1
    
    # Prepare storage path
    storage_path = f"examples/{repository.id}/{example.directory}/v{next_version_number}"
    
    # Upload files to MinIO
    bucket_name = repository.source_url.split('/')[0]  # First part is bucket
    
    for filename, content in request.files.items():
        object_key = f"{storage_path}/{filename}"
        
        # Create file-like object from content
        file_data = io.BytesIO(content.encode('utf-8'))
        
        # Upload file
        await storage_service.upload_file(
            file_data=file_data,
            object_key=object_key,
            bucket_name=bucket_name,
            content_type="text/plain",
        )
    
    # Upload meta.yaml
    meta_data = io.BytesIO(request.meta_yaml.encode('utf-8'))
    await storage_service.upload_file(
        file_data=meta_data,
        object_key=f"{storage_path}/meta.yaml",
        bucket_name=bucket_name,
        content_type="text/yaml",
    )
    
    # Upload test.yaml if provided
    if request.test_yaml:
        test_data = io.BytesIO(request.test_yaml.encode('utf-8'))
        await storage_service.upload_file(
            file_data=test_data,
            object_key=f"{storage_path}/test.yaml",
            bucket_name=bucket_name,
            content_type="text/yaml",
        )
    
    # Create version record
    version = ExampleVersion(
        example_id=example.id,
        version_tag=request.version_tag,
        version_number=next_version_number,
        storage_path=storage_path,
        meta_yaml=request.meta_yaml,
        test_yaml=request.test_yaml,
        created_by=permissions.user_id,
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    # Invalidate cache
    await delete_cached(f"example:{example.id}")
    await delete_cached(f"example_versions:{example.id}")
    await delete_cached("examples:*")
    
    return version


@examples_router.get("/download/{version_id}", response_model=ExampleDownloadResponse)
async def download_example(
    version_id: UUID,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
    storage_service=Depends(get_storage_service),
):
    """Download an example version from storage."""
    # Check permissions
    if not permissions.permitted("example", "read"):
        raise ForbiddenException("You don't have permission to download examples")
    
    # Get version
    version = db.query(ExampleVersion).filter(
        ExampleVersion.id == version_id
    ).first()
    
    if not version:
        raise NotFoundException(f"Version {version_id} not found")
    
    # Get example and repository
    example = version.example
    repository = example.repository
    
    if repository.source_type == "git":
        raise NotImplementedException("Git download not implemented - use git clone instead")
    
    if repository.source_type not in ["minio", "s3"]:
        raise BadRequestException(f"Download not supported for {repository.source_type} repositories")
    
    # Get files from MinIO
    bucket_name = repository.source_url.split('/')[0]
    
    # List all objects in the version path
    objects = await storage_service.list_objects(
        bucket_name=bucket_name,
        prefix=version.storage_path,
    )
    
    # Download files
    files = {}
    for obj in objects:
        if obj.object_key.endswith('/'):
            continue  # Skip directories
        
        # Get relative filename
        filename = obj.object_key.replace(f"{version.storage_path}/", "")
        
        # Skip meta.yaml and test.yaml (returned separately)
        if filename in ["meta.yaml", "test.yaml"]:
            continue
        
        # Download file content
        file_data = await storage_service.download_file(
            bucket_name=bucket_name,
            object_key=obj.object_key,
        )
        
        # Read content from the stream
        content = file_data.read()
        files[filename] = content.decode('utf-8')
    
    return ExampleDownloadResponse(
        example_id=example.id,
        version_id=version.id,
        version_tag=version.version_tag,
        files=files,
        meta_yaml=version.meta_yaml,
        test_yaml=version.test_yaml,
    )


