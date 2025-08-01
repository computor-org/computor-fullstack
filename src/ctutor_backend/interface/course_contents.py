from datetime import datetime
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.course_content_types import CourseContentTypeGet
from ctutor_backend.interface.deployments import GitLabConfig, GitLabConfigGet
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model.course import CourseContent
from ctutor_backend.model.course import CourseContentKind, CourseContentType, CourseMember, CourseSubmissionGroup, CourseSubmissionGroupMember
from ctutor_backend.model.auth import User
from sqlalchemy_utils import Ltree


class CourseContentProperties(BaseModel):
    gitlab: Optional[GitLabConfig] = None
    
    model_config = ConfigDict(
        extra='allow',
    )

class CourseContentPropertiesGet(BaseModel):
    gitlab: Optional[GitLabConfigGet] = None

    model_config = ConfigDict(
        extra='allow',
    )
    
class CourseContentCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    course_id: str
    course_content_type_id: str
    properties: Optional[CourseContentProperties] = None
    version_identifier: str
    position: float = 0
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class CourseContentGet(BaseEntityGet):
    id: str
    archived_at: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    course_id: str
    course_content_type_id: str
    course_content_kind_id: str
    properties: Optional[CourseContentPropertiesGet] = None
    version_identifier: str
    position: float
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None

    course_content_type: Optional[CourseContentTypeGet] = None

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
class CourseContentList(BaseModel):
    id: str
    title: Optional[str] = None
    path: str
    course_id: str
    course_content_type_id: str
    course_content_kind_id: str
    version_identifier: str
    position: float
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None
    
    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
class CourseContentUpdate(BaseModel):
    path: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[CourseContentProperties] = None
    version_identifier: Optional[str] = None
    position: Optional[float] = None
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None

class CourseContentQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    path: Optional[str] = None
    course_id: Optional[str] = None
    course_content_type_id: Optional[str] = None
    version_identifier: Optional[str] = None
    properties: Optional[CourseContentProperties] = None
    archived: Optional[bool] = None
    position: Optional[float] = None
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None

def course_content_search(db: Session, query, params: Optional[CourseContentQuery]):
    if params.id != None:
        query = query.filter(CourseContent.id == params.id)
    if params.title != None:
        query = query.filter(CourseContent.title == params.title)
    if params.path != None:

        if params.path.endswith(".") or params.path.startswith("."):
            params.path = params.path.strip(".")

        query = query.filter(CourseContent.path == Ltree(params.path))

    if params.course_id != None:
        query = query.filter(CourseContent.course_id == params.course_id)
    if params.course_content_type_id != None:
        query = query.filter(CourseContent.course_content_type_id == params.course_content_type_id)
    if params.version_identifier != None:
        query = query.filter(CourseContent.version_identifier == params.version_identifier)
    if params.position != None:
        query = query.filter(CourseContent.position == params.position)
    if params.max_group_size != None:
        query = query.filter(CourseContent.max_group_size == params.max_group_size)
    if params.max_test_runs != None:
        query = query.filter(CourseContent.max_test_runs == params.max_test_runs)
    if params.max_submissions != None:
        query = query.filter(CourseContent.max_submissions == params.max_submissions)
    if params.execution_backend_id != None:
        query = query.filter(CourseContent.execution_backend_id == params.execution_backend_id)

    if params.archived != None and params.archived != False:
        query = query.filter(CourseContent.archived_at != None)
    else:
        query = query.filter(CourseContent.archived_at == None)
        
    return query

def post_create(course_content: CourseContent, db: Session):
    
    course_members = (
        db.scalars(db.query(CourseMember.id)
        .join(User, User.id == CourseMember.user_id)
        .join(CourseContentType, CourseContentType.id == course_content.course_content_type_id)
        .join(CourseContentKind, CourseContentKind.id == CourseContentType.course_content_kind_id)
        .filter(
            CourseMember.course_id == course_content.course_id,
            CourseContentKind.submittable == True,
            course_content.max_group_size == 1,
            User.user_type == "user"
        )).all()
    )

    for course_member in course_members:
        submission_group = CourseSubmissionGroup(
            course_id=course_content.course_id,
            course_content_id=course_content.id,
            max_group_size=course_content.max_group_size,
            max_test_runs=course_content.max_test_runs,
            max_submissions=course_content.max_submissions
        )
        
        db.add(submission_group)
        db.commit()
        db.refresh(submission_group)
        
        submission_group_member = CourseSubmissionGroupMember(
            course_submission_group_id = submission_group.id,
            course_member_id = course_member
        )

        db.add(submission_group_member)
        db.commit()
        db.refresh(submission_group_member)

class CourseContentInterface(EntityInterface):
    create = CourseContentCreate
    get = CourseContentGet
    list = CourseContentList
    update = CourseContentUpdate
    query = CourseContentQuery
    search = course_content_search
    endpoint = "course-contents"
    model = CourseContent
    cache_ttl = 300  # 5 minutes cache for course content data
    post_create = post_create