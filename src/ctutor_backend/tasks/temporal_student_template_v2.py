"""
Temporal workflows for generating student templates from Example Library.
Version 2: Direct generation from MinIO without assignments repository.
"""
import logging
import os
import tempfile
import shutil
import yaml
import json
from datetime import timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from sqlalchemy.orm import Session

from .temporal_base import BaseWorkflow, WorkflowResult
from .temporal_hierarchy_management import transform_localhost_url
from .registry import register_task
from ..database import get_db
from ..model.course import Course, CourseContent
from ..model.example import Example, ExampleVersion, ExampleRepository
from ..model.organization import Organization
from ..services.storage_service import StorageService

logger = logging.getLogger(__name__)


@activity.defn(name="generate_student_template_v2")
async def generate_student_template_v2(course_id: str, student_template_url: str) -> Dict[str, Any]:
    """
    Generate student template repository directly from Example Library.
    
    This new version:
    1. Gets CourseContent records with example_id
    2. Downloads examples directly from MinIO
    3. Processes according to meta.yaml
    4. Generates student-template repository
    """
    logger.info(f"Generating student template v2 for course {course_id}")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Get course details
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Get organization directly using the foreign key relationship
        organization = db.query(Organization).filter(Organization.id == course.organization_id).first()
        if not organization:
            raise ValueError(f"Organization not found for course {course_id}. Organization ID: {course.organization_id}")
        
        # Get GitLab token from organization properties
        gitlab_token = None
        if organization.properties and 'gitlab' in organization.properties:
            gitlab_config = organization.properties.get('gitlab', {})
            gitlab_token = gitlab_config.get('access_token')
        
        if not gitlab_token:
            logger.warning(f"No GitLab token found in organization {organization.title} properties")
        else:
            logger.info(f"Using GitLab token from organization {organization.title}")
        
        # Use the URL passed from the API
        # Transform localhost to Docker host IP if running in container
        student_template_url = transform_localhost_url(student_template_url)
        logger.info(f"Using student template URL: {student_template_url}")
        
        # Create temporary directories
        temp_dir = tempfile.mkdtemp(prefix='student-template-gen-')
        template_staging_path = os.path.join(temp_dir, 'staging')
        template_repo_path = os.path.join(temp_dir, 'student-template')
        os.makedirs(template_staging_path, exist_ok=True)
        
        # Import git inside activity to avoid workflow sandbox restrictions
        import git
        from datetime import datetime, timezone
        
        # Clone or create student template repository
        # gitlab_token retrieved from organization properties above
        
        try:
            if gitlab_token and 'http' in student_template_url:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(student_template_url)
                auth_netloc = f"oauth2:{gitlab_token}@{parsed.netloc}"
                auth_url = urlunparse((parsed.scheme, auth_netloc, parsed.path, 
                                     parsed.params, parsed.query, parsed.fragment))
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
        
        # Get all CourseContent with examples
        course_contents = db.query(CourseContent).filter(
            CourseContent.course_id == course_id,
            CourseContent.example_id.isnot(None),
            CourseContent.archived_at.is_(None)
        ).order_by(CourseContent.path).all()
        
        logger.info(f"Found {len(course_contents)} course contents with examples")
        
        if len(course_contents) == 0:
            logger.warning(f"No course contents with examples found for course {course_id}. This will result in an empty student template.")
        
        # Initialize storage service
        storage_service = StorageService()
        
        # Process each CourseContent with an example
        processed_count = 0
        errors = []
        
        for content in course_contents:
            try:
                logger.info(f"Processing {content.path} with example {content.example_id}")
                
                # Get example and repository details
                example = db.query(Example).filter(Example.id == content.example_id).first()
                if not example:
                    logger.error(f"Example {content.example_id} not found")
                    errors.append(f"Example not found for {content.path}")
                    continue
                
                # Get the repository to determine bucket name
                repository = example.repository
                if not repository:
                    logger.error(f"Repository not found for example {content.example_id}")
                    errors.append(f"Repository not found for {content.path}")
                    continue
                
                # Get example version details
                version = db.query(ExampleVersion).filter(
                    ExampleVersion.example_id == content.example_id,
                    ExampleVersion.version_tag == content.example_version
                ).first()
                
                if not version:
                    # Try to get latest version if specific version not found
                    version = db.query(ExampleVersion).filter(
                        ExampleVersion.example_id == content.example_id
                    ).order_by(ExampleVersion.version_number.desc()).first()
                
                if not version:
                    logger.error(f"No version found for example {content.example_id}")
                    errors.append(f"No version found for {content.path}")
                    continue
                
                # Download example from MinIO using repository's bucket
                storage_path = version.storage_path
                bucket_name = repository.source_url  # Use repository's source_url as bucket name
                prefix = storage_path.strip('/')
                
                logger.info(f"Downloading from bucket: {bucket_name}, path: {storage_path}")
                
                # Download all files for this example
                example_files = {}
                objects = await storage_service.list_objects(
                    prefix=prefix,
                    bucket_name=bucket_name
                )
                
                for obj in objects:
                    try:
                        # Download file content
                        file_data = await storage_service.download_file(
                            object_key=obj.object_name,
                            bucket_name=bucket_name
                        )
                        
                        # Get relative path within example
                        relative_path = obj.object_name
                        if prefix:
                            relative_path = obj.object_name.replace(prefix, '').lstrip('/')
                        
                        example_files[relative_path] = file_data
                    except Exception as e:
                        logger.error(f"Failed to download {obj.object_name}: {e}")
                
                # Process example for student template
                # Convert content.path (Ltree) to string first
                content_path_str = str(content.path)
                target_path = Path(template_staging_path) / content_path_str.replace('.', '/')
                result = await process_example_for_student_template_v2(
                    example_files, target_path, content, version
                )
                
                if result['success']:
                    processed_count += 1
                else:
                    errors.append(f"Failed to process {content.path}: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"Failed to process content {content.path}: {e}")
                errors.append(f"Failed to process {content.path}: {str(e)}")
        
        # Clean existing content in repo (except .git)
        for item in Path(template_repo_path).iterdir():
            if item.name != '.git':
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        # Copy staged content to repository
        for item in Path(template_staging_path).iterdir():
            target = Path(template_repo_path) / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        
        # Create root README
        readme_path = Path(template_repo_path) / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(f"# {course.title} - Student Repository\n\n")
            f.write(f"Welcome to {course.title}!\n\n")
            f.write(f"This repository contains templates for your assignments.\n\n")
            f.write(f"## Course Information\n\n")
            f.write(f"- **Organization**: {str(course.path).split('.')[0]}\n")
            f.write(f"- **Course Family**: {str(course.path).split('.')[1] if len(str(course.path).split('.')) > 1 else 'N/A'}\n")
            f.write(f"- **Course**: {course.title}\n\n")
            f.write(f"## Contents\n\n")
            f.write(f"This repository contains {processed_count} assignments organized by topic.\n\n")
            f.write(f"## Getting Started\n\n")
            f.write(f"1. Fork this repository to your personal account\n")
            f.write(f"2. Clone your fork to your local machine\n")
            f.write(f"3. Complete assignments in their respective directories\n")
            f.write(f"4. Commit and push your solutions regularly\n\n")
            f.write(f"## Submission\n\n")
            f.write(f"Follow your instructor's guidelines for submitting assignments.\n")
        
        # Commit and push changes
        template_repo.git.add('.')
        
        if template_repo.is_dirty(untracked_files=True):
            commit_message = f"Update student template - {processed_count} assignments from Example Library"
            if errors:
                commit_message += f" ({len(errors)} errors)"
            
            template_repo.index.commit(commit_message)
            
            # Push to remote
            push_successful = False
            try:
                origin = template_repo.remote('origin')
                
                # Get current branch name
                current_branch = template_repo.active_branch.name
                logger.info(f"Current branch: {current_branch}")
                logger.info(f"Remote URL: {origin.url}")
                
                # Push with upstream tracking
                origin.push(refspec=f"{current_branch}:main", set_upstream=True)
                logger.info("Successfully pushed changes to remote")
                push_successful = True
            except Exception as e:
                logger.error(f"Failed to push to remote: {e}")
                # Try alternative push methods
                if gitlab_token and 'http' in student_template_url:
                    try:
                        push_url = auth_url if 'auth_url' in locals() else student_template_url
                        current_branch = template_repo.active_branch.name
                        logger.info(f"Trying alternative push to: {push_url}")
                        template_repo.git.push(push_url, f"{current_branch}:main", '--set-upstream')
                        logger.info("Successfully pushed with authentication")
                        push_successful = True
                    except Exception as e2:
                        logger.error(f"Failed to push even with authentication: {e2}")
                        # Don't raise - let it continue but mark the failure
                        
            if not push_successful:
                errors.append("Failed to push changes to GitLab repository")
                logger.error("All push attempts failed - changes committed locally but not pushed to remote")
            
            commit_hash = template_repo.head.commit.hexsha
        else:
            commit_hash = template_repo.head.commit.hexsha if template_repo.head.is_valid() else None
            logger.info("No changes to commit in student template")
        
        # Update course properties with last release info
        if not course.properties:
            course.properties = {}
        
        course.properties['last_template_release'] = {
            'commit_hash': commit_hash,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'processed_count': processed_count,
            'error_count': len(errors)
        }
        
        # Update CourseContent deployment status
        for content in course_contents:
            if not any(str(content.path) in error for error in errors):
                content.deployment_status = 'released'
                content.deployed_at = datetime.now(timezone.utc)
        
        db.commit()
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return {
            "success": True,
            "commit_hash": commit_hash,
            "processed_contents": processed_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Failed to generate student template: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_gen.close()


async def process_example_for_student_template_v2(
    example_files: Dict[str, bytes],
    target_path: Path,
    course_content: CourseContent,
    version: ExampleVersion
) -> Dict[str, Any]:
    """
    Process example files for student template generation.
    Uses meta.yaml to determine which files to include.
    """
    try:
        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Parse meta.yaml if it exists
        meta_yaml = None
        if 'meta.yaml' in example_files:
            try:
                meta_yaml = yaml.safe_load(example_files['meta.yaml'])
            except Exception as e:
                logger.error(f"Failed to parse meta.yaml: {e}")
        
        if not meta_yaml:
            # If no meta.yaml, include all files except tests
            for filename, content in example_files.items():
                if not filename.startswith('test_') and not filename.endswith('_test.py'):
                    file_path = target_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(content)
        else:
            # Process according to meta.yaml rules
            properties = meta_yaml.get('properties', {})
            
            # Process student template files
            student_templates = properties.get('studentTemplates', [])
            for template_file in student_templates:
                if template_file in example_files:
                    # Handle file renaming (e.g., main_template.py → main.py)
                    output_name = template_file
                    if template_file.endswith('_template.py'):
                        output_name = template_file.replace('_template.py', '.py')
                    elif template_file.endswith('_template'):
                        output_name = template_file.replace('_template', '')
                    
                    file_path = target_path / output_name
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(example_files[template_file])
            
            # Copy additional files
            additional_files = properties.get('additionalFiles', [])
            for file_name in additional_files:
                if file_name in example_files:
                    file_path = target_path / file_name
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(example_files[file_name])
            
            # Create placeholder files for student submissions
            submission_files = properties.get('studentSubmissionFiles', [])
            for submission_file in submission_files:
                submission_path = target_path / submission_file
                if not submission_path.exists():
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Create with appropriate template based on extension
                    extension = submission_path.suffix.lower()
                    if extension == '.py':
                        content = f'"""\n{course_content.title}\n\nYour solution goes here.\n"""\n\n# TODO: Implement your solution\n'
                    elif extension in ['.java', '.cpp', '.c']:
                        content = f'/*\n * {course_content.title}\n * \n * Your solution goes here.\n */\n\n// TODO: Implement your solution\n'
                    else:
                        content = f'# {course_content.title}\n# Your solution goes here\n'
                    
                    submission_path.write_text(content)
            
            # Create student-specific meta.yaml (without test references)
            student_meta = {
                'kind': meta_yaml.get('kind', 'assignment'),
                'slug': meta_yaml.get('slug', str(course_content.path).split('.')[-1]),
                'name': meta_yaml.get('name', course_content.title),
                'deployedFrom': {
                    'exampleId': str(course_content.example_id),
                    'version': version.version_tag
                }
            }
            
            # Only include safe properties for students
            if 'properties' in meta_yaml:
                student_props = {}
                for key in ['studentSubmissionFiles', 'additionalFiles', 'maxGroupSize', 'maxTestRuns', 'maxSubmissions']:
                    if key in properties:
                        student_props[key] = properties[key]
                
                if student_props:
                    student_meta['properties'] = student_props
            
            meta_output_path = target_path / 'meta.yaml'
            with open(meta_output_path, 'w') as f:
                yaml.dump(student_meta, f, default_flow_style=False, sort_keys=False)
        
        # Copy README if exists
        if 'README.md' in example_files:
            readme_path = target_path / 'README.md'
            readme_path.write_bytes(example_files['README.md'])
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Failed to process example content {course_content.path}: {e}")
        return {"success": False, "error": str(e)}


# Workflow
@register_task
@workflow.defn(name="generate_student_template_v2", sandboxed=False)
class GenerateStudentTemplateWorkflowV2(BaseWorkflow):
    """Generate student template repository directly from Example Library."""
    
    @classmethod
    def get_name(cls) -> str:
        """Get the workflow name."""
        return "generate_student_template_v2"
    
    @classmethod
    def get_task_queue(cls) -> str:
        """Get the task queue for this workflow."""
        return "computor-tasks"
    
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate student template from Example Library.
        
        Args:
            params: Dictionary containing:
                - course_id: Course UUID
                - student_template_url: GitLab repository URL for student-template
                - commit_message: Optional custom commit message
                
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Starting student template generation v2 for course {params['course_id']}")
        
        # Generate student template
        result = await workflow.execute_activity(
            generate_student_template_v2,
            args=[params['course_id'], params['student_template_url']],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result