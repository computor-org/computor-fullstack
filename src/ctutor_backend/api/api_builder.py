from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ctutor_backend.api.crud import archive_db, create_db, filter_db, get_id_db, list_db, update_db, delete_db
from typing import Annotated, Optional
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.database import get_db
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.base import EntityInterface
# from ctutor_backend.api.cache import cache_route
from ctutor_backend.redis import get_redis_client
from aiocache import BaseCache
from fastapi import FastAPI, BackgroundTasks
from fastapi import Response
class CrudRouter:

    id_type = "id"
    
    path: str
    dto: EntityInterface

    def __init__(self, dto, endpoint: Optional[str] = None):
        self.dto = dto
        if endpoint == None:
            self.path = self.dto.endpoint
        else:
            self.path = endpoint
        
        self.router = APIRouter()

        self.on_created = []
        self.on_updated = []
        self.on_deleted = []
        self.on_archived = []

    def create(self):
        async def route(background_tasks: BackgroundTasks, permissions: Annotated[Principal, Depends(get_current_permissions)], entity: self.dto.create, cache: Annotated[BaseCache, Depends(get_redis_client)], db: Session = Depends(get_db)) -> self.dto.get:
            entity_created = await create_db(permissions, db, entity, self.dto.model, self.dto.get, self.dto.post_create)

            await cache.clear(self.dto.model.__tablename__)

            for task in self.on_created:
                background_tasks.add_task(task, entity_created, db, permissions)

            return entity_created
        return route
    
    def get(self):
        # @cache_route(self.dto,self.dto.cache_ttl)
        async def route(permissions: Annotated[Principal, Depends(get_current_permissions)], id: UUID | str, db: Session = Depends(get_db)) -> self.dto.get:
            return await get_id_db(permissions, db, id, self.dto)
        return route

    def list(self):
        # @cache_route(self.dto,self.dto.cache_ttl)
        async def route(permissions: Annotated[Principal, Depends(get_current_permissions)], response: Response, params: self.dto.query = Depends(), db: Session = Depends(get_db)) -> list[self.dto.list]:
            list_result, total = await list_db(permissions, db, params, self.dto)
            response.headers["X-Total-Count"] = str(total)
            return list_result
        return route
    
    def update(self):
        async def route(background_tasks: BackgroundTasks, permissions: Annotated[Principal, Depends(get_current_permissions)], id: UUID | str, entity: self.dto.update, cache: Annotated[BaseCache, Depends(get_redis_client)], db: Session = Depends(get_db)) -> self.dto.get:
            entity_updated = update_db(permissions, db, id, entity, self.dto.model, self.dto.get, None, self.dto.post_update)

            await cache.clear(self.dto.model.__tablename__)

            for task in self.on_updated:
                background_tasks.add_task(task, entity_updated, db, permissions)

            return entity_updated
        return route

    def delete(self):
        async def route(background_tasks: BackgroundTasks, permissions: Annotated[Principal, Depends(get_current_permissions)], id: UUID | str, cache: Annotated[BaseCache, Depends(get_redis_client)], db: Session = Depends(get_db)):

            if len(self.on_deleted) > 0:

                entity_deleted = await get_id_db(permissions, db, id, self.dto)

                await cache.clear(self.dto.model.__tablename__)

                for task in self.on_created:
                    background_tasks.add_task(task, entity_deleted, db, permissions)

            return delete_db(permissions, db, id, self.dto.model)

        return route
    
    def archive(self):  
        if hasattr(self.dto.model, "archived_at"):   
            async def route(background_tasks: BackgroundTasks, permissions: Annotated[Principal, Depends(get_current_permissions)], id: UUID | str, db: Session = Depends(get_db)):

                if len(self.on_archived) > 0:

                    entity_archived = await get_id_db(permissions, db, id, self.dto)

                    for task in self.on_archived:
                        background_tasks.add_task(task, entity_archived, db, permissions)

                return archive_db(permissions, db, id, self.dto.model)
            return route
        else:
            return None

    def filter(self):
        async def route(permissions: Annotated[Principal, Depends(get_current_permissions)], filters: Optional[dict] = None, params: self.dto.query = Depends(), db: Session = Depends(get_db)) -> list[self.dto.list]:
            return await filter_db(permissions, db, self.dto.model, params, self.dto.search, filters)
        return route

    def register_routes(self, app: FastAPI):
        
        scope_name = self.path.replace("/","").replace("_"," ")

        self.router.add_api_route("", self.create(), methods=["POST"], 
                    status_code=status.HTTP_201_CREATED, name=f"{self.create.__name__} {scope_name.capitalize()}",dependencies=[Depends(get_current_permissions)])
        self.router.add_api_route(f"/{{{CrudRouter.id_type}}}", self.get(), methods=["GET"], 
                    status_code=status.HTTP_200_OK, name=f"{self.get.__name__} {scope_name.capitalize()}",dependencies=[Depends(get_current_permissions)])
        self.router.add_api_route("", self.list(), methods=["GET"], 
                    status_code=status.HTTP_200_OK, name=f"{self.list.__name__} {scope_name.capitalize()}",dependencies=[Depends(get_current_permissions)])
        self.router.add_api_route(f"/{{{CrudRouter.id_type}}}", self.update(), methods=["PATCH"], 
                    status_code=status.HTTP_200_OK, name=f"{self.update.__name__} {scope_name.capitalize()}",dependencies=[Depends(get_current_permissions)])
        self.router.add_api_route(f"/{{{CrudRouter.id_type}}}", self.delete(), methods=["DELETE"], 
                    status_code=status.HTTP_204_NO_CONTENT, name=f"{self.delete.__name__} {scope_name.capitalize()}", dependencies=[Depends(get_current_permissions)])
        
        archive_fun = self.archive()
        
        if archive_fun != None:
            self.router.add_api_route(f"/{{{CrudRouter.id_type}}}/archive", archive_fun, methods=["PATCH"], 
                status_code=status.HTTP_204_NO_CONTENT, name=f"{archive_fun.__name__} {scope_name.capitalize()}", dependencies=[Depends(get_current_permissions)])
        
        # self.router.add_api_route("-filtered", self.filter(), methods=["GET"],
        #         status_code=status.HTTP_200_OK, name=f"{self.filter.__name__} {scope_name.capitalize()}",dependencies=[Depends(get_current_permissions)])

        app.include_router(
            self.router,
            prefix=f"/{self.path}",
            tags=[scope_name]
        )
        
        return self

