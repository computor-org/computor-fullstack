from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.deployments import GitLabConfig
from ctutor_backend.interface.base import EntityInterface, ListQuery, BaseEntityGet
from ctutor_backend.model.course import CourseSubmissionGroup

class SubmissionGroupProperties(BaseModel):
    gitlab: Optional[GitLabConfig] = None
    
    model_config = ConfigDict(
        extra='allow',
    )
    
class SubmissionGroupCreate(BaseModel):
    properties: Optional[SubmissionGroupProperties] = None
    max_group_size: int = 1
    max_submissions: Optional[int] = None
    course_content_id: str
    status: Optional[str] = None

class SubmissionGroupGet(BaseEntityGet, SubmissionGroupCreate):
    id: str
    course_id: str
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
class SubmissionGroupList(BaseModel):
    id: str
    properties: Optional[SubmissionGroupProperties] = None
    max_group_size: int
    max_submissions: Optional[int] = None
    course_id: str
    course_content_id: str
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
    
class SubmissionGroupUpdate(BaseModel):
    properties: Optional[SubmissionGroupProperties] = None
    max_group_size: Optional[int] = None
    max_submissions: Optional[int] = None
    status: Optional[str] = None

class SubmissionGroupQuery(ListQuery):
    id: Optional[str] = None
    max_group_size: Optional[int] = None
    max_submissions: Optional[int] = None
    course_id: Optional[str] = None
    course_content_id: Optional[str] = None
    properties: Optional[SubmissionGroupProperties] = None
    status: Optional[str] = None

def submission_group_search(db: Session, query, params: Optional[SubmissionGroupQuery]):
    if params.id != None:
        query = query.filter(CourseSubmissionGroup.id == params.id)
    if params.max_group_size != None:
        query = query.filter(CourseSubmissionGroup.max_group_size == params.max_group_size)
    if params.max_submissions != None:
        query = query.filter(CourseSubmissionGroup.max_submissions == params.max_submissions)
    if params.course_id != None:
        query = query.filter(CourseSubmissionGroup.course_id == params.course_id)
    if params.course_content_id != None:
        query = query.filter(CourseSubmissionGroup.course_content_id == params.course_content_id)
    if params.status != None:
        query = query.filter(CourseSubmissionGroup.status == params.status)
        
    return query

class SubmissionGroupInterface(EntityInterface):
    create = SubmissionGroupCreate
    get = SubmissionGroupGet
    list = SubmissionGroupList
    update = SubmissionGroupUpdate
    query = SubmissionGroupQuery
    search = submission_group_search
    endpoint = "submission-groups"
    model = CourseSubmissionGroup
    cache_ttl = 120  # 2 minutes - submission groups change moderately frequently