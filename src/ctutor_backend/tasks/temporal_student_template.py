"""
Temporal workflows for generating student templates from assignments repository.
Enhanced to handle example-sourced content.
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
import git

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from sqlalchemy.orm import Session

from .temporal_base import BaseWorkflow, WorkflowResult
from .registry import register_task
from ..database import get_db
from ..model.course import Course, CourseContent
from ..model.example import Example

logger = logging.getLogger(__name__)


@activity.defn(name="generate_student_template_with_examples")
async def generate_student_template_with_examples(course_id: str) -> Dict[str, Any]:
    """
    Generate student template repository from assignments repository,
    accounting for Example Library sourced content.
    """
    logger.info(f"Generating student template for course {course_id} with example support")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Get course details
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Get all CourseContent with and without examples
        course_contents = db.query(CourseContent).filter(
            CourseContent.course_id == course_id,
            CourseContent.archived_at.is_(None)
        ).order_by(CourseContent.path).all()
        
        # Get repository URLs
        properties = course.properties or {}
        gitlab_data = properties.get('gitlab', {})
        assignments_url = gitlab_data.get('assignments_url')
        student_template_url = gitlab_data.get('student_template_url')
        
        if not assignments_url or not student_template_url:
            raise ValueError("Missing repository URLs in course properties")
        
        # Create temporary directories
        temp_dir = tempfile.mkdtemp()
        assignments_path = os.path.join(temp_dir, 'assignments')
        template_path = os.path.join(temp_dir, 'student-template')
        
        # Clone repositories
        gitlab_token = os.environ.get('GITLAB_TOKEN', '')
        
        # Clone assignments repository
        if gitlab_token and 'http' in assignments_url:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(assignments_url)
            auth_netloc = f"oauth2:{gitlab_token}@{parsed.netloc}"
            auth_url = urlunparse((parsed.scheme, auth_netloc, parsed.path, 
                                 parsed.params, parsed.query, parsed.fragment))
            assignments_repo = git.Repo.clone_from(auth_url, assignments_path)
        else:
            assignments_repo = git.Repo.clone_from(assignments_url, assignments_path)
        
        # Clone or create student template repository
        try:
            if gitlab_token and 'http' in student_template_url:
                parsed = urlparse(student_template_url)
                auth_netloc = f"oauth2:{gitlab_token}@{parsed.netloc}"
                auth_url = urlunparse((parsed.scheme, auth_netloc, parsed.path, 
                                     parsed.params, parsed.query, parsed.fragment))
                template_repo = git.Repo.clone_from(auth_url, template_path)
            else:
                template_repo = git.Repo.clone_from(student_template_url, template_path)
        except Exception as e:
            logger.info(f"Could not clone student template repo, creating new: {e}")
            os.makedirs(template_path, exist_ok=True)
            template_repo = git.Repo.init(template_path)
        
        # Process each CourseContent
        processed_count = 0
        example_count = 0
        
        for content in course_contents:
            source_path = Path(assignments_path) / content.path.replace('.', '/')
            target_path = Path(template_path) / content.path.replace('.', '/')
            
            if not source_path.exists():
                logger.warning(f"Source path {source_path} does not exist, skipping")
                continue
            
            if content.example_id:
                # Handle example-sourced content
                result = await process_example_for_student_template(
                    str(source_path), str(target_path), content, db
                )
                if result['success']:
                    example_count += 1
                    processed_count += 1
            else:
                # Handle traditional content
                result = await process_traditional_content_for_template(
                    str(source_path), str(target_path), content
                )
                if result['success']:
                    processed_count += 1
        
        # Update root README
        readme_path = Path(template_path) / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(f"# {course.title} - Student Repository\n\n")
            f.write(f"Welcome to {course.title}!\n\n")
            f.write(f"This repository contains templates for your assignments.\n\n")
            f.write(f"## Statistics\n\n")
            f.write(f"- Total assignments: {processed_count}\n")
            f.write(f"- Example-based assignments: {example_count}\n\n")
            f.write(f"## Getting Started\n\n")
            f.write(f"1. Fork this repository to your account\n")
            f.write(f"2. Clone your fork to your local machine\n")
            f.write(f"3. Complete assignments in their respective directories\n")
            f.write(f"4. Commit and push your solutions\n\n")
        
        # Commit and push changes
        template_repo.git.add('.')
        
        if template_repo.is_dirty(untracked_files=True):
            template_repo.index.commit(
                f"Update student template - {processed_count} assignments ({example_count} from examples)"
            )
            
            origin = template_repo.remote('origin')
            origin.push()
            
            commit_hash = template_repo.head.commit.hexsha
        else:
            commit_hash = template_repo.head.commit.hexsha
            logger.info("No changes to commit in student template")
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return {
            "success": True,
            "commit_hash": commit_hash,
            "processed_contents": processed_count,
            "example_contents": example_count
        }
        
    except Exception as e:
        logger.error(f"Failed to generate student template: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db_gen.close()


async def process_example_for_student_template(
    source_path: str,
    target_path: str,
    course_content: CourseContent,
    db: Session
) -> Dict[str, Any]:
    """
    Process example-sourced content for student template generation.
    Uses meta.yaml to determine which files to include/exclude.
    """
    try:
        # Read .example-library tracking file
        tracking_file = Path(source_path) / '.example-library'
        if tracking_file.exists():
            tracking_data = json.loads(tracking_file.read_text())
            example_id = tracking_data['example_id']
        else:
            # Fallback to database
            example_id = str(course_content.example_id)
        
        # Create target directory
        target_path_obj = Path(target_path)
        target_path_obj.mkdir(parents=True, exist_ok=True)
        
        # Process files according to meta.yaml rules
        meta_yaml_path = Path(source_path) / 'meta.yaml'
        if meta_yaml_path.exists():
            with open(meta_yaml_path, 'r') as f:
                meta_yaml = yaml.safe_load(f) or {}
            
            properties = meta_yaml.get('properties', {})
            
            # Copy student template files
            student_templates = properties.get('studentTemplates', [])
            for template_file in student_templates:
                source_file = Path(source_path) / template_file
                target_file = target_path_obj / template_file
                if source_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)
            
            # Copy additional files (non-solution files)
            additional_files = properties.get('additionalFiles', [])
            for additional_file in additional_files:
                source_file = Path(source_path) / additional_file
                target_file = target_path_obj / additional_file
                if source_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)
            
            # Create student-specific meta.yaml
            student_meta = create_student_meta_yaml(meta_yaml, course_content)
            meta_output_path = target_path_obj / 'meta.yaml'
            with open(meta_output_path, 'w') as f:
                yaml.dump(student_meta, f, default_flow_style=False, sort_keys=False)
            
            # Copy README if exists
            readme_source = Path(source_path) / 'README.md'
            if readme_source.exists():
                shutil.copy2(readme_source, target_path_obj / 'README.md')
            
            # Create files specified in studentSubmissionFiles
            submission_files = properties.get('studentSubmissionFiles', [])
            for submission_file in submission_files:
                submission_path = target_path_obj / submission_file
                if not submission_path.exists():
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Create template file based on extension
                    extension = submission_path.suffix.lower()
                    
                    if extension == '.py':
                        content = f'"""\n{course_content.title}\n\nYour solution goes here.\n"""\n\n# TODO: Implement your solution\n'
                    elif extension in ['.java', '.cpp', '.c']:
                        content = f'/*\n * {course_content.title}\n * \n * Your solution goes here.\n */\n\n// TODO: Implement your solution\n'
                    else:
                        content = f'# {course_content.title}\n# Your solution goes here\n'
                    
                    submission_path.write_text(content)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Failed to process example content {course_content.path}: {e}")
        return {"success": False, "error": str(e)}


async def process_traditional_content_for_template(
    source_path: str,
    target_path: str,
    course_content: CourseContent
) -> Dict[str, Any]:
    """
    Process traditional (non-example) content for student template.
    """
    try:
        source_path_obj = Path(source_path)
        target_path_obj = Path(target_path)
        
        # Create target directory
        target_path_obj.mkdir(parents=True, exist_ok=True)
        
        # Look for meta.yaml in source
        meta_yaml_path = source_path_obj / 'meta.yaml'
        if meta_yaml_path.exists():
            # Process according to meta.yaml
            with open(meta_yaml_path, 'r') as f:
                meta_yaml = yaml.safe_load(f) or {}
            
            properties = meta_yaml.get('properties', {})
            
            # Process files as in example-based content
            for key in ['studentTemplates', 'additionalFiles']:
                for file_path in properties.get(key, []):
                    source_file = source_path_obj / file_path
                    target_file = target_path_obj / file_path
                    if source_file.exists():
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_file, target_file)
            
            # Create submission files
            for submission_file in properties.get('studentSubmissionFiles', []):
                submission_path = target_path_obj / submission_file
                if not submission_path.exists():
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    submission_path.write_text(f"# {course_content.title}\n# Your solution goes here\n")
        else:
            # No meta.yaml - copy selective files
            # Copy README
            readme_source = source_path_obj / 'README.md'
            if readme_source.exists():
                shutil.copy2(readme_source, target_path_obj / 'README.md')
            
            # Copy non-solution files
            for item in source_path_obj.iterdir():
                if item.is_file() and not item.name.startswith('test_') and \
                   not item.name.endswith('_solution.py'):
                    shutil.copy2(item, target_path_obj / item.name)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Failed to process traditional content {course_content.path}: {e}")
        return {"success": False, "error": str(e)}


def create_student_meta_yaml(meta_yaml: Dict[str, Any], course_content: CourseContent) -> Dict[str, Any]:
    """
    Create a student-specific version of meta.yaml.
    Removes test files and solution references.
    """
    student_meta = {
        "kind": meta_yaml.get("kind", "assignment"),
        "slug": meta_yaml.get("slug", course_content.path.split('.')[-1]),
        "name": meta_yaml.get("name", course_content.title),
        "properties": {}
    }
    
    # Copy safe properties
    original_props = meta_yaml.get("properties", {})
    student_props = student_meta["properties"]
    
    # Include files that students need
    if "studentSubmissionFiles" in original_props:
        student_props["studentSubmissionFiles"] = original_props["studentSubmissionFiles"]
    
    if "additionalFiles" in original_props:
        student_props["additionalFiles"] = original_props["additionalFiles"]
    
    # Copy configuration properties
    for key in ["maxGroupSize", "maxTestRuns", "maxSubmissions"]:
        if key in original_props:
            student_props[key] = original_props[key]
    
    # Add deployment information
    if course_content.example_id:
        student_meta["deployedFrom"] = {
            "exampleId": str(course_content.example_id),
            "version": course_content.example_version
        }
    
    return student_meta


# Workflow
@workflow.defn(name="generate_student_template")
class GenerateStudentTemplateWorkflow(BaseWorkflow):
    """Generate or update student template repository from assignments."""
    
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate student template with example support.
        
        Args:
            params: Dictionary containing:
                - course_id: Course UUID
                
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Starting student template generation for course {params['course_id']}")
        
        # Generate student template with example support
        result = await workflow.execute_activity(
            generate_student_template_with_examples,
            params['course_id'],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result


# Register the workflow
register_task(
    'generate_student_template',
    GenerateStudentTemplateWorkflow,
    'Generate student template repository with example support',
    'course_management'
)