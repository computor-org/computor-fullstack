"""
Pydantic DTOs for ExampleDeployment.

These DTOs handle the API interface for example deployment tracking.
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, Dict, Any

from .base import BaseEntityGet


class ExampleDeploymentCreate(BaseModel):
    """Create a new deployment record."""
    example_id: str = Field(description="UUID of the example to deploy")
    example_version_id: str = Field(description="UUID of the specific version to deploy")
    course_id: str = Field(description="UUID of the course")
    course_content_id: Optional[str] = Field(
        default=None,
        description="UUID of the CourseContent (if exists)"
    )
    deployment_path: str = Field(
        description="Path in student-template (e.g., 'week1.assignment1')"
    )
    commit_hash: Optional[str] = Field(
        default=None,
        description="Git commit hash after deployment"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    model_config = ConfigDict(use_enum_values=True)


class ExampleDeploymentUpdate(BaseModel):
    """Update deployment record (mainly for status changes)."""
    status: Optional[Literal["active", "replaced", "removed", "failed"]] = None
    removed_at: Optional[datetime] = None
    removed_by: Optional[str] = None
    removal_reason: Optional[str] = None
    commit_hash: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(use_enum_values=True)


class ExampleDeploymentGet(BaseEntityGet):
    """Get deployment record with all details."""
    id: str
    example_id: str
    example_version_id: str
    course_id: str
    course_content_id: Optional[str]
    deployment_path: str
    deployed_at: datetime
    deployed_by: Optional[str]
    status: str
    removed_at: Optional[datetime]
    removed_by: Optional[str]
    removal_reason: Optional[str]
    commit_hash: Optional[str]
    properties: Optional[Dict[str, Any]]
    
    # Nested relationships (optional)
    example_title: Optional[str] = None
    example_version_tag: Optional[str] = None
    course_path: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ExampleDeploymentList(BaseModel):
    """List view of deployments."""
    id: str
    example_id: str
    example_version_id: str
    deployment_path: str
    deployed_at: datetime
    status: str
    example_title: Optional[str] = None
    example_version_tag: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class DeploymentStatusUpdate(BaseModel):
    """Update deployment status when content changes."""
    deployment_id: str
    action: Literal["remove", "replace", "fail"]
    reason: str
    new_example_id: Optional[str] = Field(
        default=None,
        description="For replacement: new example ID"
    )
    new_example_version_id: Optional[str] = Field(
        default=None,
        description="For replacement: new version ID"
    )
    
    model_config = ConfigDict(use_enum_values=True)


class CourseDeploymentState(BaseModel):
    """Complete deployment state for a course."""
    course_id: str
    repository_url: str
    last_commit: Optional[str]
    active_deployments: list[ExampleDeploymentGet]
    removed_deployments: list[ExampleDeploymentGet]
    
    def get_deployment_at_path(self, path: str) -> Optional[ExampleDeploymentGet]:
        """Get the active deployment at a specific path."""
        for deployment in self.active_deployments:
            if deployment.deployment_path == path:
                return deployment
        return None
    
    def has_deployment_at_path(self, path: str) -> bool:
        """Check if there's an active deployment at a path."""
        return self.get_deployment_at_path(path) is not None
    
    model_config = ConfigDict(use_enum_values=True)