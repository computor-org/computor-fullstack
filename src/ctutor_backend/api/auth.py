import datetime
import json
import hashlib
import base64
import binascii
from typing import Annotated, Any
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasicCredentials
from gitlab import Gitlab
from fastapi import Depends, Request
from ctutor_backend.api.permissions import db_get_claims, db_get_course_claims
from ctutor_backend.database import get_db
from ctutor_backend.gitlab_utils import gitlab_current_user
from ctutor_backend.interface.auth import GLPAuthConfig
from ctutor_backend.interface.permissions import Principal, build_claim_actions
from ctutor_backend.interface.tokens import decrypt_api_key
nt, User
from ctutor_backend.api.exceptions import NotFoundException, UnauthorizedException
from fastapi.security.utils import get_authorization_scheme_param
from ctutor_backend.model.sqlalchemy_models.role import UserRole
from ctutor_backend.redis import get_redis_client

_expiry_time_authenticated = 1800

def get_user_id_from_basic(username: str, password: str, db: Session):

    results = (
        db.query(
            User.id,
            User.password,
            User.user_type,
            User.token_expiration,
            UserRole.role_id
        )
        .outerjoin(UserRole, UserRole.user_id == User.id)
        .filter(
            User.username == username
        ).all()
    )
    
    user_id, user_password, user_type, token_expiration = results[0][:4]

    if user_type == 'token':
        now = datetime.datetime.now(datetime.timezone.utc)
        if token_expiration is None or token_expiration < now:
            raise Exception()

    role_ids = []
    for res in results:
        if res[4] != None:
            role_ids.append(res[4])

    if user_id == None:
        raise Exception()

    if password != decrypt_api_key(user_password):
        raise Exception()

    return user_id, role_ids

def get_user_id_from_gitlab_creds(gitlab_credentials: GLPAuthConfig, db: Session):

    gl = Gitlab(url=gitlab_credentials.url,private_token=gitlab_credentials.token)

    try:
        user_dict = gitlab_current_user(gl)
    except:
        raise UnauthorizedException()

    results = (
        db.query(
            User.id,
            UserRole.role_id
        )
        .join(Account, Account.user_id == User.id)
        .outerjoin(UserRole, UserRole.user_id == User.id)
        .filter(
            Account.type == "gitlab",
            Account.provider_account_id == user_dict["username"]
        ).all()
    )

    if len(results) == 0:
        raise NotFoundException()
    
    user_id = results[0][0]
    role_ids = []
    for user_id, role_id in results:
        if role_id != None:
            role_ids.append(role_id)
    
    return user_id, role_ids

def auth_type_switch(request: Request) -> GLPAuthConfig | HTTPBasicCredentials | None:
  
    header_creds = request.headers.get("GLP-CREDS", None)

    if header_creds != None:
        gitlab_creds = json.loads(base64.b64decode(header_creds))
        return GLPAuthConfig(**gitlab_creds)

    authorization = request.headers.get("Authorization")
    if authorization != None:
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != "basic":
            return None
        try:
            data = base64.b64decode(param).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise UnauthorizedException()
        username, separator, password = data.partition(":")
        if not separator:
            raise UnauthorizedException()
        return HTTPBasicCredentials(username=username, password=password)

    raise UnauthorizedException()

async def get_current_permissions(credentials: Annotated[GLPAuthConfig | HTTPBasicCredentials | dict, Depends(auth_type_switch)]):

    if credentials.__class__ == HTTPBasicCredentials:
        return get_permissions_from_basic_auth(credentials)
    elif credentials.__class__ == GLPAuthConfig:
        return await get_user_permission_from_glpat(credentials)
    else:
        raise NotFoundException()

async def get_user_permission_from_glpat(gitlab_credentials: GLPAuthConfig):

    cache = await get_redis_client()
    
    hashed_cache_key = hashlib.sha256(f"{gitlab_credentials.url}::{gitlab_credentials.token}".encode()).hexdigest()

    cached_auth = await cache.get(hashed_cache_key)

    if cached_auth != None:
        return Principal.model_validate(json.loads(cached_auth),from_attributes=True)

    with next(get_db()) as db:
        user_id, role_ids = get_user_id_from_gitlab_creds(gitlab_credentials, db)
        claim_values = db_get_claims(user_id, db)
        claim_values.extend(db_get_course_claims(user_id, db))

    principal = Principal(
        user_id=user_id,
        gitlab_credentials=gitlab_credentials,
        roles=role_ids,
        claims=build_claim_actions(claim_values)
    )

    try:
        await cache.set(hashed_cache_key, principal.model_dump_json(), ttl=_expiry_time_authenticated)
    except Exception as e:
        raise e

    return principal

def get_permissions_from_basic_auth(credentials: HTTPBasicCredentials):

    current_username_bytes = credentials.username.encode()
    current_password_bytes = credentials.password.encode()

    try:
        username = current_username_bytes.decode()
        password = current_password_bytes.decode()


        if username == None or username == "" or password == None or password == "":
            raise UnauthorizedException()

        with next(get_db()) as db:
            user_id, role_ids = get_user_id_from_basic(username,password,db)
            claim_values = db_get_claims(user_id, db)
            claim_values.extend(db_get_course_claims(user_id, db))

        principal = Principal(
            user_id=user_id,
            roles=role_ids,
            claims=build_claim_actions(claim_values)
        )

        return principal
        
    except UnauthorizedException as e:
        raise e

    except Exception as e:
        print(f"ERROR {str(e)}")
        raise UnauthorizedException(
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

def get_permissions_from_mockup(user_id: str):

    try:
        with next(get_db()) as db:
            results = (
                db.query(
                    User.id,
                    UserRole.role_id,
                )
                .select_from(User)
                .join(UserRole, UserRole.user_id == User.id)
                .filter(or_(User.id == user_id,User.username == user_id)).all()
            )
        print(results)
        user_id = results[0][0]
        role_ids = []
        claim_values = db_get_claims(user_id, db)
        claim_values.extend(db_get_course_claims(user_id, db))

        for res in results:
            if res[1] != None:
                role_ids.append(res[1])

        if user_id == None:
            raise Exception()

        principal = Principal(
            user_id=user_id,
            roles=role_ids,
            claims=build_claim_actions(claim_values)
        )

        return principal
        
    except UnauthorizedException as e:
        raise e

    except Exception as e:
        print(f"ERROR {str(e)}")
        raise UnauthorizedException(
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

class HeaderAuthCredentials(BaseModel):
    type: Any
    credentials: Any

def get_auth_credentials(credentials: Annotated[GLPAuthConfig | HTTPBasicCredentials | dict, Depends(auth_type_switch)]) -> HeaderAuthCredentials:

    if credentials.__class__ == GLPAuthConfig:
        return HeaderAuthCredentials(type=GLPAuthConfig,credentials=credentials)
    
    elif credentials.__class__ == HTTPBasicCredentials:
        return HeaderAuthCredentials(type=HTTPBasicCredentials,credentials={"username":credentials.username})

    else:
        return None