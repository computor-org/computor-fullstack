"""
Pydantic interfaces for deployment tracking.

This module contains DTOs for the deployment system that tracks
example assignments to course content.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from ctutor_backend.interface.example import ExampleVersionList

from .base import BaseEntityGet, EntityInterface, ListQuery

if TYPE_CHECKING:
    from .example import ExampleVersionGet
    from .course_contents import CourseContentGet


# Deployment DTOs

class DeploymentMetadata(BaseModel):
    """Metadata stored with deployments."""
    workflow_id: Optional[str] = Field(None, description="Temporal workflow ID")
    files_deployed: Optional[List[str]] = Field(None, description="List of files deployed")
    git_commit: Optional[str] = Field(None, description="Git commit hash")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details if deployment failed")
    migrated_properties: Optional[Dict[str, Any]] = Field(None, description="Properties migrated from old schema")
    
    model_config = ConfigDict(extra='allow')


class CourseContentDeploymentCreate(BaseModel):
    """Create a new deployment (typically done automatically)."""
    course_content_id: UUID = Field(description="Course content to deploy to")
    example_version_id: UUID = Field(description="Example version to deploy")
    deployment_status: Literal["pending", "deploying", "deployed", "failed", "unassigned"] = Field(
        default="pending",
        description="Initial deployment status"
    )
    deployment_message: Optional[str] = Field(None, description="Optional message")
    deployment_metadata: Optional[DeploymentMetadata] = Field(None, description="Additional metadata")
    
    model_config = ConfigDict(use_enum_values=True)


class CourseContentDeploymentUpdate(BaseModel):
    """Update deployment status."""
    deployment_status: Optional[Literal["pending", "deploying", "deployed", "failed", "unassigned"]] = None
    deployment_message: Optional[str] = None
    deployed_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    deployment_path: Optional[str] = None
    deployment_metadata: Optional[DeploymentMetadata] = None
    
    model_config = ConfigDict(use_enum_values=True)


class CourseContentDeploymentGet(BaseEntityGet):
    """Get deployment details."""
    id: UUID
    course_content_id: UUID
    example_version_id: Optional[UUID]
    deployment_status: str
    deployment_message: Optional[str]
    assigned_at: datetime
    deployed_at: Optional[datetime]
    last_attempt_at: Optional[datetime]
    deployment_path: Optional[str]
    deployment_metadata: Optional[Dict[str, Any]]
    workflow_id: Optional[str]  # Current/last Temporal workflow ID
    
    # Relationships (optionally loaded)
    example_version: Optional['ExampleVersionGet'] = None
    course_content: Optional['CourseContentGet'] = None
    
    model_config = ConfigDict(from_attributes=True)


class CourseContentDeploymentList(BaseModel):
    """List view of deployments."""
    id: UUID
    course_content_id: UUID
    example_version_id: Optional[UUID]
    deployment_status: str
    assigned_at: datetime
    deployed_at: Optional[datetime]

    example_version: Optional['ExampleVersionList'] = None
    
    model_config = ConfigDict(from_attributes=True)


class CourseContentDeploymentQuery(ListQuery):
    """Query parameters for deployments."""
    course_content_id: Optional[UUID] = None
    example_version_id: Optional[UUID] = None
    deployment_status: Optional[str] = None
    deployed: Optional[bool] = None  # True for deployed_at IS NOT NULL
    failed: Optional[bool] = None  # True for status='failed'


# Deployment History DTOs

class DeploymentHistoryCreate(BaseModel):
    """Create a deployment history entry."""
    deployment_id: UUID
    action: Literal["assigned", "reassigned", "deployed", "failed", "unassigned", "updated", "migrated"]
    action_details: Optional[str] = None
    example_version_id: Optional[UUID] = None
    previous_example_version_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class DeploymentHistoryGet(BaseModel):
    """Get deployment history entry."""
    id: UUID
    deployment_id: UUID
    action: str
    action_details: Optional[str]
    example_version_id: Optional[UUID]
    previous_example_version_id: Optional[UUID]
    meta: Optional[Dict[str, Any]] = Field(None, alias="meta")  # Database column is 'meta'
    workflow_id: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]
    
    # Relationships
    example_version: Optional['ExampleVersionGet'] = None
    previous_example_version: Optional['ExampleVersionGet'] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentHistoryList(BaseModel):
    """List view of deployment history."""
    id: UUID
    deployment_id: UUID
    action: str
    created_at: datetime
    workflow_id: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Aggregate DTOs for API responses

class DeploymentWithHistory(BaseModel):
    """Deployment with its full history."""
    deployment: CourseContentDeploymentGet
    history: List[DeploymentHistoryGet]
    
    model_config = ConfigDict(from_attributes=True)


class DeploymentSummary(BaseModel):
    """Summary of deployments for a course."""
    course_id: UUID
    total_content: int = Field(description="Total course content items")
    submittable_content: int = Field(description="Total submittable content (assignments)")
    deployments_total: int = Field(description="Total deployments")
    deployments_pending: int = Field(description="Deployments pending")
    deployments_deployed: int = Field(description="Successfully deployed") 
    deployments_failed: int = Field(description="Failed deployments")
    last_deployment_at: Optional[datetime] = Field(None, description="Most recent deployment")
    
    model_config = ConfigDict(from_attributes=True)


class AssignExampleRequest(BaseModel):
    """Request to assign an example to course content."""
    example_version_id: UUID = Field(description="Example version to assign")
    deployment_message: Optional[str] = Field(None, description="Optional message about this assignment")


class DeployExampleRequest(BaseModel):
    """Request to deploy assigned examples."""
    course_id: UUID = Field(description="Course to deploy examples for")
    content_ids: Optional[List[UUID]] = Field(None, description="Specific content IDs to deploy (all if None)")
    force: bool = Field(False, description="Force re-deployment even if already deployed")


# Interface definitions

from sqlalchemy.orm import Session
from ..model.deployment import CourseContentDeployment, DeploymentHistory


def deployment_search(db: Session, query, params: Optional[CourseContentDeploymentQuery]):
    """Search deployments based on query parameters."""
    if params.course_content_id is not None:
        query = query.filter(CourseContentDeployment.course_content_id == params.course_content_id)
    if params.example_version_id is not None:
        query = query.filter(CourseContentDeployment.example_version_id == params.example_version_id)
    if params.deployment_status is not None:
        query = query.filter(CourseContentDeployment.deployment_status == params.deployment_status)
    if params.deployed is not None:
        if params.deployed:
            query = query.filter(CourseContentDeployment.deployed_at.isnot(None))
        else:
            query = query.filter(CourseContentDeployment.deployed_at.is_(None))
    if params.failed is not None:
        if params.failed:
            query = query.filter(CourseContentDeployment.deployment_status == "failed")
        else:
            query = query.filter(CourseContentDeployment.deployment_status != "failed")
    
    return query


class CourseContentDeploymentInterface(EntityInterface):
    """Interface for CourseContentDeployment entity."""
    create = CourseContentDeploymentCreate
    get = CourseContentDeploymentGet
    list = CourseContentDeploymentList
    update = CourseContentDeploymentUpdate
    query = CourseContentDeploymentQuery
    search = deployment_search
    endpoint = "deployments"
    model = CourseContentDeployment
    cache_ttl = 60  # Short cache for deployment status


class DeploymentHistoryInterface(EntityInterface):
    """Interface for DeploymentHistory entity (read-only)."""
    create = DeploymentHistoryCreate
    get = DeploymentHistoryGet
    list = DeploymentHistoryList
    update = None  # History is immutable
    query = ListQuery  # Use base query
    search = None
    endpoint = "deployment-history"
    model = DeploymentHistory
    cache_ttl = 300  # Longer cache for historical data