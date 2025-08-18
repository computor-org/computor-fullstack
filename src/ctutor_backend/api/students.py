import json
from uuid import UUID
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from ctutor_backend.api.exceptions import BadRequestException, InternalServerException, NotFoundException
from ctutor_backend.api.mappers import course_member_course_content_result_mapper
from ctutor_backend.api.messages import get_submission_mergerequest
from ctutor_backend.api.permissions import check_course_permissions
from ctutor_backend.api.queries import user_course_content_list_query, user_course_content_query
from ctutor_backend.interface.auth import GLPAuthConfig
from ctutor_backend.interface.course_contents import CourseContentGet
from ctutor_backend.interface.course_members import CourseMemberProperties
from ctutor_backend.interface.student_course_contents import CourseContentStudentInterface, CourseContentStudentList, CourseContentStudentQuery
from ctutor_backend.api.auth import HeaderAuthCredentials, get_auth_credentials, get_current_permissions
from ctutor_backend.database import get_db
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.student_courses import CourseStudentGet, CourseStudentInterface, CourseStudentList, CourseStudentQuery, CourseStudentRepository
from ctutor_backend.interface.submission_groups import (
    SubmissionGroupStudent, SubmissionGroupStudentQuery, SubmissionGroupRepository,
    SubmissionGroupMemberBasic, SubmissionGroupGradingStudent
)
from ctutor_backend.model.auth import User
from ctutor_backend.model.course import (
    Course, CourseContent, CourseMember, CourseSubmissionGroup, 
    CourseSubmissionGroupMember, CourseSubmissionGroupGrading
)
from ctutor_backend.redis_cache import get_redis_client
from aiocache import BaseCache
from sqlalchemy import func

student_router = APIRouter()

async def student_get_course_content_cached(course_content_id: str, permissions: Principal, cache: BaseCache, db: Session):

    cache_key = f"{permissions.get_user_id_or_throw()}:course-contents:{course_content_id}"

    course_content = await cache.get(cache_key)

    if course_content != None:
        return CourseContentGet.model_validate(json.loads(course_content),from_attributes=True)

    query = check_course_permissions(permissions,CourseContent,"_student",db).filter(CourseContent.id == course_content_id).first()

    if query == None:
        raise NotFoundException()
    
    course_content = CourseContentGet.model_validate(query,from_attributes=True)

    try:
        await cache.set(cache_key, course_content.model_dump_json(), ttl=120)

    except Exception as e:
        raise e
    
    return course_content

async def student_course_content_messages_cached(course_content_id: str, user_id: str, permissions: Principal, cache: BaseCache, db: Session) -> tuple[CourseMemberProperties,str,str]:

    cache_key = f"{permissions.get_user_id_or_throw()}:course-contents:{course_content_id}"

    course_content = await cache.get(cache_key)

    if course_content != None:
        cached_obj = json.loads(course_content)

        course_member_properties = CourseMemberProperties.model_validate(cached_obj["properties"],from_attributes=True)
        course_content_id = cached_obj["course_content_id"]
        course_content_path = cached_obj["course_content_path"]

        return course_member_properties, course_content_id, course_content_path

    query = db.query(CourseMember.properties,CourseContent.id,CourseContent.path) \
        .select_from(CourseMember) \
            .join(Course,Course.id == CourseMember.course_id) \
                .join(CourseContent,CourseContent.course_id == Course.id) \
                    .join(User,User.id == CourseMember.user_id) \
                        .filter(
                            CourseContent.id == course_content_id,
                            CourseMember.user_id == user_id
                        ).first()
    
    if query == None:
        raise NotFoundException()

    course_member_properties = CourseMemberProperties(**query[0])
    course_content_id = str(query[1])
    course_content_path = str(query[2])

    try:
        await cache.set(cache_key, json.dumps({"properties":course_member_properties.model_dump(),"course_content_id": course_content_id,"course_content_path": course_content_path}), ttl=120)

    except Exception as e:
        raise e

    return course_member_properties, course_content_id, course_content_path

