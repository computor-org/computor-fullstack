from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import EntityInterface, ListQuery
from ctutor_backend.interface.course_content_types import CourseContentTypeGet, CourseContentTypeList
from ctutor_backend.model.course import Course, CourseMember
from ..types import Ltree

class CourseStudentRepository(BaseModel):
    provider_url: Optional[str] = None
    full_path: Optional[str] = None

class CourseStudentGet(BaseModel):
    id: str
    title: Optional[str] = None
    course_family_id: Optional[str] = None
    organization_id: Optional[str] = None
    version_identifier: Optional[str] = None
    course_content_types: list[CourseContentTypeGet]
    path: str

    repository: CourseStudentRepository

    model_config = ConfigDict(from_attributes=True)

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

class CourseStudentList(BaseModel):
    id: str
    title: Optional[str] = None
    course_family_id: Optional[str] = None
    organization_id: Optional[str] = None
    version_identifier: Optional[str] = None
    path: str
    course_content_types: list[CourseContentTypeList]

    repository: CourseStudentRepository

    model_config = ConfigDict(from_attributes=True)

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

class CourseStudentQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    course_family_id: Optional[str] = None
    organization_id: Optional[str] = None
    version_identifier: Optional[str] = None
    provider_url: Optional[str] = None
    full_path: Optional[str] = None
    full_path_student: Optional[str] = None

def course_student_search(db: Session, query, params: Optional[CourseStudentQuery]):
    if params.id != None:
        query = query.filter(Course.id == params.id)
    if params.title != None:
        query = query.filter(Course.title == params.title)
    if params.description != None:
        query = query.filter(Course.description == params.description)
    if params.path != None:
        query = query.filter(Course.path == Ltree(params.path))
    if params.course_family_id != None:
        query = query.filter(Course.course_family_id == params.course_family_id)
    if params.organization_id != None:
        query = query.filter(Course.organization_id == params.organization_id)
    if params.version_identifier != None:
        query = query.filter(Course.version_identifier == params.version_identifier)

    if params.provider_url != None:
        query = query.filter(Course.properties["gitlab"].op("->>")("url") == params.provider_url)
    if params.full_path != None:
        query = query.filter(Course.properties["gitlab"].op("->>")("full_path") == params.full_path)
    if params.full_path_student != None:
        query = query.join(CourseMember,CourseMember.course_id == Course.id).filter(CourseMember.properties["gitlab"].op("->>")("full_path") == params.full_path_student)

    return query

class CourseStudentInterface(EntityInterface):
    list = CourseStudentList
    query = CourseStudentQuery
    search = course_student_search
    endpoint = "student-courses"
    cache_ttl = 300  # 5 minutes - student course data changes moderately