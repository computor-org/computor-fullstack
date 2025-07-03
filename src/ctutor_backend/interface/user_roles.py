from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.users import UserInterface
from ctutor_backend.model.models import UserRole
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery

class UserRoleCreate(BaseModel):
    user_id: str
    role_id: str

class UserRoleGet(BaseEntityGet):
    user_id: str
    role_id: str
    
class UserRoleList(BaseModel):
    user_id: str
    role_id: str
    
class UserRoleUpdate(BaseModel):
    role_id: str

class UserRoleQuery(ListQuery):
    user_id: Optional[str] = None
    role_id: Optional[str] = None

def user_role_search(db: Session, query, params: Optional[UserRoleQuery]):
    if params.user_id != None:
        query = query.filter(UserRole.user_id == params.user_id)
    if params.role_id != None:
        query = query.filter(UserRole.role_id == params.role_id)
    return query

class UserRoleInterface(EntityInterface):
    create = UserRoleCreate
    get = UserRoleGet
    list = UserRoleList
    update = UserRoleUpdate
    query = UserRoleQuery
    search = user_role_search
    endpoint = "user-roles"
    model = UserRole