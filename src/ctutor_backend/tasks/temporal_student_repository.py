"""
Temporal workflows for creating and managing student repositories.
This workflow handles forking the student-template repository when students join a course.
"""
import logging
import json
from datetime import timedelta
from typing import Dict, Any, Optional
from uuid import UUID

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from sqlalchemy.orm import Session
from gitlab import Gitlab
from gitlab.exceptions import GitlabCreateError, GitlabGetError

from .temporal_base import BaseWorkflow, WorkflowResult
from .registry import register_task
from ..database import get_db
from ..model.course import Course, CourseMember, CourseSubmissionGroup, CourseSubmissionGroupMember
from ..model.organization import Organization
from ..gitlab_utils import gitlab_fork_project, gitlab_unprotect_branches
from ..settings import settings

logger = logging.getLogger(__name__)


@activity.defn(name="create_student_repository")
async def create_student_repository(
    course_member_id: str,
    course_id: str,
    submission_group_id: str
) -> Dict[str, Any]:
    """
    Create a student repository by forking the student-template.
    
    Args:
        course_member_id: ID of the course member (student)
        course_id: ID of the course
        submission_group_id: ID of the submission group
        
    Returns:
        Dict containing repository information
    """
    db = next(get_db())
    
    try:
        # Get course member and course information
        course_member = db.query(CourseMember).filter(CourseMember.id == course_member_id).first()
        if not course_member:
            raise ValueError(f"Course member {course_member_id} not found")
            
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")
            
        # Get GitLab properties from course
        course_properties = course.properties or {}
        gitlab_namespace_id = course_properties.get('gitlab_students_group_id')
        student_template_id = course_properties.get('gitlab_student_template_id')
        
        if not gitlab_namespace_id:
            raise ValueError(f"Course {course_id} missing gitlab_students_group_id")
        if not student_template_id:
            raise ValueError(f"Course {course_id} missing gitlab_student_template_id")
            
        # Get user information for repository naming
        user = course_member.user
        username = user.email.split('@')[0] if user.email else f"user_{user.id}"
        
        # Initialize GitLab client
        gitlab = Gitlab(settings.gitlab_url, private_token=settings.gitlab_token)
        
        # Generate repository name and path
        repo_name = f"{username}-{course.slug}"
        repo_path = repo_name.lower().replace(' ', '-').replace('_', '-')
        
        logger.info(f"Forking student-template {student_template_id} to {repo_path} in namespace {gitlab_namespace_id}")
        
        # Fork the student-template repository
        try:
            gitlab_fork_project(
                gitlab=gitlab,
                fork_id=student_template_id,
                dest_path=repo_path,
                dest_name=repo_name,
                namespace_id=gitlab_namespace_id
            )
            
            # Get the newly created project
            # Wait a moment for GitLab to process the fork
            import asyncio
            await asyncio.sleep(2)
            
            # Find the forked project
            projects = gitlab.groups.get(gitlab_namespace_id).projects.list(search=repo_path)
            forked_project = None
            for project in projects:
                if project.path == repo_path:
                    forked_project = gitlab.projects.get(project.id)
                    break
                    
            if not forked_project:
                raise ValueError(f"Forked project {repo_path} not found after creation")
                
            # Unprotect branches to allow student pushes
            try:
                gitlab_unprotect_branches(gitlab, forked_project.id, "main")
            except Exception as e:
                logger.warning(f"Could not unprotect main branch: {e}")
                
            try:
                gitlab_unprotect_branches(gitlab, forked_project.id, "master")
            except Exception as e:
                logger.warning(f"Could not unprotect master branch: {e}")
                
            # Update submission group with repository information
            submission_group = db.query(CourseSubmissionGroup).filter(
                CourseSubmissionGroup.id == submission_group_id
            ).first()
            
            if submission_group:
                repository_info = {
                    "gitlab_project_id": forked_project.id,
                    "gitlab_project_path": forked_project.path_with_namespace,
                    "http_url_to_repo": forked_project.http_url_to_repo,
                    "ssh_url_to_repo": forked_project.ssh_url_to_repo,
                    "web_url": forked_project.web_url
                }
                
                # Store repository info in properties
                submission_group.properties = submission_group.properties or {}
                submission_group.properties.update(repository_info)
                db.commit()
                
                logger.info(f"Successfully created student repository {repo_path} for {username}")
                
                return {
                    "success": True,
                    "repository": repository_info,
                    "course_member_id": course_member_id,
                    "submission_group_id": submission_group_id
                }
                
        except GitlabCreateError as e:
            if "has already been taken" in str(e):
                logger.warning(f"Repository {repo_path} already exists")
                # Try to find existing repository
                projects = gitlab.groups.get(gitlab_namespace_id).projects.list(search=repo_path)
                for project in projects:
                    if project.path == repo_path:
                        repository_info = {
                            "gitlab_project_id": project.id,
                            "gitlab_project_path": project.path_with_namespace,
                            "http_url_to_repo": project.http_url_to_repo,
                            "ssh_url_to_repo": project.ssh_url_to_repo,
                            "web_url": project.web_url
                        }
                        
                        # Update submission group
                        submission_group = db.query(CourseSubmissionGroup).filter(
                            CourseSubmissionGroup.id == submission_group_id
                        ).first()
                        if submission_group:
                            submission_group.properties = submission_group.properties or {}
                            submission_group.properties.update(repository_info)
                            db.commit()
                            
                        return {
                            "success": True,
                            "repository": repository_info,
                            "course_member_id": course_member_id,
                            "submission_group_id": submission_group_id,
                            "existing": True
                        }
            raise e
            
    except Exception as e:
        logger.error(f"Failed to create student repository: {e}")
        raise e
    finally:
        db.close()


