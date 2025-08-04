from uuid import UUID
from typing import Any, Optional
from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import exc
from ctutor_backend.api.exceptions import BadRequestException, NotFoundException, InternalServerException
from ctutor_backend.api.permissions import check_permissions
from ctutor_backend.interface.filter import apply_filters
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.base import EntityInterface, ListQuery
from sqlalchemy.inspection import inspect
from ..custom_types import Ltree, LtreeType
from sqlalchemy.exc import StatementError

async def create_db(permissions: Principal, db: Session, entity: BaseModel, db_type: Any, response_type: BaseModel, post_create: Any = None):
    
    resource = db_type.__tablename__

    if permissions.permitted(resource,"create"):
        pass

    else:
        raise NotFoundException()

    try:
        model_dump = entity.model_dump(exclude_unset=True)

        # columns of custom postgresql type Ltree needs to be threated separately
        mapper = inspect(db_type)

        for column in mapper.columns.keys():
            if isinstance(mapper.columns[column].type, LtreeType):
                if column in model_dump.keys() and model_dump[column] != None and isinstance(model_dump[column],str):
                    model_dump[column] = Ltree(model_dump[column])

        db_item = db_type(**model_dump)

        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        response = response_type.model_validate(db_item,from_attributes=True)

        if post_create != None:
            post_create(db_item, db)

        return response
    #except IntegrityError as e:
    except Exception as e:
        print(e.args)
        db.rollback()
        raise BadRequestException(detail=e.args)

async def get_id_db(permissions: Principal, db: Session, id: UUID | str, interface: EntityInterface, scope: str = "get"):

    db_type = interface.model

    query = check_permissions(permissions,db_type,scope,db)

    if query == None:
        raise NotFoundException()
    
    try:
        item = query.filter(db_type.id == id).first()

        if item == None:
            raise NotFoundException(detail=f"{db_type.__name__} with id [{id}] not found")
        
        return interface.get.model_validate(item,from_attributes=True)
    
    except HTTPException as e:
        raise e
    
    except StatementError as e:
        raise BadRequestException(detail=e.args)

    except Exception as e:
        raise NotFoundException(detail=e.args)

async def list_db(permissions: Principal, db: Session, params: ListQuery, interface: EntityInterface):
        
    db_type = interface.model
    query_func = interface.search

    query = check_permissions(permissions,db_type,"list",db)

    if query == None:
        return []
 
    query = query_func(db, query, params)

    total = query.order_by(None).count()

    if params.limit != None:
        query = query.limit(params.limit)
    if params.skip != None:
        query = query.offset(params.skip)
    
    query_result = [interface.list.model_validate(entity,from_attributes=True) for entity in query.all()]

    return query_result, total

def update_db(permissions: Principal, db: Session, id: UUID | str | None, entity: Any, db_type: Any, response_type: BaseModel, db_item = None, post_update: Any = None):
    if id != None:

        query = check_permissions(permissions,db_type,"update",db)

        if query == None:
            raise NotFoundException()

        db_item = query.filter(db_type.id == id).first()

        if db_item == None:
            raise NotFoundException()
        
    if isinstance(entity,BaseModel):
        entity = entity.model_dump(exclude_unset=True)

    old_db_item = response_type(**db_item.__dict__)

    # Handle Ltree columns specially
    mapper = inspect(db_type)
    for column in mapper.columns.keys():
        if isinstance(mapper.columns[column].type, LtreeType):
            if column in entity.keys() and entity[column] != None and isinstance(entity[column], str):
                entity[column] = Ltree(entity[column])

    try:
        for key in entity.keys():
            attr = entity.get(key)
            setattr(db_item, key, attr)

        db.commit()
        db.refresh(db_item)

        if post_update != None:
            post_update(db_item, old_db_item, db)

        return response_type(**db_item.__dict__)

    except Exception as e:
        db.rollback()
        print(f"Exception in update_db: {e}")
        print(f"Exception type: {type(e)}")
        print(f"Exception args: {e.args}")
        import traceback
        traceback.print_exc()
        raise BadRequestException(detail=str(e))

def delete_db(permissions: Principal, db: Session, id: UUID | str, db_type: Any):

    query = check_permissions(permissions,db_type,"delete",db)
    
    entity = query.filter(db_type.id == id).first()
    
    if not entity:
        raise NotFoundException(detail=f"{db_type.__name__} not found")

    try:
        db.delete(entity)
        db.commit()
    except exc.SQLAlchemyError as e:
        # TODO: proper error handling
        raise InternalServerException(detail=e.args)
    except Exception as e:
        raise InternalServerException(detail=e.args)

    return {"ok": True}

def archive_db(permissions: Principal, db: Session, id: UUID | str | None, db_type: Any, db_item = None):

    query = check_permissions(permissions,db_type,"archive",db)

    try:
        if db_item == None and id != None:
            db_item = query.filter(db_type.id == id).first()
        
        setattr(db_item, "archived_at", datetime.now())
            
        db.commit()
        db.refresh(db_item)
    except exc.SQLAlchemyError as e:
        # TODO: proper error handling
        raise InternalServerException(detail=e.args)
    except Exception as e:
        raise InternalServerException(detail=e.args)
    
    return {"ok": True}

async def filter_db(permissions: Principal, db: Session, db_type: Any, params: ListQuery, query_func, filter: Optional[dict] = None):

    query = check_permissions(permissions,db_type,"filter",db)

    if query == None:
       return []

    query = query_func(db, query, params)

    if filter != None and filter != {}:
        query = query.filter(apply_filters(query, db_type, filter))

        #print(f'{query.statement.compile(compile_kwargs={"literal_binds": True})}')
    
    if params.limit != None:
        query = query.limit(params.limit)
    if params.skip != None:
        query = query.offset(params.skip)

    return query