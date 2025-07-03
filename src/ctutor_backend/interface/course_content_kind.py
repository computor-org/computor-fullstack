from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model import CourseContentKind
    
class CourseContentKindCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    has_ascendants: bool
    has_descendants: bool
    submittable: bool

class CourseContentKindGet(BaseEntityGet,CourseContentKindCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)

class CourseContentKindList(BaseModel):
    id: str
    title: Optional[str] = None
    has_ascendants: bool
    has_descendants: bool
    submittable: bool

    model_config = ConfigDict(from_attributes=True)

class CourseContentKindUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class CourseContentKindQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    has_ascendants: Optional[bool] = None
    has_descendants: Optional[bool] = None
    submittable: Optional[bool] = None

def course_content_kind_search(db: Session, query, params: Optional[CourseContentKindQuery]):
    if params.id != None:
        query = query.filter(CourseContentKind.id == params.id)
    if params.title != None:
        query = query.filter(CourseContentKind.title == params.title)
    if params.has_ascendants != None:
        query = query.filter(CourseContentKind.has_ascendants == params.has_ascendants)
    if params.has_descendants != None:
        query = query.filter(CourseContentKind.has_descendants == params.has_descendants)
    if params.submittable != None:
        query = query.filter(CourseContentKind.submittable == params.submittable)

    return query

class CourseContentKindInterface(EntityInterface):
    create = CourseContentKindCreate
    get = CourseContentKindGet
    list = CourseContentKindList
    update = CourseContentKindUpdate
    query = CourseContentKindQuery
    search = course_content_kind_search
    endpoint = "course-content-kinds"
    model = CourseContentKind
    cache_ttl=600