from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model.sqlalchemy_models.execution import ExecutionBackend

class ExecutionBackendCreate(BaseModel):
    type: str
    slug: str
    properties: Optional[dict] = None

class ExecutionBackendGet(BaseEntityGet,ExecutionBackendCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)

class ExecutionBackendList(BaseModel):
    id: str
    type: str
    slug: str

    model_config = ConfigDict(from_attributes=True)

class ExecutionBackendUpdate(BaseModel):
    type: Optional[str] = None
    slug: Optional[str] = None
    properties: Optional[dict] = None

class ExecutionBackendQuery(ListQuery):
    id: Optional[str] = None
    type: Optional[str] = None
    slug: Optional[str] = None
    properties: Optional[str] = None

def execution_backend_search(db: Session, query, params: Optional[ExecutionBackendQuery]):
    if params.id != None:
        query = query.filter(ExecutionBackend.id == params.id)
    if params.type != None:
        query = query.filter(ExecutionBackend.type == params.type)
    if params.slug != None:
        query = query.filter(ExecutionBackend.slug == params.slug)

    return query

class ExecutionBackendInterface(EntityInterface):
    create = ExecutionBackendCreate
    get = ExecutionBackendGet
    list = ExecutionBackendList
    update = ExecutionBackendUpdate
    query = ExecutionBackendQuery
    search = execution_backend_search
    endpoint = "execution-backends"
    model = ExecutionBackend
    cache_ttl=60