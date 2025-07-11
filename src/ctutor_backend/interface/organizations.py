from enum import Enum
from pydantic import BaseModel, ConfigDict, validator
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.interface.deployments import GitLabConfig, GitLabConfigGet
from ctutor_backend.model.sqlalchemy_models.organization import Organization
from sqlalchemy_utils import Ltree

class OrganizationType(str,Enum):
    user = "user"
    community = "community"
    organization = "organization"

class OrganizationProperties(BaseModel):
    gitlab: Optional[GitLabConfig] = None
    
    model_config = ConfigDict(
        extra='allow',
    )

class OrganizationPropertiesGet(BaseModel):
    gitlab: Optional[GitLabConfigGet] = None
    
    model_config = ConfigDict(
        extra='allow',
    )

class OrganizationCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    organization_type: OrganizationType
    user_id: Optional[str] = None
    properties: Optional[OrganizationProperties] = None
    number: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    fax_number: Optional[str] = None
    url: Optional[str] = None
    postal_code: Optional[str] = None
    street_address: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class OrganizationGet(BaseEntityGet):
    id: str
    path: str
    title: Optional[str] = None
    description: Optional[str] = None
    organization_type: OrganizationType
    user_id: Optional[str] = None
    properties: Optional[OrganizationPropertiesGet] = None
    number: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    fax_number: Optional[str] = None
    url: Optional[str] = None
    postal_code: Optional[str] = None
    street_address: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    @validator('path', pre=True)
    def cast_str_to_ltree(cls, value):
        return str(value)

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

class OrganizationList(BaseModel):
    id: str
    path: str
    title: Optional[str] = None
    organization_type: OrganizationType
    user_id: Optional[str] = None

    @validator('path', pre=True)
    def cast_str_to_ltree(cls, value):
        return str(value)
    
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

class OrganizationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    organization_type: Optional[OrganizationType] = None
    user_id: Optional[str] = None
    properties: Optional[OrganizationProperties] = None
    number: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    fax_number: Optional[str] = None
    url: Optional[str] = None
    postal_code: Optional[str] = None
    street_address: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class OrganizationQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    organization_type: Optional[OrganizationType] = None
    user_id: Optional[str] = None
    properties: Optional[OrganizationProperties] = None
    number: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    fax_number: Optional[str] = None
    url: Optional[str] = None
    postal_code: Optional[str] = None
    street_address: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

def organization_search(db: Session, query, params: Optional[OrganizationQuery]):
    if params.id != None:
        query = query.filter(Organization.id == params.id)
    if params.title != None:
        query = query.filter(Organization.title == params.title)
    if params.description != None:
        query = query.filter(Organization.description == params.description)
    if params.path != None:
        query = query.filter(Organization.path == Ltree(params.path))
    if params.organization_type != None:
        query = query.filter(Organization.organization_type == params.organization_type)
    if params.user_id != None:
        query = query.filter(Organization.user_id == params.user_id)
    if params.number != None:
        query = query.filter(Organization.number == params.number)
    if params.email != None:
        query = query.filter(Organization.email == params.email)
    if params.telephone != None:
        query = query.filter(Organization.telephone == params.telephone)
    if params.fax_number != None:
        query = query.filter(Organization.fax_number == params.fax_number)
    if params.url != None:
        query = query.filter(Organization.url == params.url)
    if params.postal_code != None:
        query = query.filter(Organization.postal_code == params.postal_code)
    if params.street_address != None:
        query = query.filter(Organization.street_address == params.street_address)
    if params.locality != None:
        query = query.filter(Organization.locality == params.locality)
    if params.region != None:
        query = query.filter(Organization.region == params.region)
    if params.country != None:
        query = query.filter(Organization.country == params.country)

    return query

class OrganizationInterface(EntityInterface):
    create = OrganizationCreate
    get = OrganizationGet
    list = OrganizationList
    update = OrganizationUpdate
    query = OrganizationQuery
    search = organization_search
    endpoint = "organizations"
    model = Organization
    cache_ttl = 60