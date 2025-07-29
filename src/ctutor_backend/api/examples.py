"""
FastAPI endpoints for Example Library management.
"""

import io
import json
import logging
import yaml
from typing import List, Optional
from uuid import UUID
from sqlalchemy_utils import Ltree
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..interface.permissions import Principal
from ..interface.example import (
    ExampleGet,
    ExampleList,
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
from ..redis_cache import get_redis_client
from ..services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

examples_router = APIRouter(prefix="/examples", tags=["examples"])

# Cache TTL values
CACHE_TTL_LIST = 300  # 5 minutes
CACHE_TTL_GET = 600   # 10 minutes

# Note: Basic CRUD operations are handled by CrudRouter in server.py

# ==============================================================================
# Example Endpoints
# ==============================================================================

@examples_router.get("", response_model=List[ExampleList])
async def list_examples(
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
    redis_client=Depends(get_redis_client),
):
    """List all examples."""
    # Check permissions
    if not permissions.permitted("example", "read"):
        raise ForbiddenException("You don't have permission to view examples")
    
    # Try cache first
    cache_key = "examples:list"
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return [ExampleList.model_validate(e) for e in json.loads(cached_result)]
    
    # Get examples
    examples = db.query(Example).all()
    
    # Cache result
    result = [ExampleList.model_validate(e) for e in examples]
    # Use model_dump with mode='json' to handle UUID serialization
    serializable_data = [r.model_dump(mode='json') for r in result]
    await redis_client.set(cache_key, json.dumps(serializable_data), ttl=CACHE_TTL_LIST)
    
    return result


@examples_router.get("/{example_id}", response_model=ExampleGet)
async def get_example(
    example_id: UUID,
    db: Session = Depends(get_db),
    permissions: Principal = Depends(get_current_permissions),
    redis_client=Depends(get_redis_client),
):
    """Get a specific example."""
    # Check permissions
    if not permissions.permitted("example", "read"):
        raise ForbiddenException("You don't have permission to view examples")
    
    # Try cache first
    cache_key = f"example:{example_id}"
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return ExampleGet.model_validate(json.loads(cached_result))
    
    # Get example
    example = db.query(Example).filter(Example.id == example_id).first()
    
    if not example:
        raise NotFoundException(f"Example {example_id} not found")
    
    # Cache result
    result = ExampleGet.model_validate(example)
    # Use model_dump with mode='json' to handle UUID serialization
    await redis_client.set(cache_key, json.dumps(result.model_dump(mode='json')), ttl=CACHE_TTL_GET)
    
    return result


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
    redis_client = await get_redis_client()
    await redis_client.delete(f"example:{example_id}")
    await redis_client.delete(f"example_versions:{example_id}")
    
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
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return [ExampleVersionList.model_validate(v) for v in json.loads(cached_result)]
    
    # Get versions
    versions = db.query(ExampleVersion).filter(
        ExampleVersion.example_id == example_id
    ).order_by(ExampleVersion.version_number.desc()).all()
    
    # Cache result
    result = [ExampleVersionList.model_validate(v) for v in versions]
    # Use model_dump with mode='json' to handle UUID serialization
    serializable_data = [r.model_dump(mode='json') for r in result]
    await redis_client.set(cache_key, json.dumps(serializable_data), ttl=CACHE_TTL_LIST)
    
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
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return ExampleVersionGet.model_validate(json.loads(cached_result))
    
    # Get version
    version = db.query(ExampleVersion).filter(
        ExampleVersion.id == version_id
    ).first()
    
    if not version:
        raise NotFoundException(f"Version {version_id} not found")
    
    # Cache result
    result = ExampleVersionGet.model_validate(version)
    # Use model_dump with mode='json' to handle UUID serialization
    await redis_client.set(cache_key, json.dumps(result.model_dump(mode='json')), ttl=CACHE_TTL_GET)
    
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
    redis_client = await get_redis_client()
    await redis_client.delete(f"example:{example_id}")
    
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
    redis_client = await get_redis_client()
    await redis_client.delete(f"example:{example_id}")
    
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
    
    # Validate that meta.yaml is included
    if 'meta.yaml' not in request.files:
        raise BadRequestException("meta.yaml file is required")
    
    # Parse meta.yaml to extract example metadata
    try:
        meta_content = request.files['meta.yaml']
        meta_data = yaml.safe_load(meta_content)
    except yaml.YAMLError as e:
        raise BadRequestException(f"Invalid meta.yaml format: {str(e)}")
    
    # Extract metadata from meta.yaml
    title = meta_data.get('title', request.directory.replace('-', ' ').replace('_', ' ').title())
    description = meta_data.get('description', '')
    slug = meta_data.get('slug', request.directory.replace('-', '.').replace('_', '.'))
    
    # Extract tags and other metadata
    tags = []
    if 'tags' in meta_data:
        tags = meta_data['tags'] if isinstance(meta_data['tags'], list) else [meta_data['tags']]
    
    # Determine subject from meta.yaml or directory name
    subject = meta_data.get('language', meta_data.get('subject'))
    if not subject:
        # Try to infer from directory name or file extensions
        for filename in request.files.keys():
            if filename.endswith('.py'):
                subject = 'python'
                break
            elif filename.endswith('.java'):
                subject = 'java'
                break
            elif filename.endswith(('.cpp', '.c', '.h')):
                subject = 'cpp'
                break
    
    # Check if example exists
    example = db.query(Example).filter(
        Example.example_repository_id == request.repository_id,
        Example.directory == request.directory
    ).first()
    
    # Create or update example
    if not example:
        example = Example(
            example_repository_id=request.repository_id,
            directory=request.directory,
            identifier=Ltree(slug),
            title=title,
            description=description,
            subject=subject,
            tags=tags,
            created_by=permissions.user_id,
            updated_by=permissions.user_id,
        )
        db.add(example)
        db.flush()
    else:
        # Update existing example with new metadata
        example.identifier = Ltree(slug)
        example.title = title
        example.description = description
        example.subject = subject
        example.tags = tags
        example.updated_by = permissions.user_id
    
    # Get next version number
    last_version = db.query(ExampleVersion).filter(
        ExampleVersion.example_id == example.id
    ).order_by(ExampleVersion.version_number.desc()).first()
    
    next_version_number = (last_version.version_number + 1) if last_version else 1
    
    # Prepare storage path
    storage_path = f"examples/{repository.id}/{example.directory}/v{next_version_number}"
    
    # Upload files to MinIO
    bucket_name = repository.source_url.split('/')[0]  # First part is bucket
    
    # Get test.yaml content if it exists
    test_yaml_content = request.files.get('test.yaml')
    
    for filename, content in request.files.items():
        object_key = f"{storage_path}/{filename}"
        
        # Create file-like object from content
        file_data = io.BytesIO(content.encode('utf-8'))
        
        # Determine content type
        content_type = "text/yaml" if filename.endswith('.yaml') else "text/plain"
        
        # Upload file
        await storage_service.upload_file(
            file_data=file_data,
            object_key=object_key,
            bucket_name=bucket_name,
            content_type=content_type,
        )
    
    # Create version record
    version = ExampleVersion(
        example_id=example.id,
        version_tag=request.version_tag,
        version_number=next_version_number,
        storage_path=storage_path,
        meta_yaml=meta_content,
        test_yaml=test_yaml_content,
        created_by=permissions.user_id,
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    # Invalidate cache
    redis_client = await get_redis_client()
    await redis_client.delete(f"example:{example.id}")
    await redis_client.delete(f"example_versions:{example.id}")
    await redis_client.delete("examples:list")  # Clear examples list cache
    
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
        if obj.object_name.endswith('/'):
            continue  # Skip directories
        
        # Get relative filename
        filename = obj.object_name.replace(f"{version.storage_path}/", "")
        
        # Skip meta.yaml and test.yaml (returned separately)
        if filename in ["meta.yaml", "test.yaml"]:
            continue
        
        # Download file content
        file_data = await storage_service.download_file(
            bucket_name=bucket_name,
            object_key=obj.object_name,
        )
        
        # file_data is already bytes, no need to read()
        files[filename] = file_data.decode('utf-8')
    
    return ExampleDownloadResponse(
        example_id=example.id,
        version_id=version.id,
        version_tag=version.version_tag,
        files=files,
        meta_yaml=version.meta_yaml,
        test_yaml=version.test_yaml,
    )


