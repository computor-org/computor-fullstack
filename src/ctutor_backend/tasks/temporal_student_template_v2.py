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


async def download_example_files(repository: ExampleRepository, version: ExampleVersion) -> Dict[str, bytes]:
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


async def download_example_from_git(repository: ExampleRepository, version: ExampleVersion) -> Dict[str, bytes]:
    """
    Download example files from a Git repository.
    
    Args:
        repository: ExampleRepository with source_type='git'
        version: ExampleVersion with storage path information
        
    Returns:
        Dictionary mapping file paths to their content
        
    Raises:
        NotImplementedError: Git repositories are not yet supported
    """
    logger.error(f"Git source type not implemented for repository {repository.name}")
    raise NotImplementedError(f"Git source type is not yet implemented for repository '{repository.name}'")


async def download_example_from_object_storage(
    repository: ExampleRepository, 
    version: ExampleVersion
) -> Dict[str, bytes]:
    """
    Download example files from MinIO/S3 object storage.
    
    Args:
        repository: ExampleRepository with source_type in ['minio', 's3']
        version: ExampleVersion with storage path information
        
    Returns:
        Dictionary mapping file paths to their content
    """
    # Initialize storage service
    storage_service = StorageService()
    
    storage_path = version.storage_path
    bucket_name = repository.source_url  # Use repository's source_url as bucket name
    prefix = storage_path.strip('/')
    
    logger.info(f"Downloading from {repository.source_type} bucket: {bucket_name}, path: {storage_path}")
    
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
    
    return example_files


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
        
        course_family = course.course_family
        organization = course.organization
        
        # # Get organization directly using the foreign key relationship
        # organization = db.query(Organization).filter(Organization.id == course.organization_id).first()
        # if not organization:
        #     raise ValueError(f"Organization not found for course {course_id}. Organization ID: {course.organization_id}")
        
        # Get GitLab token from organization properties
        gitlab_token = None
        if organization.properties and 'gitlab' in organization.properties:
            gitlab_config = organization.properties.get('gitlab', {})
            encrypted_token = gitlab_config.get('token')  # Use 'token' field as defined in GitLabConfig
            
            if encrypted_token:
                # Decrypt the GitLab token
                from ..interface.tokens import decrypt_api_key
                try:
                    gitlab_token = decrypt_api_key(encrypted_token)
                    logger.info(f"Using decrypted GitLab token from organization {organization.title}")
                except Exception as e:
                    logger.error(f"Failed to decrypt GitLab token for organization {organization.title}: {str(e)}")
                    gitlab_token = None
        
        if not gitlab_token:
            logger.warning(f"No GitLab token found in organization {organization.title} properties")
        
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

                # Get the repository to determine bucket name
                repository = example.repository
                if not repository:
                    logger.error(f"Repository not found for example {content.example_id}")
                    errors.append(f"Repository not found for {content.path}")
                    continue
                
                # Download example files based on repository source type
                try:
                    example_files = await download_example_files(repository, version)
                except NotImplementedError as e:
                    logger.error(f"Not implemented: {e}")
                    errors.append(str(e))
                    continue
                except ValueError as e:
                    logger.error(f"Invalid source type: {e}")
                    errors.append(f"Invalid source type for {content.path}: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Failed to download example files: {e}")
                    errors.append(f"Failed to download files for {content.path}: {str(e)}")
                    continue
                
                # Process example for student template
                content_path_str = str(content.example.identifier)  # Use example identifier as directory name
                target_path = Path(template_staging_path) / content_path_str
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
        
        # Update repository content (preserve existing directories, only update assigned examples)
        # Only remove/update files that are being actively managed, preserve everything else
        
        # Copy/update only the staged content to repository
        for item in Path(template_staging_path).iterdir():
            target = Path(template_repo_path) / item.name
            
            if item.is_dir():
                # If directory exists, remove it first, then replace with new content
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                # For files, just copy/overwrite
                shutil.copy2(item, target)
        
        # Create root README
        readme_path = Path(template_repo_path) / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(f"# {course.title} - Student Repository\n\n")
            f.write(f"Welcome to {course.title}!\n\n")
            f.write(f"This repository contains templates for your assignments.\n\n")
            f.write(f"## Course Information\n\n")
            f.write(f"- **Organization**: {str(course.path).split('.')[0]}\n")
            f.write(f"- **Course Family**: {str(course_family.path).split('.')[1] if len(str(course_family.path).split('.')) > 1 else 'N/A'}\n")
            f.write(f"- **Course**: {course.title}\n\n")
            f.write(f"## Contents\n\n")
            f.write(f"This repository contains {processed_count} assignments organized by topic.\n\n")
            
            # Generate tree structure table for CourseContents with examples
            if course_contents:
                f.write(f"## Assignment Structure\n\n")
                f.write(f"| Course Tree | Example Directory | Example Title |\n")
                f.write(f"|------------------|-------------------|---------------|\n")
                
                # Sort course contents by path for better tree visualization
                sorted_contents = sorted(course_contents, key=lambda x: str(x.path))
                
                for content in sorted_contents:
                    if content.example_id and hasattr(content, 'example') and content.example:
                        # Create tree structure visualization from ltree path
                        path_parts = str(content.path).split('.')
                        
                        # Create indented tree structure
                        if len(path_parts) == 1:
                            tree_structure = path_parts[0]
                        else:
                            # Show hierarchy with indentation
                            tree_structure = path_parts[0]
                            for i in range(1, len(path_parts)):
                                tree_structure += " → " + path_parts[i]
                        
                        # Get example directory (identifier) and title
                        example_dir = str(content.example.identifier)
                        example_title = content.example.title
                        example_version = content.example_version if content.example_version else "latest"
                        
                        f.write(f"| {tree_structure} | [`{example_dir}`](./{example_dir}) | {example_title} (v{example_version}) |\n")
                
                f.write(f"\n")
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
        
        # Create or update ExampleDeployment records
        deployment_timestamp = datetime.now(timezone.utc)
        
        for content in course_contents:
            if not any(str(content.path) in error for error in errors):
                # Update CourseContent status
                content.deployment_status = 'deployed'
                content.deployed_at = deployment_timestamp
                
        
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


