import logging
from sqlalchemy.orm import Session, joinedload
from ctutor_backend.interface.course_content_types import CourseContentTypeList
from ctutor_backend.interface.student_course_contents import (
    CourseContentStudentList, ResultStudentList, SubmissionGroupStudentList,
    SubmissionGroupRepository, SubmissionGroupMemberBasic, SubmissionGroupGradingStudent
)
from ctutor_backend.model.course import CourseSubmissionGroupMember, CourseMember, CourseContent, CourseSubmissionGroupGrading
from ctutor_backend.model.auth import User
from ctutor_backend.model.deployment import CourseContentDeployment
from ctutor_backend.model.example import ExampleVersion, Example

logger = logging.getLogger(__name__)

def course_member_course_content_result_mapper(course_member_course_content_result, db: Session = None):

    query = course_member_course_content_result

    course_content = query[0]
    result_count = query[1]
    result = query[2]
    course_submission_group = query[3]
    submitted_count = query[4] if len(query) > 4 else None
    submission_status = query[5] if len(query) > 5 else None
    submission_grading = query[6] if len(query) > 6 else None
    
    # Get directory from deployment's example if available, otherwise from properties
    directory = None
    if hasattr(course_content, 'deployment') and course_content.deployment and db:
        # Get the example through deployment
        from ctutor_backend.model.deployment import CourseContentDeployment
        from ctutor_backend.model.example import Example, ExampleVersion
        
        deployment = course_content.deployment
        if deployment.example_version_id:
            # Get example version and then example
            example_version = db.query(ExampleVersion).filter(
                ExampleVersion.id == deployment.example_version_id
            ).first()
            if example_version and example_version.example:
                directory = example_version.example.directory
    
    # Fallback to properties if no example directory found
    if not directory and course_content.properties:
        directory = course_content.properties.get("gitlab", {}).get("directory")

    repository = None
    if course_submission_group != None and course_submission_group.properties != None:
        gitlab_info = course_submission_group.properties.get('gitlab', {})
        base_url = gitlab_info.get('url', '').rstrip('/')
        full_path = gitlab_info.get('full_path', '')
        clone_url = f"{base_url}/{full_path}.git"

        repository = SubmissionGroupRepository(
                            provider="gitlab",
                            url=gitlab_info.get('url', ''),
                            full_path=gitlab_info.get('full_path', ''),
                            clone_url=clone_url,
                            web_url=gitlab_info.get('web_url'))
    
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
            directory=directory,
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
            submission_group=SubmissionGroupStudentList(
                    id=str(course_submission_group.id) if course_submission_group else None,
                    status=submission_status,
                    grading=submission_grading,
                    count=submitted_count if submitted_count != None else 0,
                    max_submissions=course_submission_group.max_submissions if course_submission_group else None,
                    max_group_size=course_submission_group.max_group_size if course_submission_group else None,
                    repository=repository
                ) if course_submission_group != None else None
        )