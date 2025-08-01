from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy.orm import Session, aliased
from ctutor_backend.interface.deployments import GitLabConfigGet
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.interface.users import UserList
from ctutor_backend.model import CourseMember
from ctutor_backend.model import CourseContent, CourseContentKind, CourseContentType, CourseSubmissionGroup, CourseSubmissionGroupMember
from ctutor_backend.model import User


class CourseMemberGitLabConfig(GitLabConfigGet):
  full_path_submission: Optional[str] = None

class CourseMemberProperties(BaseModel):
    gitlab: Optional[CourseMemberGitLabConfig] = None
    
    model_config = ConfigDict(
        extra='allow'
    )
    
class CourseMemberCreate(BaseModel):
    id: Optional[str] = None
    properties: Optional[CourseMemberProperties] = None
    user_id: str
    course_id: str
    course_group_id: Optional[str] = None
    course_role_id: str

class CourseMemberGet(BaseEntityGet):
    id: str
    properties: Optional[CourseMemberProperties] = None
    user_id: str
    course_id: str
    course_group_id: Optional[str] = None
    course_role_id: str
    user: Optional[UserList] = None

    model_config = ConfigDict(from_attributes=True)

class CourseMemberList(BaseModel):
    id: str
    user_id: str
    course_id: str
    course_group_id: Optional[str] = None # not done
    course_role_id: str
    user: UserList

    model_config = ConfigDict(from_attributes=True)

class CourseMemberUpdate(BaseModel):
    properties: Optional[CourseMemberProperties] = None
    course_group_id: Optional[str] = None
    course_role_id: Optional[str] = None
    
class CourseMemberQuery(ListQuery):
    id: Optional[str] = None
    user_id: Optional[str] = None
    course_id: Optional[str] = None
    course_group_id: Optional[str] = None
    course_role_id: Optional[str] = None
    properties: Optional[CourseMemberProperties] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None

def course_member_search(db: Session, query, params: Optional[CourseMemberQuery]):

    UserA = aliased(User)
    query = query.join(UserA, UserA.id == CourseMember.user_id)

    if params.id != None:
        query = query.filter(CourseMember.id == params.id)
    if params.user_id != None:
        query = query.filter(CourseMember.user_id == params.user_id)
    if params.course_id != None:
        query = query.filter(CourseMember.course_id == params.course_id)
    if params.course_group_id != None:
        query = query.filter(CourseMember.course_group_id == params.course_group_id)
    if params.course_role_id != None:
        query = query.filter(CourseMember.course_role_id == params.course_role_id)

    if params.given_name != None:
        query = query.filter(UserA.given_name == params.given_name)
    if params.family_name != None:
        query = query.filter(UserA.family_name == params.family_name)
  
    return query.order_by(UserA.family_name)

def post_create(course_member: CourseMember, db: Session):

    if course_member.user.user_type != "user":
        return
    
    course_contents = (
        db.query(
            CourseContent.id,
            CourseContent.course_id,
            CourseContent.max_test_runs,
            CourseContent.max_submissions,
            CourseContent.max_group_size)
        .join(CourseContentType, CourseContentType.id == CourseContent.course_content_type_id)
        .join(CourseContentKind, CourseContentKind.id == CourseContentType.course_content_kind_id)
        .filter(
            CourseContent.course_id == course_member.course_id,
            CourseContentKind.submittable == True,
            CourseContent.max_group_size == 1
        ).all()
    )

    for id, course_id, max_test_runs, max_submissions, max_group_size in course_contents:
        submission_group = CourseSubmissionGroup(
            course_id=course_id,
            course_content_id=id,
            max_group_size=max_group_size,
            max_test_runs=max_test_runs,
            max_submissions=max_submissions
        )

        db.add(submission_group)
        db.commit()
        db.refresh(submission_group)
        
        submission_group_member = CourseSubmissionGroupMember(
            course_submission_group_id = submission_group.id,
            course_member_id = course_member.id
        )

        db.add(submission_group_member)
        db.commit()
        db.refresh(submission_group_member)

class CourseMemberInterface(EntityInterface):
    create = CourseMemberCreate
    get = CourseMemberGet
    list = CourseMemberList
    update = CourseMemberUpdate
    query = CourseMemberQuery
    search = course_member_search
    endpoint = "course-members"
    model = CourseMember
    post_create = post_create
    cache_ttl = 300  # 5 minutes - membership changes moderately frequently