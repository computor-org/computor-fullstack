from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model.auth import Account

class AccountCreate(BaseModel):
    provider: str
    type: str
    provider_account_id: str
    user_id: str
    properties: Optional[dict] = None
    
class AccountGet(BaseEntityGet,AccountCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)

class AccountList(BaseModel):
    id: str
    provider: str
    type: str
    provider_account_id: str
    user_id: str

    model_config = ConfigDict(from_attributes=True)
    
class AccountUpdate(BaseModel):
    provider: Optional[str] = None
    type: Optional[str] = None
    provider_account_id: Optional[str] = None
    properties: Optional[dict] = None

class AccountQuery(ListQuery):
    id: Optional[str] = None
    provider: Optional[str] = None
    type: Optional[str] = None
    provider_account_id: Optional[str] = None
    user_id: Optional[str] = None
    properties: Optional[str] = None
    
def account_search(db: Session, query, params: Optional[AccountQuery]):
    if params.id != None:
        query = query.filter(Account.id == params.id)
    if params.provider != None:
        query = query.filter(Account.provider == params.provider)
    if params.type != None:
        query = query.filter(Account.type == params.type)
    if params.provider_account_id != None:
        query = query.filter(Account.provider_account_id == params.provider_account_id)
    if params.user_id != None:
        query = query.filter(Account.user_id == params.user_id)

    return query

class AccountInterface(EntityInterface):
    create = AccountCreate
    get = AccountGet
    list = AccountList
    update = AccountUpdate
    query = AccountQuery
    search = account_search
    endpoint = "accounts"
    model = Account