@student_router.get("/course-contents/{course_content_id}", response_model=CourseContentStudentList)
def student_get_course_content(course_content_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    course_contents_result = user_course_content_query(permissions.get_user_id_or_throw(),course_content_id,db)
 
    return course_member_course_content_result_mapper(course_contents_result)

@student_router.get("/course-contents", response_model=list[CourseContentStudentList])
def student_list_course_contents(permissions: Annotated[Principal, Depends(get_current_permissions)], params: CourseContentStudentQuery = Depends(), db: Session = Depends(get_db)):

    query = user_course_content_list_query(permissions.get_user_id_or_throw(),db)

    course_contents_results = CourseContentStudentInterface.search(db,query,params).all()

    response_list: list[CourseContentStudentList] = []

    for course_contents_result in course_contents_results:
        response_list.append(course_member_course_content_result_mapper(course_contents_result))

    return response_list

@student_router.get("/courses", response_model=list[CourseStudentList])
async def student_list_courses(permissions: Annotated[Principal, Depends(get_current_permissions)], params: CourseStudentQuery = Depends(), db: Session = Depends(get_db)):

    # TODO: query should be improved: course_contents for course_group_members shall be available. All ascendant sould be included afterwards, but in one query.

    courses = CourseStudentInterface.search(db,check_course_permissions(permissions,Course,"_student",db),params).all()

    response_list: list[CourseStudentList] = []

    for course in courses:

        response_list.append(CourseStudentList(
            id=course.id,
            title=course.title,
            course_family_id=course.course_family_id,
            organization_id=course.organization_id,
            course_content_types=course.course_content_types,
            path=course.path,
            repository=CourseStudentRepository(
                provider_url=course.properties["gitlab"]["url"],
                full_path=course.properties["gitlab"]["full_path"]
            )
        ))

    return response_list

@student_router.get("/courses/{course_id}", response_model=CourseStudentGet)
async def student_get_course(course_id: UUID | str,permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    course = check_course_permissions(permissions,Course,"_student",db).filter(Course.id == course_id).first()

    return CourseStudentGet(
        id=course.id,
        title=course.title,
        course_family_id=course.course_family_id,
        organization_id=course.organization_id,
        course_content_types=course.course_content_types,
        path=course.path,
        repository=CourseStudentRepository(
            provider_url=course.properties["gitlab"]["url"],
            full_path=course.properties["gitlab"]["full_path"]
        )
    )

@student_router.get("/course-contents/{course_content_id}/messages", response_model=list[dict])
async def student_list_course_content_messages(
    course_content_id: UUID | str, 
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    auth_headers: Annotated[HeaderAuthCredentials,Depends(get_auth_credentials)],
    cache: Annotated[BaseCache, Depends(get_redis_client)], 
    db: Session = Depends(get_db)
):

    user_id = permissions.get_user_id_or_throw()

    course_member_properties, course_content_id, course_content_path = await student_course_content_messages_cached(course_content_id,user_id,permissions,cache,db)

    if auth_headers.type != GLPAuthConfig:
        raise BadRequestException(details="GitLab messages are restricted to GLPAT authenticated users")

    merge_request = await get_submission_mergerequest(auth_headers.credentials,user_id,course_member_properties.gitlab.full_path_submission,course_content_id,course_content_path)

    if merge_request == None:
        raise NotFoundException()

    notes = merge_request.notes.list()

    note_response = []
    for note in notes:
        note_response.append(note.asdict())

    return note_response

class CourseContentMessage(BaseModel):
    body: str

@student_router.post("/course-contents/{course_content_id}/messages", response_model=list[dict])
async def student_post_course_content_messages(
    course_content_id: UUID | str, 
    message: CourseContentMessage, 
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    auth_headers: Annotated[HeaderAuthCredentials,Depends(get_auth_credentials)],
    cache: Annotated[BaseCache, Depends(get_redis_client)],
    db: Session = Depends(get_db)):

    if auth_headers.type != GLPAuthConfig:
        raise BadRequestException(details="GitLab messages are restricted to GLPAT authenticated users")

    user_id = permissions.get_user_id_or_throw()

    course_member_properties, course_content_id, course_content_path = await student_course_content_messages_cached(course_content_id,user_id,permissions,cache,db)

    merge_request = await get_submission_mergerequest(auth_headers.credentials,user_id,course_member_properties.gitlab.full_path_submission,course_content_id,course_content_path)

    if merge_request == None:
        raise NotFoundException()

    try:
        merge_request.notes.create({"body": message.body})
    except Exception as e:
        raise InternalServerException(detail=e.args)
    
    notes = merge_request.notes.list()

    note_response = []
    for note in notes:
        note_response.append(note.asdict())

    return note_response

@student_router.get("/repositories", response_model=list[str])
async def get_signup_init_data(permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    # TODO: only gitlab is implemented yet
    properties = [q[0] for q in db.query(CourseMember.properties) \
        .join(User,User.id == CourseMember.user_id) \
            .filter(User.id == permissions.user_id,CourseMember.properties["gitlab"] != None).all()]

    repositories = []

    for p in properties:
        props = CourseMemberProperties(**p)
        repositories.append(f"{props.gitlab.url}/{props.gitlab.full_path}")

    return repositories


@student_router.get("/submission-groups", response_model=list[SubmissionGroupStudent])
async def student_list_submission_groups(
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    params: SubmissionGroupStudentQuery = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get all submission groups for the current student.
    Returns only submission groups where the student is a member.
    Includes repository information and latest grading.
    """
    user_id = permissions.get_user_id_or_throw()
    
    # Base query for submission groups where the user is a member
    query = db.query(CourseSubmissionGroup).join(
        CourseSubmissionGroupMember,
        CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id
    ).join(
        CourseMember,
        CourseSubmissionGroupMember.course_member_id == CourseMember.id
    ).filter(
        CourseMember.user_id == user_id
    )
    
    # Apply filters
    if params.course_id:
        query = query.filter(CourseSubmissionGroup.course_id == params.course_id)
    if params.course_content_id:
        query = query.filter(CourseSubmissionGroup.course_content_id == params.course_content_id)
    if params.has_repository is not None:
        if params.has_repository:
            query = query.filter(CourseSubmissionGroup.properties['gitlab'] != None)
        else:
            query = query.filter(CourseSubmissionGroup.properties['gitlab'] == None)
    
    submission_groups = query.all()
    
    response = []
    for sg in submission_groups:
        # Get course content info
        course_content = db.query(CourseContent).filter(
            CourseContent.id == sg.course_content_id
        ).first()
        
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
            CourseSubmissionGroupMember.course_submission_group_id == sg.id
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
        
        # Get latest grading
        latest_grading = None
        if params.is_graded is None or params.is_graded:
            grading_query = db.query(
                CourseSubmissionGroupGrading,
                User.full_name.label('grader_name')
            ).join(
                CourseMember,
                CourseSubmissionGroupGrading.graded_by_course_member_id == CourseMember.id
            ).join(
                User,
                CourseMember.user_id == User.id
            ).filter(
                CourseSubmissionGroupGrading.course_submission_group_id == sg.id
            ).order_by(
                CourseSubmissionGroupGrading.created_at.desc()
            ).first()
            
            if grading_query:
                grading, grader_name = grading_query
                latest_grading = SubmissionGroupGradingStudent(
                    id=str(grading.id),
                    grading=grading.grading,
                    status=grading.status,
                    graded_by=grader_name,
                    created_at=grading.created_at
                )
        
        # Build repository info if available
        repository = None
        if sg.properties and sg.properties.get('gitlab'):
            gitlab_info = sg.properties['gitlab']
            repository = SubmissionGroupRepository(
                provider="gitlab",
                url=gitlab_info.get('url', ''),
                full_path=gitlab_info.get('full_path', ''),
                clone_url=gitlab_info.get('clone_url'),
                web_url=gitlab_info.get('web_url')
            )
        
        # Create response object
        response.append(SubmissionGroupStudent(
            id=str(sg.id),
            course_id=str(sg.course_id),
            course_content_id=str(sg.course_content_id),
            course_content_title=course_content.title if course_content else None,
            course_content_path=str(course_content.path) if course_content else None,
            max_group_size=sg.max_group_size,
            current_group_size=len(members),
            members=members,
            repository=repository,
            latest_grading=latest_grading,
            created_at=sg.created_at,
            updated_at=sg.updated_at
        ))
    
    return response