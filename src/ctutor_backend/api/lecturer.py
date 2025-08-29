from uuid import UUID
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from ctutor_backend.database import get_db
from ctutor_backend.interface.courses import CourseGet, CourseInterface, CourseList, CourseQuery
from ctutor_backend.permissions.auth import get_current_permissions
from ctutor_backend.permissions.core import check_course_permissions
from ctutor_backend.permissions.principal import Principal
from ctutor_backend.api.exceptions import NotFoundException
from ctutor_backend.model.course import Course
lecturer_router = APIRouter()

@lecturer_router.get("/courses/{course_id}", response_model=CourseGet)
async def lecturer_get_courses(course_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    course = check_course_permissions(permissions,Course,"_lecturer",db).filter(Course.id == course_id).first()

    if course == None:
        raise NotFoundException()

    return course

@lecturer_router.get("/courses", response_model=list[CourseList])
def lecturer_list_courses(permissions: Annotated[Principal, Depends(get_current_permissions)], params: CourseQuery = Depends(), db: Session = Depends(get_db)):

    query = check_course_permissions(permissions,Course,"_lecturer",db)

    return CourseInterface.search(db,query,params)