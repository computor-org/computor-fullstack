import json
from uuid import UUID
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy import case
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from aiocache import SimpleMemoryCache
from ctutor_backend.api.messages import get_submission_mergerequest
from ctutor_backend.api.students import CourseContentMessage
from ctutor_backend.database import get_db
from ctutor_backend.interface.auth import GLPAuthConfig
from ctutor_backend.interface.course_content_types import CourseContentTypeList
from ctutor_backend.interface.course_member_comments import CourseMemberCommentList
from ctutor_backend.interface.course_members import CourseMemberGet, CourseMemberInterface, CourseMemberProperties, CourseMemberQuery
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.api.auth import HeaderAuthCredentials, get_auth_credentials, get_current_permissions
from ctutor_backend.api.permissions import allowed_course_role_ids, check_course_permissions
from ctutor_backend.api.exceptions import BadRequestException, ForbiddenException, InternalServerException, NotFoundException
from ctutor_backend.api.mappers import course_member_course_content_result_mapper
from ctutor_backend.interface.student_courses import CourseStudentInterface, CourseStudentQuery
from ctutor_backend.interface.tutor_course_members import TutorCourseMemberCourseContent, TutorCourseMemberGet, TutorCourseMemberList
from ctutor_backend.interface.tutor_courses import CourseTutorGet, CourseTutorList, CourseTutorRepository
from ctutor_backend.model.sqlalchemy_models.course import CourseContent, CourseContentKind, CourseMember, CourseMemberComment, CourseSubmissionGroup, CourseSubmissionGroupMember, Result, User
from ctutor_backend.api.queries import course_course_member_list_query, course_member_course_content_list_query, course_member_course_content_query, latest_result_subquery, results_count_subquery
from ctutor_backend.interface.student_course_contents import CourseContentStudentInterface, CourseContentStudentList, CourseContentStudentQuery, CourseContentStudentUpdate, ResultStudentList, SubmissionGroupStudentList
from ctutor_backend.redis import get_redis_client
from aiocache import BaseCache

_tutor_cache = SimpleMemoryCache()

_expiry_time_tutors = 3600 # in seconds

async def get_cached_data(course_id: str):
    # cached = await RedisCache.getInstance().get(f"{course_id}")
    cached = await _tutor_cache.get(f"{course_id}")

    if cached != None:
        return cached
    return None

async def set_cached_data(course_id: str, data: dict):
    # await RedisCache.getInstance().add(f"{course_id}", data, _expiry_time_students)
    await _tutor_cache.set(f"{course_id}", data, _expiry_time_tutors)

tutor_router = APIRouter()

@tutor_router.get("/course-members/{course_member_id}/course-contents/{course_content_id}", response_model=CourseContentStudentList)
def tutor_get_course_contents(course_content_id: UUID | str, course_member_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):
    
    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise ForbiddenException()

    course_contents_result = course_member_course_content_query(course_member_id,course_content_id,db)

    return course_member_course_content_result_mapper(course_contents_result)

@tutor_router.get("/course-members/{course_member_id}/course-contents", response_model=list[CourseContentStudentList])
def tutor_list_course_contents(course_member_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], params: CourseContentStudentQuery = Depends(), db: Session = Depends(get_db)):

    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise ForbiddenException()

    query = course_member_course_content_list_query(course_member_id,db)

    course_contents_results = CourseContentStudentInterface.search(db,query,params).all()
 
    response_list: list[CourseContentStudentList] = []

    for course_contents_result in course_contents_results:
        response_list.append(course_member_course_content_result_mapper(course_contents_result))

    return response_list

