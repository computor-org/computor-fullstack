import logging
from sqlalchemy.orm import Session, joinedload
from ctutor_backend.interface.course_content_types import CourseContentTypeList
from ctutor_backend.interface.student_course_contents import (
    CourseContentStudentList, ResultStudentList, SubmissionGroupStudentList,
    SubmissionGroupRepository, SubmissionGroupMemberBasic, SubmissionGroupGradingStudent
)
from ctutor_backend.model.course import CourseSubmissionGroupMember, CourseMember, CourseContent, CourseSubmissionGroupGrading
from ctutor_backend.model.auth import User

logger = logging.getLogger(__name__)

def build_enhanced_submission_group(course_submission_group, submission_status, submission_grading, submitted_count, db: Session):
    """
    Build enhanced submission group data with repository, members, and example information
    """
    if not course_submission_group:
        return None
    
    # Get course content info with example relationship
    course_content = db.query(CourseContent).options(
        joinedload(CourseContent.example)
    ).filter(
        CourseContent.id == course_submission_group.course_content_id
    ).first()
    
    # Get example identifier if course content has an example
    example_identifier = None
    if course_content and course_content.example:
        example_identifier = str(course_content.example.identifier)
    
    # Get course content path
    course_content_path = None
    course_content_title = None
    if course_content:
        course_content_path = str(course_content.path) if course_content.path else None
        course_content_title = course_content.title
    
    # Get all members
    members_query = db.query(
        CourseSubmissionGroupMember,
        User.id.label('user_id'),
        User.username,
        User.given_name,
        User.family_name
    ).join(
        CourseMember,
        CourseSubmissionGroupMember.course_member_id == CourseMember.id
    ).join(
        User,
        CourseMember.user_id == User.id
    ).filter(
        CourseSubmissionGroupMember.course_submission_group_id == course_submission_group.id
    )
    
    members = []
    for member_row in members_query.all():
        # Construct full name from given_name and family_name
        full_name = None
        if member_row.given_name or member_row.family_name:
            full_name = f"{member_row.given_name or ''} {member_row.family_name or ''}".strip()
        
        members.append(SubmissionGroupMemberBasic(
            id=str(member_row[0].id),
            user_id=str(member_row.user_id),
            course_member_id=str(member_row[0].course_member_id),
            username=member_row.username,
            full_name=full_name
        ))
    
    # Build repository info if available
    repository = None
    if course_submission_group.properties:
        # Check for gitlab info in properties
        gitlab_info = course_submission_group.properties.get('gitlab', {})
        
        # Also check for http_url_to_repo at the root level (backward compatibility)
        http_url = course_submission_group.properties.get('http_url_to_repo')
        
        if gitlab_info.get('full_path'):
            # Get clone URL - try multiple possible sources
            clone_url = (
                gitlab_info.get('clone_url') or 
                gitlab_info.get('http_url_to_repo') or
                http_url
            )
            
            if not clone_url and gitlab_info.get('url') and gitlab_info.get('full_path'):
                # Construct clone URL from base URL and path
                base_url = gitlab_info.get('url', '').rstrip('/')
                full_path = gitlab_info.get('full_path', '')
                clone_url = f"{base_url}/{full_path}.git"
            
            repository = SubmissionGroupRepository(
                provider="gitlab",
                url=gitlab_info.get('url', ''),
                full_path=gitlab_info.get('full_path', ''),
                clone_url=clone_url,
                web_url=gitlab_info.get('web_url')
            )
    
    # Get latest grading with grader name
    latest_grading = None
    if submission_status and submission_grading is not None:
        # Try to get grader information
        grading_query = db.query(
            CourseSubmissionGroupGrading,
            User.given_name,
            User.family_name
        ).join(
            CourseMember,
            CourseSubmissionGroupGrading.graded_by_course_member_id == CourseMember.id
        ).join(
            User,
            CourseMember.user_id == User.id
        ).filter(
            CourseSubmissionGroupGrading.course_submission_group_id == course_submission_group.id
        ).order_by(
            CourseSubmissionGroupGrading.created_at.desc()
        ).first()
        
        if grading_query:
            grading, given_name, family_name = grading_query
            # Construct grader name from given_name and family_name
            grader_name = None
            if given_name or family_name:
                grader_name = f"{given_name or ''} {family_name or ''}".strip()
            latest_grading = SubmissionGroupGradingStudent(
                id=str(grading.id),
                grading=grading.grading,
                status=grading.status,
                graded_by=grader_name,
                created_at=grading.created_at
            )
    
    return SubmissionGroupStudentList(
        id=str(course_submission_group.id),
        course_content_title=course_content_title,
        course_content_path=course_content_path,
        example_identifier=example_identifier,
        max_group_size=course_submission_group.max_group_size,
        current_group_size=len(members),
        members=members,
        repository=repository,
        latest_grading=latest_grading,
        # Backward compatibility fields
        status=submission_status,
        grading=submission_grading,
        count=submitted_count if submitted_count is not None else 0,
        max_submissions=course_submission_group.max_submissions
    )

def course_member_course_content_result_mapper(course_member_course_content_result, db: Session = None):

    query = course_member_course_content_result

    course_content = query[0]
    result_count = query[1]
    result = query[2]
    course_submission_group = query[3]
    submitted_count = query[4] if len(query) > 4 else None
    submission_status = query[5] if len(query) > 5 else None
    submission_grading = query[6] if len(query) > 6 else None

    return CourseContentStudentList(
            id=course_content.id,
            title=course_content.title,
            path=course_content.path,
            course_id=course_content.course_id,
            course_content_type_id=course_content.course_content_type_id,
            course_content_kind_id=course_content.course_content_kind_id,
            course_content_type=CourseContentTypeList.model_validate(course_content.course_content_type),
            position=course_content.position,
            max_group_size=course_content.max_group_size,
            directory=course_content.properties.get("gitlab", {}).get("directory") if course_content.properties else None,
            color=course_content.course_content_type.color,
            submitted=True if submitted_count != None and submitted_count > 0 else False,
            result_count=result_count if result_count != None else 0,
            max_test_runs=course_content.max_test_runs,
            result=ResultStudentList(
                execution_backend_id=result.execution_backend_id,
                test_system_id=result.test_system_id,
                version_identifier=result.version_identifier,
                status=result.status,
                result=result.result,
                result_json=result.result_json,
                submit=result.submit
            ) if result != None and result.test_system_id != None else None,
            submission_group=build_enhanced_submission_group(
                course_submission_group, submission_status, submission_grading, submitted_count, db
            ) if course_submission_group != None and db != None else (
                SubmissionGroupStudentList(
                    id=str(course_submission_group.id) if course_submission_group else None,
                    status=submission_status,
                    grading=submission_grading,
                    count=submitted_count if submitted_count != None else 0,
                    max_submissions=course_submission_group.max_submissions if course_submission_group else None,
                    max_group_size=course_submission_group.max_group_size if course_submission_group else None,
                ) if course_submission_group != None else None
            )
        )