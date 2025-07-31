"""
Temporal workflows for deploying examples from Example Library to course repositories.
"""
import logging
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import shutil
import yaml

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from sqlalchemy.orm import Session
from sqlalchemy import update
from minio import Minio
import git

from .temporal_base import BaseWorkflow, WorkflowResult
from .registry import register_task
from ..database import get_db
from ..model.course import CourseContent, Course
from ..model.example import Example, ExampleVersion, ExampleDependency
from ..services.storage_service import StorageService

logger = logging.getLogger(__name__)


# Data Classes for Workflow Parameters
class ExampleDeployment:
    """Single example deployment request."""
    def __init__(self, course_content_id: str, example_id: str, example_version: str, target_path: str):
        self.course_content_id = course_content_id
        self.example_id = example_id
        self.example_version = example_version
        self.target_path = target_path


class DeployExamplesParams:
    """Parameters for deploy_examples_to_course workflow."""
    def __init__(self, course_id: str, deployments: List[ExampleDeployment]):
        self.course_id = course_id
        self.deployments = deployments


class DeployExamplesResult:
    """Result of example deployment workflow."""
    def __init__(self, success: bool, deployed_count: int = 0, failed_count: int = 0, 
                 commit_hash: Optional[str] = None, deployment_results: Optional[List[Dict]] = None,
                 errors: Optional[List[str]] = None):
        self.success = success
        self.deployed_count = deployed_count
        self.failed_count = failed_count
        self.commit_hash = commit_hash
        self.deployment_results = deployment_results or []
        self.errors = errors or []


# Activities
@activity.defn(name="validate_deployment_request")
async def validate_deployment_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate deployment request and check permissions."""
    logger.info(f"Validating deployment request for course: {params['course_id']}")
    
    errors = []
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == params['course_id']).first()
        if not course:
            errors.append(f"Course {params['course_id']} not found")
            return {"valid": False, "errors": errors}
        
        # Validate each deployment
        for deployment in params['deployments']:
            # Check if CourseContent exists
            course_content = db.query(CourseContent).filter(
                CourseContent.id == deployment['course_content_id'],
                CourseContent.course_id == params['course_id']
            ).first()
            
            if not course_content:
                errors.append(f"CourseContent {deployment['course_content_id']} not found in course")
                continue
            
            # Check if Example exists
            example = db.query(Example).filter(Example.id == deployment['example_id']).first()
            if not example:
                errors.append(f"Example {deployment['example_id']} not found")
                continue
            
            # Validate version if not "latest"
            if deployment['example_version'] != "latest":
                version = db.query(ExampleVersion).filter(
                    ExampleVersion.example_id == deployment['example_id'],
                    ExampleVersion.version_tag == deployment['example_version']
                ).first()
                if not version:
                    errors.append(f"Version {deployment['example_version']} not found for example {deployment['example_id']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "course": {
                "id": str(course.id),
                "title": course.title,
                "properties": course.properties or {}
            }
        }
        
    finally:
        db_gen.close()


@activity.defn(name="download_examples_from_library")
async def download_examples_from_library(deployments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Download example files and metadata from MinIO storage."""
    logger.info(f"Downloading {len(deployments)} examples from library")
    
    examples_data = {}
    metadata_data = {}
    errors = []
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Initialize storage service
        storage_service = StorageService()
        
        for deployment in deployments:
            try:
                # Get example from database
                example = db.query(Example).filter(Example.id == deployment['example_id']).first()
                if not example:
                    errors.append(f"Example {deployment['example_id']} not found")
                    continue
                
                # Determine version to download
                version_tag = deployment['example_version']
                if version_tag == "latest":
                    # Get latest version
                    version = db.query(ExampleVersion).filter(
                        ExampleVersion.example_id == deployment['example_id']
                    ).order_by(ExampleVersion.version_number.desc()).first()
                    
                    if version:
                        version_tag = version.version_tag
                    else:
                        errors.append(f"No versions found for example {deployment['example_id']}")
                        continue
                else:
                    # Get specific version
                    version = db.query(ExampleVersion).filter(
                        ExampleVersion.example_id == deployment['example_id'],
                        ExampleVersion.version_tag == version_tag
                    ).first()
                    
                    if not version:
                        errors.append(f"Version {version_tag} not found for example {deployment['example_id']}")
                        continue
                
                # Download files from MinIO
                storage_path = version.storage_path
                logger.info(f"Downloading from storage path: {storage_path}")
                
                # Parse bucket and prefix from storage path
                parts = storage_path.strip('/').split('/', 1)
                bucket_name = parts[0] if parts else 'computor-storage'
                prefix = parts[1] if len(parts) > 1 else ''
                
                # Download all files in the example directory
                files = {}
                
                # List objects using storage service
                objects_list = await storage_service.list_objects(
                    prefix=prefix,
                    bucket_name=bucket_name
                )
                
                for obj_metadata in objects_list:
                    # Download each file using storage service
                    file_data = await storage_service.download_file(
                        object_key=obj_metadata.object_key,
                        bucket_name=bucket_name
                    )
                    
                    # Get relative path within example
                    relative_path = obj_metadata.object_key.replace(prefix, '').lstrip('/')
                    files[relative_path] = file_data
                
                # Parse metadata from version
                metadata = None
                if version.meta_yaml:
                    metadata = yaml.safe_load(version.meta_yaml)
                
                examples_data[deployment['example_id']] = files
                metadata_data[deployment['example_id']] = metadata
                
            except Exception as e:
                logger.error(f"Failed to download example {deployment['example_id']}: {e}")
                errors.append(f"Failed to download example {deployment['example_id']}: {str(e)}")
        
        return {
            "examples": examples_data,
            "metadata": metadata_data,
            "errors": errors
        }
        
    finally:
        db_gen.close()


