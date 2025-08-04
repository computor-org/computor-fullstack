from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.interface.deployments import GitLabConfig, GitLabConfigGet
from ctutor_backend.interface.organizations import OrganizationGet
from ctutor_backend.model.course import CourseFamily
from ..types import Ltree

class CourseFamilyProperties(BaseModel):
    gitlab: Optional[GitLabConfig] = None
    
    model_config = ConfigDict(
        extra='allow',
    )

class CourseFamilyPropertiesGet(BaseModel):
    gitlab: Optional[GitLabConfigGet] = None
    
    model_config = ConfigDict(
        extra='allow',
    )

class CourseFamilyCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    organization_id: str
    properties: Optional[CourseFamilyProperties] = None

class CourseFamilyGet(BaseEntityGet):
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    organization_id: str
    properties: Optional[CourseFamilyPropertiesGet] = None

    organization: Optional[OrganizationGet] = None

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)
    
    model_config = ConfigDict(from_attributes=True)

class CourseFamilyList(BaseModel):
    id: str
    title: Optional[str] = None
    organization_id: str
    path: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)
    
class CourseFamilyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    organization_id: Optional[str] = None
    properties: Optional[CourseFamilyProperties] = None


class CourseFamilyQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    organization_id: Optional[str] = None
    properties: Optional[str] = None
    
def course_family_search(db: Session, query, params: Optional[CourseFamilyQuery]):
    if params.id != None:
        query = query.filter(CourseFamily.id == params.id)
    if params.title != None:
        query = query.filter(CourseFamily.title == params.title)
    if params.description != None:
        query = query.filter(CourseFamily.description == params.description)
    if params.path != None:
        query = query.filter(CourseFamily.path == Ltree(params.path))
    if params.organization_id != None:
        query = query.filter(CourseFamily.organization_id == params.organization_id)
    # if params.properties != None:
    #     properties_dict = json.loads(params.properties)
    #     query = query.filter(CourseFamily.properties == properties_dict)
    return query

class CourseFamilyInterface(EntityInterface):
    create = CourseFamilyCreate
    get = CourseFamilyGet
    list = CourseFamilyList
    update = CourseFamilyUpdate
    query = CourseFamilyQuery
    search = course_family_search
    endpoint = "course-families"
    model = CourseFamily
    cache_ttl=60