"""
API endpoints for deploying examples from Example Library to courses.
"""
from typing import Annotated, List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import asyncio
from datetime import datetime, timezone
import yaml

from ..api.auth import get_current_permissions
from ..database import get_db
from ..interface.permissions import Principal
from ..model.course import Course, CourseContent
from ..model.example import Example, ExampleVersion, ExampleDependency
from ..redis_cache import get_redis_client
from ..tasks.temporal_client import get_temporal_client
from ..tasks.temporal_example_deployment import DeployExamplesToCourseWorkflow
from aiocache import BaseCache

# DTOs for API
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class ExampleDeploymentRequest(BaseModel):
    """Single example deployment request."""
    course_content_id: str = Field(description="UUID of the CourseContent to deploy to")
    example_id: str = Field(description="UUID of the Example to deploy")
    example_version: str = Field(default="latest", description="Version to deploy (default: latest)")
    target_path: str = Field(description="Target path in repository (e.g., 'week1.assignment1')")
    
    @field_validator('target_path')
    @classmethod
    def validate_target_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Target path cannot be empty')
        # Validate ltree format
        if not all(part.replace('_', '').replace('-', '').isalnum() for part in v.split('.')):
            raise ValueError('Target path must be in ltree format (e.g., "week1.assignment1")')
        return v.strip().lower()


class DeployExamplesRequest(BaseModel):
    """Request to deploy multiple examples to a course."""
    deployments: List[ExampleDeploymentRequest] = Field(
        description="List of examples to deploy",
        min_length=1
    )


class DeploymentStatusResponse(BaseModel):
    """Response for deployment status check."""
    status: str = Field(description="Workflow status: running, completed, failed")
    progress: Optional[Dict[str, Any]] = Field(default=None, description="Progress information")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Deployment results")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ExampleDeploymentResponse(BaseModel):
    """Response for example deployment request."""
    workflow_id: str = Field(description="Temporal workflow ID for tracking")
    status: str = Field(description="Initial status")
    deployments_requested: int = Field(description="Number of deployments requested")


class ExampleUpdateRequest(BaseModel):
    """Request to update example version for course content."""
    example_version: str = Field(description="New version to deploy")
    update_strategy: str = Field(default="overwrite", description="Update strategy: overwrite, merge, skip")
    
    @field_validator('update_strategy')
    @classmethod
    def validate_update_strategy(cls, v):
        if v not in ['overwrite', 'merge', 'skip']:
            raise ValueError('Update strategy must be one of: overwrite, merge, skip')
        return v


class BulkDeploymentStatusResponse(BaseModel):
    """Response for bulk deployment status."""
    total_examples: int = Field(description="Total number of examples deployed")
    deployed: int = Field(description="Successfully deployed examples")
    pending: int = Field(description="Examples pending deployment")
    failed: int = Field(description="Failed deployments")
    updates_available: int = Field(description="Examples with updates available")
    deployments: List[Dict[str, Any]] = Field(description="Detailed deployment information")


class ExampleForCourseResponse(BaseModel):
    """Response for browsing examples available for a course."""
    examples: List[Dict[str, Any]] = Field(description="List of available examples")
    total: int = Field(description="Total number of examples")
    filters: Dict[str, List[str]] = Field(description="Available filters")


class ExampleDeploymentPreviewResponse(BaseModel):
    """Response for deployment preview."""
    example: Dict[str, Any] = Field(description="Example details")
    version: Optional[Dict[str, Any]] = Field(description="Version details")
    dependencies: List[Dict[str, Any]] = Field(description="Required dependencies")
    conflicts: List[Dict[str, Any]] = Field(description="Potential conflicts")
    file_structure: Dict[str, Any] = Field(description="Files to be deployed")


# Create router
example_deployment_router = APIRouter(
    prefix="/api/v1/courses",
    tags=["example-deployment"]
)