@activity.defn(name="create_team_repository")
async def create_team_repository(
    submission_group_id: str,
    course_id: str,
    team_members: list[str]
) -> Dict[str, Any]:
    """
    Create a team repository for group assignments.
    
    Args:
        submission_group_id: ID of the submission group
        course_id: ID of the course
        team_members: List of course member IDs in the team
        
    Returns:
        Dict containing repository information
    """
    db = next(get_db())
    
    try:
        # Get course information
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")
            
        submission_group = db.query(CourseSubmissionGroup).filter(
            CourseSubmissionGroup.id == submission_group_id
        ).first()
        if not submission_group:
            raise ValueError(f"Submission group {submission_group_id} not found")
            
        # Get GitLab properties
        course_properties = course.properties or {}
        gitlab_namespace_id = course_properties.get('gitlab_students_group_id')
        student_template_id = course_properties.get('gitlab_student_template_id')
        
        if not gitlab_namespace_id or not student_template_id:
            raise ValueError(f"Course {course_id} missing GitLab configuration")
            
        # Get team member names for repository naming
        team_name_parts = []
        for member_id in team_members[:3]:  # Use first 3 members for naming
            member = db.query(CourseMember).filter(CourseMember.id == member_id).first()
            if member and member.user:
                username = member.user.email.split('@')[0] if member.user.email else f"user_{member.user.id}"
                team_name_parts.append(username)
                
        team_name = "-".join(team_name_parts) if team_name_parts else f"team-{submission_group_id[:8]}"
        
        # Initialize GitLab client
        gitlab = Gitlab(settings.gitlab_url, private_token=settings.gitlab_token)
        
        # Generate repository name and path
        content_path = submission_group.course_content.path.replace('.', '-')
        repo_name = f"team-{content_path}-{team_name}"
        repo_path = repo_name.lower().replace(' ', '-').replace('_', '-')[:63]  # GitLab path limit
        
        logger.info(f"Creating team repository {repo_path} for {len(team_members)} members")
        
        # Fork the student-template repository
        gitlab_fork_project(
            gitlab=gitlab,
            fork_id=student_template_id,
            dest_path=repo_path,
            dest_name=repo_name,
            namespace_id=gitlab_namespace_id
        )
        
        # Get the newly created project
        import asyncio
        await asyncio.sleep(2)
        
        projects = gitlab.groups.get(gitlab_namespace_id).projects.list(search=repo_path)
        team_project = None
        for project in projects:
            if project.path == repo_path:
                team_project = gitlab.projects.get(project.id)
                break
                
        if not team_project:
            raise ValueError(f"Team project {repo_path} not found after creation")
            
        # Unprotect branches
        gitlab_unprotect_branches(gitlab, team_project.id, "main")
        gitlab_unprotect_branches(gitlab, team_project.id, "master")
        
        # Add team members as developers
        for member_id in team_members:
            member = db.query(CourseMember).filter(CourseMember.id == member_id).first()
            if member and member.properties and member.properties.get('gitlab_user_id'):
                gitlab_user_id = member.properties['gitlab_user_id']
                try:
                    team_project.members.create({
                        'user_id': gitlab_user_id,
                        'access_level': 30  # Developer access
                    })
                except Exception as e:
                    logger.warning(f"Could not add member {gitlab_user_id} to project: {e}")
                    
        # Update submission group with repository information
        repository_info = {
            "gitlab_project_id": team_project.id,
            "gitlab_project_path": team_project.path_with_namespace,
            "http_url_to_repo": team_project.http_url_to_repo,
            "ssh_url_to_repo": team_project.ssh_url_to_repo,
            "web_url": team_project.web_url,
            "team_members": team_members
        }
        
        submission_group.properties = submission_group.properties or {}
        submission_group.properties.update(repository_info)
        db.commit()
        
        logger.info(f"Successfully created team repository {repo_path}")
        
        return {
            "success": True,
            "repository": repository_info,
            "submission_group_id": submission_group_id,
            "team_size": len(team_members)
        }
        
    except Exception as e:
        logger.error(f"Failed to create team repository: {e}")
        raise e
    finally:
        db.close()


