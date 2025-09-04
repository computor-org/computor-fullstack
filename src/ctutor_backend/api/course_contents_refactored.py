"""
Refactored course contents API using the new deployment system.

This module handles course content management with clean separation
between content hierarchy and example deployments.
"""

import json
import os
from typing import Annotated, Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

import yaml
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from pydantic import BaseModel, Field

from ctutor_backend.permissions.auth import get_current_permissions
from ctutor_backend.permissions.core import check_course_permissions
from ctutor_backend.permissions.principal import Principal

from ctutor_backend.api.exceptions import BadRequestException, NotFoundException
from ctutor_backend.api.filesystem import get_path_course_content, mirror_entity_to_filesystem
from ctutor_backend.database import get_db
from ctutor_backend.interface.course_contents import CourseContentGet, CourseContentInterface
from ctutor_backend.interface.deployment import (
    AssignExampleRequest,
    DeploymentWithHistory,
    DeploymentSummary,
    CourseContentDeploymentCreate,
    DeploymentHistoryCreate
)
from ctutor_backend.api.api_builder import CrudRouter
from ctutor_backend.model.course import CourseContent, Course, CourseContentType, CourseContentKind
from ctutor_backend.model.example import Example, ExampleVersion
from ctutor_backend.model.deployment import CourseContentDeployment, DeploymentHistory
from ctutor_backend.redis_cache import get_redis_client
from aiocache import BaseCache

# Create the router
course_content_router = CrudRouter(CourseContentInterface)


# File operations (unchanged)
class CourseContentFileQuery(BaseModel):
    filename: Optional[str] = None


@course_content_router.router.get("/files/{course_content_id}", response_model=dict)
async def get_course_content_meta(
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    course_content_id: UUID | str,
    file_query: CourseContentFileQuery = Depends(),
    db: Session = Depends(get_db)
):
    """Get file content from course content directory."""
    if check_course_permissions(permissions, CourseContent, "_tutor", db).filter(
        CourseContent.id == course_content_id
    ).first() is None:
        raise NotFoundException()

    course_content_dir = await get_path_course_content(course_content_id, db)

    if file_query.filename is None:
        raise BadRequestException()

    with open(os.path.join(course_content_dir, file_query.filename), 'r') as file:
        content = file.read()

        if file_query.filename.endswith(".yaml") or file_query.filename.endswith(".yml"):
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    return data
            except Exception:
                raise BadRequestException()

        elif file_query.filename.endswith(".json"):
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    return data
            except Exception:
                raise BadRequestException()
        else:
            return {"content": content}


# Event handlers for filesystem mirroring
async def event_wrapper(entity: CourseContentGet, db: Session, permissions: Principal):
    try:
        await mirror_entity_to_filesystem(str(entity.id), CourseContentInterface, db)
    except Exception as e:
        print(e)


course_content_router.on_created.append(event_wrapper)
course_content_router.on_updated.append(event_wrapper)


# New deployment endpoints

@course_content_router.router.post(
    "/{content_id}/assign-example",
    response_model=DeploymentWithHistory
)
async def assign_example_to_content(
    content_id: UUID,
    request: AssignExampleRequest,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Assign an example version to course content.
    
    This creates or updates a deployment record, linking the example to the content.
    Only submittable content (assignments) can have examples assigned.
    """
    # Get course content
    content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CourseContent {content_id} not found"
        )
    
    # Check permissions on the course
    if check_course_permissions(permissions, Course, "_lecturer", db).filter(
        Course.id == content.course_id
    ).first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this course content"
        )
    
    # Verify this is submittable content
    content_type = db.query(CourseContentType).filter(
        CourseContentType.id == content.course_content_type_id
    ).first()
    
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Course content type not found"
        )
    
    content_kind = db.query(CourseContentKind).filter(
        CourseContentKind.id == content_type.course_content_kind_id
    ).first()
    
    if not content_kind or not content_kind.submittable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign examples to non-submittable content types"
        )
    
    # Validate example version exists
    example_version = db.query(ExampleVersion).options(
        joinedload(ExampleVersion.example)
    ).filter(ExampleVersion.id == request.example_version_id).first()
    
    if not example_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Example version {request.example_version_id} not found"
        )
    
    # Get or create deployment record
    deployment = db.query(CourseContentDeployment).filter(
        CourseContentDeployment.course_content_id == content_id
    ).first()
    
    if deployment:
        # Update existing deployment (reassignment)
        previous_version_id = deployment.example_version_id
        deployment.example_version_id = request.example_version_id
        deployment.deployment_status = "pending"
        deployment.deployment_message = request.deployment_message
        deployment.updated_by = permissions.user_id if hasattr(permissions, 'user_id') else None
        deployment.updated_at = datetime.utcnow()
        
        # Add history entry for reassignment
        history_entry = DeploymentHistory(
            deployment_id=deployment.id,
            action="reassigned" if previous_version_id else "assigned",
            action_details=f"Assigned {example_version.example.title} v{example_version.version_tag}",
            example_version_id=request.example_version_id,
            previous_example_version_id=previous_version_id,
            created_by=permissions.user_id if hasattr(permissions, 'user_id') else None
        )
        db.add(history_entry)
        
    else:
        # Create new deployment
        deployment = CourseContentDeployment(
            course_content_id=content_id,
            example_version_id=request.example_version_id,
            deployment_status="pending",
            deployment_message=request.deployment_message,
            created_by=permissions.user_id if hasattr(permissions, 'user_id') else None,
            updated_by=permissions.user_id if hasattr(permissions, 'user_id') else None
        )
        db.add(deployment)
        db.flush()  # Get the ID
        
        # Add initial history entry
        history_entry = DeploymentHistory(
            deployment_id=deployment.id,
            action="assigned",
            action_details=f"Assigned {example_version.example.title} v{example_version.version_tag}",
            example_version_id=request.example_version_id,
            created_by=permissions.user_id if hasattr(permissions, 'user_id') else None
        )
        db.add(history_entry)
    
    db.commit()
    db.refresh(deployment)
    
    # Load history
    history = db.query(DeploymentHistory).filter(
        DeploymentHistory.deployment_id == deployment.id
    ).order_by(DeploymentHistory.created_at.desc()).all()
    
    # Clear cache
    if cache:
        await cache.delete(f"course:{content.course_id}:deployments")
    
    # Return deployment with history
    return DeploymentWithHistory(
        deployment=deployment,
        history=history
    )


@course_content_router.router.delete(
    "/{content_id}/example",
    response_model=Dict[str, str]
)
async def unassign_example_from_content(
    content_id: UUID,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Remove example assignment from course content.
    
    This updates the deployment record to unassigned status.
    The actual removal from student-template happens during next generation.
    """
    # Get course content
    content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CourseContent {content_id} not found"
        )
    
    # Check permissions
    if check_course_permissions(permissions, Course, "_maintainer", db).filter(
        Course.id == content.course_id
    ).first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this course content"
        )
    
    # Get deployment record
    deployment = db.query(CourseContentDeployment).filter(
        CourseContentDeployment.course_content_id == content_id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No deployment found for this content"
        )
    
    # Update deployment status
    previous_version_id = deployment.example_version_id
    deployment.example_version_id = None
    deployment.deployment_status = "unassigned"
    deployment.deployment_message = "Example unassigned"
    deployment.updated_by = permissions.user_id if hasattr(permissions, 'user_id') else None
    
    # Add history entry
    history_entry = DeploymentHistory(
        deployment_id=deployment.id,
        action="unassigned",
        action_details="Example unassigned from course content",
        previous_example_version_id=previous_version_id,
        created_by=permissions.user_id if hasattr(permissions, 'user_id') else None
    )
    db.add(history_entry)
    
    db.commit()
    
    # Clear cache
    if cache:
        await cache.delete(f"course:{content.course_id}:deployments")
    
    return {"status": "unassigned", "message": "Example unassigned successfully"}