@example_deployment_router.post(
    "/{course_id}/deploy-examples",
    response_model=ExampleDeploymentResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def deploy_examples_to_course(
    course_id: str,
    request: DeployExamplesRequest,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """
    Deploy examples from Example Library to course repository.
    
    This endpoint initiates a Temporal workflow to:
    1. Download examples from MinIO storage
    2. Deploy them to the course's assignments repository
    3. Handle dependencies between examples
    4. Commit and push changes to GitLab
    5. Update CourseContent records with deployment status
    
    Returns a workflow ID for tracking the deployment progress.
    """
    # Check if user has permission to modify course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    # TODO: Add proper permission check
    # For now, check if user is authenticated
    if not permissions.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deploy examples to this course"
        )
    
    # Validate all course content IDs belong to this course
    course_content_ids = [d.course_content_id for d in request.deployments]
    course_contents = db.query(CourseContent).filter(
        and_(
            CourseContent.id.in_(course_content_ids),
            CourseContent.course_id == course_id
        )
    ).all()
    
    if len(course_contents) != len(course_content_ids):
        found_ids = {str(cc.id) for cc in course_contents}
        missing_ids = set(course_content_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CourseContent IDs not found in course: {missing_ids}"
        )
    
    # Validate all example IDs exist
    example_ids = [d.example_id for d in request.deployments]
    examples = db.query(Example).filter(Example.id.in_(example_ids)).all()
    
    if len(examples) != len(set(example_ids)):
        found_ids = {str(e.id) for e in examples}
        missing_ids = set(example_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Example IDs not found: {missing_ids}"
        )
    
    # Prepare workflow parameters
    workflow_params = {
        "course_id": course_id,
        "deployments": [
            {
                "course_content_id": d.course_content_id,
                "example_id": d.example_id,
                "example_version": d.example_version,
                "target_path": d.target_path
            }
            for d in request.deployments
        ]
    }
    
    # Start Temporal workflow
    temporal_client = await get_temporal_client()
    workflow_id = f"deploy-examples-{course_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    handle = await temporal_client.start_workflow(
        DeployExamplesToCourseWorkflow.run,
        workflow_params,
        id=workflow_id,
        task_queue="computor-tasks"
    )
    
    # Update CourseContent deployment status to "deploying"
    for cc_id in course_content_ids:
        course_content = next(cc for cc in course_contents if str(cc.id) == cc_id)
        course_content.deployment_status = "deploying"
        course_content.deployment_task_id = workflow_id
    
    db.commit()
    
    return ExampleDeploymentResponse(
        workflow_id=workflow_id,
        status="started",
        deployments_requested=len(request.deployments)
    )


