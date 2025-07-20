"""
System-level Celery tasks for course and student management.

These tasks replace the Prefect flows for release operations.
"""
import os
import tempfile
from typing import Dict, Any, List, Optional
from uuid import UUID

from celery import current_task

from ctutor_backend.api.system import ReleaseStudentsCreate
from ctutor_backend.api.tests_celery import create_submission as api_create_submission
from ctutor_backend.api.utils import collect_sub_path_positions_if_meta_exists
from ctutor_backend.generator.gitlab_builder import CodeabilityGitlabBuilder
from ctutor_backend.interface.deployments import ApiConfig, ComputorDeploymentConfig, CodeabilityReleaseBuilder
from ctutor_backend.interface.tests import Submission
from ctutor_backend.tasks.celery_app import app


EXECUTION_BACKEND_API_URL = os.environ.get("EXECUTION_BACKEND_API_URL")
EXECUTION_BACKEND_API_USER = os.environ.get("EXECUTION_BACKEND_API_USER")
EXECUTION_BACKEND_API_PASSWORD = os.environ.get("EXECUTION_BACKEND_API_PASSWORD")


def convert_to_gitlab_paths(release_dir_list: List[str]) -> List[str]:
    """Convert paths to GitLab-compatible format."""
    gitlab_paths = []

    for path in release_dir_list:
        converted_path = path.replace("\\", "/")
        
        if len(path) > 2 and path[1:3] == ":\\":
            raise ValueError(f"Invalid path: {path} - Path cannot start with a drive letter.")

        path = path.lstrip("\\/")
        gitlab_paths.append(path.replace("\\", "/"))

    return gitlab_paths


def get_worker_api_deployment():
    """Get API deployment configuration."""
    return ApiConfig(
        url=EXECUTION_BACKEND_API_URL,
        user=EXECUTION_BACKEND_API_USER,
        password=EXECUTION_BACKEND_API_PASSWORD
    )


def get_builder(deployment: ComputorDeploymentConfig, work_dir: str) -> CodeabilityReleaseBuilder:
    """Get the appropriate builder for the deployment."""
    if deployment.organization.gitlab is not None:
        return CodeabilityGitlabBuilder(get_worker_api_deployment(), deployment, work_dir)
    else:
        raise NotImplementedError("Only GitLab is currently supported")


@app.task(bind=True, name="ctutor_backend.tasks.system.release_student")
def release_student_task(self, deployment_dict: Dict[str, Any], payload_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create student projects in GitLab.
    
    This is a Celery task that replaces the Prefect flow.
    """
    task_id = self.request.id
    deployment = ComputorDeploymentConfig(**deployment_dict)
    payload = ReleaseStudentsCreate(**payload_dict)
    
    results = []
    errors = []
    
    with tempfile.TemporaryDirectory() as tmp:
        builder = get_builder(deployment, tmp)

        for i, student in enumerate(payload.students):
            try:
                # Update progress
                progress = int((i / len(payload.students)) * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={'current': i, 'total': len(payload.students), 'progress': progress}
                )
                
                # Create student project
                course_member = builder.create_student_project(
                    student.user,
                    student.course_group_id,
                    student.role
                )
                
                results.append({
                    'student_id': str(student.user_id) if student.user_id else None,
                    'status': 'success',
                    'course_member': course_member.model_dump() if hasattr(course_member, 'model_dump') else str(course_member)
                })
                print(f"Imported student => {course_member}")

            except Exception as e:
                error_msg = f"Failed to import student {student.user_id}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                results.append({
                    'student_id': str(student.user_id) if student.user_id else None,
                    'status': 'failed',
                    'error': str(e)
                })
    
    return {
        'task_id': task_id,
        'success': len(errors) == 0,
        'total_students': len(payload.students),
        'successful': len(payload.students) - len(errors),
        'failed': len(errors),
        'results': results,
        'errors': errors
    }


@app.task(bind=True, name="ctutor_backend.tasks.system.release_course")
def release_course_task(
    self,
    deployment_dict: Dict[str, Any],
    release_dir: Optional[str] = None,
    ascendants: bool = False,
    descendants: bool = False,
    release_dir_list: List[str] = None
) -> Dict[str, Any]:
    """
    Release course content to GitLab.
    
    This is a Celery task that replaces the Prefect flow.
    """
    task_id = self.request.id
    deployment = ComputorDeploymentConfig(**deployment_dict)
    
    if release_dir_list is None:
        release_dir_list = []
    
    with tempfile.TemporaryDirectory() as tmp:
        builder = get_builder(deployment, tmp)
        error_log = []

        if len(release_dir_list) > 0:
            release_dir_list = convert_to_gitlab_paths(release_dir_list)

            # Handle empty path (root release)
            if any(len(s) == 0 for s in release_dir_list):
                error_log.extend(builder.create_course_release())
                release_dir_list = [p for p in release_dir_list if p]  # Remove empty strings

                if len(error_log) > 0:
                    return {
                        'task_id': task_id,
                        'success': False,
                        'errors': error_log
                    }
    
            # Process each directory
            for i, dir_path in enumerate(release_dir_list):
                self.update_state(
                    state='PROGRESS',
                    meta={'current': i, 'total': len(release_dir_list), 'directory': dir_path}
                )
                error_log.extend(builder.create_release(dir_path))

                if len(error_log) > 0:
                    return {
                        'task_id': task_id,
                        'success': False,
                        'errors': error_log
                    }
            
            return {
                'task_id': task_id,
                'success': True,
                'directories_released': release_dir_list
            }

        else:
            # CASE: course-content
            if release_dir is not None:
                if ascendants:
                    parts = release_dir.split("/")
                    past_part = None
                    
                    for part in parts:
                        if past_part is None:
                            past_part = part
                        else:
                            past_part = f"{past_part}/{part}"
                        error_log.extend(builder.create_release(past_part))

                error_log.extend(builder.create_release(release_dir))

                if descendants:
                    path_desc = builder.get_directory_testing()
                    data = collect_sub_path_positions_if_meta_exists(
                        os.path.join(path_desc, release_dir)
                    )

                    for d in data:
                        error_log.extend(builder.create_release(os.path.join(release_dir, d[0])))

            # CASE: course
            else:
                error_log.extend(builder.create_course_release())

                if descendants:
                    data = collect_sub_path_positions_if_meta_exists(
                        builder.get_directory_testing()
                    )

                    for d in data:
                        error_log.extend(builder.create_release(d[0]))

            if len(error_log) > 0:
                return {
                    'task_id': task_id,
                    'success': False,
                    'errors': error_log
                }
            else:
                return {
                    'task_id': task_id,
                    'success': True,
                    'release_dir': release_dir,
                    'ascendants': ascendants,
                    'descendants': descendants
                }


@app.task(bind=True, name="ctutor_backend.tasks.system.submit_result")
def submit_result_task(self, submission_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit test results.
    
    This is a Celery task that replaces the Prefect flow.
    """
    task_id = self.request.id
    
    try:
        submission = Submission(**submission_dict)
        api_create_submission(submission)
        
        return {
            'task_id': task_id,
            'success': True,
            'submission_id': submission_dict.get('id'),
            'result_id': submission_dict.get('result_id')
        }
    except Exception as e:
        return {
            'task_id': task_id,
            'success': False,
            'error': str(e)
        }