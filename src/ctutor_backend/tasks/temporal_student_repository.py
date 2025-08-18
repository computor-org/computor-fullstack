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


async def fork_project_with_polling(
    gitlab: Gitlab,
    source_project_id: int,
    dest_path: str,
    dest_name: str,
    namespace_id: int,
    max_attempts: int = 10,
    poll_interval: int = 5,
    initial_wait: int = 2
) -> Any:
    """
    Fork a GitLab project and poll for completion.
    
    Args:
        gitlab: GitLab client instance
        source_project_id: ID of the project to fork
        dest_path: Path for the forked project
        dest_name: Name for the forked project
        namespace_id: GitLab namespace ID where to create the fork
        max_attempts: Maximum number of polling attempts
        poll_interval: Seconds between polling attempts
        initial_wait: Initial wait before starting to poll
        
    Returns:
        The forked GitLab project object
        
    Raises:
        ValueError: If the fork is not found after max_attempts
    """
    import asyncio
    
    # Initiate the fork
    gitlab_fork_project(
        gitlab=gitlab,
        fork_id=source_project_id,
        dest_path=dest_path,
        dest_name=dest_name,
        namespace_id=namespace_id
    )
    
    # Initial wait before polling
    await asyncio.sleep(initial_wait)
    
    # Poll for fork completion
    forked_project = None
    for attempt in range(max_attempts):
        # Find the forked project
        projects = gitlab.groups.get(namespace_id).projects.list(search=dest_path)
        for project in projects:
            if project.path == dest_path:
                forked_project = gitlab.projects.get(project.id)
                break
        
        if forked_project:
            logger.info(f"Fork completed after {attempt + 1} attempt(s)")
            return forked_project
            
        if attempt < max_attempts - 1:
            logger.info(f"Fork not ready yet, waiting {poll_interval} seconds (attempt {attempt + 1}/{max_attempts})")
            await asyncio.sleep(poll_interval)
            
    raise ValueError(f"Forked project {dest_path} not found after {max_attempts} attempts")


async def add_members_to_project(
    gitlab: Gitlab,
    project,
    member_ids: list[str],
    db: Session,
    access_level: int = 40
) -> None:
    """
    Add course members as maintainers to a GitLab project.
    
    Args:
        gitlab: GitLab client instance
        project: GitLab project object
        member_ids: List of course member IDs to add
        db: Database session
        access_level: GitLab access level (40 = Maintainer)
    """
    for member_id in member_ids:
        member = db.query(CourseMember).filter(CourseMember.id == member_id).first()
        if not member or not member.user:
            continue
            
        gitlab_user_id = None
        member_props = member.properties or {}
        
        # Get or find GitLab user ID
        if member_props.get('gitlab_user_id'):
            gitlab_user_id = member_props['gitlab_user_id']
        elif member.user.email:
            # Try to find by email
            try:
                users = gitlab.users.list(search=member.user.email)
                if users:
                    gitlab_user_id = users[0].id
                    # Store for future use
                    member.properties = member_props
                    member.properties['gitlab_user_id'] = gitlab_user_id
                    db.add(member)
                    db.commit()
            except Exception as e:
                logger.warning(f"Could not find GitLab user for {member.user.email}: {e}")
        
        if gitlab_user_id:
            try:
                project.members.create({
                    'user_id': gitlab_user_id,
                    'access_level': access_level
                })
                logger.info(f"Added user {gitlab_user_id} as maintainer to project {project.id}")
            except Exception as e:
                logger.warning(f"Could not add member {gitlab_user_id} to project: {e}")


