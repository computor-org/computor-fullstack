from ctutor_backend.interface.course_content_types import CourseContentTypeList
from ctutor_backend.interface.student_course_contents import CourseContentStudentList, ResultStudentList, SubmissionGroupStudentList

def course_member_course_content_result_mapper(course_member_course_content_result):

    query = course_member_course_content_result

    course_content = query[0]
    result_count = query[1]
    result = query[2]
    course_submission_group = query[3]
    submitted_count = query[4] if len(query) > 4 else None

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
            directory=course_content.properties["gitlab"]["directory"],
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
            submission=SubmissionGroupStudentList(
                id=course_submission_group.id,
                status=course_submission_group.status,
                grading=course_submission_group.grading,
                count=submitted_count if submitted_count != None else 0,
                max_submissions=course_submission_group.max_submissions
            ) if course_submission_group != None else None
        )