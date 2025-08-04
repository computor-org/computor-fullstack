"""
Temporal workflows for organization, course family, and course hierarchy management.
"""
import logging
from datetime import timedelta
from typing import Dict, Any, Optional
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from sqlalchemy.orm import Session

from .temporal_base import BaseWorkflow, WorkflowResult
from .registry import register_task
from ..interface.deployments import ComputorDeploymentConfig, OrganizationConfig, GitLabConfig, CourseFamilyConfig, CourseConfig
from ..database import get_db
from ..model.organization import Organization
from ..model.course import CourseFamily, Course

logger = logging.getLogger(__name__)


def transform_localhost_url(url: str) -> str:
    """
    Transform localhost URLs to Docker host IP for container-to-host communication.
    
    Args:
        url: URL that may contain localhost
        
    Returns:
        URL with localhost replaced by Docker host IP (172.17.0.1)
    """
    if url and "localhost" in url:
        return url.replace("localhost", "172.17.0.1")
    return url


# Activities
@activity.defn(name="create_organization_activity")
async def create_organization_activity(
    org_config: Dict[str, Any],
    gitlab_url: str,
    gitlab_token: str,
    user_id: str
) -> Dict[str, Any]:
    """Activity to create an organization using GitLabBuilderNew."""
    # Import GitLabBuilderNew inside activity to avoid workflow sandbox restrictions
    from ..generator.gitlab_builder_new import GitLabBuilderNew
    
    logger.info(f"Starting organization creation activity for: {org_config.get('name')}")
    logger.info(f"GitLab URL: {gitlab_url}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Org config: {org_config}")
    
    try:
        # Transform localhost URLs for Docker environment
        gitlab_url = transform_localhost_url(gitlab_url)
        logger.info(f"Transformed GitLab URL: {gitlab_url}")
        
        # Convert dict to proper config objects
        gitlab_config = GitLabConfig(
            url=gitlab_url,
            token=gitlab_token,
            parent=org_config.get("gitlab", {}).get("parent"),
            path=org_config.get("path")
        )
        
        org_config_obj = OrganizationConfig(
            name=org_config.get("name"),
            path=org_config.get("path"),
            description=org_config.get("description", ""),
            gitlab=gitlab_config
        )
        
        # Create minimal dummy objects for required fields
        dummy_course_family = CourseFamilyConfig(
            name="temp",
            path="temp",
            description=""
        )
        
        dummy_course = CourseConfig(
            name="temp", 
            path="temp",
            description=""
        )
        
        deployment_config = ComputorDeploymentConfig(
            organization=org_config_obj,
            courseFamily=dummy_course_family,
            course=dummy_course
        )
        
        # Create the builder and organization
        logger.info("Creating database session and GitLab builder")
        db_gen = get_db()
        db = next(db_gen)
        try:
            logger.info("Database session created successfully")
            builder = GitLabBuilderNew(db, gitlab_url, gitlab_token)
            logger.info("GitLab builder created successfully")
            
            logger.info("Calling _create_organization method")
            result = builder._create_organization(deployment_config, user_id)
            logger.info(f"Organization creation result: {result}")
            
            if result["success"]:
                # Commit the transaction to save the organization
                db.commit()
                
                response = {
                    "organization_id": result["organization"].id if result["organization"] else None,
                    "status": "created",
                    "name": org_config.get("name"),
                    "gitlab_group_id": result["gitlab_group"].id if result["gitlab_group"] else None,
                    "gitlab_created": result["gitlab_created"],
                    "db_created": result["db_created"]
                }
                logger.info(f"Returning success response: {response}")
                return response
            else:
                error_response = {
                    "organization_id": None,
                    "status": "failed",
                    "name": org_config.get("name"),
                    "error": result.get("error", "Unknown error occurred")
                }
                logger.error(f"Organization creation failed: {error_response}")
                return error_response
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
                
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Exception in organization creation activity: {error_msg}")
        error_response = {
            "organization_id": None,
            "status": "failed", 
            "name": org_config.get("name"),
            "error": error_msg
        }
        logger.error(f"Returning error response: {error_response}")
        return error_response