@workflow.defn(name="StudentRepositoryCreationWorkflow")
class StudentRepositoryCreationWorkflow(BaseWorkflow):
    """
    Workflow to create student repositories when they join a course.
    Handles both individual and team repositories.
    """
    
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> WorkflowResult:
        """
        Execute the student repository creation workflow.
        
        Expected params:
        - course_member_id: ID of the course member
        - course_id: ID of the course
        - submission_group_ids: List of submission group IDs to process
        - is_team: Whether this is for team repositories
        - team_members: List of member IDs (for team repos)
        """
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2
        )
        
        try:
            course_member_id = params.get('course_member_id')
            course_id = params.get('course_id')
            submission_group_ids = params.get('submission_group_ids', [])
            is_team = params.get('is_team', False)
            team_members = params.get('team_members', [])
            
            results = []
            
            if is_team:
                # Create team repositories
                for submission_group_id in submission_group_ids:
                    result = await workflow.execute_activity(
                        create_team_repository,
                        args=[submission_group_id, course_id, team_members],
                        retry_policy=retry_policy,
                        start_to_close_timeout=timedelta(minutes=5)
                    )
                    results.append(result)
            else:
                # Create individual repositories
                for submission_group_id in submission_group_ids:
                    result = await workflow.execute_activity(
                        create_student_repository,
                        args=[course_member_id, course_id, submission_group_id],
                        retry_policy=retry_policy,
                        start_to_close_timeout=timedelta(minutes=5)
                    )
                    results.append(result)
                    
            return WorkflowResult(
                success=True,
                message=f"Created {len(results)} repositories",
                data={"repositories": results}
            )
            
        except Exception as e:
            logger.error(f"Student repository creation workflow failed: {e}")
            return WorkflowResult(
                success=False,
                message=str(e),
                error=str(e)
            )


# Register the workflow
register_task("student_repository_creation", StudentRepositoryCreationWorkflow)