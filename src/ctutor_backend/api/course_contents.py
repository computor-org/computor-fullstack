import json
import os
from pydantic import BaseModel
import yaml
from typing import Annotated, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.exceptions import BadRequestException, NotFoundException
from ctutor_backend.api.filesystem import get_path_course_content, mirror_entity_to_filesystem
from ctutor_backend.api.permissions import check_course_permissions
from ctutor_backend.database import get_db
from ctutor_backend.interface.course_contents import CourseContentGet, CourseContentInterface
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.api.api_builder import CrudRouter
from ctutor_backend.model.models import CourseContent

course_content_router = CrudRouter(CourseContentInterface)

class CourseContentFileQuery(BaseModel):
    filename: Optional[str] = None

@course_content_router.router.get("/files/{course_content_id}", response_model=dict)
async def get_course_content_meta(permissions: Annotated[Principal, Depends(get_current_permissions)], course_content_id: UUID | str, file_query: CourseContentFileQuery = Depends(), db: Session = Depends(get_db)):

    if check_course_permissions(permissions,CourseContent,"_study_assistant",db).filter(CourseContent.id == course_content_id).first() == None:
        raise NotFoundException()

    course_content_dir = await get_path_course_content(course_content_id,db)

    if file_query.filename == None:
        raise BadRequestException()

    with open(os.path.join(course_content_dir,file_query.filename),'r') as file:
        content = file.read()

        if file_query.filename.endswith(".yaml") or file_query.filename.endswith(".yml"):
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    return data
            except Exception:
                raise BadRequestException()

        elif file_query.filename.endswith(".json"):
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    return data
            except Exception:
                raise BadRequestException()
        else:
            return {"content": content}


async def event_wrapper(entity: CourseContentGet, db: Session, permissions: Principal):
    try:
        await mirror_entity_to_filesystem(str(entity.id),CourseContentInterface,db)
    except Exception as e:
        print(e)

course_content_router.on_created.append(event_wrapper)
course_content_router.on_updated.append(event_wrapper)