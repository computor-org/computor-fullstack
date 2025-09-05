"""
Temporal workflows for generating student templates from Example Library.
Version 2: Fixed deployment status handling and sandbox restrictions.
"""
import logging
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from .temporal_base import BaseWorkflow, WorkflowResult
from .registry import register_task

logger = logging.getLogger(__name__)


async def download_example_files(repository: Any, version: Any) -> Dict[str, bytes]:
    """
    Download example files from repository based on its source type.
    
    Args:
        repository: ExampleRepository with source type information
        version: ExampleVersion with storage path information
        
    Returns:
        Dictionary mapping file paths to their content
        
    Raises:
        NotImplementedError: For unsupported repository types
        ValueError: For invalid source types
    """
    if repository.source_type == 'git':
        return await download_example_from_git(repository, version)
    elif repository.source_type in ['minio', 's3']:
        return await download_example_from_object_storage(repository, version)
    else:
        raise ValueError(f"Unsupported source type: {repository.source_type}")


async def download_example_from_git(repository: Any, version: Any) -> Dict[str, bytes]:
    """Download example files from Git repository."""
    import os
    import tempfile
    import shutil
    import git
    
    files = {}
    temp_dir = tempfile.mkdtemp()
    
    try:
        repo = git.Repo.clone_from(repository.url, temp_dir, branch=version.version_tag)
        
        for root, dirs, file_list in os.walk(temp_dir):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file_name in file_list:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, temp_dir)
                
                with open(file_path, 'rb') as f:
                    files[relative_path] = f.read()
        
        return files
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def download_example_from_object_storage(repository: Any, version: Any) -> Dict[str, bytes]:
    """Download example files from MinIO/S3 object storage."""
    from ..services.storage_service import StorageService
    
    # Determine bucket name based on repository properties
    bucket_name = repository.properties.get('bucket', 'examples')
    
    # Use the storage path from version to locate files
    prefix = version.storage_path
    if not prefix:
        # Fallback: construct path from example identifier and version
        example_id = repository.example_id
        prefix = f"{example_id}/{version.version_tag}"
    
    logger.info(f"Downloading from bucket: {bucket_name}, prefix: {prefix}")
    
    # Initialize storage service
    storage = StorageService()
    
    # List and download all files with the prefix
    files = {}
    try:
        objects = storage.client.list_objects(bucket_name, prefix=prefix, recursive=True)
        
        for obj in objects:
            # Skip directories
            if obj.object_name.endswith('/'):
                continue
            
            # Get relative path (remove prefix)
            relative_path = obj.object_name[len(prefix):].lstrip('/')
            
            # Download file content
            response = storage.client.get_object(bucket_name, obj.object_name)
            files[relative_path] = response.read()
            response.close()
            response.release_conn()
        
        return files
    except Exception as e:
        logger.error(f"Failed to download from object storage: {e}")
        raise


