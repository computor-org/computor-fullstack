"""
Temporal workflows for organization, course family, and course hierarchy management.
"""
from datetime import timedelta
from typing import Dict, Any, Optional
from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from .temporal_base import BaseWorkflow, WorkflowResult
from .registry import register_task


# Activities
@activity.defn(name="create_organization_activity")
async def create_organization_activity(
    org_config: Dict[str, Any],
    gitlab_url: str,
    gitlab_token: str,
    user_id: str
) -> Dict[str, Any]:
    """Activity to create an organization."""
    # Implementation would go here
    # For now, return a simple result
    return {
        "organization_id": "org-123",
        "status": "created",
        "name": org_config.get("name", "New Organization")
    }


@activity.defn(name="create_course_family_activity")
async def create_course_family_activity(
    family_config: Dict[str, Any],
    organization_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Activity to create a course family."""
    # Implementation would go here
    # For now, return a simple result
    return {
        "course_family_id": "cf-123",
        "status": "created",
        "name": family_config.get("name", "New Course Family")
    }


@activity.defn(name="create_course_activity")
async def create_course_activity(
    course_config: Dict[str, Any],
    course_family_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Activity to create a course."""
    # Implementation would go here
    # For now, return a simple result
    return {
        "course_id": "course-123",
        "status": "created",
        "name": course_config.get("name", "New Course")
    }


# Workflows
@register_task
@workflow.defn(name="create_organization", sandboxed=False)
class CreateOrganizationWorkflow(BaseWorkflow):
    """Workflow for creating an organization."""
    
    @classmethod
    def get_name(cls) -> str:
        return "create_organization"
    
    @classmethod
    def get_execution_timeout(cls) -> timedelta:
        return timedelta(minutes=10)
    
    @workflow.run
    async def run(self, parameters: Dict[str, Any]) -> WorkflowResult:
        """
        Create organization workflow.
        
        Args:
            parameters: Dictionary containing:
                - org_config: Organization configuration
                - gitlab_url: GitLab URL
                - gitlab_token: GitLab access token
                - user_id: User ID creating the organization
            
        Returns:
            WorkflowResult
        """
        # Extract parameters
        org_config = parameters.get('org_config', {})
        gitlab_url = parameters.get('gitlab_url')
        gitlab_token = parameters.get('gitlab_token')
        user_id = parameters.get('user_id')
        
        workflow.logger.info(f"Creating organization: {org_config.get('name')}")
        
        try:
            # Execute creation activity
            result = await workflow.execute_activity(
                create_organization_activity,
                args=[org_config, gitlab_url, gitlab_token, user_id],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    backoff_coefficient=2.0,
                    maximum_attempts=3,
                )
            )
            
            return WorkflowResult(
                status="completed",
                result=result,
                metadata={"workflow_type": "create_organization"}
            )
            
        except Exception as e:
            workflow.logger.error(f"Organization creation failed: {str(e)}")
            return WorkflowResult(
                status="failed",
                result=None,
                error=str(e),
                metadata={"workflow_type": "create_organization"}
            )


@register_task
@workflow.defn(name="create_course_family", sandboxed=False)
class CreateCourseFamilyWorkflow(BaseWorkflow):
    """Workflow for creating a course family."""
    
    @classmethod
    def get_name(cls) -> str:
        return "create_course_family"
    
    @classmethod
    def get_execution_timeout(cls) -> timedelta:
        return timedelta(minutes=10)
    
    @workflow.run
    async def run(self, parameters: Dict[str, Any]) -> WorkflowResult:
        """
        Create course family workflow.
        
        Args:
            parameters: Dictionary containing:
                - family_config: Course family configuration
                - organization_id: Parent organization ID
                - user_id: User ID creating the course family
            
        Returns:
            WorkflowResult
        """
        # Extract parameters
        family_config = parameters.get('family_config', {})
        organization_id = parameters.get('organization_id')
        user_id = parameters.get('user_id')
        
        workflow.logger.info(f"Creating course family: {family_config.get('name')}")
        
        try:
            # Execute creation activity
            result = await workflow.execute_activity(
                create_course_family_activity,
                args=[family_config, organization_id, user_id],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    backoff_coefficient=2.0,
                    maximum_attempts=3,
                )
            )
            
            return WorkflowResult(
                status="completed",
                result=result,
                metadata={"workflow_type": "create_course_family"}
            )
            
        except Exception as e:
            workflow.logger.error(f"Course family creation failed: {str(e)}")
            return WorkflowResult(
                status="failed",
                result=None,
                error=str(e),
                metadata={"workflow_type": "create_course_family"}
            )


@register_task
@workflow.defn(name="create_course", sandboxed=False)
class CreateCourseWorkflow(BaseWorkflow):
    """Workflow for creating a course."""
    
    @classmethod
    def get_name(cls) -> str:
        return "create_course"
    
    @classmethod
    def get_execution_timeout(cls) -> timedelta:
        return timedelta(minutes=10)
    
    @workflow.run
    async def run(self, parameters: Dict[str, Any]) -> WorkflowResult:
        """
        Create course workflow.
        
        Args:
            parameters: Dictionary containing:
                - course_config: Course configuration
                - course_family_id: Parent course family ID
                - user_id: User ID creating the course
            
        Returns:
            WorkflowResult
        """
        # Extract parameters
        course_config = parameters.get('course_config', {})
        course_family_id = parameters.get('course_family_id')
        user_id = parameters.get('user_id')
        
        workflow.logger.info(f"Creating course: {course_config.get('name')}")
        
        try:
            # Execute creation activity
            result = await workflow.execute_activity(
                create_course_activity,
                args=[course_config, course_family_id, user_id],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    backoff_coefficient=2.0,
                    maximum_attempts=3,
                )
            )
            
            return WorkflowResult(
                status="completed",
                result=result,
                metadata={"workflow_type": "create_course"}
            )
            
        except Exception as e:
            workflow.logger.error(f"Course creation failed: {str(e)}")
            return WorkflowResult(
                status="failed",
                result=None,
                error=str(e),
                metadata={"workflow_type": "create_course"}
            )