@tutor_router.patch("/course-members/{course_member_id}/course-contents/{course_content_id}", response_model=CourseContentStudentList)
def tutor_update_course_contents(course_content_id: UUID | str, course_member_id: UUID | str, course_member_update: CourseContentStudentUpdate, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):
    
    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise ForbiddenException()

    latest_result_sub = latest_result_subquery(None,course_member_id,course_content_id,db)
    results_count_sub = results_count_subquery(None,course_member_id,course_content_id,db)

    query = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count
        ) \
        .select_from(CourseContent) \
        .filter(CourseContent.id == course_content_id) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .join(CourseMember, CourseMember.id == course_member_id) \
        .join(Course,(Course.id == CourseContent.course_id) & (Course.id == CourseMember.course_id)) \
        .outerjoin(CourseSubmissionGroupMember,
              (CourseSubmissionGroupMember.course_member_id == CourseMember.id) &
              (CourseSubmissionGroupMember.course_content_id == CourseContent.id)) \
        .outerjoin(CourseSubmissionGroup, CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .outerjoin(
            latest_result_sub,
            CourseSubmissionGroupMember.course_content_id == latest_result_sub.c.course_content_id
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            (CourseSubmissionGroupMember.course_content_id == results_count_sub.c.course_content_id)
        ).first()

    course_content, result_count, result, course_submission_group, submitted_count = query

    entity = course_member_update.model_dump(exclude_unset=True)
    
    for key in entity.keys():
        attr = entity.get(key)
        setattr(course_submission_group, key, attr)

    db.commit()
    db.refresh(course_submission_group)
    
    return CourseContentStudentList(
            id=course_content.id,
            title=course_content.title,
            path=course_content.path,
            course_id=course_content.course_id,
            course_content_type_id=course_content.course_content_type_id,
            course_content_kind_id=course_content.course_content_kind_id,
            course_content_type=CourseContentTypeList.model_validate(course_content.course_content_type),
            version_identifier=course_content.version_identifier,
            position=course_content.position,
            max_group_size=course_content.max_group_size,
            directory=course_content.properties["gitlab"]["directory"],
            color=course_content.course_content_type.color,
            #submitted=True if submitted_count != None and submitted_count > 0 else False,
            result_count=result_count if result_count != None else 0,
            max_test_runs=course_content.max_test_runs,
            result=ResultStudentList(
                execution_backend_id=result.execution_backend_id,
                test_system_id=result.test_system_id,
                version_identifier=result.version_identifier,
                status=result.status,
                result=result.result,
                submit=result.submit
            ) if result != None and result.test_system_id != None else None,
            submission=SubmissionGroupStudentList(
                id=course_submission_group.id,
                status=course_submission_group.status,
                grading=course_submission_group.grading,
                count=submitted_count if submitted_count != None else 0,
                max_submissions=course_submission_group.max_submissions
            )
        )

@tutor_router.get("/courses/{course_id}", response_model=CourseTutorGet)
async def tutor_get_courses(course_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    course = check_course_permissions(permissions,Course,"_study_assistant",db).filter(Course.id == course_id).first()

    if course == None:
        raise NotFoundException()

    return CourseTutorGet(
                id=course.id,
                title=course.title,
                course_family_id=course.course_family_id,
                organization_id=course.organization_id,
                version_identifier=course.version_identifier,
                path=course.path,
                repository=CourseTutorRepository(
                    provider_url=course.properties["gitlab"]["url"],
                    full_path_reference=f'{course.properties["gitlab"]["full_path"]}/reference'
                )
            )

@tutor_router.get("/courses", response_model=list[CourseTutorList])
def tutor_list_courses(permissions: Annotated[Principal, Depends(get_current_permissions)], params: CourseStudentQuery = Depends(), db: Session = Depends(get_db)):

    query = check_course_permissions(permissions,Course,"_study_assistant",db)

    courses = CourseStudentInterface.search(db,query,params).all()

    response_list: list[CourseTutorList] = []

    for course in courses:
        response_list.append(CourseTutorList(
            id=course.id,
            title=course.title,
            course_family_id=course.course_family_id,
            organization_id=course.organization_id,
            version_identifier=course.version_identifier,
            path=course.path,
            repository=CourseTutorRepository(
                provider_url=course.properties["gitlab"]["url"],
                full_path_reference=f'{course.properties["gitlab"]["full_path"]}/reference'
            )
        ))

    return response_list

@tutor_router.get("/courses/{course_id}/current", response_model=CourseMemberGet)
async def tutor_get_courses(course_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    course_member = check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(Course.id == course_id, CourseMember.user_id == permissions.get_user_id_or_throw()).first()

    if course_member == None:
        raise NotFoundException()

    return CourseMemberGet(**course_member.__dict__)

@tutor_router.get("/course-members/{course_member_id}", response_model=TutorCourseMemberGet)
def tutor_get_course_members(course_member_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    course_member = check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first()

    course_contents_results = course_member_course_content_list_query(course_member_id,db).all()

    response_list: list[TutorCourseMemberCourseContent] = []

    for course_contents_result in course_contents_results:
        query = course_contents_result
        course_content = query[0]

        result = query[2]

        if result != None:
            submit = result.submit
            status = result.status

            todo = True if submit == True and status == None else False
            if todo == True:
                response_list.append(TutorCourseMemberCourseContent(id=course_content.id,path=str(course_content.path)))

    tutor_course_member = TutorCourseMemberGet.model_validate(course_member,from_attributes=True)
    tutor_course_member.unreviewed_course_contents = response_list

    return tutor_course_member

@tutor_router.get("/course-members", response_model=list[TutorCourseMemberList])
def tutor_list_course_members(permissions: Annotated[Principal, Depends(get_current_permissions)], params: CourseMemberQuery = Depends(), db: Session = Depends(get_db)):

    subquery = db.query(Course.id).select_from(User).filter(User.id == permissions.get_user_id_or_throw()) \
        .join(CourseMember, CourseMember.user_id == User.id) \
            .join(Course, Course.id == CourseMember.course_id) \
                .filter(CourseMember.course_role_id.in_((allowed_course_role_ids("_study_assistant")))).all()

    query = course_course_member_list_query(db)

    query = CourseMemberInterface.search(db,query,params)

    if permissions.is_admin != True:
        query = query.join(Course,Course.id == CourseMember.course_id).filter(Course.id.in_([r.id for r in subquery])).join(User,User.id == CourseMember.user_id).order_by(User.family_name).all()

    response_list: list[TutorCourseMemberList] = []

    for course_member, latest_result_date in query:
        tutor_course_member = TutorCourseMemberList.model_validate(course_member,from_attributes=True)
        tutor_course_member.unreviewed = True if latest_result_date != None else False
        response_list.append(tutor_course_member)

    return response_list


async def tutor_course_content_messages_cached(course_content_id: str, course_member_id: str, cache: BaseCache, db: Session) -> tuple[CourseMemberProperties,str,str]:

    cache_key = f"course-members:{course_member_id}:course-contents:{course_content_id}"

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
                    .filter(
                        CourseContent.id == course_content_id,
                        CourseMember.id == course_member_id
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

@tutor_router.get("/course-members/{course_member_id}/course-contents/{course_content_id}/messages", response_model=list[dict])
async def tutor_list_course_content_messages(
    course_member_id: UUID | str, 
    course_content_id: UUID | str, 
    permissions: Annotated[Principal, Depends(get_current_permissions)], 
    auth_headers: Annotated[HeaderAuthCredentials,Depends(get_auth_credentials)],
    cache: Annotated[BaseCache, Depends(get_redis_client)], 
    db: Session = Depends(get_db)
):

    if auth_headers.type != GLPAuthConfig:
        raise BadRequestException(details="GitLab messages are restricted to GLPAT authenticated users")

    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise NotFoundException()

    course_member_properties, course_content_id, course_content_path = await tutor_course_content_messages_cached(course_content_id,course_member_id,cache,db)

    user_id = db.query(User.id).join(CourseMember,CourseMember.user_id == User.id).filter(CourseMember.id == course_member_id).scalar()

    merge_request = await get_submission_mergerequest(auth_headers.credentials,user_id,course_member_properties.gitlab.full_path_submission,course_content_id,course_content_path)

    if merge_request == None:
        raise NotFoundException()

    notes = merge_request.notes.list()

    note_response = []
    for note in notes:
        note_response.append(note.asdict())

    return note_response

@tutor_router.post("/course-members/{course_member_id}/course-contents/{course_content_id}/messages", response_model=list[dict])
async def tutor_post_course_content_messages(
    course_member_id: UUID | str,
    course_content_id: UUID | str, 
    message: CourseContentMessage, 
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    auth_headers: Annotated[HeaderAuthCredentials,Depends(get_auth_credentials)],
    cache: Annotated[BaseCache, Depends(get_redis_client)],
    db: Session = Depends(get_db)):

    if auth_headers.type != GLPAuthConfig:
        raise BadRequestException(details="GitLab messages are restricted to GLPAT authenticated users")

    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise NotFoundException()

    user_id = db.query(User.id).join(CourseMember,CourseMember.user_id == User.id).filter(CourseMember.id == course_member_id).scalar()

    course_member_properties, course_content_id, course_content_path = await tutor_course_content_messages_cached(course_content_id,course_member_id,cache,db)

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

def is_owner_expression(transmitter_id):
    return case(
        (CourseMemberComment.transmitter_id == transmitter_id, True),
        else_=False
    ).label("owner")

class CourseMemberCommentTutorList(CourseMemberCommentList):
    owner: bool

class CourseMemberCommentTutorCreate(BaseModel):
    message: str

class CourseMemberCommentTutorUpdate(BaseModel):
    message: str

@tutor_router.get("/course-members/{course_member_id}/comments", response_model=list[CourseMemberCommentTutorList])
async def tutor_list_course_member_comments(course_member_id: UUID | str,  permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    if permissions.is_admin == True:
        comments = db.query(CourseMemberComment) \
        .filter(CourseMemberComment.course_member_id == course_member_id).all()

        return [
            CourseMemberCommentTutorList(
                id=c.id,
                message=c.message,
                transmitter_id=c.transmitter_id,
                transmitter=c.transmitter,
                course_member_id=c.course_member_id,
                created_at=c.created_at,
                updated_at=c.updated_at,
                owner=False
            )
            for c in comments
        ]

    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise NotFoundException()
    
    transmitter_id = db.query(CourseMember.id).select_from(CourseMember) \
        .join(Course,Course.id == CourseMember.course_id) \
            .filter(CourseMember.user_id == permissions.user_id).first()[0]

    comments = db.query(CourseMemberComment,is_owner_expression(transmitter_id)) \
        .filter(CourseMemberComment.course_member_id == course_member_id).all()

    return [
        CourseMemberCommentTutorList(
            id=c.id,
            message=c.message,
            transmitter_id=c.transmitter_id,
            transmitter=c.transmitter,
            course_member_id=c.course_member_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            owner=owner
        )
        for c, owner in comments
    ]

@tutor_router.post("/course-members/{course_member_id}/comments", response_model=list[CourseMemberCommentList])
async def tutor_post_course_member_comments(
    course_member_id: UUID | str,
    comment: CourseMemberCommentTutorCreate,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)):

    if permissions.is_admin == True:
        # TODO: change transmitter_id to nullable, null is admin
        raise BadRequestException(detail="[admin] is not permitted.")

    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise NotFoundException()

    transmitter_id = db.query(CourseMember.id).select_from(CourseMember) \
            .join(Course,Course.id == CourseMember.course_id) \
                .filter(CourseMember.user_id == permissions.user_id).first()[0]

    if len(comment.message) == 0:
        raise BadRequestException(detail="The comment is empty.")

    db_item = CourseMemberComment(
        message=comment.message,
        transmitter_id=transmitter_id,
        course_member_id=course_member_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    comments = db.query(CourseMemberComment,is_owner_expression(transmitter_id)) \
        .filter(CourseMemberComment.course_member_id == course_member_id).all()

    return [
        CourseMemberCommentTutorList(
            id=c.id,
            message=c.message,
            transmitter_id=c.transmitter_id,
            transmitter=c.transmitter,
            course_member_id=c.course_member_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            owner=owner
        )
        for c, owner in comments
    ]

@tutor_router.patch("/course-members/{course_member_id}/comments/{course_member_comment_id}", response_model=list[CourseMemberCommentList])
async def tutor_update_course_member_comment(
    course_member_id: UUID | str,
    course_member_comment_id: UUID | str,
    comment: CourseMemberCommentTutorUpdate,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)):

    if permissions.is_admin == True:
        # TODO: change transmitter_id to nullable, null is admin
        raise BadRequestException(detail="[admin] is not permitted.")

    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise NotFoundException()

    transmitter = db.query(CourseMember).select_from(CourseMember) \
            .join(Course,Course.id == CourseMember.course_id) \
                .filter(CourseMember.user_id == permissions.user_id).first()
                
    db_item = db.query(CourseMemberComment).filter(CourseMemberComment.id == course_member_comment_id).first()
    
    if db_item.transmitter_id != transmitter.id:
        raise ForbiddenException()

    if len(comment.message) == 0:
        raise BadRequestException(detail="The comment is empty.")

    entity = comment.model_dump(exclude_unset=True)

    for key in entity.keys():
        attr = entity.get(key)
        setattr(db_item, key, attr)

    db.commit()
    db.refresh(db_item)
    
    comments = db.query(CourseMemberComment,is_owner_expression(transmitter.id)) \
        .filter(CourseMemberComment.course_member_id == course_member_id).all()

    return [
        CourseMemberCommentTutorList(
            id=c.id,
            message=c.message,
            transmitter_id=c.transmitter_id,
            transmitter=c.transmitter,
            course_member_id=c.course_member_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            owner=owner
        )
        for c, owner in comments
    ]

@tutor_router.delete("/course-members/{course_member_id}/comments/{course_member_comment_id}", response_model=list[CourseMemberCommentList])
async def tutor_delete_course_member_comment(
    course_member_id: UUID | str,
    course_member_comment_id: UUID | str,
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)):

    if permissions.is_admin == True:
        # TODO: change transmitter_id to nullable, null is admin
        raise BadRequestException(detail="[admin] is not permitted.")

    if check_course_permissions(permissions,CourseMember,"_study_assistant",db).filter(CourseMember.id == course_member_id).first() == None:
        raise NotFoundException()

    transmitter = db.query(CourseMember).select_from(CourseMember) \
            .join(Course,Course.id == CourseMember.course_id) \
                .filter(CourseMember.user_id == permissions.user_id).first()
                
    comment = db.query(CourseMemberComment).filter(CourseMemberComment.id == course_member_comment_id).first()
    
    if comment.transmitter_id != transmitter.id and transmitter.course_role_id not in ["_maintainer","_owner"]:
        raise ForbiddenException()

    db.delete(comment)
    db.commit()
    
    comments = db.query(CourseMemberComment,is_owner_expression(transmitter.id)) \
        .filter(CourseMemberComment.course_member_id == course_member_id).all()

    return [
        CourseMemberCommentTutorList(
            id=c.id,
            message=c.message,
            transmitter_id=c.transmitter_id,
            transmitter=c.transmitter,
            course_member_id=c.course_member_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            owner=owner
        )
        for c, owner in comments
    ]