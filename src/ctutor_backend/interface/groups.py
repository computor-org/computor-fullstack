from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model.group import Group

class GroupType(str, Enum):
    fixed = "fixed"
    dynamic = "dynamic"

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Group name")
    description: Optional[str] = Field(None, max_length=1024, description="Group description")
    group_type: GroupType = Field(description="Type of group (fixed or dynamic)")
    properties: Optional[dict] = Field(None, description="Additional group properties")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Group name cannot be empty or only whitespace')
        return v.strip()
    
    model_config = ConfigDict(use_enum_values=True)

class GroupGet(BaseEntityGet):
    id: str = Field(description="Group unique identifier")
    name: str = Field(description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    group_type: GroupType = Field(description="Type of group")
    properties: Optional[dict] = Field(None, description="Additional properties")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    
    @property
    def display_name(self) -> str:
        """Get display name for the group"""
        return self.name
    
    @property
    def is_archived(self) -> bool:
        """Check if the group is archived"""
        return self.archived_at is not None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class GroupList(BaseModel):
    id: str = Field(description="Group unique identifier")
    name: str = Field(description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    group_type: GroupType = Field(description="Type of group")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    
    @property
    def display_name(self) -> str:
        """Get display name for lists"""
        return self.name
    
    @property
    def is_archived(self) -> bool:
        """Check if the group is archived"""
        return self.archived_at is not None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Group name")
    description: Optional[str] = Field(None, max_length=1024, description="Group description")
    group_type: Optional[GroupType] = Field(None, description="Type of group")
    properties: Optional[dict] = Field(None, description="Additional properties")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Group name cannot be empty or only whitespace')
        return v.strip() if v else v
    
    model_config = ConfigDict(use_enum_values=True)

class GroupQuery(ListQuery):
    id: Optional[str] = Field(None, description="Filter by group ID")
    name: Optional[str] = Field(None, description="Filter by group name")
    group_type: Optional[GroupType] = Field(None, description="Filter by group type")
    archived: Optional[bool] = Field(None, description="Filter by archived status")
    
    model_config = ConfigDict(use_enum_values=True)

def group_search(db: Session, query, params: Optional[GroupQuery]):
    if params.id is not None:
        query = query.filter(Group.id == params.id)
    if params.name is not None:
        query = query.filter(Group.name.ilike(f"%{params.name}%"))
    if params.group_type is not None:
        query = query.filter(Group.group_type == params.group_type)
    
    if params.archived is not None and params.archived:
        query = query.filter(Group.archived_at.is_not(None))
    else:
        query = query.filter(Group.archived_at.is_(None))
    
    return query

class GroupInterface(EntityInterface):
    create = GroupCreate
    get = GroupGet
    list = GroupList
    update = GroupUpdate
    query = GroupQuery
    search = group_search
    endpoint = "groups"
    model = Group
    cache_ttl = 300  # 5 minutes cache for group data