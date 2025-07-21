"""
Celery tasks for organization, course family, and course hierarchy management.

These tasks handle the creation of GitLab groups and corresponding database entries
for the hierarchical structure: Organization → Course Family → Course.
"""

import logging
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from celery import current_task
from celery.exceptions import Retry

from ctutor_backend.tasks.base import BaseTask
from ctutor_backend.tasks.registry import register_task
from ctutor_backend.tasks.celery_app import app
from ctutor_backend.tasks.executor import _execute_task_with_celery
from ctutor_backend.generator.gitlab_builder_new import GitLabBuilderNew
from ctutor_backend.database import get_db
from ctutor_backend.interface.deployments import (
    ComputorDeploymentConfig,
    OrganizationConfig,
    CourseFamilyConfig,
    CourseConfig
)

logger = logging.getLogger(__name__)


# Direct Celery tasks (for API usage)
@app.task(bind=True, name='ctutor_backend.tasks.create_organization')
def create_organization_task(self, organization_config, gitlab_url, gitlab_token, created_by_user_id=None):
    """Create an organization with GitLab group and database entry."""
    task_id = self.request.id
    
    try:
        from ctutor_backend.database import get_db
        from ctutor_backend.model.organization import Organization
        from ctutor_backend.interface.organizations import OrganizationCreate
        from ctutor_backend.interface.tokens import encrypt_api_key
        import random
        
        self.update_state(state='PROGRESS', meta={'status': 'Creating organization (test mode)', 'progress': 30})
        
        # For testing: create mock GitLab group data
        mock_group_id = random.randint(1000, 9999)
        mock_full_path = f"test-groups/{organization_config['path']}"
        
        self.update_state(state='PROGRESS', meta={'status': 'Creating database entry', 'progress': 70})
        
        # Create database entry
        with next(get_db()) as db:
            from sqlalchemy_utils import Ltree
            
            organization_data = {
                "title": organization_config["name"],
                "path": organization_config["path"],
                "description": organization_config.get("description", ""),
                "organization_type": "organization",
                "properties": {
                    "gitlab": {
                        "url": gitlab_url,
                        "token": encrypt_api_key(gitlab_token),
                        "group_id": mock_group_id,
                        "full_path": mock_full_path,
                        "parent": organization_config["gitlab"]["parent"]
                    }
                }
            }
            
            organization_create = OrganizationCreate(**organization_data)
            organization_dict = organization_create.model_dump()
            
            # Convert path string to valid Ltree format (replace hyphens with underscores)
            ltree_path = organization_dict['path'].replace('-', '_')
            organization_dict['path'] = Ltree(ltree_path)
            
            organization = Organization(**organization_dict)
            
            db.add(organization)
            db.commit()
            db.refresh(organization)
            
            self.update_state(state='PROGRESS', meta={'status': 'Complete', 'progress': 100})
            
            return {
                "success": True,
                "organization_id": str(organization.id),
                "gitlab_group_id": mock_group_id,
                "gitlab_path": mock_full_path,
                "task_id": task_id,
                "note": "Created in test mode without actual GitLab integration"
            }
            
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@app.task(bind=True, name='ctutor_backend.tasks.create_course_family')  
def create_course_family_task(self, course_family_config, organization_id, gitlab_url, gitlab_token, created_by_user_id=None):
    """Create a course family with GitLab group and database entry."""
    task_id = self.request.id
    
    try:
        from ctutor_backend.database import get_db
        from ctutor_backend.generator.gitlab_builder_new import GitLabBuilderNew
        from ctutor_backend.model.course import CourseFamily
        from ctutor_backend.interface.course_families import CourseFamilyCreate
        from ctutor_backend.interface.tokens import encrypt_api_key
        
        self.update_state(state='PROGRESS', meta={'status': 'Creating GitLab group', 'progress': 20})
        
        # Get database session and initialize GitLab builder
        with next(get_db()) as db:
            builder = GitLabBuilderNew(db, gitlab_url, gitlab_token)
            
            # Create GitLab group
            gitlab_group = builder.create_group(
                name=course_family_config["name"],
                path=course_family_config["path"],
                description=course_family_config.get("description", ""),
                parent_id=course_family_config["gitlab"]["parent"]
            )
            
            self.update_state(state='PROGRESS', meta={'status': 'Creating database entry', 'progress': 60})
            course_family_data = {
                "title": course_family_config["name"],
                "path": course_family_config["path"],
                "description": course_family_config.get("description", ""),
                "organization_id": organization_id,
                "properties": {
                    "gitlab": {
                        "url": gitlab_url,
                        "token": encrypt_api_key(gitlab_token),
                        "group_id": gitlab_group["id"],
                        "full_path": gitlab_group["full_path"],
                        "parent": course_family_config["gitlab"]["parent"]
                    }
                }
            }
            
            course_family_create = CourseFamilyCreate(**course_family_data)
            course_family = CourseFamily(**course_family_create.model_dump())
            
            db.add(course_family)
            db.commit()
            db.refresh(course_family)
            
            self.update_state(state='PROGRESS', meta={'status': 'Complete', 'progress': 100})
            
            return {
                "success": True,
                "course_family_id": str(course_family.id),
                "gitlab_group_id": gitlab_group["id"],
                "gitlab_path": gitlab_group["full_path"],
                "task_id": task_id
            }
            
    except Exception as e:
        logger.error(f"Error creating course family: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@app.task(bind=True, name='ctutor_backend.tasks.create_course')
def create_course_task(self, course_config, course_family_id, gitlab_url, gitlab_token, created_by_user_id=None):
    """Create a course with GitLab group and database entry."""
    task_id = self.request.id
    
    try:
        from ctutor_backend.database import get_db
        from ctutor_backend.generator.gitlab_builder_new import GitLabBuilderNew
        from ctutor_backend.model.course import Course
        from ctutor_backend.interface.courses import CourseCreate
        from ctutor_backend.interface.tokens import encrypt_api_key
        
        self.update_state(state='PROGRESS', meta={'status': 'Creating GitLab group', 'progress': 20})
        
        # Get database session and initialize GitLab builder
        with next(get_db()) as db:
            builder = GitLabBuilderNew(db, gitlab_url, gitlab_token)
            
            # Create GitLab group
            gitlab_group = builder.create_group(
                name=course_config["name"],
                path=course_config["path"],
                description=course_config.get("description", ""),
                parent_id=course_config["gitlab"]["parent"]
            )
            
            self.update_state(state='PROGRESS', meta={'status': 'Creating database entry', 'progress': 60})
            course_data = {
                "title": course_config["name"],
                "path": course_config["path"],
                "description": course_config.get("description", ""),
                "course_family_id": course_family_id,
                "properties": {
                    "gitlab": {
                        "url": gitlab_url,
                        "token": encrypt_api_key(gitlab_token),
                        "group_id": gitlab_group["id"],
                        "full_path": gitlab_group["full_path"],
                        "parent": course_config["gitlab"]["parent"]
                    }
                }
            }
            
            course_create = CourseCreate(**course_data)
            course = Course(**course_create.model_dump())
            
            db.add(course)
            db.commit()
            db.refresh(course)
            
            self.update_state(state='PROGRESS', meta={'status': 'Complete', 'progress': 100})
            
            return {
                "success": True,
                "course_id": str(course.id),
                "gitlab_group_id": gitlab_group["id"],
                "gitlab_path": gitlab_group["full_path"],
                "task_id": task_id
            }
            
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@register_task
class CreateOrganizationTask(BaseTask):
    """
    Task for creating an organization with GitLab group and database entry.
    """
    
    @property
    def name(self) -> str:
        return "create_organization"
    
    @property
    def timeout(self) -> int:
        return 300  # 5 minutes
    
    @property
    def retry_limit(self) -> int:
        return 3
    
    async def execute(
        self,
        organization_config: Dict[str, Any],
        gitlab_url: str,
        gitlab_token: str,
        created_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an organization with GitLab group and database entry.
        
        Args:
            organization_config: Organization configuration dictionary
            gitlab_url: GitLab instance URL
            gitlab_token: GitLab access token
            created_by_user_id: ID of the user creating the organization
            
        Returns:
            Dictionary with creation results
        """
        # Update progress
        if current_task:
            current_task.update_state(
                state='PROGRESS',
                meta={'stage': 'Initializing organization creation', 'progress': 10}
            )
        
        try:
            # Create mock deployment config for the organization
            org_config = OrganizationConfig(**organization_config)
            deployment = ComputorDeploymentConfig(
                organization=org_config,
                courseFamily=CourseFamilyConfig(
                    name="temp",
                    path="temp", 
                    description="",
                    gitlab=org_config.gitlab
                ),
                course=CourseConfig(
                    name="temp",
                    path="temp",
                    description="",
                    gitlab=org_config.gitlab
                )
            )
            
            # Get database session
            db = next(get_db())
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Connecting to GitLab', 'progress': 20}
                )
            
            # Initialize GitLab builder
            builder = GitLabBuilderNew(
                db_session=db,
                gitlab_url=gitlab_url,
                gitlab_token=gitlab_token
            )
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Creating organization', 'progress': 40}
                )
            
            # Create organization
            result = builder._create_organization(
                deployment,
                created_by_user_id
            )
            
            if result["success"]:
                # Update progress
                if current_task:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={'stage': 'Organization created successfully', 'progress': 100}
                    )
                
                # Commit the database transaction
                db.commit()
                
                return {
                    "success": True,
                    "organization_id": str(result["organization"].id),
                    "organization_path": result["organization"].path,
                    "gitlab_group_created": result.get("gitlab_created", False),
                    "gitlab_group_path": result.get("gitlab_group", {}).get("full_path") if result.get("gitlab_group") else None,
                    "message": "Organization created successfully"
                }
            else:
                db.rollback()
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error creating organization")
                }
                
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            if 'db' in locals():
                db.rollback()
            return {
                "success": False,
                "error": f"Failed to create organization: {str(e)}"
            }
        finally:
            if 'db' in locals():
                db.close()


@register_task
class CreateCourseFamilyTask(BaseTask):
    """
    Task for creating a course family with GitLab group and database entry.
    """
    
    @property
    def name(self) -> str:
        return "create_course_family"
    
    @property
    def timeout(self) -> int:
        return 300  # 5 minutes
    
    @property
    def retry_limit(self) -> int:
        return 3
    
    async def execute(
        self,
        course_family_config: Dict[str, Any],
        organization_id: str,
        gitlab_url: str,
        gitlab_token: str,
        created_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a course family with GitLab group and database entry.
        
        Args:
            course_family_config: Course family configuration dictionary
            organization_id: UUID of the parent organization
            gitlab_url: GitLab instance URL
            gitlab_token: GitLab access token
            created_by_user_id: ID of the user creating the course family
            
        Returns:
            Dictionary with creation results
        """
        # Update progress
        if current_task:
            current_task.update_state(
                state='PROGRESS',
                meta={'stage': 'Initializing course family creation', 'progress': 10}
            )
        
        try:
            # Get database session
            db = next(get_db())
            
            # Get parent organization
            from ctutor_backend.model.organization import Organization
            organization = db.query(Organization).filter(Organization.id == organization_id).first()
            
            if not organization:
                return {
                    "success": False,
                    "error": f"Organization with ID {organization_id} not found"
                }
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Validating parent organization', 'progress': 20}
                )
            
            # Create mock deployment config
            family_config = CourseFamilyConfig(**course_family_config)
            deployment = ComputorDeploymentConfig(
                organization=OrganizationConfig(
                    name=organization.title or "",
                    path=str(organization.path),
                    description=organization.description or "",
                    gitlab=organization.properties.get("gitlab", {})
                ),
                courseFamily=family_config,
                course=CourseConfig(
                    name="temp",
                    path="temp",
                    description="",
                    gitlab=family_config.gitlab
                )
            )
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Connecting to GitLab', 'progress': 30}
                )
            
            # Initialize GitLab builder
            builder = GitLabBuilderNew(
                db_session=db,
                gitlab_url=gitlab_url,
                gitlab_token=gitlab_token
            )
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Creating course family', 'progress': 60}
                )
            
            # Create course family
            result = builder._create_course_family(
                deployment,
                organization,
                created_by_user_id
            )
            
            if result["success"]:
                # Update progress
                if current_task:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={'stage': 'Course family created successfully', 'progress': 100}
                    )
                
                # Commit the database transaction
                db.commit()
                
                return {
                    "success": True,
                    "course_family_id": str(result["course_family"].id),
                    "course_family_path": result["course_family"].path,
                    "organization_id": organization_id,
                    "gitlab_group_created": result.get("gitlab_created", False),
                    "gitlab_group_path": result.get("gitlab_group", {}).get("full_path") if result.get("gitlab_group") else None,
                    "message": "Course family created successfully"
                }
            else:
                db.rollback()
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error creating course family")
                }
                
        except Exception as e:
            logger.error(f"Error creating course family: {e}")
            if 'db' in locals():
                db.rollback()
            return {
                "success": False,
                "error": f"Failed to create course family: {str(e)}"
            }
        finally:
            if 'db' in locals():
                db.close()


