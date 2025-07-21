"""
Celery tasks for organization, course family, and course hierarchy management.

These tasks handle the creation of GitLab groups and corresponding database entries
for the hierarchical structure: Organization → Course Family → Course.
"""

import logging
import tempfile
import os
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
from ctutor_backend.model.course import Course
from ctutor_backend.interface.deployments import (
    ComputorDeploymentConfig,
    OrganizationConfig,
    CourseFamilyConfig,
    CourseConfig
)

logger = logging.getLogger(__name__)


def _resolve_gitlab_url_for_docker(gitlab_url: str) -> str:
    """
    Resolve GitLab URL for Docker environment.
    
    When running in Docker, localhost URLs need to be converted to use the Docker host IP.
    This handles the common case where GitLab URL is stored as localhost in the database
    but needs to be accessed as the Docker host IP from within containers.
    
    Args:
        gitlab_url: Original GitLab URL from database
        
    Returns:
        Resolved GitLab URL appropriate for the current environment
    """
    # Check if we're running in Docker
    is_docker = (
        os.path.exists('/.dockerenv') or 
        os.environ.get('DOCKER_ENV') == 'true' or
        os.environ.get('IN_DOCKER') == 'true'
    )
    
    if is_docker and 'localhost' in gitlab_url:
        # Replace localhost with Docker host IP
        resolved_url = gitlab_url.replace('localhost', '172.17.0.1')
        logger.info(f"Docker environment detected, resolved GitLab URL: {gitlab_url} -> {resolved_url}")
        return resolved_url
    
    # Use original URL if not in Docker or doesn't contain localhost
    return gitlab_url


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
        import gitlab
        
        self.update_state(state='PROGRESS', meta={'status': 'Connecting to GitLab', 'progress': 10})
        
        # Resolve GitLab URL for Docker environment
        resolved_gitlab_url = _resolve_gitlab_url_for_docker(gitlab_url)
        
        # Connect to GitLab
        gl = gitlab.Gitlab(resolved_gitlab_url, private_token=gitlab_token, keep_base_url=True)
        gl.auth()
        
        self.update_state(state='PROGRESS', meta={'status': 'Creating GitLab group', 'progress': 30})
        
        # Create GitLab group
        parent_id = organization_config["gitlab"]["parent"]
        group_data = {
            "name": organization_config["name"],
            "path": organization_config["path"],
            "description": organization_config.get("description", ""),
            "visibility": "private"
        }
        
        if parent_id:
            group_data["parent_id"] = parent_id
        
        try:
            # Check if group already exists
            groups = gl.groups.list(search=organization_config["path"], all=True)
            gitlab_group = None
            
            for g in groups:
                if g.path == organization_config["path"]:
                    gitlab_group = g
                    logger.info(f"Found existing GitLab group: {g.full_path}")
                    break
            
            if not gitlab_group:
                gitlab_group = gl.groups.create(group_data)
                logger.info(f"Created new GitLab group: {gitlab_group.full_path}")
            
        except Exception as e:
            logger.error(f"Error creating GitLab group: {e}")
            # Continue with database creation even if GitLab fails
            gitlab_group = None
        
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
                        "parent": organization_config["gitlab"]["parent"]
                    }
                }
            }
            
            # Add GitLab group info if created
            if gitlab_group:
                organization_data["properties"]["gitlab"]["group_id"] = gitlab_group.id
                organization_data["properties"]["gitlab"]["full_path"] = gitlab_group.full_path
                organization_data["properties"]["gitlab"]["web_url"] = gitlab_group.web_url
            
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
                "gitlab_group_id": gitlab_group.id if gitlab_group else None,
                "gitlab_path": gitlab_group.full_path if gitlab_group else None,
                "gitlab_web_url": gitlab_group.web_url if gitlab_group else None,
                "task_id": task_id
            }
            
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@app.task(bind=True, name='ctutor_backend.tasks.create_course_family')  
def create_course_family_task(self, course_family_config, organization_id, created_by_user_id=None):
    """Create a course family with GitLab group and database entry."""
    task_id = self.request.id
    
    try:
        from ctutor_backend.database import get_db
        from ctutor_backend.model.organization import Organization
        from ctutor_backend.model.course import CourseFamily
        from ctutor_backend.interface.course_families import CourseFamilyCreate
        from ctutor_backend.interface.tokens import encrypt_api_key, decrypt_api_key
        import gitlab
        
        # Get database session
        with next(get_db()) as db:
            # Fetch organization to get GitLab config
            organization = db.query(Organization).filter(Organization.id == organization_id).first()
            if not organization:
                raise Exception(f"Organization {organization_id} not found")
            
            # Check if organization has GitLab integration
            gitlab_config = organization.properties.get("gitlab", {})
            gitlab_group = None
            
            if course_family_config.get("has_gitlab") and gitlab_config.get("group_id"):
                # Get GitLab credentials from organization
                gitlab_url = gitlab_config.get("url")
                gitlab_token_encrypted = gitlab_config.get("token")
                parent_group_id = gitlab_config.get("group_id")
                
                if not gitlab_url or not gitlab_token_encrypted:
                    raise Exception("Organization has GitLab integration but missing credentials")
                
                # Decrypt the token
                gitlab_token = decrypt_api_key(gitlab_token_encrypted)
                
                self.update_state(state='PROGRESS', meta={'status': 'Connecting to GitLab', 'progress': 10})
                
                # Resolve GitLab URL for Docker environment
                resolved_gitlab_url = _resolve_gitlab_url_for_docker(gitlab_url)
                
                # Connect to GitLab
                gl = gitlab.Gitlab(resolved_gitlab_url, private_token=gitlab_token, keep_base_url=True)
                gl.auth()
                
                self.update_state(state='PROGRESS', meta={'status': 'Creating GitLab subgroup', 'progress': 30})
                
                # Create GitLab subgroup under parent
                group_data = {
                    "name": course_family_config["name"],
                    "path": course_family_config["path"],
                    "description": course_family_config.get("description", ""),
                    "visibility": "private",
                    "parent_id": parent_group_id
                }
                
                try:
                    # Check if group already exists
                    groups = gl.groups.list(search=course_family_config["path"], all=True)
                    
                    for g in groups:
                        if g.path == course_family_config["path"] and g.parent_id == parent_group_id:
                            gitlab_group = g
                            logger.info(f"Found existing GitLab group: {g.full_path}")
                            break
                    
                    if not gitlab_group:
                        gitlab_group = gl.groups.create(group_data)
                        logger.info(f"Created new GitLab subgroup: {gitlab_group.full_path}")
                
                except Exception as e:
                    logger.error(f"Error creating GitLab group: {e}")
                    raise
            
            self.update_state(state='PROGRESS', meta={'status': 'Creating database entry', 'progress': 60})
            
            # Build course family data
            course_family_data = {
                "title": course_family_config["name"],
                "path": course_family_config["path"],
                "description": course_family_config.get("description", ""),
                "organization_id": organization_id,
                "properties": {}
            }
            
            # Add GitLab properties if GitLab group was created
            if gitlab_group:
                course_family_data["properties"]["gitlab"] = {
                    "url": gitlab_url,
                    "token": encrypt_api_key(gitlab_token),
                    "group_id": gitlab_group.id,
                    "full_path": gitlab_group.full_path,
                    "web_url": gitlab_group.web_url,
                    "parent": parent_group_id
                }
            
            # Convert path to Ltree format (replace hyphens with underscores)
            from sqlalchemy_utils import Ltree
            ltree_path = course_family_config["path"].replace('-', '_')
            
            course_family_create = CourseFamilyCreate(**course_family_data)
            course_family_dict = course_family_create.model_dump()
            course_family_dict['path'] = Ltree(ltree_path)
            course_family = CourseFamily(**course_family_dict)
            
            db.add(course_family)
            db.commit()
            db.refresh(course_family)
            
            self.update_state(state='PROGRESS', meta={'status': 'Complete', 'progress': 100})
            
            result = {
                "success": True,
                "course_family_id": str(course_family.id),
                "task_id": task_id
            }
            
            if gitlab_group:
                result.update({
                    "gitlab_group_id": gitlab_group.id,
                    "gitlab_path": gitlab_group.full_path,
                    "gitlab_web_url": gitlab_group.web_url
                })
            
            return result
            
    except Exception as e:
        logger.error(f"Error creating course family: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@app.task(bind=True, name='ctutor_backend.tasks.create_course')
def create_course_task(self, course_config, course_family_id, created_by_user_id=None):
    """Create a course with GitLab group and database entry."""
    task_id = self.request.id
    
    try:
        from ctutor_backend.database import get_db
        from ctutor_backend.model.course import Course, CourseFamily
        from ctutor_backend.interface.courses import CourseCreate
        from ctutor_backend.interface.tokens import encrypt_api_key, decrypt_api_key
        import gitlab
        
        # Get database session
        with next(get_db()) as db:
            # Fetch course family to get GitLab config
            course_family = db.query(CourseFamily).filter(CourseFamily.id == course_family_id).first()
            if not course_family:
                raise Exception(f"Course family {course_family_id} not found")
            
            # Check if course family has GitLab integration
            gitlab_config = course_family.properties.get("gitlab", {})
            gitlab_group = None
            
            if course_config.get("has_gitlab") and gitlab_config.get("group_id"):
                # Get GitLab credentials from course family
                gitlab_url = gitlab_config.get("url")
                gitlab_token_encrypted = gitlab_config.get("token")
                parent_group_id = gitlab_config.get("group_id")
                
                if not gitlab_url or not gitlab_token_encrypted:
                    raise Exception("Course family has GitLab integration but missing credentials")
                
                # Decrypt the token
                gitlab_token = decrypt_api_key(gitlab_token_encrypted)
                
                self.update_state(state='PROGRESS', meta={'status': 'Connecting to GitLab', 'progress': 10})
                
                # Resolve GitLab URL for Docker environment
                resolved_gitlab_url = _resolve_gitlab_url_for_docker(gitlab_url)
                
                # Connect to GitLab
                gl = gitlab.Gitlab(resolved_gitlab_url, private_token=gitlab_token, keep_base_url=True)
                gl.auth()
                
                self.update_state(state='PROGRESS', meta={'status': 'Creating GitLab subgroup', 'progress': 30})
                
                # Create GitLab subgroup under parent
                group_data = {
                    "name": course_config["name"],
                    "path": course_config["path"],
                    "description": course_config.get("description", ""),
                    "visibility": "private",
                    "parent_id": parent_group_id
                }
                
                try:
                    # Check if group already exists
                    groups = gl.groups.list(search=course_config["path"], all=True)
                    
                    for g in groups:
                        if g.path == course_config["path"] and g.parent_id == parent_group_id:
                            gitlab_group = g
                            logger.info(f"Found existing GitLab group: {g.full_path}")
                            break
                    
                    if not gitlab_group:
                        gitlab_group = gl.groups.create(group_data)
                        logger.info(f"Created new GitLab subgroup: {gitlab_group.full_path}")
                
                except Exception as e:
                    logger.error(f"Error creating GitLab group: {e}")
                    raise
            
            self.update_state(state='PROGRESS', meta={'status': 'Creating database entry', 'progress': 60})
            
            # Build course data
            course_data = {
                "title": course_config["name"],
                "path": course_config["path"],
                "description": course_config.get("description", ""),
                "course_family_id": course_family_id,
                "organization_id": course_family.organization_id,  # Required field from course family
                "properties": {}
            }
            
            # Add GitLab properties if GitLab group was created
            if gitlab_group:
                course_data["properties"]["gitlab"] = {
                    "url": gitlab_url,
                    "token": encrypt_api_key(gitlab_token),
                    "group_id": gitlab_group.id,
                    "full_path": gitlab_group.full_path,
                    "web_url": gitlab_group.web_url,
                    "parent": parent_group_id
                }
            
            # Convert path to Ltree format (replace hyphens with underscores)
            from sqlalchemy_utils import Ltree
            ltree_path = course_config["path"].replace('-', '_')
            
            course_create = CourseCreate(**course_data)
            course_dict = course_create.model_dump()
            course_dict['path'] = Ltree(ltree_path)
            # Manually add organization_id from course family relationship
            course_dict['organization_id'] = course_family.organization_id
            course = Course(**course_dict)
            
            db.add(course)
            db.flush()  # Get the ID before additional GitLab operations
            
            # Additional GitLab setup if GitLab group was created
            if gitlab_group:
                self.update_state(state='PROGRESS', meta={'status': 'Creating students group', 'progress': 70})
                
                # Create students group under the course
                students_group_result = _create_students_group(
                    course=course,
                    parent_group=gitlab_group,
                    gl=gl
                )
                
                if not students_group_result["success"]:
                    logger.warning(f"Failed to create students group: {students_group_result['error']}")
                else:
                    logger.info(f"Created students group: {students_group_result['gitlab_group'].full_path}")
                
                self.update_state(state='PROGRESS', meta={'status': 'Creating course projects', 'progress': 80})
                
                # Create course projects (assignments, student-template, reference)
                projects_result = _create_course_projects(
                    course=course,
                    parent_group=gitlab_group,
                    gl=gl
                )
                
                if not projects_result["success"]:
                    logger.warning(f"Failed to create course projects: {projects_result['error']}")
                else:
                    logger.info(f"Created course projects: {', '.join(projects_result['created_projects'])}")
            
            db.commit()
            db.refresh(course)
            
            self.update_state(state='PROGRESS', meta={'status': 'Complete', 'progress': 100})
            
            result = {
                "success": True,
                "course_id": str(course.id),
                "task_id": task_id
            }
            
            if gitlab_group:
                result.update({
                    "gitlab_group_id": gitlab_group.id,
                    "gitlab_path": gitlab_group.full_path,
                    "gitlab_web_url": gitlab_group.web_url
                })
            
            return result
            
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

def _create_students_group(
    course,
    parent_group,
    gl
) -> Dict[str, Any]:
    """Create students group under a course."""
    result = {
        "success": False,
        "gitlab_group": None,
        "error": None
    }
    
    try:
        # Check if students group already exists
        students_path = "students"
        
        # Try to find existing students group
        try:
            existing_groups = parent_group.subgroups.list(search=students_path)
            for group in existing_groups:
                if group.path == students_path:
                    students_group = gl.groups.get(group.id)
                    logger.info(f"Students group already exists: {students_group.full_path}")
                    result["gitlab_group"] = students_group
                    result["success"] = True
                    return result
        except Exception as e:
            logger.warning(f"Error checking for existing students group: {e}")
        
        # Create students group
        group_data = {
            'name': 'Students',
            'path': students_path,
            'parent_id': parent_group.id,
            'description': f'Students group for {course.title}',
            'visibility': 'private'
        }
        
        students_group = gl.groups.create(group_data)
        logger.info(f"Created students group: {students_group.full_path}")
        
        # Update course properties to include students group info
        if not course.properties:
            course.properties = {}
        
        if "gitlab" not in course.properties:
            course.properties["gitlab"] = {}
        
        course.properties["gitlab"]["students_group"] = {
            "group_id": students_group.id,
            "full_path": students_group.full_path,
            "web_url": f"{gl.api_url.replace('/api/v4', '')}/groups/{students_group.full_path}",
            "created_at": datetime.now().isoformat()
        }
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(course, "properties")
        
        result["gitlab_group"] = students_group
        result["success"] = True
        
    except Exception as e:
        logger.error(f"Failed to create students group: {e}")
        result["error"] = str(e)
    
    return result
    
def _create_course_projects(
    course,
    parent_group,
    gl
) -> Dict[str, Any]:
    """Create course projects (assignments, student-template, reference) under a course."""
    result = {
        "success": False,
        "created_projects": [],
        "existing_projects": [],
        "error": None
    }
    
    # Standard course projects
    project_configs = [
        {
            "name": "Assignments",
            "path": "assignments",
            "description": f"Assignment templates and grading scripts for {course.title}",
            "visibility": "private"
        },
        {
            "name": "Student Template",
            "path": "student-template",
            "description": f"Template repository for students in {course.title}",
            "visibility": "private"
        },
        {
            "name": "Reference",
            "path": "reference",
            "description": f"Reference solutions and instructor materials for {course.title}",
            "visibility": "private"
        }
    ]
    
    try:
        for project_config in project_configs:
            project_path = project_config["path"]
            
            # Check if project already exists
            try:
                existing_projects = gl.projects.list(
                    search=project_path,
                    namespace_id=parent_group.id
                )
                
                project_exists = False
                for existing in existing_projects:
                    if existing.path == project_path and existing.namespace['id'] == parent_group.id:
                        logger.info(f"Project already exists: {existing.path_with_namespace}")
                        result["existing_projects"].append(project_path)
                        project_exists = True
                        break
                
                if not project_exists:
                    # Create project
                    project_data = {
                        'name': project_config["name"],
                        'path': project_path,
                        'namespace_id': parent_group.id,
                        'description': project_config["description"],
                        'visibility': project_config["visibility"],
                        'initialize_with_readme': True,
                        'default_branch': 'main'
                    }
                    
                    project = gl.projects.create(project_data)
                    logger.info(f"Created project: {project.path_with_namespace}")
                    result["created_projects"].append(project_path)
                    
            except Exception as e:
                logger.warning(f"Error creating project {project_path}: {e}")
                continue
        
        # Update course properties to include projects info
        if not course.properties:
            course.properties = {}
        
        if "gitlab" not in course.properties:
            course.properties["gitlab"] = {}
        
        course.properties["gitlab"]["projects"] = {
            "assignments": {
                "path": "assignments",
                "full_path": f"{parent_group.full_path}/assignments",
                "web_url": f"{gl.api_url.replace('/api/v4', '')}/{parent_group.full_path}/assignments",
                "description": "Assignment templates and grading scripts"
            },
            "student_template": {
                "path": "student-template",
                "full_path": f"{parent_group.full_path}/student-template",
                "web_url": f"{gl.api_url.replace('/api/v4', '')}/{parent_group.full_path}/student-template",
                "description": "Template repository for students"
            },
            "reference": {
                "path": "reference",
                "full_path": f"{parent_group.full_path}/reference",
                "web_url": f"{gl.api_url.replace('/api/v4', '')}/{parent_group.full_path}/reference",
                "description": "Reference solutions and instructor materials"
            },
            "created_at": datetime.now().isoformat()
        }
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(course, "properties")
        
        result["success"] = True
        
    except Exception as e:
        logger.error(f"Failed to create course projects: {e}")
        result["error"] = str(e)
    
    return result


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




@app.task(bind=True, name='ctutor_backend.tasks.create_hierarchy')
def create_hierarchy_celery(self, **kwargs):
    """Celery wrapper for CreateHierarchyTask."""
    return _execute_task_with_celery(self, CreateHierarchyTask, **kwargs)