from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from sqlalchemy.orm import Session
from text_unidecode import unidecode
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.interface.student_profile import StudentProfileGet
from ctutor_backend.model.auth import User

class UserTypeEnum(str, Enum):
    user = "user"
    token = "token"

class UserCreate(BaseModel):
    id: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    number: Optional[str] = None
    user_type: Optional[UserTypeEnum] = None
    username: Optional[str] = None
    properties: Optional[dict] = None

class UserGet(BaseEntityGet):
    id: str = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    number: Optional[str] = None
    user_type: Optional[UserTypeEnum] = None
    username: Optional[str] = None
    properties: Optional[dict] = None

    archived_at: datetime | None = None

    student_profiles: List[StudentProfileGet] = []

    model_config = ConfigDict(from_attributes=True)

class UserList(BaseEntityGet):
    id: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    user_type: Optional[UserTypeEnum]
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    number: Optional[str] = None
    username: Optional[str] = None

class UserQuery(ListQuery):
    id: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    number: Optional[str] = None
    user_type: Optional[UserTypeEnum] = None
    properties: Optional[dict] = None
    archived: Optional[bool] = None
    username: Optional[str] = None

def user_search(db: Session, query, params: Optional[UserQuery]):

    if params.id != None:
        query = query.filter(User.id == params.id)
    if params.given_name != None:
        query = query.filter(User.given_name == params.given_name)
    if params.family_name != None:
        query = query.filter(User.family_name == params.family_name)
    if params.email != None:
        query = query.filter(User.email == params.email)
    if params.number != None:
        query = query.filter(User.number == params.number)
    if params.user_type != None:
        query = query.filter(User.user_type == params.user_type)
    if params.username != None:
        query = query.filter(User.username == params.username)
        
    if params.archived != None and params.archived != False:
        query = query.filter(User.archived_at != None)
    else:
        query = query.filter(User.archived_at == None)
    
    return query

class UserInterface(EntityInterface):
    create = UserCreate
    get = UserGet
    list = UserList
    update = UserUpdate
    query = UserQuery
    search = user_search
    endpoint = "users"
    model = User


def replace_special_chars(name: str) -> str:
    return unidecode(name.lower().replace("ö","oe").replace("ä","ae").replace("ü","ue").encode().decode("utf8"))

def gitlab_project_path(user: UserGet | UserList):
    first_name = replace_special_chars(user.given_name).replace(" ", "_")
    family_name = replace_special_chars(user.family_name).replace(" ", "_")

    return f"{family_name}_{first_name}"