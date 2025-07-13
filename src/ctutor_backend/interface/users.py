from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, validator, EmailStr
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
    id: Optional[str] = Field(None, description="User ID (UUID will be generated if not provided)")
    given_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's given name")
    family_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's family name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    number: Optional[str] = Field(None, min_length=1, max_length=255, description="User number/identifier")
    user_type: Optional[UserTypeEnum] = Field(UserTypeEnum.user, description="Type of user account")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    properties: Optional[dict] = Field(None, description="Additional user properties")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
                raise ValueError('Username can only contain alphanumeric characters, underscores, hyphens, and dots')
        return v
    
    @validator('given_name', 'family_name')
    def validate_names(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        return v.strip() if v else v
    
    model_config = ConfigDict(use_enum_values=True)

class UserGet(BaseEntityGet):
    id: str = Field(description="User unique identifier")
    given_name: Optional[str] = Field(None, description="User's given name")
    family_name: Optional[str] = Field(None, description="User's family name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    number: Optional[str] = Field(None, description="User number/identifier")
    user_type: Optional[UserTypeEnum] = Field(None, description="Type of user account")
    username: Optional[str] = Field(None, description="Unique username")
    properties: Optional[dict] = Field(None, description="Additional user properties")
    archived_at: Optional[datetime] = Field(None, description="Timestamp when user was archived")
    student_profiles: List[StudentProfileGet] = Field(default=[], description="Associated student profiles")
    
    @property
    def full_name(self) -> str:
        """Get the user's full name"""
        parts = []
        if self.given_name:
            parts.append(self.given_name)
        if self.family_name:
            parts.append(self.family_name)
        return ' '.join(parts) if parts else ''
    
    @property
    def display_name(self) -> str:
        """Get the user's display name (full name or username)"""
        full_name = self.full_name
        return full_name if full_name else (self.username or f"User {self.id[:8]}")
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class UserList(BaseModel):
    id: str = Field(description="User unique identifier")
    given_name: Optional[str] = Field(None, description="User's given name")
    family_name: Optional[str] = Field(None, description="User's family name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    user_type: Optional[UserTypeEnum] = Field(None, description="Type of user account")
    username: Optional[str] = Field(None, description="Unique username")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    
    @property
    def display_name(self) -> str:
        """Get the user's display name for lists"""
        if self.given_name and self.family_name:
            return f"{self.given_name} {self.family_name}"
        elif self.given_name:
            return self.given_name
        elif self.username:
            return self.username
        return f"User {self.id[:8]}"
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class UserUpdate(BaseModel):
    given_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's given name")
    family_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's family name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    number: Optional[str] = Field(None, min_length=1, max_length=255, description="User number/identifier")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    properties: Optional[dict] = Field(None, description="Additional user properties")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
                raise ValueError('Username can only contain alphanumeric characters, underscores, hyphens, and dots')
        return v
    
    @validator('given_name', 'family_name')
    def validate_names(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        return v.strip() if v else v

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
    cache_ttl = 300  # 5 minutes cache for user data


def replace_special_chars(name: str) -> str:
    return unidecode(name.lower().replace("ö","oe").replace("ä","ae").replace("ü","ue").encode().decode("utf8"))

def gitlab_project_path(user: UserGet | UserList):
    first_name = replace_special_chars(user.given_name).replace(" ", "_")
    family_name = replace_special_chars(user.family_name).replace(" ", "_")

    return f"{family_name}_{first_name}"