@activity.defn(name="prepare_assignments_repository") 
async def prepare_assignments_repository(course_id: str) -> Dict[str, Any]:
    """Clone or update the assignments repository for the course."""
    logger.info(f"Preparing assignments repository for course: {course_id}")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Get course details
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Get GitLab repository URL from course properties
        properties = course.properties or {}
        gitlab_data = properties.get('gitlab', {})
        assignments_url = gitlab_data.get('assignments_url')
        
        if not assignments_url:
            raise ValueError(f"No assignments repository URL found for course {course_id}")
        
        # Create temporary directory for repository
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, 'assignments')
        
        # Clone repository
        logger.info(f"Cloning repository from {assignments_url}")
        
        # Get GitLab token from environment or config
        gitlab_token = os.environ.get('GITLAB_TOKEN', '')
        
        # Clone with authentication if token is available
        if gitlab_token and 'http' in assignments_url:
            # Insert token into URL
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(assignments_url)
            auth_netloc = f"oauth2:{gitlab_token}@{parsed.netloc}"
            auth_url = urlunparse((parsed.scheme, auth_netloc, parsed.path, 
                                 parsed.params, parsed.query, parsed.fragment))
            repo = git.Repo.clone_from(auth_url, repo_path)
        else:
            repo = git.Repo.clone_from(assignments_url, repo_path)
        
        return {
            "local_path": repo_path,
            "temp_dir": temp_dir,
            "assignments_url": assignments_url,
            "branch": repo.active_branch.name
        }
        
    finally:
        db_gen.close()


@activity.defn(name="deploy_single_example")
async def deploy_single_example(params: Dict[str, Any]) -> Dict[str, Any]:
    """Deploy a single example to the assignments repository at the specified path."""
    logger.info(f"Deploying example {params['example_id']} to {params['target_path']}")
    
    try:
        repository_path = params['repository_path']
        target_path = params['target_path']
        example_files = params['example_files']
        example_metadata = params.get('example_metadata', {})
        
        # Create target directory structure based on Ltree path
        target_dir = Path(repository_path) / target_path.replace('.', '/')
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy example files to target directory
        files_deployed = []
        for filename, content in example_files.items():
            if filename == 'metadata.json':  # Skip internal metadata
                continue
            
            target_file = target_dir / filename
            
            # Ensure subdirectories exist
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            if isinstance(content, str):
                target_file.write_text(content, encoding='utf-8')
            else:
                target_file.write_bytes(content)
            
            files_deployed.append(filename)
        
        # Update meta.yaml with course-specific settings if exists
        meta_yaml_path = target_dir / 'meta.yaml'
        if meta_yaml_path.exists() and example_metadata:
            # Read existing meta.yaml
            with open(meta_yaml_path, 'r') as f:
                meta_data = yaml.safe_load(f) or {}
            
            # Add course-specific metadata
            meta_data['courseContentId'] = params['course_content_id']
            meta_data['deployedFrom'] = {
                'exampleId': params['example_id'],
                'version': params.get('example_version', 'latest')
            }
            
            # Write updated meta.yaml
            with open(meta_yaml_path, 'w') as f:
                yaml.dump(meta_data, f, default_flow_style=False, sort_keys=False)
        
        # Create .example-library tracking file
        tracking_file = target_dir / '.example-library'
        tracking_data = {
            'example_id': params['example_id'],
            'example_version': params.get('example_version', 'latest'),
            'deployed_at': datetime.now(timezone.utc).isoformat(),
            'course_content_id': params['course_content_id']
        }
        tracking_file.write_text(json.dumps(tracking_data, indent=2))
        
        return {
            "success": True,
            "example_id": params['example_id'],
            "target_path": target_path,
            "files_deployed": files_deployed,
            "deployment_metadata": tracking_data
        }
        
    except Exception as e:
        logger.error(f"Failed to deploy example {params['example_id']}: {e}")
        return {
            "success": False,
            "example_id": params['example_id'],
            "target_path": params.get('target_path'),
            "error": str(e)
        }