@activity.defn(name="create_course_family_activity")
async def create_course_family_activity(
    family_config: Dict[str, Any],
    organization_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Activity to create a course family using GitLabBuilderNew."""
    # Import GitLabBuilderNew inside activity to avoid workflow sandbox restrictions
    from ..generator.gitlab_builder_new import GitLabBuilderNew
    
    logger.info(f"Starting course family creation activity for: {family_config.get('name')}")
    logger.info(f"Organization ID: {organization_id}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Family config: {family_config}")
    
    try:
        # Get organization from database to inherit GitLab credentials
        db_gen = get_db()
        db = next(db_gen)
        try:
            org = db.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                raise ValueError(f"Organization {organization_id} not found")
            
            # Extract GitLab config from organization
            org_gitlab = org.properties.get("gitlab", {}) if org.properties else {}
            gitlab_url = org_gitlab.get("url")
            gitlab_token = org_gitlab.get("token")
            
            if not gitlab_url or not gitlab_token:
                raise ValueError("Organization missing GitLab configuration")
                
            # Transform localhost URLs for Docker environment
            gitlab_url = transform_localhost_url(gitlab_url)
            logger.info(f"Transformed GitLab URL: {gitlab_url}")
            
            # Create course family config objects
            gitlab_config = GitLabConfig(
                url=gitlab_url,
                token=gitlab_token,
                parent=org_gitlab.get("group_id"),
                path=family_config.get("path")
            )
            
            family_config_obj = CourseFamilyConfig(
                name=family_config.get("name"),
                path=family_config.get("path"),
                description=family_config.get("description", "")
            )
            
            # Create minimal dummy objects for required fields
            dummy_org = OrganizationConfig(
                name=org.title or str(org.path),  # Organizations use 'title' not 'name'
                path=str(org.path),  # Convert Ltree to string
                description=org.description or "",
                gitlab=gitlab_config
            )
            
            dummy_course = CourseConfig(
                name="temp", 
                path="temp",
                description=""
            )
            
            deployment_config = ComputorDeploymentConfig(
                organization=dummy_org,
                courseFamily=family_config_obj,
                course=dummy_course
            )
            
            # Create the builder and course family
            builder = GitLabBuilderNew(db, gitlab_url, gitlab_token)
            result = builder._create_course_family(deployment_config, org, user_id)
            
            if result["success"]:
                # Commit the transaction to save the course family
                db.commit()
                
                response = {
                    "course_family_id": result["course_family"].id if result["course_family"] else None,
                    "status": "created",
                    "name": family_config.get("name"),
                    "gitlab_group_id": result["gitlab_group"].id if result["gitlab_group"] else None,
                    "gitlab_created": result["gitlab_created"],
                    "db_created": result["db_created"]
                }
                logger.info(f"Returning success response: {response}")
                return response
            else:
                error_response = {
                    "course_family_id": None,
                    "status": "failed",
                    "name": family_config.get("name"),
                    "error": result.get("error", "Unknown error occurred")
                }
                logger.error(f"Course family creation failed: {error_response}")
                return error_response
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
                
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Exception in course family creation activity: {error_msg}")
        error_response = {
            "course_family_id": None,
            "status": "failed", 
            "name": family_config.get("name"),
            "error": error_msg
        }
        logger.error(f"Returning error response: {error_response}")
        return error_response


@activity.defn(name="create_course_activity")
async def create_course_activity(
    course_config: Dict[str, Any],
    course_family_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Activity to create a course using GitLabBuilderNew."""
    # Import GitLabBuilderNew inside activity to avoid workflow sandbox restrictions
    from ..generator.gitlab_builder_new import GitLabBuilderNew
    
    logger.info(f"Starting course creation activity for: {course_config.get('name')}")
    logger.info(f"Course Family ID: {course_family_id}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Course config: {course_config}")
    
    try:
        # Get course family from database to inherit GitLab credentials
        db_gen = get_db()
        db = next(db_gen)
        try:
            family = db.query(CourseFamily).filter(CourseFamily.id == course_family_id).first()
            if not family:
                raise ValueError(f"Course family {course_family_id} not found")
            
            # Get organization for GitLab config
            org = db.query(Organization).filter(Organization.id == family.organization_id).first()
            if not org:
                raise ValueError(f"Organization {family.organization_id} not found")
            
            # Extract GitLab config from organization and course family
            org_gitlab = org.properties.get("gitlab", {}) if org.properties else {}
            family_gitlab = family.properties.get("gitlab", {}) if family.properties else {}
            
            gitlab_url = org_gitlab.get("url")
            gitlab_token = org_gitlab.get("token")
            
            if not gitlab_url or not gitlab_token:
                raise ValueError("Organization missing GitLab configuration")
                
            # Transform localhost URLs for Docker environment
            gitlab_url = transform_localhost_url(gitlab_url)
            logger.info(f"Transformed GitLab URL: {gitlab_url}")
            
            # Create course config objects
            gitlab_config = GitLabConfig(
                url=gitlab_url,
                token=gitlab_token,
                parent=family_gitlab.get("group_id"),
                path=course_config.get("path")
            )
            
            course_config_obj = CourseConfig(
                name=course_config.get("name"),
                path=course_config.get("path"),
                description=course_config.get("description", "")
            )
            
            # Create config objects for required fields
            org_config = OrganizationConfig(
                name=org.title or str(org.path),  # Organizations use 'title' not 'name'
                path=str(org.path),  # Convert Ltree to string
                description=org.description or "",
                gitlab=gitlab_config
            )
            
            family_config_obj = CourseFamilyConfig(
                name=family.title or str(family.path),  # Course families use 'title' not 'name'
                path=str(family.path),  # Convert Ltree to string
                description=family.description or ""
            )
            
            deployment_config = ComputorDeploymentConfig(
                organization=org_config,
                courseFamily=family_config_obj,
                course=course_config_obj
            )
            
            # Create the builder and course
            builder = GitLabBuilderNew(db, gitlab_url, gitlab_token)
            result = builder._create_course(deployment_config, org, family, user_id)
            
            if result["success"]:
                # Commit the transaction to save the course
                db.commit()
                
                response = {
                    "course_id": result["course"].id if result["course"] else None,
                    "status": "created",
                    "name": course_config.get("name"),
                    "gitlab_group_id": result["gitlab_group"].id if result["gitlab_group"] else None,
                    "gitlab_created": result["gitlab_created"],
                    "db_created": result["db_created"]
                }
                logger.info(f"Returning success response: {response}")
                return response
            else:
                error_response = {
                    "course_id": None,
                    "status": "failed",
                    "name": course_config.get("name"),
                    "error": result.get("error", "Unknown error occurred")
                }
                logger.error(f"Course creation failed: {error_response}")
                return error_response
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
                
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Exception in course creation activity: {error_msg}")
        error_response = {
            "course_id": None,
            "status": "failed", 
            "name": course_config.get("name"),
            "error": error_msg
        }
        logger.error(f"Returning error response: {error_response}")
        return error_response


# Workflows
@register_task
@workflow.defn(name="create_organization", sandboxed=False)
class CreateOrganizationWorkflow(BaseWorkflow):
    """Workflow for creating an organization."""
    
    @classmethod
    def get_name(cls) -> str:
        return "create_organization"
    
    @classmethod
    def get_task_queue(cls) -> str:
        return "computor-tasks"
    
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
        # Validate required parameters
        required_params = ['org_config', 'gitlab_url', 'gitlab_token', 'user_id']
        missing_params = [param for param in required_params if not parameters.get(param)]
        if missing_params:
            error_msg = f"Missing required parameters: {', '.join(missing_params)}"
            workflow.logger.error(error_msg)
            return WorkflowResult(
                status="failed",
                result=None,
                error=error_msg,
                metadata={"workflow_type": "create_organization"}
            )
        
        # Extract parameters
        org_config = parameters.get('org_config', {})
        gitlab_url = parameters.get('gitlab_url')
        gitlab_token = parameters.get('gitlab_token')
        user_id = parameters.get('user_id')
        
        # Validate organization config
        if not org_config.get('name') or not org_config.get('path'):
            error_msg = "Organization config must include 'name' and 'path'"
            workflow.logger.error(error_msg)
            return WorkflowResult(
                status="failed",
                result=None,
                error=error_msg,
                metadata={"workflow_type": "create_organization"}
            )
        
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
    def get_task_queue(cls) -> str:
        return "computor-tasks"
    
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
        # Validate required parameters
        required_params = ['family_config', 'organization_id', 'user_id']
        missing_params = [param for param in required_params if not parameters.get(param)]
        if missing_params:
            error_msg = f"Missing required parameters: {', '.join(missing_params)}"
            workflow.logger.error(error_msg)
            return WorkflowResult(
                status="failed",
                result=None,
                error=error_msg,
                metadata={"workflow_type": "create_course_family"}
            )
        
        # Extract parameters
        family_config = parameters.get('family_config', {})
        organization_id = parameters.get('organization_id')
        user_id = parameters.get('user_id')
        
        # Validate course family config
        if not family_config.get('name') or not family_config.get('path'):
            error_msg = "Course family config must include 'name' and 'path'"
            workflow.logger.error(error_msg)
            return WorkflowResult(
                status="failed",
                result=None,
                error=error_msg,
                metadata={"workflow_type": "create_course_family"}
            )
        
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
    def get_task_queue(cls) -> str:
        return "computor-tasks"
    
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
        # Validate required parameters
        required_params = ['course_config', 'course_family_id', 'user_id']
        missing_params = [param for param in required_params if not parameters.get(param)]
        if missing_params:
            error_msg = f"Missing required parameters: {', '.join(missing_params)}"
            workflow.logger.error(error_msg)
            return WorkflowResult(
                status="failed",
                result=None,
                error=error_msg,
                metadata={"workflow_type": "create_course"}
            )
        
        # Extract parameters
        course_config = parameters.get('course_config', {})
        course_family_id = parameters.get('course_family_id')
        user_id = parameters.get('user_id')
        
        # Validate course config
        if not course_config.get('name') or not course_config.get('path'):
            error_msg = "Course config must include 'name' and 'path'"
            workflow.logger.error(error_msg)
            return WorkflowResult(
                status="failed",
                result=None,
                error=error_msg,
                metadata={"workflow_type": "create_course"}
            )
        
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


@register_task
@workflow.defn(name="deploy_computor_hierarchy", sandboxed=False)
class DeployComputorHierarchyWorkflow(BaseWorkflow):
    """
    Orchestrator workflow that chains existing workflows to deploy a complete
    organization -> course family -> course hierarchy from a deployment configuration.
    
    This workflow reuses the CreateOrganizationWorkflow, CreateCourseFamilyWorkflow,
    and CreateCourseWorkflow to create the full hierarchy from a YAML configuration.
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "deploy_computor_hierarchy"
    
    @classmethod
    def get_task_queue(cls) -> str:
        return "computor-tasks"
    
    @classmethod
    def get_execution_timeout(cls) -> timedelta:
        return timedelta(minutes=30)
    
    @workflow.run
    async def run(self, parameters: Dict[str, Any]) -> WorkflowResult:
        """
        Execute the deployment orchestration.
        
        Args:
            parameters: Dictionary containing:
                - deployment_config: Complete deployment configuration with:
                    - organization: Organization configuration
                    - course_family: Course family configuration  
                    - course: Course configuration
                    - deploy_examples: Whether to deploy examples (optional)
                    - settings: Global settings (optional)
                - user_id: ID of the user initiating the deployment
            
        Returns:
            WorkflowResult with deployment status and created entity IDs
        """
        # Validate required parameters
        if not parameters.get('deployment_config') or not parameters.get('user_id'):
            error_msg = "Missing required parameters: deployment_config and user_id"
            workflow.logger.error(error_msg)
            return WorkflowResult(
                status="failed",
                result=None,
                error=error_msg,
                metadata={"workflow_type": "deploy_computor_hierarchy"}
            )
        
        deployment_config = parameters['deployment_config']
        user_id = parameters['user_id']
        
        try:
            workflow.logger.info("Starting deployment orchestration")
            
            # Track created entities
            created_entities = {
                "organization": None,
                "course_family": None,
                "course": None
            }
            
            # Prepare GitLab configuration
            gitlab_config = deployment_config["organization"].get("gitlab", {})
            gitlab_url = gitlab_config.get("url", "")
            gitlab_token = gitlab_config.get("token", "")
            
            # Handle environment variable substitution for token
            if gitlab_token.startswith("${") and gitlab_token.endswith("}"):
                import os
                env_var = gitlab_token[2:-1]
                gitlab_token = os.environ.get(env_var, "")
            
            # Step 1: Create Organization using existing workflow
            workflow.logger.info("Triggering organization creation workflow...")
            org_params = {
                "org_config": deployment_config["organization"],
                "gitlab_url": gitlab_url,
                "gitlab_token": gitlab_token,
                "user_id": user_id
            }
            
            org_workflow_handle = await workflow.start_child_workflow(
                CreateOrganizationWorkflow.run,
                args=[org_params],
                id=f"create-org-{workflow.info().workflow_id}",
                task_queue="computor-tasks",
                execution_timeout=timedelta(minutes=10)
            )
            
            org_result = await org_workflow_handle
            
            if org_result.status != "completed":
                raise Exception(f"Organization creation failed: {org_result.error}")
            
            created_entities["organization"] = org_result.result
            org_id = org_result.result.get("organization_id")
            workflow.logger.info(f"Organization created with ID: {org_id}")
            
            # Step 2: Create Course Family using existing workflow
            workflow.logger.info("Triggering course family creation workflow...")
            family_params = {
                "family_config": deployment_config["course_family"],
                "organization_id": str(org_id),
                "user_id": user_id
            }
            
            family_workflow_handle = await workflow.start_child_workflow(
                CreateCourseFamilyWorkflow.run,
                args=[family_params],
                id=f"create-family-{workflow.info().workflow_id}",
                task_queue="computor-tasks",
                execution_timeout=timedelta(minutes=10)
            )
            
            family_result = await family_workflow_handle
            
            if family_result.status != "completed":
                raise Exception(f"Course family creation failed: {family_result.error}")
            
            created_entities["course_family"] = family_result.result
            family_id = family_result.result.get("course_family_id")
            workflow.logger.info(f"Course family created with ID: {family_id}")
            
            # Step 3: Create Course using existing workflow
            workflow.logger.info("Triggering course creation workflow...")
            course_params = {
                "course_config": deployment_config["course"],
                "course_family_id": str(family_id),
                "user_id": user_id
            }
            
            course_workflow_handle = await workflow.start_child_workflow(
                CreateCourseWorkflow.run,
                args=[course_params],
                id=f"create-course-{workflow.info().workflow_id}",
                task_queue="computor-tasks",
                execution_timeout=timedelta(minutes=10)
            )
            
            course_result = await course_workflow_handle
            
            if course_result.status != "completed":
                raise Exception(f"Course creation failed: {course_result.error}")
            
            created_entities["course"] = course_result.result
            course_id = course_result.result.get("course_id")
            workflow.logger.info(f"Course created with ID: {course_id}")
            
            # Step 4: Deploy examples if configured
            if deployment_config.get("deploy_examples", False):
                workflow.logger.info("Example deployment requested - would trigger temporal_examples workflow")
                # TODO: Trigger temporal_examples workflow when ready
                # example_workflow_handle = await workflow.start_child_workflow(
                #     "deploy_examples",
                #     args=[{"course_id": course_id, "config": deployment_config}],
                #     id=f"deploy-examples-{workflow.info().workflow_id}",
                #     task_queue="computor-tasks",
                #     execution_timeout=timedelta(minutes=30)
                # )
                # await example_workflow_handle
            
            # Build full path
            full_path = (
                f"{deployment_config['organization']['path']}/"
                f"{deployment_config['course_family']['path']}/"
                f"{deployment_config['course']['path']}"
            )
            
            # Build success result
            result_data = {
                "deployment_status": "success",
                "created_entities": created_entities,
                "full_path": full_path,
                "organization_id": str(org_id),
                "course_family_id": str(family_id),
                "course_id": str(course_id)
            }
            
            workflow.logger.info(f"Deployment orchestration completed successfully. Full path: {full_path}")
            return WorkflowResult(
                status="completed",
                result=result_data,
                metadata={
                    "workflow_type": "deploy_computor_hierarchy",
                    "full_path": full_path
                }
            )
            
        except Exception as e:
            workflow.logger.error(f"Deployment orchestration failed: {str(e)}")
            return WorkflowResult(
                status="failed",
                result={
                    "created_entities": created_entities,
                    "partial_deployment": any(created_entities.values())
                },
                error=str(e),
                metadata={"workflow_type": "deploy_computor_hierarchy"}
            )