class LookUpRouter:

    id_type = "id"
    
    path: str
    dto: EntityInterface

    def __init__(self, dto, endpoint: Optional[str] = None):
        self.dto = dto
        if endpoint == None:
            self.path = self.dto.endpoint
        else:
            self.path = endpoint
        
        self.router = APIRouter()
        
    def get(self):
        async def route(permissions: Annotated[Principal, Depends(get_current_permissions)], id: str, db: Session = Depends(get_db)) -> self.dto.get:
            return await get_id_db(permissions, db, id, self.dto)
        return route

    
    def list(self):
        async def route(permissions: Annotated[Principal, Depends(get_current_permissions)], response: Response, params: self.dto.query = Depends(), db: Session = Depends(get_db)) -> list[self.dto.list]:
            list_result, total = await list_db(permissions, db, params, self.dto)
            response.headers["X-Total-Count"] = str(total)
            return list_result
        return route
    
    def register_routes(self, app: FastAPI):
        
        scope_name = self.path.replace("/","").replace("_"," ")

        self.router.add_api_route(f"/{{{LookUpRouter.id_type}}}", self.get(), methods=["GET"], 
                    status_code=status.HTTP_200_OK, name=f"{self.get.__name__} {scope_name.capitalize()}",dependencies=[Depends(get_current_permissions)])
        self.router.add_api_route("", self.list(), methods=["GET"], 
                    status_code=status.HTTP_200_OK, name=f"{self.list.__name__} {scope_name.capitalize()}",dependencies=[Depends(get_current_permissions)])
        
        app.include_router(
            self.router,
            prefix=f"/{self.path}",
            tags=[scope_name]
        )