# Activities
@activity.defn(name="generate_student_template_activity_v2")
async def generate_student_template_activity_v2(
    course_id: str, 
    student_template_url: str,
    workflow_id: str = None
) -> Dict[str, Any]:
    """
    Generate student template repository from examples assigned to course content.
    
    This activity:
    1. Sets all assigned deployments to 'deploying' status
    2. Clones/creates the student-template repository
    3. Downloads example files from MinIO/S3
    4. Processes examples (removes solutions, adds README)
    5. Commits and pushes to GitLab
    6. Updates deployment status and tracking
    
    Args:
        course_id: Course to generate template for
        student_template_url: GitLab URL of student template repository
        workflow_id: Temporal workflow ID for tracking
    
    Returns:
        Dict with success status and details
    """
    # Import all SQLAlchemy models and database dependencies inside activity
    import git
    import os
    import tempfile
    import shutil
    from pathlib import Path
    from datetime import datetime, timezone
    from sqlalchemy.orm import joinedload
    from sqlalchemy import and_
    from ..utils.docker_utils import transform_localhost_url
    from ..database import get_db
    from ..model.course import Course, CourseContent
    from ..model.example import Example, ExampleVersion, ExampleRepository
    from ..model.deployment import CourseContentDeployment, DeploymentHistory
    from ..model.execution import ExecutionBackend
    from ..services.storage_service import StorageService
    
    db_gen = next(get_db())
    db = db_gen
    
    try:
        # First, update all assigned deployments to 'deploying' status
        logger.info(f"Updating deployments to 'deploying' status for course {course_id}")
        
        deployments_to_process = db.query(CourseContentDeployment).join(
            CourseContent
        ).filter(
            and_(
                CourseContent.course_id == course_id,
                CourseContentDeployment.example_version_id.isnot(None),  # Has an assigned example
                CourseContentDeployment.deployment_status.in_(["pending", "failed"])  # Ready to deploy
            )
        ).all()
        
        # Update all to 'deploying' and add history
        for deployment in deployments_to_process:
            deployment.deployment_status = "deploying"
            deployment.last_attempt_at = datetime.now(timezone.utc)
            if workflow_id:
                deployment.workflow_id = workflow_id
            
            # Add history entry
            history = DeploymentHistory(
                deployment_id=deployment.id,
                action="deploying",
                action_details="Started deployment via student template generation",
                example_version_id=deployment.example_version_id,
                performed_by="system"
            )
            db.add(history)
        
        db.commit()
        
        logger.info(f"Updated {len(deployments_to_process)} deployments to 'deploying' status")
        
        # Transform localhost URLs for Docker environments
        student_template_url = transform_localhost_url(student_template_url)
        logger.info(f"Using student template URL: {student_template_url}")
        
        # Check if we need GitLab token
        gitlab_token = os.getenv('GITLAB_TOKEN')
        
        # Use temp directory for repository work
        with tempfile.TemporaryDirectory() as temp_dir:
            template_repo_path = os.path.join(temp_dir, "student-template")
            
            # Create authenticated URL if we have a token and it's HTTP
            auth_url = student_template_url
            if gitlab_token and 'http' in student_template_url:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(student_template_url)
                auth_netloc = f"oauth2:{gitlab_token}@{parsed.hostname}"
                if parsed.port:
                    auth_netloc += f":{parsed.port}"
                auth_url = urlunparse((
                    parsed.scheme,
                    auth_netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
            
            # Try to clone existing repo or create new one
            try:
                if gitlab_token and 'http' in student_template_url:
                    template_repo = git.Repo.clone_from(auth_url, template_repo_path)
                else:
                    template_repo = git.Repo.clone_from(student_template_url, template_repo_path)
            except Exception as e:
                logger.info(f"Could not clone student template repo, creating new: {e}")
                os.makedirs(template_repo_path, exist_ok=True)
                template_repo = git.Repo.init(template_repo_path)
                
                # Set default branch to main
                template_repo.git.checkout('-b', 'main')
                
                # Add remote
                if 'http' in student_template_url:
                    template_repo.create_remote('origin', student_template_url)
            
            # Get all CourseContent with assigned examples (deployments in 'deploying' status)
            course_contents = db.query(CourseContent).options(
                joinedload(CourseContent.deployment).joinedload(CourseContentDeployment.example_version).joinedload(ExampleVersion.example).joinedload(Example.versions),
                joinedload(CourseContent.deployment).joinedload(CourseContentDeployment.example_version).joinedload(ExampleVersion.example).joinedload(Example.repository)
            ).filter(
                CourseContent.course_id == course_id,
                CourseContent.id.in_(
                    db.query(CourseContentDeployment.course_content_id)
                    .filter(
                        CourseContentDeployment.deployment_status == "deploying",
                        CourseContentDeployment.example_version_id.isnot(None)
                    )
                ),
                CourseContent.archived_at.is_(None)
            ).order_by(CourseContent.path).all()
            
            logger.info(f"Found {len(course_contents)} course contents to deploy")
            
            if len(course_contents) == 0:
                logger.warning(f"No course contents to deploy for course {course_id}. This will result in an empty student template.")
            
            # Process each CourseContent with an example
            processed_count = 0
            errors = []
            
            for content in course_contents:
                try:
                    if not content.deployment or not content.deployment.example_version:
                        logger.error(f"No deployment found for {content.path}")
                        errors.append(f"No deployment found for {content.path}")
                        continue
                        
                    example_version = content.deployment.example_version
                    example = example_version.example
                    
                    logger.info(f"Processing {content.path} with example {example.id} version {example_version.version_tag}")
                    
                    if not example:
                        logger.error(f"Example not found for deployment at {content.path}")
                        errors.append(f"Example not found for {content.path}")
                        continue
                    
                    # Get the repository to determine bucket name
                    repository = example.repository
                    if not repository:
                        logger.error(f"Repository not found for example {example.id}")
                        errors.append(f"Repository not found for {content.path}")
                        continue
                    
                    # Extract execution backend slug from meta_yaml and link to course_content
                    if not content.execution_backend_id:
                        backend_slug = example.get_execution_backend_slug(example_version.version_tag)
                        if backend_slug:
                            # Find the execution backend by slug
                            exec_backend = db.query(ExecutionBackend).filter(
                                ExecutionBackend.slug == backend_slug
                            ).first()
                            
                            if exec_backend:
                                # Link the execution backend to the course content
                                content.execution_backend_id = exec_backend.id
                                logger.info(f"Linked execution backend '{backend_slug}' to course content {content.path}")
                            else:
                                logger.warning(f"Execution backend '{backend_slug}' not found in database for {content.path}")
                    
                    # Download example files based on repository source type
                    files = await download_example_files(repository, example_version)
                    
                    if not files:
                        logger.error(f"No files downloaded for {content.path}")
                        errors.append(f"No files downloaded for {content.path}")
                        continue
                    
                    logger.info(f"Downloaded {len(files)} files for {content.path}")
                    
                    # Determine target directory in student template
                    # Use the path from course_content, removing any leading/trailing slashes
                    target_dir = content.path.strip('/')
                    full_target_path = os.path.join(template_repo_path, target_dir)
                    
                    # Create target directory if it doesn't exist
                    os.makedirs(full_target_path, exist_ok=True)
                    
                    # Write each file to the student template repository
                    for file_path, file_content in files.items():
                        # Skip solution files
                        if 'solution' in file_path.lower() or 'loesung' in file_path.lower():
                            logger.debug(f"Skipping solution file: {file_path}")
                            continue
                        
                        # Full path for the file in the template repo
                        full_file_path = os.path.join(full_target_path, file_path)
                        
                        # Create parent directories if needed
                        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
                        
                        # Write file
                        with open(full_file_path, 'wb') as f:
                            f.write(file_content)
                        
                        logger.debug(f"Wrote {file_path} to {full_file_path}")
                    
                    # Create a simple README for the assignment
                    readme_path = os.path.join(full_target_path, "README.md")
                    if not os.path.exists(readme_path):
                        readme_content = f"""# {content.title}

This is your assignment workspace for **{content.title}**.

## Assignment Path
`{content.path}`

## Instructions
Please refer to the course materials for detailed instructions.

## Submission
Follow the course submission guidelines to submit your work.
"""
                        with open(readme_path, 'w') as f:
                            f.write(readme_content)
                        logger.debug(f"Created README.md for {content.path}")
                    
                    processed_count += 1
                    logger.info(f"Successfully processed {content.path}")
                    
                    # Update deployment status to deployed with history
                    content.deployment.deployment_status = "deployed"
                    content.deployment.deployed_at = datetime.now(timezone.utc)
                    
                    # Add success history entry
                    history = DeploymentHistory(
                        deployment_id=content.deployment.id,
                        action="deployed",
                        action_details=f"Successfully deployed to student template at {target_dir}",
                        example_version_id=content.deployment.example_version_id,
                        performed_by="system"
                    )
                    db.add(history)
                    
                except Exception as e:
                    error_msg = f"Failed to process {content.path}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    
                    # Update deployment status to failed with history
                    if content.deployment:
                        content.deployment.deployment_status = "failed"
                        content.deployment.deployment_message = str(e)[:500]  # Truncate error message
                        
                        # Add failure history entry
                        history = DeploymentHistory(
                            deployment_id=content.deployment.id,
                            action="failed",
                            action_details=f"Failed to deploy: {str(e)[:200]}",
                            example_version_id=content.deployment.example_version_id,
                            performed_by="system"
                        )
                        db.add(history)
            
            # Commit database changes
            db.commit()
            
            # If we processed any content, commit and push to Git
            if processed_count > 0:
                try:
                    # Stage all changes
                    template_repo.git.add(A=True)
                    
                    # Check if there are changes to commit
                    if template_repo.is_dirty():
                        # Commit changes
                        commit_message = f"Deploy {processed_count} examples from Example Library"
                        template_repo.index.commit(commit_message)
                        logger.info(f"Committed changes: {commit_message}")
                        
                        # Push to remote
                        if 'origin' in [remote.name for remote in template_repo.remotes]:
                            if gitlab_token and 'http' in student_template_url:
                                # Push with authentication
                                template_repo.git.push('origin', 'main', env={'GIT_ASKPASS': 'echo', 'GIT_USERNAME': 'oauth2', 'GIT_PASSWORD': gitlab_token})
                            else:
                                template_repo.git.push('origin', 'main')
                            logger.info("Pushed changes to GitLab")
                        else:
                            logger.warning("No remote 'origin' found, skipping push")
                    else:
                        logger.info("No changes to commit")
                        
                except Exception as e:
                    error_msg = f"Failed to commit/push changes: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Prepare result
            success = processed_count > 0 and len(errors) < len(course_contents)
            
            result = {
                "success": success,
                "processed_count": processed_count,
                "total_count": len(course_contents),
                "errors": errors,
                "message": f"Processed {processed_count}/{len(course_contents)} examples"
            }
            
            if errors:
                result["message"] += f" with {len(errors)} errors"
            
            return result
            
    except Exception as e:
        logger.error(f"Failed to generate student template: {str(e)}", exc_info=True)
        
        # Mark all 'deploying' deployments as failed
        try:
            failed_deployments = db.query(CourseContentDeployment).join(
                CourseContent
            ).filter(
                and_(
                    CourseContent.course_id == course_id,
                    CourseContentDeployment.deployment_status == "deploying"
                )
            ).all()
            
            for deployment in failed_deployments:
                deployment.deployment_status = "failed"
                deployment.deployment_message = str(e)[:500]
                
                # Add failure history
                history = DeploymentHistory(
                    deployment_id=deployment.id,
                    action="failed",
                    action_details=f"Workflow failed: {str(e)[:200]}",
                    example_version_id=deployment.example_version_id,
                    performed_by="system"
                )
                db.add(history)
            
            db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update deployment statuses: {db_error}")
        
        return {
            "success": False,
            "processed_count": 0,
            "errors": [str(e)],
            "message": f"Failed to generate student template: {str(e)}"
        }
    finally:
        db_gen.close()


@register_task
@workflow.defn(name="generate_student_template_v2", sandboxed=False)
class GenerateStudentTemplateWorkflowV2(BaseWorkflow):
    """
    Temporal workflow for generating student template repositories.
    
    This workflow orchestrates the generation of student templates from
    examples stored in the Example Library.
    """
    
    @classmethod
    def get_name(cls) -> str:
        """Get the workflow name for registration."""
        return "generate_student_template_v2"

    @classmethod
    def get_task_queue(cls) -> str:
        return "computor-tasks"
    
    @classmethod
    def get_execution_timeout(cls) -> timedelta:
        return timedelta(minutes=30)
    
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> WorkflowResult:
        """Run the student template generation workflow."""
        course_id = params.get('course_id')
        student_template_url = params.get('student_template_url')
        
        if not course_id:
            return WorkflowResult(
                status="failed",
                result=None,
                error="course_id is required"
            )
        
        if not student_template_url:
            return WorkflowResult(
                status="failed",
                result=None,
                error="student_template_url is required"
            )
        
        # Get workflow ID for tracking
        workflow_id = workflow.info().workflow_id
        
        # Execute the activity with retry policy
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
            backoff_coefficient=2.0
        )
        
        try:
            result = await workflow.execute_activity(
                generate_student_template_activity_v2,
                args=[course_id, student_template_url, workflow_id],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy
            )
            
            return WorkflowResult(
                status="completed" if result.get('success', False) else "failed",
                result=result,
                error=result.get('errors', []) if not result.get('success') else None,
                metadata={"workflow_id": workflow_id}
            )
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            return WorkflowResult(
                status="failed",
                result=None,
                error=str(e)
            )