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
    content = db.query(CourseContent).filter(CourseContent.id == str(content_id)).first()
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
        CourseContentDeployment.course_content_id == str(content_id)
    ).first()
    
    if deployment:
        # Update existing deployment (reassignment)
        previous_version_id = deployment.example_version_id
        deployment.example_version_id = str(request.example_version_id)
        deployment.deployment_status = "pending"
        deployment.deployment_message = request.deployment_message
        deployment.updated_by = permissions.user_id if hasattr(permissions, 'user_id') else None
        deployment.updated_at = datetime.utcnow()
        
        # Add history entry for reassignment
        history_entry = DeploymentHistory(
            deployment_id=deployment.id,
            action="reassigned" if previous_version_id else "assigned",
            action_details=f"Assigned {example_version.example.title} v{example_version.version_tag}",
            example_version_id=str(request.example_version_id),
            previous_example_version_id=str(previous_version_id) if previous_version_id else None,
            created_by=permissions.user_id if hasattr(permissions, 'user_id') else None
        )
        db.add(history_entry)
        
    else:
        # Create new deployment
        deployment = CourseContentDeployment(
            course_content_id=str(content_id),
            example_version_id=str(request.example_version_id),
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
            example_version_id=str(request.example_version_id),
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
    
    # Return deployment with history (exclude course_content to avoid recursion)
    deployment_dict = {
        "id": deployment.id,
        "course_content_id": deployment.course_content_id,
        "example_version_id": deployment.example_version_id,
        "deployment_status": deployment.deployment_status,
        "deployment_path": deployment.deployment_path,
        "assigned_at": deployment.assigned_at,  # Required field
        "deployed_at": deployment.deployed_at,
        "last_attempt_at": deployment.last_attempt_at,
        "deployment_message": deployment.deployment_message,
        "deployment_metadata": deployment.deployment_metadata,
        "created_at": deployment.created_at,
        "updated_at": deployment.updated_at,
        "created_by": deployment.created_by,
        "updated_by": deployment.updated_by,
        # Don't include course_content to avoid recursion
    }
    
    # Convert history to dicts with correct field names
    history_dicts = []
    for h in history:
        history_dicts.append({
            "id": h.id,
            "deployment_id": h.deployment_id,
            "action": h.action,
            "action_details": h.action_details,
            "example_version_id": h.example_version_id,
            "previous_example_version_id": h.previous_example_version_id,
            "meta": h.meta,  # Use the correct field name
            "workflow_id": h.workflow_id,
            "created_at": h.created_at,
            "created_by": h.created_by,
        })
    
    return DeploymentWithHistory(
        deployment=deployment_dict,
        history=history_dicts
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
    content = db.query(CourseContent).filter(CourseContent.id == str(content_id)).first()
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
        CourseContentDeployment.course_content_id == str(content_id)
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
        previous_example_version_id=str(previous_version_id) if previous_version_id else None,
        created_by=permissions.user_id if hasattr(permissions, 'user_id') else None
    )
    db.add(history_entry)
    
    db.commit()
    
    # Clear cache
    if cache:
        await cache.delete(f"course:{content.course_id}:deployments")
    
    return {"status": "unassigned", "message": "Example unassigned successfully"}


@course_content_router.router.get(
    "/deployment/{content_id}",
    response_model=Dict[str, Any]
)
async def get_deployment_status_with_workflow(
    content_id: UUID,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """
    Get detailed deployment status including Temporal workflow information.
    
    Returns deployment data and checks the Temporal workflow status if one is running.
    """
    # Check content exists
    content = db.query(CourseContent).filter(CourseContent.id == str(content_id)).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course content not found"
        )
    
    # Check permissions
    if check_course_permissions(permissions, Course, "_student", db).filter(
        Course.id == content.course_id
    ).first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view deployment status"
        )
    
    # Get deployment with relationships
    deployment = db.query(CourseContentDeployment).options(
        joinedload(CourseContentDeployment.example_version).joinedload(ExampleVersion.example)
    ).filter(
        CourseContentDeployment.course_content_id == str(content_id)
    ).first()
    
    if not deployment:
        return {
            "deployment": None,
            "workflow": None,
            "message": "No deployment found for this content"
        }
    
    # Build deployment info
    deployment_info = {
        "id": str(deployment.id),
        "course_content_id": str(deployment.course_content_id),
        "example_version_id": str(deployment.example_version_id) if deployment.example_version_id else None,
        "deployment_status": deployment.deployment_status,
        "deployment_message": deployment.deployment_message,
        "assigned_at": deployment.assigned_at.isoformat() if deployment.assigned_at else None,
        "deployed_at": deployment.deployed_at.isoformat() if deployment.deployed_at else None,
        "last_attempt_at": deployment.last_attempt_at.isoformat() if deployment.last_attempt_at else None,
        "deployment_path": deployment.deployment_path,
        "workflow_id": deployment.workflow_id
    }
    
    # If there's an example version, include its info
    if deployment.example_version:
        deployment_info["example_version"] = {
            "id": str(deployment.example_version.id),
            "version_tag": deployment.example_version.version_tag,
            "example": {
                "id": str(deployment.example_version.example.id),
                "identifier": str(deployment.example_version.example.identifier),
                "title": deployment.example_version.example.title
            } if deployment.example_version.example else None
        }
    
    # Check Temporal workflow status if workflow_id exists
    workflow_info = None
    if deployment.workflow_id:
        try:
            # Import Temporal client
            from temporalio.client import Client
            from datetime import datetime, timezone
            import os
            
            # Get Temporal configuration
            temporal_host = os.environ.get('TEMPORAL_HOST', 'localhost')
            temporal_port = os.environ.get('TEMPORAL_PORT', '7233')
            temporal_namespace = os.environ.get('TEMPORAL_NAMESPACE', 'default')
            
            # Create Temporal client
            async def get_workflow_status():
                client = await Client.connect(
                    f"{temporal_host}:{temporal_port}",
                    namespace=temporal_namespace
                )
                
                try:
                    # Get workflow handle
                    handle = client.get_workflow_handle(deployment.workflow_id)
                    
                    # Describe the workflow to get its status
                    description = await handle.describe()
                    
                    return {
                        "workflow_id": deployment.workflow_id,
                        "status": description.status.name if description.status else "UNKNOWN",
                        "start_time": description.start_time.isoformat() if description.start_time else None,
                        "close_time": description.close_time.isoformat() if description.close_time else None,
                        "execution_time": description.execution_time.isoformat() if description.execution_time else None,
                        "task_queue": description.task_queue,
                        "workflow_type": description.workflow_type,
                        "is_running": description.status.name in ["RUNNING", "PENDING"] if description.status else False
                    }
                except Exception as e:
                    return {
                        "workflow_id": deployment.workflow_id,
                        "status": "NOT_FOUND",
                        "error": str(e),
                        "is_running": False
                    }
            
            # Run the async function
            workflow_info = await get_workflow_status()
            
            # Auto-update deployment status based on workflow status
            if workflow_info["status"] == "COMPLETED" and deployment.deployment_status == "in_progress":
                deployment.deployment_status = "deployed"
                deployment.deployed_at = datetime.now(timezone.utc)
                deployment.deployment_message = "Deployment completed successfully"
                db.commit()
                deployment_info["deployment_status"] = "deployed"
                deployment_info["deployed_at"] = deployment.deployed_at.isoformat()
                
            elif workflow_info["status"] in ["FAILED", "TERMINATED", "TIMED_OUT"] and deployment.deployment_status == "in_progress":
                deployment.deployment_status = "failed"
                deployment.deployment_message = f"Workflow {workflow_info['status'].lower()}"
                db.commit()
                deployment_info["deployment_status"] = "failed"
                
        except Exception as e:
            workflow_info = {
                "error": f"Failed to connect to Temporal: {str(e)}",
                "workflow_id": deployment.workflow_id
            }
    
    # Get recent history
    history = db.query(DeploymentHistory).filter(
        DeploymentHistory.deployment_id == deployment.id
    ).order_by(DeploymentHistory.created_at.desc()).limit(5).all()
    
    history_items = [
        {
            "id": str(h.id),
            "action": h.action,
            "action_details": h.action_details,
            "workflow_id": h.workflow_id,
            "created_at": h.created_at.isoformat()
        } for h in history
    ]
    
    return {
        "deployment": deployment_info,
        "workflow": workflow_info,
        "recent_history": history_items
    }


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
    content = db.query(CourseContent).filter(CourseContent.id == str(content_id)).first()
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
        CourseContentDeployment.course_content_id == str(content_id)
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