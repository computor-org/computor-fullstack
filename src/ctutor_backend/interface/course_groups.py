from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model.sqlalchemy_models.course import CourseGroup

class CourseGroupCreate(BaseModel):
    title: Optional[str | None] = None
    description: Optional[str | None] = None
    course_id: str
    properties: Optional[dict] = None

class CourseGroupGet(BaseEntityGet,CourseGroupCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)
class CourseGroupList(BaseModel):
    id: str
    title: Optional[str | None] = None
    course_id: str

    model_config = ConfigDict(from_attributes=True)
    
class CourseGroupUpdate(BaseModel):
    title: Optional[str | None] = None
    description: Optional[str | None] = None
    course_id: Optional[str | None] = None
    properties: Optional[dict] = None

class CourseGroupQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str | None] = None
    course_id: Optional[str] = None
    properties: Optional[str] = None
    
def course_group_search(db: Session, query, params: Optional[CourseGroupQuery]):
    if params.id != None:
        query = query.filter(CourseGroup.id == params.id)
    if params.title != None:
        query = query.filter(CourseGroup.title == params.title)
    if params.course_id != None:
        query = query.filter(CourseGroup.course_id == params.course_id)

    return query.order_by(CourseGroup.title)

class CourseGroupInterface(EntityInterface):
    create = CourseGroupCreate
    get = CourseGroupGet
    list = CourseGroupList
    update = CourseGroupUpdate
    query = CourseGroupQuery
    search = course_group_search
    endpoint = "course-groups"
    model = CourseGroup
    cache_ttl=60