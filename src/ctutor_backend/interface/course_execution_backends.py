from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.model.course import CourseExecutionBackend
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery

class CourseExecutionBackendCreate(BaseModel):
    execution_backend_id: str
    course_id: str
    properties: Optional[dict] = None

class CourseExecutionBackendGet(BaseEntityGet):
    execution_backend_id: str
    course_id: str
    properties: Optional[dict] = None
    
class CourseExecutionBackendList(BaseModel):
    execution_backend_id: str
    course_id: str
    
class CourseExecutionBackendUpdate(BaseModel):
    properties: Optional[dict] = None

class CourseExecutionBackendQuery(ListQuery):
    execution_backend_id: Optional[str] = None
    course_id: Optional[str] = None
    properties: Optional[str] = None

def course_execution_backend_search(db: Session, query, params: Optional[CourseExecutionBackendQuery]):
    if params.execution_backend_id != None:
        query = query.filter(CourseExecutionBackend.execution_backend_id == params.execution_backend_id)
    if params.course_id != None:
        query = query.filter(CourseExecutionBackend.course_id == params.course_id)

    return query

class CourseExecutionBackendInterface(EntityInterface):
    create = CourseExecutionBackendCreate
    get = CourseExecutionBackendGet
    list = CourseExecutionBackendList
    update = CourseExecutionBackendUpdate
    query = CourseExecutionBackendQuery
    search = course_execution_backend_search
    endpoint = "course-execution-backends"
    model = CourseExecutionBackend