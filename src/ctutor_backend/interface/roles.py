from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import EntityInterface, ListQuery
from ctutor_backend.model.models import Role

class RoleGet(BaseModel):
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    builtin: bool

    model_config = ConfigDict(from_attributes=True)

class RoleList(BaseModel):
    id: str
    title: Optional[str] = None
    builtin: bool

    model_config = ConfigDict(from_attributes=True)
    
class RoleQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    builtin: Optional[bool] = None

def role_search(db: Session, query, params: Optional[RoleQuery]):
    if params.id != None:
        query = query.filter(Role.id == params.id)
    if params.title != None:
        query = query.filter(Role.title == params.title)
    if params.description != None:
        query = query.filter(Role.description == params.description)
    return query

class RoleInterface(EntityInterface):
    create = None
    get = RoleGet
    list = RoleList
    update = None
    query = RoleQuery
    search = role_search
    endpoint = "roles"
    model = Role
    cache_ttl=600