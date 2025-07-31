"""
API endpoints for managing example assignments to course content.
This implements the two-step process:
1. Assign examples to CourseContent (database only)
2. Generate student template (Git operations)
"""
from typing import Annotated, List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from datetime import datetime, timezone
from uuid import UUID

from ..api.auth import get_current_permissions
from ..database import get_db
from ..interface.permissions import Principal
from ..model.course import Course, CourseContent
from ..model.example import Example, ExampleVersion
from ..redis_cache import get_redis_client
from ..tasks.temporal_client import get_temporal_client
from aiocache import BaseCache

# DTOs
from pydantic import BaseModel, Field


class AssignExampleRequest(BaseModel):
    """Request to assign an example to course content."""
    example_id: str = Field(description="UUID of the Example to assign")
    example_version: str = Field(default="latest", description="Version to assign (default: latest)")


class BulkAssignExamplesRequest(BaseModel):
    """Request to assign multiple examples to course contents."""
    assignments: List[Dict[str, str]] = Field(
        description="List of assignments with course_content_id, example_id, and example_version"
    )


class CourseContentExampleResponse(BaseModel):
    """Response for course content with example information."""
    id: str
    path: str
    title: str
    example: Optional[Dict[str, Any]] = None
    deployment_status: str = Field(description="pending_release, released, modified")


class PendingChange(BaseModel):
    """Represents a pending change for template generation."""
    type: str = Field(description="new, update, remove")
    content_id: str
    path: str
    title: str
    example_name: Optional[str] = None
    example_id: Optional[str] = None
    from_version: Optional[str] = None
    to_version: Optional[str] = None


class PendingChangesResponse(BaseModel):
    """Response for pending changes check."""
    total_changes: int
    changes: List[PendingChange]
    last_release: Optional[Dict[str, Any]] = None


class GenerateTemplateRequest(BaseModel):
    """Request to generate student template."""
    commit_message: Optional[str] = Field(
        default=None,
        description="Custom commit message (optional)"
    )


class GenerateTemplateResponse(BaseModel):
    """Response for template generation request."""
    workflow_id: str
    status: str = "started"
    contents_to_process: int


# Create router
course_content_examples_router = APIRouter(
    prefix="/courses",
    tags=["course-content-examples"]
)


@course_content_examples_router.post(
    "/course-contents/{content_id}/assign-example",
    response_model=CourseContentExampleResponse
)
async def assign_example_to_content(
    content_id: str,
    request: AssignExampleRequest,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Assign an example to course content (database only).
    
    This is step 1 of the two-step process. It only updates the database
    to link the example to the course content. No Git operations occur.
    The actual deployment happens when generating the student template.
    """
    # Get course content
    content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CourseContent {content_id} not found"
        )
    
    # Check permissions on the course
    course = db.query(Course).filter(Course.id == content.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated course not found"
        )
    
    # TODO: Add proper permission check
    if not permissions.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this course content"
        )
    
    # Validate example exists
    example = db.query(Example).filter(Example.id == request.example_id).first()
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Example {request.example_id} not found"
        )
    
    # Get the requested version
    if request.example_version == "latest":
        version = db.query(ExampleVersion).filter(
            ExampleVersion.example_id == request.example_id
        ).order_by(ExampleVersion.version_number.desc()).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for example {request.example_id}"
            )
        version_tag = version.version_tag
    else:
        version = db.query(ExampleVersion).filter(
            and_(
                ExampleVersion.example_id == request.example_id,
                ExampleVersion.version_tag == request.example_version
            )
        ).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {request.example_version} not found for example"
            )
        version_tag = request.example_version
    
    # Update course content
    content.example_id = UUID(request.example_id)
    content.example_version = version_tag
    content.deployment_status = "pending_release"
    
    db.commit()
    db.refresh(content)
    
    # Clear cache
    if cache:
        await cache.delete(f"course:{content.course_id}:contents")
    
    # Return updated content with example info
    return CourseContentExampleResponse(
        id=str(content.id),
        path=str(content.path),
        title=content.title,
        example={
            "id": str(example.id),
            "name": example.title,
            "version": version_tag,
            "latest_version": version.version_tag if version else version_tag,
            "has_update": False
        },
        deployment_status=content.deployment_status
    )


@course_content_examples_router.post(
    "/courses/{course_id}/assign-examples",
    response_model=Dict[str, Any]
)
async def bulk_assign_examples(
    course_id: str,
    request: BulkAssignExamplesRequest,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Assign multiple examples to course contents in bulk (database only).
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    # TODO: Add proper permission check
    if not permissions.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this course"
        )
    
    assigned = 0
    updated = 0
    failed = 0
    
    for assignment in request.assignments:
        try:
            content_id = assignment.get("course_content_id")
            example_id = assignment.get("example_id")
            example_version = assignment.get("example_version", "latest")
            
            # Get course content
            content = db.query(CourseContent).filter(
                and_(
                    CourseContent.id == content_id,
                    CourseContent.course_id == course_id
                )
            ).first()
            
            if not content:
                failed += 1
                continue
            
            # Check if already has an example
            is_update = content.example_id is not None
            
            # Assign example
            content.example_id = UUID(example_id) if example_id else None
            content.example_version = example_version
            content.deployment_status = "pending_release"
            
            if is_update:
                updated += 1
            else:
                assigned += 1
                
        except Exception as e:
            failed += 1
            continue
    
    db.commit()
    
    # Clear cache
    if cache:
        await cache.delete(f"course:{course_id}:contents")
    
    return {
        "assigned": assigned,
        "updated": updated,
        "failed": failed
    }


@course_content_examples_router.delete(
    "/course-contents/{content_id}/example"
)
async def remove_example_assignment(
    content_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Remove example assignment from course content.
    
    This only clears the database assignment. The content will be
    removed from the student template on the next generation.
    """
    # Get course content
    content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CourseContent {content_id} not found"
        )
    
    # TODO: Add proper permission check
    if not permissions.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this course content"
        )
    
    # Clear example assignment
    content.example_id = None
    content.example_version = None
    content.deployment_status = "pending_release"
    
    db.commit()
    
    # Clear cache
    if cache:
        await cache.delete(f"course:{content.course_id}:contents")
    
    return {"status": "removed"}


