from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import EntityInterface, ListQuery
from sqlalchemy_utils import Ltree

from ctutor_backend.model.course import Course

class CourseTutorRepository(BaseModel):
    provider_url: Optional[str] = None
    full_path_reference: Optional[str] = None

class CourseTutorGet(BaseModel):
    id: str
    title: Optional[str] = None
    course_family_id: Optional[str] = None
    organization_id: Optional[str] = None
    version_identifier: Optional[str] = None
    path: str

    repository: CourseTutorRepository

    model_config = ConfigDict(from_attributes=True)

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

class CourseTutorList(BaseModel):
    id: str
    title: Optional[str] = None
    course_family_id: Optional[str] = None
    organization_id: Optional[str] = None
    version_identifier: Optional[str] = None
    path: str

    repository: CourseTutorRepository

    model_config = ConfigDict(from_attributes=True)

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

class CourseTutorQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    course_family_id: Optional[str] = None
    organization_id: Optional[str] = None
    version_identifier: Optional[str] = None

def course_tutor_search(db: Session, query, params: Optional[CourseTutorQuery]):
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

    return query

class CourseTutorInterface(EntityInterface):
    list = CourseTutorList
    query = CourseTutorQuery
    search = course_tutor_search
    endpoint = "tutor-courses"
    cache_ttl = 300  # 5 minutes - tutor course data changes moderately