@example_deployment_router.get(
    "/{course_id}/deployment-status/{workflow_id}",
    response_model=DeploymentStatusResponse
)
async def get_deployment_status(
    course_id: str,
    workflow_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """
    Check the status of an example deployment workflow.
    
    Returns the current status and progress of the deployment.
    """
    # Verify course exists and user has access
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    # Get workflow status from Temporal
    temporal_client = await get_temporal_client()
    
    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Try to get result if completed
        try:
            result = await asyncio.wait_for(handle.result(), timeout=0.1)
            return DeploymentStatusResponse(
                status="completed",
                results=result.get("deployment_results", []),
                progress={
                    "completed": result.get("deployed_count", 0),
                    "failed": result.get("failed_count", 0),
                    "total": result.get("deployed_count", 0) + result.get("failed_count", 0)
                }
            )
        except asyncio.TimeoutError:
            # Still running
            # TODO: Get progress from workflow queries
            return DeploymentStatusResponse(
                status="running",
                progress={"message": "Deployment in progress..."}
            )
        
    except Exception as e:
        # Check if workflow exists in database
        course_content = db.query(CourseContent).filter(
            CourseContent.deployment_task_id == workflow_id
        ).first()
        
        if not course_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return DeploymentStatusResponse(
            status="failed",
            error=str(e)
        )


@example_deployment_router.patch(
    "/{course_id}/content/{content_id}/example",
    response_model=Dict[str, Any]
)
async def update_example_version(
    course_id: str,
    content_id: str,
    request: ExampleUpdateRequest,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """
    Update the example version for a course content item.
    
    This allows updating to a newer version of an already deployed example.
    """
    # Get course content
    course_content = db.query(CourseContent).filter(
        and_(
            CourseContent.id == content_id,
            CourseContent.course_id == course_id
        )
    ).first()
    
    if not course_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CourseContent {content_id} not found in course {course_id}"
        )
    
    if not course_content.example_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CourseContent does not have an example deployed"
        )
    
    # Check if the requested version exists
    if request.example_version != "latest":
        version = db.query(ExampleVersion).filter(
            and_(
                ExampleVersion.example_id == course_content.example_id,
                ExampleVersion.version_tag == request.example_version
            )
        ).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {request.example_version} not found for example"
            )
    
    # Handle different update strategies
    if request.update_strategy == "skip":
        return {"message": "Update skipped as requested"}
    
    # For overwrite and merge, trigger a new deployment
    deployment_request = DeployExamplesRequest(
        deployments=[
            ExampleDeploymentRequest(
                course_content_id=content_id,
                example_id=str(course_content.example_id),
                example_version=request.example_version,
                target_path=str(course_content.path)
            )
        ]
    )
    
    # Mark as customized if using merge strategy
    if request.update_strategy == "merge":
        course_content.is_customized = True
        course_content.last_customized_at = datetime.now(timezone.utc)
        db.commit()
    
    # Trigger deployment
    result = await deploy_examples_to_course(
        course_id, deployment_request, permissions, db
    )
    
    return {
        "workflow_id": result.workflow_id,
        "status": "update_started",
        "update_strategy": request.update_strategy
    }