@activity.defn(name="generate_student_and_assignments_repositories")
async def generate_student_and_assignments_repositories(
    course_id: str, 
    student_template_url: str, 
    assignments_url: str
) -> Dict[str, Any]:
    """
    Generate both student template and assignments repositories.
    
    This generates:
    1. student-template: Processed version for students (no solutions)
    2. assignments: Full example content with solutions (reference repository)
    """
    logger.info(f"Generating student template and assignments repositories for course {course_id}")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Get course details
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Generate student template (existing logic)
        student_result = await generate_student_template_v2(course_id, student_template_url)
        
        # Generate assignments repository (full example content)
        assignments_result = await generate_assignments_repository(course_id, assignments_url)
        
        return {
            "success": student_result.get("success", False) and assignments_result.get("success", False),
            "student_template": student_result,
            "assignments": assignments_result
        }
        
    except Exception as e:
        logger.error(f"Failed to generate repositories: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_gen.close()


@activity.defn(name="generate_assignments_repository")
async def generate_assignments_repository(course_id: str, assignments_url: str) -> Dict[str, Any]:
    """
    Generate assignments repository with full example content (unmodified).
    This serves as the reference repository for lecturers and tutors.
    """
    logger.info(f"Generating assignments repository for course {course_id}")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Get course details
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        organization = course.organization
        
        # Get GitLab token from organization properties
        gitlab_token = None
        if organization.properties and 'gitlab' in organization.properties:
            gitlab_config = organization.properties.get('gitlab', {})
            encrypted_token = gitlab_config.get('token')
            
            if encrypted_token:
                from ..interface.tokens import decrypt_api_key
                try:
                    gitlab_token = decrypt_api_key(encrypted_token)
                    logger.info(f"Using decrypted GitLab token from organization {organization.title}")
                except Exception as e:
                    logger.error(f"Failed to decrypt GitLab token: {str(e)}")
                    gitlab_token = None
        
        if not gitlab_token:
            logger.warning(f"No GitLab token found in organization {organization.title} properties")
        
        # Transform URL for Docker environment
        assignments_url = transform_localhost_url(assignments_url)
        logger.info(f"Using assignments URL: {assignments_url}")
        
        # Create temporary directories
        temp_dir = tempfile.mkdtemp(prefix='assignments-gen-')
        assignments_staging_path = os.path.join(temp_dir, 'staging')
        assignments_repo_path = os.path.join(temp_dir, 'assignments')
        os.makedirs(assignments_staging_path, exist_ok=True)
        
        import git
        from datetime import datetime, timezone
        
        # Clone or create assignments repository
        try:
            if gitlab_token and 'http' in assignments_url:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(assignments_url)
                auth_netloc = f"oauth2:{gitlab_token}@{parsed.netloc}"
                auth_url = urlunparse((parsed.scheme, auth_netloc, parsed.path, 
                                     parsed.params, parsed.query, parsed.fragment))
                assignments_repo = git.Repo.clone_from(auth_url, assignments_repo_path)
            else:
                assignments_repo = git.Repo.clone_from(assignments_url, assignments_repo_path)
        except Exception as e:
            logger.error(f"Failed to clone assignments repository: {e}")
            return {"success": False, "error": f"Failed to clone repository: {str(e)}"}
        
        # Clear existing content except .git
        for item in os.listdir(assignments_repo_path):
            if item == '.git':
                continue
            item_path = os.path.join(assignments_repo_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        
        # Get course contents with examples
        course_contents = db.query(CourseContent).filter(
            CourseContent.course_id == course_id,
            CourseContent.example_id.isnot(None)
        ).all()
        
        processed_count = 0
        errors = []
        
        # Process each course content
        for content in course_contents:
            try:
                if not content.example:
                    logger.warning(f"CourseContent {content.path} has example_id but no example relationship")
                    continue
                
                if not content.example_version:
                    logger.warning(f"CourseContent {content.path} has no example_version specified")
                    continue
                
                # Find the specific version
                version = None
                for v in content.example.versions:
                    if v.version == content.example_version:
                        version = v
                        break
                
                if not version:
                    logger.error(f"Version {content.example_version} not found for example {content.example.identifier}")
                    continue
                
                # Download example files
                example_files = await download_example_files(content.example.repository, version)
                
                # For assignments repository, copy ALL files unmodified to preserve full example
                content_path_str = str(content.example.identifier)
                assignment_path = Path(assignments_repo_path) / content_path_str
                
                # Process full example content for assignments repository
                await process_full_example_for_assignments_repository(
                    example_files, assignment_path, content, version
                )
                
                processed_count += 1
                
            except Exception as e:
                error_msg = f"Failed to process content {content.path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Create README for assignments repository
        readme_content = f"""# Assignments Repository - {course.title}

This repository contains the complete example content with solutions for course assignments.

## Purpose
- **Reference repository** for lecturers and tutors
- Contains **full example content** including solutions, test files, and metadata
- **Do not share** with students (contains solutions)

## Usage
- Lecturers: Edit and improve examples
- Tutors: Reference for grading and student assistance
- Generated automatically from Example Library

## Contents
"""
        
        for content in course_contents:
            if content.example:
                readme_content += f"- `{content.example.identifier}/` - {content.title}\n"
        
        readme_content += f"""
---
*Last updated: {datetime.now(timezone.utc).isoformat()}*
*Generated by Computor Example Library*
"""
        
        readme_path = os.path.join(assignments_repo_path, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Commit and push changes
        assignments_repo.git.add('.')
        if assignments_repo.git.diff('--staged'):
            commit_message = f"Update assignments repository for {course.title}\n\n" \
                           f"Processed {processed_count} examples from Example Library\n" \
                           f"Generated: {datetime.now(timezone.utc).isoformat()}"
            assignments_repo.git.commit('-m', commit_message)
            
            # Push changes
            try:
                if gitlab_token and 'http' in assignments_url:
                    origin = assignments_repo.remote('origin')
                    origin.set_url(auth_url)
                assignments_repo.git.push('origin', 'main')
                commit_hash = assignments_repo.head.commit.hexsha
                logger.info(f"Pushed assignments repository changes: {commit_hash}")
            except Exception as e:
                logger.error(f"Failed to push assignments repository: {e}")
                return {"success": False, "error": f"Failed to push: {str(e)}"}
        else:
            logger.info("No changes to commit in assignments repository")
            commit_hash = assignments_repo.head.commit.hexsha if assignments_repo.head.is_valid() else "no-changes"
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return {
            "success": True,
            "commit_hash": commit_hash,
            "processed_contents": processed_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Failed to generate assignments repository: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_gen.close()


async def process_full_example_for_assignments_repository(
    example_files: Dict[str, bytes],
    target_path: Path,
    course_content: CourseContent,
    version: ExampleVersion
) -> Dict[str, Any]:
    """
    Process example files for assignments repository (full, unmodified content).
    Copies ALL files from the example to preserve complete reference.
    """
    try:
        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Copy ALL files unmodified (including solutions, meta.yaml, etc.)
        for filename, content in example_files.items():
            file_path = target_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Failed to process full example content for {course_content.path}: {e}")
        return {"success": False, "error": str(e)}


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
        
        # Process content directory files
        for filename, content in example_files.items():
            if filename.startswith('content/'):
                # Handle index*.md files specially - rename to README*.md
                if filename.startswith('content/index'):
                    # Handle index.md -> README.md
                    if filename == 'content/index.md':
                        readme_path = target_path / 'README.md'
                        readme_path.write_bytes(content)
                    # Handle index_<lang>.md -> README_<lang>.md
                    elif filename.startswith('content/index_') and filename.endswith('.md'):
                        # Extract language suffix
                        lang_suffix = filename[len('content/index'):-3]  # Gets '_de' from 'content/index_de.md'
                        readme_filename = f'README{lang_suffix}.md'
                        readme_path = target_path / readme_filename
                        readme_path.write_bytes(content)
                # Copy all other content files (mediaFiles, etc.) preserving structure
                else:
                    # Remove 'content/' prefix and copy to assignment root
                    relative_path = filename.replace('content/', '', 1)
                    file_path = target_path / relative_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(content)
        
        if meta_yaml:
            properties = meta_yaml.get('properties', {})
            
            # 3. Process additionalFiles - copy to assignment root
            additional_files = properties.get('additionalFiles', [])
            for file_name in additional_files:
                if file_name in example_files:
                    # Copy to root of assignment directory
                    file_path = target_path / Path(file_name).name  # Use only filename, not path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(example_files[file_name])
            
            # 4. Process studentSubmissionFiles - ensure all required files exist
            # Use content from studentTemplates when available, otherwise create empty
            submission_files = properties.get('studentSubmissionFiles', [])
            student_templates = properties.get('studentTemplates', [])
            
            # Build a map of template filenames to their content
            template_content_map = {}
            for template_path in student_templates:
                # Try to find the template file in example_files
                file_content = None
                actual_path = None
                
                if template_path in example_files:
                    file_content = example_files[template_path]
                    actual_path = template_path
                else:
                    # Try to find by filename
                    filename = Path(template_path).name
                    for file_path, content in example_files.items():
                        if Path(file_path).name == filename:
                            # Prefer paths containing 'studentTemplate'
                            if 'studentTemplate' in file_path:
                                file_content = content
                                actual_path = file_path
                                break
                            elif file_content is None:
                                file_content = content
                                actual_path = file_path
                
                if file_content is not None:
                    # Store the content mapped to just the filename
                    filename = Path(template_path).name
                    template_content_map[filename] = file_content
                    logger.info(f"Found template content for: {filename} from {actual_path}")
                else:
                    logger.warning(f"Student template file not found: {template_path}")
            
            # Now create all studentSubmissionFiles
            for submission_file in submission_files:
                submission_path = target_path / submission_file
                submission_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Check if we have template content for this file
                if submission_file in template_content_map:
                    # Use template content
                    submission_path.write_bytes(template_content_map[submission_file])
                    logger.info(f"Created {submission_file} from template")
                else:
                    # Create empty file
                    submission_path.write_text('')
                    logger.info(f"Created empty file: {submission_file}")
        else:
            # No meta.yaml - fallback processing
            logger.warning(f"No meta.yaml found for {course_content.path}, using fallback processing")
            for filename, content in example_files.items():
                # Skip test files and meta files
                if not filename.startswith('test') and not filename.endswith('_test.py') and filename != 'meta.yaml':
                    file_path = target_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(content)
        
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
        
        # Generate both student template and assignments repository
        result = await workflow.execute_activity(
            generate_student_and_assignments_repositories,
            args=[params['course_id'], params.get('student_template_url'), params.get('assignments_url')],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result