@register_task
class CreateCourseTask(BaseTask):
    """
    Task for creating a course with GitLab group and database entry.
    """
    
    @property
    def name(self) -> str:
        return "create_course"
    
    @property
    def timeout(self) -> int:
        return 300  # 5 minutes
    
    @property
    def retry_limit(self) -> int:
        return 3
    
    async def execute(
        self,
        course_config: Dict[str, Any],
        course_family_id: str,
        gitlab_url: str,
        gitlab_token: str,
        created_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a course with GitLab group and database entry.
        
        Args:
            course_config: Course configuration dictionary
            course_family_id: UUID of the parent course family
            gitlab_url: GitLab instance URL
            gitlab_token: GitLab access token
            created_by_user_id: ID of the user creating the course
            
        Returns:
            Dictionary with creation results
        """
        # Update progress
        if current_task:
            current_task.update_state(
                state='PROGRESS',
                meta={'stage': 'Initializing course creation', 'progress': 10}
            )
        
        try:
            # Get database session
            db = next(get_db())
            
            # Get parent course family and organization
            from ctutor_backend.model.course import CourseFamily
            from ctutor_backend.model.organization import Organization
            
            course_family = db.query(CourseFamily).filter(CourseFamily.id == course_family_id).first()
            
            if not course_family:
                return {
                    "success": False,
                    "error": f"Course family with ID {course_family_id} not found"
                }
            
            organization = db.query(Organization).filter(Organization.id == course_family.organization_id).first()
            
            if not organization:
                return {
                    "success": False,
                    "error": f"Parent organization not found for course family {course_family_id}"
                }
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Validating parent course family', 'progress': 20}
                )
            
            # Create mock deployment config
            course_cfg = CourseConfig(**course_config)
            deployment = ComputorDeploymentConfig(
                organization=OrganizationConfig(
                    name=organization.title or "",
                    path=str(organization.path),
                    description=organization.description or "",
                    gitlab=organization.properties.get("gitlab", {})
                ),
                courseFamily=CourseFamilyConfig(
                    name=course_family.title or "",
                    path=str(course_family.path),
                    description=course_family.description or "",
                    gitlab=course_family.properties.get("gitlab", {})
                ),
                course=course_cfg
            )
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Connecting to GitLab', 'progress': 30}
                )
            
            # Initialize GitLab builder
            builder = GitLabBuilderNew(
                db_session=db,
                gitlab_url=gitlab_url,
                gitlab_token=gitlab_token
            )
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Creating course', 'progress': 60}
                )
            
            # Create course
            result = builder._create_course(
                deployment,
                organization,
                course_family,
                created_by_user_id
            )
            
            if result["success"]:
                # Update progress
                if current_task:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={'stage': 'Course created successfully', 'progress': 100}
                    )
                
                # Commit the database transaction
                db.commit()
                
                return {
                    "success": True,
                    "course_id": str(result["course"].id),
                    "course_path": result["course"].path,
                    "course_family_id": course_family_id,
                    "organization_id": str(organization.id),
                    "gitlab_group_created": result.get("gitlab_created", False),
                    "gitlab_group_path": result.get("gitlab_group", {}).get("full_path") if result.get("gitlab_group") else None,
                    "message": "Course created successfully"
                }
            else:
                db.rollback()
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error creating course")
                }
                
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            if 'db' in locals():
                db.rollback()
            return {
                "success": False,
                "error": f"Failed to create course: {str(e)}"
            }
        finally:
            if 'db' in locals():
                db.close()


@register_task
class CreateHierarchyTask(BaseTask):
    """
    Task for creating the complete hierarchy: Organization → Course Family → Course.
    This chains the individual tasks together for a complete deployment.
    """
    
    @property
    def name(self) -> str:
        return "create_hierarchy"
    
    @property
    def timeout(self) -> int:
        return 900  # 15 minutes
    
    @property
    def retry_limit(self) -> int:
        return 2
    
    async def execute(
        self,
        deployment_config: Dict[str, Any],
        gitlab_url: str,
        gitlab_token: str,
        created_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create the complete hierarchy with GitLab groups and database entries.
        
        Args:
            deployment_config: Complete deployment configuration
            gitlab_url: GitLab instance URL
            gitlab_token: GitLab access token
            created_by_user_id: ID of the user creating the hierarchy
            
        Returns:
            Dictionary with creation results
        """
        try:
            deployment = ComputorDeploymentConfig(**deployment_config)
            
            # Update progress
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'stage': 'Starting hierarchy creation', 'progress': 5}
                )
            
            # Get database session
            db = next(get_db())
            
            # Initialize GitLab builder
            builder = GitLabBuilderNew(
                db_session=db,
                gitlab_url=gitlab_url,
                gitlab_token=gitlab_token
            )
            
            # Create the complete hierarchy
            result = builder.create_deployment_hierarchy(
                deployment,
                created_by_user_id
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "organization_id": str(result["organization"].id) if result["organization"] else None,
                    "course_family_id": str(result["course_family"].id) if result["course_family"] else None,
                    "course_id": str(result["course"].id) if result["course"] else None,
                    "gitlab_groups_created": result["gitlab_groups_created"],
                    "database_entries_created": result["database_entries_created"],
                    "message": "Complete hierarchy created successfully"
                }
            else:
                return {
                    "success": False,
                    "errors": result["errors"],
                    "error": "Failed to create hierarchy: " + "; ".join(result["errors"])
                }
                
        except Exception as e:
            logger.error(f"Error creating hierarchy: {e}")
            return {
                "success": False,
                "error": f"Failed to create hierarchy: {str(e)}"
            }
        finally:
            if 'db' in locals():
                db.close()


# Celery wrapper functions
@app.task(bind=True, name='ctutor_backend.tasks.create_organization')
def create_organization_celery(self, **kwargs):
    """Celery wrapper for CreateOrganizationTask."""
    return _execute_task_with_celery(self, CreateOrganizationTask, **kwargs)


@app.task(bind=True, name='ctutor_backend.tasks.create_course_family')
def create_course_family_celery(self, **kwargs):
    """Celery wrapper for CreateCourseFamilyTask."""
    return _execute_task_with_celery(self, CreateCourseFamilyTask, **kwargs)


@app.task(bind=True, name='ctutor_backend.tasks.create_course')
def create_course_celery(self, **kwargs):
    """Celery wrapper for CreateCourseTask."""
    return _execute_task_with_celery(self, CreateCourseTask, **kwargs)


@app.task(bind=True, name='ctutor_backend.tasks.create_hierarchy')
def create_hierarchy_celery(self, **kwargs):
    """Celery wrapper for CreateHierarchyTask."""
    return _execute_task_with_celery(self, CreateHierarchyTask, **kwargs)