@example_deployment_router.get(
    "/{course_id}/examples/deployment-status",
    response_model=BulkDeploymentStatusResponse
)
async def get_bulk_deployment_status(
    course_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Get deployment status for all examples in a course.
    
    Returns summary statistics and detailed information about each deployment.
    """
    # Check cache first
    cache_key = f"course:{course_id}:deployment-status:{permissions.user_id}"
    if cache:
        cached = await cache.get(cache_key)
        if cached:
            return BulkDeploymentStatusResponse.model_validate_json(cached)
    
    # Get all course contents with examples
    course_contents = db.query(CourseContent).filter(
        and_(
            CourseContent.course_id == course_id,
            CourseContent.example_id.isnot(None)
        )
    ).all()
    
    deployments = []
    deployed = 0
    pending = 0
    failed = 0
    updates_available = 0
    
    for cc in course_contents:
        deployment_info = {
            "course_content_id": str(cc.id),
            "path": str(cc.path),
            "title": cc.title,
            "example_id": str(cc.example_id),
            "example_version": cc.example_version,
            "deployment_status": cc.deployment_status,
            "deployed_at": cc.deployed_at.isoformat() if cc.deployed_at else None,
            "is_customized": cc.is_customized
        }
        
        # Count statuses
        if cc.deployment_status == "deployed":
            deployed += 1
            
            # Check for updates
            if cc.example_version != "latest":
                # Get latest version
                latest_version = db.query(ExampleVersion).filter(
                    ExampleVersion.example_id == cc.example_id
                ).order_by(ExampleVersion.version_number.desc()).first()
                
                if latest_version and latest_version.version_tag != cc.example_version:
                    updates_available += 1
                    deployment_info["update_available"] = True
                    deployment_info["latest_version"] = latest_version.version_tag
                    
        elif cc.deployment_status == "pending" or cc.deployment_status == "deploying":
            pending += 1
        elif cc.deployment_status == "failed":
            failed += 1
        
        deployments.append(deployment_info)
    
    result = BulkDeploymentStatusResponse(
        total_examples=len(course_contents),
        deployed=deployed,
        pending=pending,
        failed=failed,
        updates_available=updates_available,
        deployments=deployments
    )
    
    # Cache the result
    if cache:
        await cache.set(
            cache_key,
            result.model_dump_json(),
            ttl=60  # Cache for 1 minute
        )
    
    return result


# Additional endpoints for Example Library integration

@example_deployment_router.get(
    "/{course_id}/available-examples",
    response_model=ExampleForCourseResponse
)
async def get_examples_for_course(
    course_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    language: Optional[str] = Query(None, description="Filter by programming language")
):
    """
    Browse examples available for deployment to a course.
    
    Returns filtered and searchable list of examples from the Example Library.
    """
    # Base query
    query = db.query(Example)
    
    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Example.title.ilike(search_pattern),
                Example.description.ilike(search_pattern)
            )
        )
    
    if category:
        query = query.filter(Example.category == category)
    
    if language:
        query = query.filter(Example.subject == language)
    
    # TODO: Filter by content type compatibility
    
    # Get results
    examples = query.all()
    
    # Get available filters
    categories = db.query(Example.category).distinct().filter(
        Example.category.isnot(None)
    ).all()
    languages = db.query(Example.subject).distinct().filter(
        Example.subject.isnot(None)
    ).all()
    
    # Format response
    example_list = []
    for example in examples:
        # Get latest version
        latest_version = db.query(ExampleVersion).filter(
            ExampleVersion.example_id == example.id
        ).order_by(ExampleVersion.version_number.desc()).first()
        
        example_list.append({
            "id": str(example.id),
            "title": example.title,
            "description": example.description,
            "category": example.category,
            "language": example.subject,
            "tags": example.tags or [],
            "latest_version": latest_version.version_tag if latest_version else None,
            "repository_id": str(example.example_repository_id)
        })
    
    return ExampleForCourseResponse(
        examples=example_list,
        total=len(example_list),
        filters={
            "categories": [c[0] for c in categories if c[0]],
            "languages": [l[0] for l in languages if l[0]]
        }
    )


@example_deployment_router.get(
    "/{course_id}/examples/{example_id}/deployment-preview",
    response_model=ExampleDeploymentPreviewResponse
)
async def get_example_deployment_preview(
    course_id: str,
    example_id: str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    version: str = Query("latest", description="Version to preview"),
    target_path: str = Query(..., description="Target deployment path")
):
    """
    Preview what will be deployed for a specific example.
    
    Shows files, dependencies, and potential conflicts before deployment.
    """
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
    
    # Check for conflicts
    conflicts = []
    
    # Check if path already has content
    existing_content = db.query(CourseContent).filter(
        and_(
            CourseContent.course_id == course_id,
            CourseContent.path == target_path
        )
    ).first()
    
    if existing_content:
        conflict_info = {
            "type": "path_exists",
            "path": target_path,
            "current_content": existing_content.title
        }
        
        if existing_content.example_id:
            conflict_info["current_example_id"] = str(existing_content.example_id)
            conflict_info["current_example_version"] = existing_content.example_version
        
        conflicts.append(conflict_info)
    
    # Get dependencies
    dependencies = []
    dep_records = db.query(ExampleDependency).filter(
        ExampleDependency.example_id == example_id
    ).all()
    
    for dep in dep_records:
        dep_example = db.query(Example).filter(Example.id == dep.depends_id).first()
        if dep_example:
            dependencies.append({
                "example_id": str(dep_example.id),
                "title": dep_example.title,
                "required": True
            })
    
    # Parse file structure from meta.yaml
    file_structure = {
        "files": [],
        "size_mb": 0
    }
    
    if version_obj.meta_yaml:
        try:
            meta_data = yaml.safe_load(version_obj.meta_yaml)
            # Extract file information
            if "files" in meta_data:
                file_structure["files"] = meta_data["files"]
            # TODO: Calculate actual size from MinIO
        except:
            pass
    
    return ExampleDeploymentPreviewResponse(
        example={
            "id": str(example.id),
            "title": example.title,
            "description": example.description,
            "category": example.category,
            "language": example.subject
        },
        version={
            "id": str(version_obj.id),
            "version_tag": version_obj.version_tag,
            "created_at": version_obj.created_at.isoformat()
        },
        dependencies=dependencies,
        conflicts=conflicts,
        file_structure=file_structure
    )