@course_content_examples_router.get(
    "/courses/{course_id}/pending-changes",
    response_model=PendingChangesResponse
)
async def get_pending_changes(
    course_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """
    Get pending changes that will be applied in the next template generation.
    
    Compares current assignments with the last release to show what will change.
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    # Get all course contents
    contents = db.query(CourseContent).filter(
        CourseContent.course_id == course_id
    ).all()
    
    changes = []
    
    for content in contents:
        # Determine change type based on deployment status
        if content.deployment_status == "pending_release":
            if content.example_id:
                # Check if it's new or update
                if content.deployed_at is None:
                    change_type = "new"
                else:
                    change_type = "update"
                
                # Get example details
                example = db.query(Example).filter(
                    Example.id == content.example_id
                ).first()
                
                change = PendingChange(
                    type=change_type,
                    content_id=str(content.id),
                    path=str(content.path),
                    title=content.title,
                    example_name=example.title if example else None,
                    example_id=str(content.example_id),
                    to_version=content.example_version
                )
                
                # For updates, try to get the from_version
                # (would need to track this properly in production)
                if change_type == "update":
                    change.from_version = "unknown"  # TODO: Track previous version
                
                changes.append(change)
            else:
                # Example was removed
                if content.deployed_at is not None:
                    changes.append(PendingChange(
                        type="remove",
                        content_id=str(content.id),
                        path=str(content.path),
                        title=content.title
                    ))
    
    # Get last release info from course properties
    last_release = None
    if course.properties and "last_template_release" in course.properties:
        last_release = course.properties["last_template_release"]
    
    return PendingChangesResponse(
        total_changes=len(changes),
        changes=changes,
        last_release=last_release
    )


@course_content_examples_router.post(
    "/courses/{course_id}/generate-student-template",
    response_model=GenerateTemplateResponse
)
async def generate_student_template(
    course_id: str,
    request: GenerateTemplateRequest,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """
    Generate student template from assigned examples (Git operations).
    
    This is step 2 of the two-step process. It triggers a Temporal workflow
    that will:
    1. Download examples from MinIO based on CourseContent assignments
    2. Process them according to meta.yaml rules
    3. Generate the student-template repository
    4. Commit and push the changes
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    # TODO: Add proper permission check
    if not permissions.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate template for this course"
        )
    
    # Check if student-template repository URL exists
    if not course.properties or "gitlab" not in course.properties:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course missing GitLab configuration"
        )
    
    gitlab_props = course.properties.get("gitlab", {})
    if "student_template_url" not in gitlab_props:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course missing student-template repository URL"
        )
    
    # Count contents to process
    contents_with_examples = db.query(func.count(CourseContent.id)).filter(
        and_(
            CourseContent.course_id == course_id,
            CourseContent.example_id.isnot(None)
        )
    ).scalar()
    
    # Prepare workflow parameters
    workflow_params = {
        "course_id": course_id,
        "commit_message": request.commit_message or f"Update student template - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    }
    
    # Start Temporal workflow
    temporal_client = await get_temporal_client()
    workflow_id = f"generate-template-{course_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Import the workflow here to avoid circular imports
    from ..tasks.temporal_student_template_v2 import GenerateStudentTemplateWorkflowV2
    
    handle = await temporal_client.start_workflow(
        GenerateStudentTemplateWorkflowV2.run,
        workflow_params,
        id=workflow_id,
        task_queue="computor-tasks"
    )
    
    # Update all pending_release contents to deploying
    db.query(CourseContent).filter(
        and_(
            CourseContent.course_id == course_id,
            CourseContent.deployment_status == "pending_release"
        )
    ).update({"deployment_status": "deploying"})
    
    db.commit()
    
    return GenerateTemplateResponse(
        workflow_id=workflow_id,
        status="started",
        contents_to_process=contents_with_examples or 0
    )


@course_content_examples_router.get(
    "/courses/{course_id}/available-examples",
    response_model=Dict[str, Any]
)
async def get_available_examples(
    course_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None,
    search: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get available examples from the Example Library for a course.
    
    Returns examples that can be deployed to course content,
    with filtering by search query, category, and language.
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    # Check cache first
    cache_key = f"course:{course_id}:available-examples:{search}:{category}:{language}:{limit}:{offset}"
    if cache:
        cached = await cache.get(cache_key)
        if cached:
            return cached
    
    # Build query for examples
    query = db.query(Example).filter(
        Example.archived_at.is_(None)
    )
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Example.title.ilike(search_pattern),
                Example.description.ilike(search_pattern),
                Example.properties['tags'].astext.ilike(search_pattern)
            )
        )
    
    # Apply category filter
    if category:
        query = query.filter(
            Example.properties['category'].astext == category
        )
    
    # Apply language filter  
    if language:
        query = query.filter(
            Example.properties['language'].astext == language
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    examples = query.offset(offset).limit(limit).all()
    
    # Get unique categories and languages for filters
    all_examples = db.query(Example).filter(Example.archived_at.is_(None)).all()
    categories = set()
    languages = set()
    
    for ex in all_examples:
        if ex.properties:
            if 'category' in ex.properties:
                categories.add(ex.properties['category'])
            if 'language' in ex.properties:
                languages.add(ex.properties['language'])
    
    # Format response
    example_list = []
    for example in examples:
        # Get latest version
        latest_version = db.query(ExampleVersion).filter(
            ExampleVersion.example_id == example.id
        ).order_by(ExampleVersion.version_number.desc()).first()
        
        example_data = {
            "id": str(example.id),
            "title": example.title,
            "description": example.description,
            "repository_id": str(example.example_repository_id),
            "latest_version": latest_version.version_tag if latest_version else None
        }
        
        # Add properties if they exist
        if example.properties:
            if 'category' in example.properties:
                example_data['category'] = example.properties['category']
            if 'language' in example.properties:
                example_data['language'] = example.properties['language']
            if 'tags' in example.properties:
                example_data['tags'] = example.properties.get('tags', [])
        
        example_list.append(example_data)
    
    result = {
        "examples": example_list,
        "total": total,
        "filters": {
            "categories": sorted(list(categories)),
            "languages": sorted(list(languages))
        }
    }
    
    # Cache the result
    if cache:
        await cache.set(cache_key, result, ttl=300)  # Cache for 5 minutes
    
    return result


@course_content_examples_router.get(
    "/courses/{course_id}/examples/{example_id}/deployment-preview",
    response_model=Dict[str, Any]
)
async def get_deployment_preview(
    course_id: str,
    example_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    version: str = "latest",
    target_path: str = None
):
    """
    Get a preview of what will happen when deploying an example.
    
    Shows files, dependencies, and potential conflicts.
    """
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    # Get example
    example = db.query(Example).filter(Example.id == example_id).first()
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Example {example_id} not found"
        )
    
    # Get version
    if version == "latest":
        version_obj = db.query(ExampleVersion).filter(
            ExampleVersion.example_id == example_id
        ).order_by(ExampleVersion.version_number.desc()).first()
    else:
        version_obj = db.query(ExampleVersion).filter(
            and_(
                ExampleVersion.example_id == example_id,
                ExampleVersion.version_tag == version
            )
        ).first()
    
    if not version_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for example"
        )
    
    # Check for conflicts if target_path provided
    conflicts = []
    if target_path:
        # Check if content already has a different example
        existing_content = db.query(CourseContent).filter(
            and_(
                CourseContent.course_id == course_id,
                CourseContent.path == target_path
            )
        ).first()
        
        if existing_content and existing_content.example_id:
            if str(existing_content.example_id) != example_id:
                existing_example = db.query(Example).filter(
                    Example.id == existing_content.example_id
                ).first()
                conflicts.append({
                    "type": "existing_example",
                    "path": target_path,
                    "current_example_id": str(existing_content.example_id),
                    "current_example_title": existing_example.title if existing_example else "Unknown",
                    "current_example_version": existing_content.example_version
                })
    
    # Get dependencies
    dependencies = []
    deps = db.query(ExampleDependency).filter(
        ExampleDependency.example_id == example_id
    ).all()
    
    for dep in deps:
        dep_example = db.query(Example).filter(
            Example.id == dep.dependency_example_id
        ).first()
        if dep_example:
            dependencies.append({
                "example_id": str(dep.dependency_example_id),
                "title": dep_example.title,
                "required": dep.required
            })
    
    # Estimate file structure (in real implementation, would check MinIO)
    file_structure = {
        "files": [
            "meta.yaml",
            "README.md",
            # Add more based on example properties
        ],
        "size_mb": 0.1  # Placeholder
    }
    
    # Add files based on properties
    if version_obj.properties:
        props = version_obj.properties.get('properties', {})
        if 'studentTemplates' in props:
            file_structure['files'].extend(props['studentTemplates'])
        if 'testFiles' in props:
            file_structure['files'].extend(props['testFiles'])
        if 'additionalFiles' in props:
            file_structure['files'].extend(props['additionalFiles'])
    
    return {
        "example": {
            "id": str(example.id),
            "title": example.title,
            "description": example.description,
            "category": example.properties.get('category') if example.properties else None,
            "language": example.properties.get('language') if example.properties else None
        },
        "version": {
            "id": str(version_obj.id),
            "version_tag": version_obj.version_tag,
            "created_at": version_obj.created_at.isoformat() if version_obj.created_at else None
        },
        "dependencies": dependencies,
        "conflicts": conflicts,
        "file_structure": file_structure
    }


