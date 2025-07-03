from typing import Optional
from pydantic import BaseModel
from ctutor_backend.interface.course_contents import CourseContentGet
from ctutor_backend.interface.repositories import Repository

class Submission(BaseModel):
    submission: Repository
    provider: str
    full_path: str
    token: str
    assignment: CourseContentGet
    module: Repository
    result_id: str
    user_id: str

class TestJob(BaseModel):
    user_id: str
    course_member_id: str
    course_content_id: str
    execution_backend_id: str
    module: Repository
    reference: Optional[Repository] = None
    test_number: int = -1
    submission_number: int = -1

class TestCreate(BaseModel):
    course_member_id: Optional[str] = None
    course_content_id: Optional[str] = None
    course_content_path: Optional[str] = None

    directory: Optional[str] = None
    project: Optional[str] = None
    provider_url: Optional[str] = None

    version_identifier: Optional[str] = None
    submit: Optional[bool] = False