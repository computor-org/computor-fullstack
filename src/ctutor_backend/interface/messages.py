from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ctutor_backend.interface.base import BaseEntityGet, BaseEntityList, EntityInterface, ListQuery
from ctutor_backend.model.message import Message


class MessageCreate(BaseModel):
    # author_id is always the current user; set in API
    parent_id: Optional[str] = None
    level: int = Field(default=0)
    title: str
    content: str

    # Targets (at least one should be provided)
    user_id: Optional[str] = None
    course_member_id: Optional[str] = None
    course_submission_group_id: Optional[str] = None
    course_group_id: Optional[str] = None


class MessageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class MessageGet(BaseEntityGet):
    id: str
    title: str
    content: str
    level: int
    parent_id: Optional[str] = None
    author_id: str

    user_id: Optional[str] = None
    course_member_id: Optional[str] = None
    course_submission_group_id: Optional[str] = None
    course_group_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MessageList(BaseEntityList):
    id: str
    title: str
    content: str
    level: int
    parent_id: Optional[str] = None
    author_id: str

    user_id: Optional[str] = None
    course_member_id: Optional[str] = None
    course_submission_group_id: Optional[str] = None
    course_group_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MessageQuery(ListQuery):
    id: Optional[str] = None
    parent_id: Optional[str] = None
    author_id: Optional[str] = None
    user_id: Optional[str] = None
    course_member_id: Optional[str] = None
    course_submission_group_id: Optional[str] = None
    course_group_id: Optional[str] = None


def message_search(db: Session, query, params: Optional[MessageQuery]):
    if params.id is not None:
        query = query.filter(Message.id == params.id)
    if params.parent_id is not None:
        query = query.filter(Message.parent_id == params.parent_id)
    if params.author_id is not None:
        query = query.filter(Message.author_id == params.author_id)
    if params.user_id is not None:
        query = query.filter(Message.user_id == params.user_id)
    if params.course_member_id is not None:
        query = query.filter(Message.course_member_id == params.course_member_id)
    if params.course_submission_group_id is not None:
        query = query.filter(Message.course_submission_group_id == params.course_submission_group_id)
    if params.course_group_id is not None:
        query = query.filter(Message.course_group_id == params.course_group_id)
    return query


class MessageInterface(EntityInterface):
    create = MessageCreate
    get = MessageGet
    list = MessageList
    update = MessageUpdate
    query = MessageQuery
    search = message_search
    endpoint = "messages"
    model = Message
    cache_ttl = 60
