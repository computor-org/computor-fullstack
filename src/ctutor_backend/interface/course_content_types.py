import json
from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.interface.course_content_kind import CourseContentKindGet
from ctutor_backend.interface.courses import CourseInterface
from ctutor_backend.model import CourseContentType
from ctutor_backend.model.models import Course

class CTutorUIColor(str, Enum):
    RED = 'red'
    ORANGE = 'orange'
    AMBER = 'amber'
    YELLOW = 'yellow'
    LIME = 'lime'
    GREEN = 'green'
    EMERALD = 'emerald'
    TEAL = 'teal'
    CYAN = 'cyan'
    SKY = 'sky'
    BLUE = 'blue'
    INDIGO = 'indigo'
    VIOLET = 'violet'
    PURPLE = 'purple'
    FUCHSIA = 'fuchsia'
    PINK = 'pink'
    ROSE = 'rose'

class CourseContentTypeCreate(BaseModel):
    slug: str
    title: Optional[str | None] = None
    description: Optional[str | None] = None
    color: Optional[CTutorUIColor] = CTutorUIColor.GREEN
    properties: Optional[dict] = None
    course_id: str
    course_content_kind_id: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class CourseContentTypeGet(BaseEntityGet):
    id: str 
    slug: str
    title: Optional[str | None] = None
    description: Optional[str | None] = None
    color: str
    properties: Optional[dict] = None
    course_id: str
    course_content_kind_id: str

    course_content_kind: Optional[CourseContentKindGet] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class CourseContentTypeList(BaseModel):
    id: str
    slug: str
    title: Optional[str | None] = None
    color: str
    course_id: str
    course_content_kind_id: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class CourseContentTypeUpdate(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[dict] = None

    model_config = ConfigDict(use_enum_values=True)

class CourseContentTypeQuery(ListQuery):
    id: Optional[str] = None
    slug: Optional[str] = None
    title: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    course_id: Optional[str] = None
    properties: Optional[str] = None
    course_content_kind_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

def course_content_type_search(db: Session, query, params: Optional[CourseContentTypeQuery]):
    if params.id != None:
        query = query.filter(CourseContentType.id == params.id)
    if params.slug != None:
        query = query.filter(CourseContentType.slug == params.slug)
    if params.title != None:
        query = query.filter(CourseContentType.title == params.title)
    if params.color != None:
        query = query.filter(CourseContentType.color == params.color)
    if params.course_id != None:
        query = query.filter(CourseContentType.course_id == params.course_id)
    if params.course_content_kind_id != None:
        query = query.filter(CourseContentType.course_content_kind_id == params.course_content_kind_id)
    # if params.properties != None:
    #     properties_dict = json.loads(params.properties)
    #     query = query.filter(CourseContentType.properties == properties_dict)
    return query

class CourseContentTypeInterface(EntityInterface):
    create = CourseContentTypeCreate
    get = CourseContentTypeGet
    list = CourseContentTypeList
    update = CourseContentTypeUpdate
    query = CourseContentTypeQuery
    search = course_content_type_search
    endpoint = "course-content-types"
    model = CourseContentType
    cache_ttl=60