@course_content_examples_router.get(
    "/courses/{course_id}/contents-with-examples",
    response_model=Dict[str, Any]
)
async def get_course_contents_with_examples(
    course_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Get all course contents with their example assignment status.
    
    Shows which contents have examples assigned and their deployment status.
    """
    # Check cache first
    cache_key = f"course:{course_id}:contents-with-examples"
    if cache:
        cached = await cache.get(cache_key)
        if cached:
            return cached
    
    # Get all course contents
    contents = db.query(CourseContent).filter(
        CourseContent.course_id == course_id
    ).order_by(CourseContent.path).all()
    
    contents_list = []
    for content in contents:
        content_data = {
            "id": str(content.id),
            "path": str(content.path),
            "title": content.title,
            "example": None
        }
        
        if content.example_id:
            # Get example details
            example = db.query(Example).filter(
                Example.id == content.example_id
            ).first()
            
            if example:
                # Check for updates
                latest_version = None
                has_update = False
                
                if content.example_version != "latest":
                    latest = db.query(ExampleVersion).filter(
                        ExampleVersion.example_id == content.example_id
                    ).order_by(ExampleVersion.version_number.desc()).first()
                    
                    if latest:
                        latest_version = latest.version_tag
                        has_update = latest.version_tag != content.example_version
                
                content_data["example"] = {
                    "id": str(example.id),
                    "name": example.title,
                    "version": content.example_version,
                    "latest_version": latest_version,
                    "has_update": has_update,
                    "release_status": content.deployment_status
                }
        
        contents_list.append(content_data)
    
    result = {"contents": contents_list}
    
    # Cache the result
    if cache:
        await cache.set(cache_key, result, ttl=300)  # Cache for 5 minutes
    
    return result