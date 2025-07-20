from typing import Annotated
from fastapi import Depends
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.exceptions import BadRequestException, NotFoundException
from ctutor_backend.database import get_db
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.tokens import encrypt_api_key
from ctutor_backend.interface.users import UserGet
from ctutor_backend.model.auth import User

user_router = APIRouter()

@user_router.get("", response_model=UserGet)
def get_current_user(
    permissions: Annotated[Principal, Depends(get_current_permissions)],
    db: Session = Depends(get_db)
):
    """Get the current authenticated user"""
    try:
        return db.query(User).filter(User.id == permissions.user_id).first()
    except Exception as e:
        print(e)
        raise NotFoundException()

class UserPassword(BaseModel):
    username: str
    password: str

@user_router.post("/password", status_code=204)
def set_user_password(permissions: Annotated[Principal, Depends(get_current_permissions)], payload: UserPassword, db: Session = Depends(get_db)):

    # TODO: add report, this should not be called from someone else
    if permissions.is_admin == False:
        raise NotFoundException()

    if len(payload.password) < 12:
        raise BadRequestException()

    if payload.username == None or len(payload.username) < 3:
        raise BadRequestException()

    with next(get_db()) as db:
        user = db.query(User).filter(User.username == payload.username).first()

        user.password = encrypt_api_key(payload.password)
        db.commit()
        db.refresh(user)