@course_content_router.router.get(
    "/courses/{course_id}/deployment-summary",
    response_model=DeploymentSummary
)
async def get_course_deployment_summary(
    course_id: UUID,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db),
    cache: Annotated[BaseCache, Depends(get_redis_client)] = None
):
    """
    Get deployment summary for a course.
    
    Shows statistics about example deployments in the course.
    """
    # Check permissions
    if check_course_permissions(permissions, Course, "_tutor", db).filter(
        Course.id == course_id
    ).first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this course"
        )
    
    # Try cache first
    cache_key = f"course:{course_id}:deployment-summary"
    if cache:
        cached = await cache.get(cache_key)
        if cached:
            return cached
    
    # Get total course content count
    total_content = db.query(CourseContent).filter(
        CourseContent.course_id == course_id,
        CourseContent.archived_at.is_(None)
    ).count()
    
    # Get submittable content count
    submittable_query = db.query(CourseContent).join(
        CourseContentType
    ).join(
        CourseContentKind
    ).filter(
        CourseContent.course_id == course_id,
        CourseContent.archived_at.is_(None),
        CourseContentKind.submittable == True
    )
    submittable_content = submittable_query.count()
    
    # Get deployment statistics
    deployments = db.query(CourseContentDeployment).join(
        CourseContent
    ).filter(
        CourseContent.course_id == course_id
    ).all()
    
    deployments_total = len(deployments)
    deployments_pending = sum(1 for d in deployments if d.deployment_status == "pending")
    deployments_deployed = sum(1 for d in deployments if d.deployment_status == "deployed")
    deployments_failed = sum(1 for d in deployments if d.deployment_status == "failed")
    
    # Get last deployment timestamp
    last_deployment = None
    for d in deployments:
        if d.deployed_at and (last_deployment is None or d.deployed_at > last_deployment):
            last_deployment = d.deployed_at
    
    summary = DeploymentSummary(
        course_id=course_id,
        total_content=total_content,
        submittable_content=submittable_content,
        deployments_total=deployments_total,
        deployments_pending=deployments_pending,
        deployments_deployed=deployments_deployed,
        deployments_failed=deployments_failed,
        last_deployment_at=last_deployment
    )
    
    # Cache the result
    if cache:
        await cache.set(cache_key, summary.dict(), ttl=300)  # 5 minutes
    
    return summary


@course_content_router.router.get(
    "/{content_id}/deployment",
    response_model=Optional[DeploymentWithHistory]
)
async def get_content_deployment(
    content_id: UUID,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """
    Get deployment information for specific course content.
    
    Returns deployment record with full history if exists.
    """
    # Get course content to check permissions
    content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CourseContent {content_id} not found"
        )
    
    # Check permissions
    if check_course_permissions(permissions, Course, "_tutor", db).filter(
        Course.id == content.course_id
    ).first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this content"
        )
    
    # Get deployment
    deployment = db.query(CourseContentDeployment).options(
        joinedload(CourseContentDeployment.example_version)
    ).filter(
        CourseContentDeployment.course_content_id == content_id
    ).first()
    
    if not deployment:
        return None
    
    # Get history
    history = db.query(DeploymentHistory).filter(
        DeploymentHistory.deployment_id == deployment.id
    ).order_by(DeploymentHistory.created_at.desc()).all()
    
    return DeploymentWithHistory(
        deployment=deployment,
        history=history
    )