@activity.defn(name="create_student_repository")
async def create_student_repository(
    course_member_id: str,
    course_id: str,
    submission_group_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a student repository by forking the student-template.
    
    Args:
        course_member_id: ID of the course member (student)
        course_id: ID of the course
        submission_group_id: ID of the submission group (optional)
        
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
        gitlab_props = course_properties.get('gitlab', {})
        gitlab_namespace_id = gitlab_props.get('students_group', {}).get('group_id')
        
        if not gitlab_namespace_id:
            raise ValueError(f"Course {course_id} missing gitlab.students_group.group_id")
        
        # Initialize GitLab client to find student-template project
        gitlab = Gitlab(settings.gitlab_url, private_token=settings.gitlab_token)
        
        # Get student-template project path from course properties
        student_template_path = gitlab_props.get('projects', {}).get('student_template', {}).get('full_path')
        if not student_template_path:
            # Fallback to URL parsing
            student_template_url = gitlab_props.get('student_template_url')
            if student_template_url:
                # Extract path from URL: http://localhost:8084/itpcp/progphys/python.2026/student-template
                import re
                match = re.search(r'/([^/]+/[^/]+/[^/]+/student-template)$', student_template_url)
                if match:
                    student_template_path = match.group(1)
        
        if not student_template_path:
            raise ValueError(f"Course {course_id} missing student-template project path")
        
        # Find the student-template project
        try:
            student_template_project = gitlab.projects.get(student_template_path.replace('/', '%2F'))
            student_template_id = student_template_project.id
        except Exception as e:
            raise ValueError(f"Could not find student-template project at {student_template_path}: {e}")
            
        # Get user information for repository naming
        user = course_member.user
        username = user.email.split('@')[0] if user.email else f"user_{user.id}"
        
        # Generate repository name and path (just the username)
        repo_name = username
        repo_path = repo_name.lower().replace(' ', '-').replace('_', '-')
        
        logger.info(f"Forking student-template {student_template_id} to {repo_path} in namespace {gitlab_namespace_id}")
        
        # Fork the student-template repository with polling
        try:
            forked_project = await fork_project_with_polling(
                gitlab=gitlab,
                source_project_id=student_template_id,
                dest_path=repo_path,
                dest_name=repo_name,
                namespace_id=gitlab_namespace_id
            )
                
            # Unprotect branches to allow student pushes
            try:
                gitlab_unprotect_branches(gitlab, forked_project.id, "main")
            except Exception as e:
                logger.warning(f"Could not unprotect main branch: {e}")
                
            try:
                gitlab_unprotect_branches(gitlab, forked_project.id, "master")
            except Exception as e:
                logger.warning(f"Could not unprotect master branch: {e}")
                
            # Add student as maintainer of the repository
            await add_members_to_project(
                gitlab=gitlab,
                project=forked_project,
                member_ids=[course_member_id],
                db=db
            )
                
            # Prepare repository information
            repository_info = {
                "gitlab_project_id": forked_project.id,
                "gitlab_project_path": forked_project.path_with_namespace,
                "http_url_to_repo": forked_project.http_url_to_repo,
                "ssh_url_to_repo": forked_project.ssh_url_to_repo,
                "web_url": forked_project.web_url
            }
            
            # Update submission group with repository information (if provided)
            if submission_group_id:
                submission_group = db.query(CourseSubmissionGroup).filter(
                    CourseSubmissionGroup.id == submission_group_id
                ).first()
                
                if submission_group:
                    # Store repository info in properties
                    submission_group.properties = submission_group.properties or {}
                    submission_group.properties.update(repository_info)
                    db.commit()
            
            # Store repository info in course member properties as well
            course_member.properties = course_member.properties or {}
            if 'gitlab_repository' not in course_member.properties:
                course_member.properties['gitlab_repository'] = {}
            course_member.properties['gitlab_repository'].update(repository_info)
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
                        existing_project = gitlab.projects.get(project.id)
                        
                        # Ensure student is maintainer even for existing repo
                        try:
                            course_member_props = course_member.properties or {}
                            gitlab_user_id = course_member_props.get('gitlab_user_id')
                            
                            if not gitlab_user_id:
                                users = gitlab.users.list(search=user.email)
                                if users:
                                    gitlab_user_id = users[0].id
                                    course_member.properties = course_member_props
                                    course_member.properties['gitlab_user_id'] = gitlab_user_id
                                    db.add(course_member)
                                    db.commit()
                            
                            if gitlab_user_id:
                                # Check if already a member
                                try:
                                    member = existing_project.members.get(gitlab_user_id)
                                    if member.access_level < 40:
                                        # Upgrade to maintainer
                                        member.access_level = 40
                                        member.save()
                                except:
                                    # Not a member yet, add as maintainer
                                    existing_project.members.create({
                                        'user_id': gitlab_user_id,
                                        'access_level': 40
                                    })
                        except Exception as e:
                            logger.warning(f"Could not ensure maintainer rights for existing repo: {e}")
                        
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
        gitlab_props = course_properties.get('gitlab', {})
        gitlab_namespace_id = gitlab_props.get('students_group', {}).get('group_id')
        
        if not gitlab_namespace_id:
            raise ValueError(f"Course {course_id} missing gitlab.students_group.group_id")
        
        # Initialize GitLab client to find student-template project
        gitlab = Gitlab(settings.gitlab_url, private_token=settings.gitlab_token)
        
        # Get student-template project path from course properties
        student_template_path = gitlab_props.get('projects', {}).get('student_template', {}).get('full_path')
        if not student_template_path:
            # Fallback to URL parsing
            student_template_url = gitlab_props.get('student_template_url')
            if student_template_url:
                # Extract path from URL
                import re
                match = re.search(r'/([^/]+/[^/]+/[^/]+/student-template)$', student_template_url)
                if match:
                    student_template_path = match.group(1)
        
        if not student_template_path:
            raise ValueError(f"Course {course_id} missing student-template project path")
        
        # Find the student-template project
        try:
            student_template_project = gitlab.projects.get(student_template_path.replace('/', '%2F'))
            student_template_id = student_template_project.id
        except Exception as e:
            raise ValueError(f"Could not find student-template project at {student_template_path}: {e}")
            
        # Get team member names for repository naming
        team_name_parts = []
        for member_id in team_members[:3]:  # Use first 3 members for naming
            member = db.query(CourseMember).filter(CourseMember.id == member_id).first()
            if member and member.user:
                username = member.user.email.split('@')[0] if member.user.email else f"user_{member.user.id}"
                team_name_parts.append(username)
                
        team_name = "-".join(team_name_parts) if team_name_parts else f"team-{submission_group_id[:8]}"
        
        # Generate repository name and path (just team-{team_name})
        repo_name = f"team-{team_name}"
        repo_path = repo_name.lower().replace(' ', '-').replace('_', '-')[:63]  # GitLab path limit
        
        logger.info(f"Creating team repository {repo_path} for {len(team_members)} members")
        
        # Fork the student-template repository with polling
        team_project = await fork_project_with_polling(
            gitlab=gitlab,
            source_project_id=student_template_id,
            dest_path=repo_path,
            dest_name=repo_name,
            namespace_id=gitlab_namespace_id
        )
            
        # Unprotect branches
        gitlab_unprotect_branches(gitlab, team_project.id, "main")
        gitlab_unprotect_branches(gitlab, team_project.id, "master")
        
        # Add team members as maintainers
        await add_members_to_project(
            gitlab=gitlab,
            project=team_project,
            member_ids=team_members,
            db=db
        )
                    
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


@register_task
@workflow.defn(name="StudentRepositoryCreationWorkflow", sandboxed=False)
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
                # Create individual student repository
                if submission_group_ids:
                    # If there are submission groups, create repository for each
                    for submission_group_id in submission_group_ids:
                        result = await workflow.execute_activity(
                            create_student_repository,
                            args=[course_member_id, course_id, submission_group_id],
                            retry_policy=retry_policy,
                            start_to_close_timeout=timedelta(minutes=5)
                        )
                        results.append(result)
                else:
                    # No submission groups yet, but still create the repository
                    result = await workflow.execute_activity(
                        create_student_repository,
                        args=[course_member_id, course_id, None],  # No submission group
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