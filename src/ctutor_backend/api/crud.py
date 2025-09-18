from uuid import UUID
from typing import Any, Optional
from datetime import datetime
from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import exc
from psycopg2.errors import NotNullViolation
from ctutor_backend.api.exceptions import BadRequestException, NotFoundException, InternalServerException
from ctutor_backend.permissions.core import check_permissions, can_perform_with_parents
from ctutor_backend.permissions.handlers import permission_registry
from ctutor_backend.permissions.principal import Principal

from ctutor_backend.interface.filter import apply_filters
from ctutor_backend.interface.base import EntityInterface, ListQuery
from sqlalchemy.inspection import inspect
from ..custom_types import Ltree, LtreeType
from sqlalchemy.exc import StatementError
from ctutor_backend.interface.tasks import TaskStatus, map_task_status_to_int

async def create_db(permissions: Principal, db: Session, entity: BaseModel, db_type: Any, response_type: BaseModel, post_create: Any = None):

    # Authorization for create
    # 1) Admin shortcut
    if not permissions.is_admin:
        # 2) Consult handler if registered; handlers are the source of truth
        handler = permission_registry.get_handler(db_type)
        # Extract context identifiers from the payload (e.g., any *_id fields)
        if isinstance(entity, BaseModel):
            model_dump = entity.model_dump(exclude_unset=True)
        else:
            model_dump = entity or {}
        # Build a simple context dict of *_id keys for handler use
        context = {k: str(v) for k, v in model_dump.items() if k.endswith("_id") and v is not None}

        if handler is None:
            # Fallback behavior per permissions.md: no handler → admin-only
            raise NotFoundException()

        # Require handler to permit creation with the provided context
        if not handler.can_perform_action(permissions, "create", resource_id=None, context=context):
            # Explicitly deny without attempting permissive fallbacks
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
            import asyncio
            if asyncio.iscoroutinefunction(post_create):
                await post_create(db_item, db)
            else:
                post_create(db_item, db)

        return response
    except exc.IntegrityError as e:
        db.rollback()
        # Just provide a cleaner version of the database error without hardcoding constraint names
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        # Try to extract just the first line and clean it up a bit
        if 'DETAIL:' in error_msg:
            # Include the DETAIL part which often has useful info
            main_error = error_msg.split('\n')[0]
            detail_part = error_msg.split('DETAIL:')[1].split('\n')[0].strip()
            clean_msg = f"{main_error}. {detail_part}"
        else:
            clean_msg = error_msg.split('\n')[0] if '\n' in error_msg else error_msg
        raise BadRequestException(detail=clean_msg)
            
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
            if isinstance(attr, TaskStatus):
                attr = map_task_status_to_int(attr)
            elif isinstance(attr, Enum):
                attr = attr.value
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
    except exc.IntegrityError as e:
        db.rollback()
        # Handle foreign key constraint violations
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        # Parse the error message to provide user-friendly feedback
        if 'NotNullViolation' in error_msg:
            # This happens when deleting would cause NULL in a required foreign key
            if 'course_content_type_id' in error_msg and 'course_content' in error_msg:
                raise BadRequestException(
                    detail="Cannot delete this course content type because it is still being used by course content items. Please remove or reassign all course content using this type first."
                )
            else:
                # Generic not null violation message
                raise BadRequestException(
                    detail="Cannot delete this item because it would violate data integrity constraints. Other records depend on this item."
                )
        elif 'ForeignKeyViolation' in error_msg or 'violates foreign key constraint' in error_msg:
            # Extract table name if possible for better error message
            if 'table' in error_msg:
                # Try to extract table name from error
                import re
                table_match = re.search(r'table "(\w+)"', error_msg)
                if table_match:
                    table_name = table_match.group(1)
                    raise BadRequestException(
                        detail=f"Cannot delete this {db_type.__tablename__.replace('_', ' ')} because it is referenced by records in {table_name.replace('_', ' ')}. Please remove those references first."
                    )
            
            # Generic foreign key violation message
            raise BadRequestException(
                detail=f"Cannot delete this {db_type.__tablename__.replace('_', ' ')} because other records depend on it. Please remove all references to this item first."
            )
        elif 'UniqueViolation' in error_msg:
            # This shouldn't happen on delete, but handle it just in case
            raise BadRequestException(detail="A unique constraint violation occurred while deleting.")
        else:
            # Generic integrity error
            raise BadRequestException(
                detail=f"Cannot delete this item due to data integrity constraints. Error: {error_msg.split('DETAIL:')[0] if 'DETAIL:' in error_msg else error_msg}"
            )
    except exc.SQLAlchemyError as e:
        db.rollback()
        # Handle other SQLAlchemy errors
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        print(f"SQLAlchemyError in delete_db: {error_msg}")
        raise InternalServerException(detail="An unexpected database error occurred while deleting.")
    except Exception as e:
        db.rollback()
        print(f"Unexpected error in delete_db: {e}")
        raise InternalServerException(detail="An unexpected error occurred while deleting.")

    return {"ok": True}

def archive_db(permissions: Principal, db: Session, id: UUID | str | None, db_type: Any, db_item = None):

    query = check_permissions(permissions,db_type,"archive",db)

    try:
        if db_item == None and id != None:
            db_item = query.filter(db_type.id == id).first()
            
        if not db_item:
            raise NotFoundException(detail=f"{db_type.__name__} not found")
        
        setattr(db_item, "archived_at", datetime.now())
            
        db.commit()
        db.refresh(db_item)
    except NotFoundException:
        raise
    except exc.IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise BadRequestException(detail=f"Cannot archive this item due to data integrity constraints.")
    except exc.SQLAlchemyError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        print(f"SQLAlchemyError in archive_db: {error_msg}")
        raise InternalServerException(detail="An unexpected database error occurred while archiving.")
    except Exception as e:
        db.rollback()
        print(f"Unexpected error in archive_db: {e}")
        raise InternalServerException(detail="An unexpected error occurred while archiving.")
    
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