@activity.defn(name="resolve_example_dependencies")
async def resolve_example_dependencies(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle dependencies between deployed examples."""
    logger.info("Resolving example dependencies")
    
    dependency_updates = []
    deployments = params['deployments']
    repository_path = params['repository_path']
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        for deployment in deployments:
            if not deployment.get('success'):
                continue
            
            try:
                # Get example dependencies from database
                dependencies = db.query(ExampleDependency).filter(
                    ExampleDependency.example_id == deployment['example_id']
                ).all()
                
                if not dependencies:
                    continue
                
                # Find where dependencies were deployed in this course
                dependency_paths = {}
                for dep in dependencies:
                    # Look for the dependency in other deployments
                    dep_deployment = next(
                        (d for d in deployments if d.get('example_id') == str(dep.depends_id)),
                        None
                    )
                    if dep_deployment and dep_deployment.get('success'):
                        dependency_paths[str(dep.depends_id)] = dep_deployment['target_path']
                
                # Update dependency references if any were found
                if dependency_paths:
                    # Update import paths in Python files (example)
                    deployment_dir = Path(repository_path) / deployment['target_path'].replace('.', '/')
                    
                    for py_file in deployment_dir.glob('**/*.py'):
                        content = py_file.read_text()
                        modified = False
                        
                        # Simple example: update relative imports
                        # This would need to be more sophisticated in practice
                        for _, dep_path in dependency_paths.items():
                            # Convert path to Python module format
                            dep_module = dep_path.replace('.', '.')
                            # Update imports (simplified example)
                            if 'from utils import' in content:
                                content = content.replace(
                                    'from utils import',
                                    f'from {dep_module}.utils import'
                                )
                                modified = True
                        
                        if modified:
                            py_file.write_text(content)
                    
                    dependency_updates.append({
                        'example_id': deployment['example_id'],
                        'target_path': deployment['target_path'],
                        'dependencies_updated': list(dependency_paths.keys())
                    })
            
            except Exception as e:
                logger.error(f"Failed to resolve dependencies for {deployment['example_id']}: {e}")
        
        return {
            "success": True,
            "dependency_updates": dependency_updates
        }
        
    finally:
        db_gen.close()


@activity.defn(name="commit_and_push_changes")
async def commit_and_push_changes(params: Dict[str, Any]) -> Dict[str, Any]:
    """Commit and push changes to the assignments repository."""
    logger.info("Committing and pushing changes to repository")
    
    try:
        repository_path = params['repository_path']
        commit_message = params['commit_message']
        deployments = params['deployments']
        
        # Open repository
        repo = git.Repo(repository_path)
        
        # Add all changes
        repo.git.add('.')
        
        # Check if there are changes to commit
        if not repo.is_dirty(untracked_files=True):
            logger.info("No changes to commit")
            return {
                "success": True,
                "commit_hash": repo.head.commit.hexsha,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "No changes to commit"
            }
        
        # Create detailed commit message
        detailed_message = f"{commit_message}\n\n"
        detailed_message += "Deployed examples:\n"
        for deployment in deployments:
            if deployment.get('success'):
                detailed_message += f"- {deployment['example_id']} -> {deployment['target_path']}\n"
        
        # Commit changes
        commit = repo.index.commit(detailed_message)
        
        # Push to remote
        origin = repo.remote('origin')
        origin.push()
        
        return {
            "success": True,
            "commit_hash": commit.hexsha,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to commit and push changes: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="update_course_content_deployment_status")
async def update_course_content_deployment_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Update CourseContent records with deployment status."""
    logger.info("Updating CourseContent deployment status")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        deployments = params['deployments']
        commit_hash = params.get('commit_hash')
        deployment_timestamp = params.get('deployment_timestamp')
        
        for deployment in deployments:
            if not deployment.get('success'):
                continue
            
            # Update CourseContent record
            db.execute(
                update(CourseContent).where(
                    CourseContent.id == deployment['course_content_id']
                ).values(
                    example_id=deployment['example_id'],
                    example_version=deployment['deployment_metadata']['example_version'],
                    deployed_at=deployment_timestamp,
                    deployment_status='deployed'
                )
            )
        
        db.commit()
        
        return {
            "success": True,
            "updated_count": len([d for d in deployments if d.get('success')])
        }
        
    except Exception as e:
        logger.error(f"Failed to update deployment status: {e}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_gen.close()


@activity.defn(name="cleanup_temp_repository")
async def cleanup_temp_repository(temp_dir: str) -> None:
    """Clean up temporary repository directory."""
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to clean up temporary directory {temp_dir}: {e}")


# Workflow
@workflow.defn(name="deploy_examples_to_course")
class DeployExamplesToCourseWorkflow(BaseWorkflow):
    """Deploy selected examples from Example Library to course assignments repository."""
    
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy examples to course repository.
        
        Args:
            params: Dictionary containing:
                - course_id: Target course UUID
                - deployments: List of deployment requests
                
        Returns:
            Dictionary with deployment results
        """
        logger.info(f"Starting example deployment workflow for course {params['course_id']}")
        
        # Step 1: Validate inputs and check permissions
        validation_result = await workflow.execute_activity(
            validate_deployment_request,
            params,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        if not validation_result['valid']:
            return {
                "success": False,
                "errors": validation_result['errors']
            }
        
        # Step 2: Download examples from MinIO/Example Library
        download_result = await workflow.execute_activity(
            download_examples_from_library,
            params['deployments'],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        if download_result.get('errors'):
            logger.warning(f"Some examples failed to download: {download_result['errors']}")
        
        # Step 3: Clone/update assignments repository
        repo_result = await workflow.execute_activity(
            prepare_assignments_repository,
            params['course_id'],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 4: Deploy examples to repository paths
        deployment_results = []
        for deployment in params['deployments']:
            example_id = deployment['example_id']
            
            # Skip if download failed
            if example_id not in download_result['examples']:
                deployment_results.append({
                    "success": False,
                    "example_id": example_id,
                    "error": "Failed to download example"
                })
                continue
            
            result = await workflow.execute_activity(
                deploy_single_example,
                {
                    "course_id": params['course_id'],
                    "course_content_id": deployment['course_content_id'],
                    "example_id": example_id,
                    "example_version": deployment['example_version'],
                    "example_files": download_result['examples'][example_id],
                    "target_path": deployment['target_path'],
                    "example_metadata": download_result['metadata'].get(example_id),
                    "repository_path": repo_result['local_path']
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            deployment_results.append(result)
        
        # Step 5: Handle dependencies and cross-references
        await workflow.execute_activity(
            resolve_example_dependencies,
            {
                "course_id": params['course_id'],
                "deployments": deployment_results,
                "repository_path": repo_result['local_path']
            },
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 6: Commit and push changes
        successful_deployments = [d for d in deployment_results if d.get('success')]
        if successful_deployments:
            commit_result = await workflow.execute_activity(
                commit_and_push_changes,
                {
                    "repository_path": repo_result['local_path'],
                    "commit_message": f"Deploy {len(successful_deployments)} examples from Example Library",
                    "deployments": deployment_results
                },
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # Step 7: Update CourseContent records
            if commit_result.get('success'):
                await workflow.execute_activity(
                    update_course_content_deployment_status,
                    {
                        "deployments": deployment_results,
                        "commit_hash": commit_result.get('commit_hash'),
                        "deployment_timestamp": commit_result.get('timestamp')
                    },
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(maximum_attempts=3)
                )
        else:
            commit_result = {"success": False, "error": "No successful deployments to commit"}
        
        # Step 8: Clean up temporary repository
        await workflow.execute_activity(
            cleanup_temp_repository,
            repo_result.get('temp_dir', ''),
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=RetryPolicy(maximum_attempts=1)
        )
        
        # Prepare final result
        deployed_count = len([r for r in deployment_results if r.get('success')])
        failed_count = len([r for r in deployment_results if not r.get('success')])
        
        return {
            "success": deployed_count > 0,
            "deployed_count": deployed_count,
            "failed_count": failed_count,
            "commit_hash": commit_result.get('commit_hash') if commit_result.get('success') else None,
            "deployment_results": deployment_results,
            "errors": download_result.get('errors', [])
        }


# Register the workflow
register_task(
    'deploy_examples_to_course',
    DeployExamplesToCourseWorkflow,
    'Deploy examples from Example Library to course repository',
    'course_management'
)