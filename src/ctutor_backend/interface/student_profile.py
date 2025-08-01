from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model.auth import StudentProfile

class StudentProfileCreate(BaseModel):
    id: Optional[str] = None
    student_id: Optional[str] = None
    student_email: Optional[str] = None
    user_id: Optional[str] = None

class StudentProfileGet(BaseEntityGet,StudentProfileCreate):
    id: str
    student_id: Optional[str] = None
    student_email: Optional[str] = None
    user_id: str

    model_config = ConfigDict(from_attributes=True)

class StudentProfileList(BaseModel):
    id: str
    student_id: Optional[str] = None
    student_email: Optional[str] = None
    user_id: str

    model_config = ConfigDict(from_attributes=True)

class StudentProfileUpdate(BaseModel):
    student_id: Optional[str] = None
    student_email: Optional[str] = None
    properties: Optional[dict] = None

class StudentProfileQuery(ListQuery):
    id: Optional[str] = None
    student_id: Optional[str] = None
    student_email: Optional[str] = None
    user_id: Optional[str] = None
    properties: Optional[dict] = None

def student_profile_search(db: Session, query, params: Optional[StudentProfileQuery]):
    if params.id != None:
        query = query.filter(StudentProfile.id == params.id)
    if params.student_id != None:
        query = query.filter(StudentProfile.student_id == params.student_id)
    if params.student_email != None:
        query = query.filter(StudentProfile.student_email == params.student_email)
    if params.user_id != None:
        query = query.filter(StudentProfile.user_id == params.user_id)
    
    return query

class StudentProfileInterface(EntityInterface):
    create = StudentProfileCreate
    get = StudentProfileGet
    list = StudentProfileList
    update = StudentProfileUpdate
    query = StudentProfileQuery
    search = student_profile_search
    endpoint = "student-profiles"
    model = StudentProfile
    cache_ttl = 300  # 5 minutes - student profile changes moderately