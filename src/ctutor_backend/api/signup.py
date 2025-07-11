from fastapi import APIRouter
from gitlab import Gitlab
from pydantic import BaseModel
from sqlalchemy import or_
from ctutor_backend.api.exceptions import BadRequestException, NotFoundException
from ctutor_backend.database import get_db
from ctutor_backend.gitlab_utils import gitlab_current_user
from ctutor_backend.interface.course_members import CourseMemberProperties
from ctutor_backend.interface.courses import CourseProperties
from ctutor_backend.interface.organizations import OrganizationProperties
from ctutor_backend.interface.tokens import decrypt_api_key
from ctutor_backend.model.auth import Account, User, StudentProfile
from ctutor_backend.model.course import Course, CourseMember
from ctutor_backend.model.organization import Organization
from gitlab.v4.objects import Project


signup_router = APIRouter()

class GitlabSignup(BaseModel):
    provider: str
    token: str

class CourseSignupResponse(BaseModel):
    course_id: str
    course_title: str
    role: str
    repository: str

class GitlabSignupResponse(BaseModel):
    courses: list[CourseSignupResponse] = []

@signup_router.post("/gitlab", response_model=GitlabSignupResponse)
async def gitlab_signup(gitlab_signup: GitlabSignup):

    gitlab_user = gitlab_current_user(Gitlab(url=gitlab_signup.provider,private_token=gitlab_signup.token))

    signup_courses: list[CourseSignupResponse] = []

    with next(get_db()) as db:

        query = db.query(User,Account) \
            .select_from(Account) \
                .filter(Account.type == "gitlab", Account.provider == gitlab_signup.provider,Account.provider_account_id == gitlab_user["username"]) \
                    .outerjoin(User,Account.user_id == User.id) \
                        .first()

        if query == None:
            user = None
            account = None
        else:
            user, account = query

        if account == None:

            user = db.query(User) \
                .outerjoin(StudentProfile, StudentProfile.user_id == User.id) \
                    .outerjoin(Account, Account.user_id == User.id) \
                        .filter(or_(StudentProfile.student_email == gitlab_user["email"], User.email == gitlab_user["email"])).first()

            if user == None:
                raise NotFoundException()
            try:
                account = Account(
                    type="gitlab",
                    provider=gitlab_signup.provider,
                    provider_account_id=gitlab_user["username"],
                    user_id=user.id
                )

                db.add(account)
                db.commit()
                db.refresh(account)

            except:
                db.rollback()

                return False

        if user == None:
            raise NotFoundException()

        query = db.query(CourseMember,Course,Organization.properties) \
            .join(Course,Course.id == CourseMember.course_id) \
                .join(Organization,Organization.id == Course.organization_id) \
                    .filter(CourseMember.user_id == user.id, Course.properties["gitlab"].op("->>")("url") == gitlab_signup.provider).all()
        
        if query == None:
            raise NotFoundException()

        for course_member, course, organization_properties in query:
            course_member_properties = CourseMemberProperties(**course_member.properties)
            course_properties = CourseProperties(**course.properties)
            organization_properties = OrganizationProperties(**organization_properties)
            token = decrypt_api_key(organization_properties.gitlab.token)

            gitlab = Gitlab(url=organization_properties.gitlab.url,private_token=token)

            template_projects = gitlab.projects.list(search=f"{course_properties.gitlab.full_path}/student-template",search_namespaces=True)
            student_projects = gitlab.projects.list(search=course_member_properties.gitlab.full_path,search_namespaces=True)
            submission_projects = gitlab.projects.list(search=course_member_properties.gitlab.full_path_submission,search_namespaces=True)

            if len(template_projects) == 0 or len(template_projects) > 1:
                raise BadRequestException()
            
            if len(student_projects) == 0 or len(student_projects) > 1:
                raise BadRequestException()

            if len(submission_projects) == 0 or len(submission_projects) > 1:
                raise BadRequestException()

            template_project: Project = template_projects[0]
            student_project: Project = student_projects[0]
            submission_project: Project = submission_projects[0]

            gitlab_user_id = gitlab_user["id"]

            try:
                template_project.members.create({
                    "user_id": gitlab_user_id,
                    "access_level": 20
                })
            except Exception as e:
                try:
                    member = template_project.members.get(gitlab_user_id)
                    member.access_level = 20
                    member.save()
                    print(f"Access 20 to {template_project.path} granted")
                except Exception as e:
                    print(f"Access 20 to {template_project.path} NOT granted {str(e)}")

            try:
                student_project.members.create({
                    "user_id": gitlab_user_id,
                    "access_level": 40
                })
            except Exception as e:
                try:
                    member = student_project.members.get(gitlab_user_id)
                    member.access_level = 40
                    member.save()
                    print(f"Access 40 to {student_project.path} granted")
                except Exception as e:
                    print(f"Access 40 to {student_project.path} NOT granted {str(e)}")

            try:
                submission_project.members.create({
                    "user_id": gitlab_user_id,
                    "access_level": 20
                })
            except Exception as e:
                try:
                    member = submission_project.members.get(gitlab_user_id)
                    member.access_level = 20
                    member.save()
                    print(f"Access 20 to {submission_project.path} granted")
                except Exception as e:
                    print(f"Access 20 to {submission_project.path} NOT granted {str(e)}")
            
            repository = f"{organization_properties.gitlab.url}/{course_member_properties.gitlab.full_path}"
            signup_courses.append(CourseSignupResponse(course_id=str(course_member.id),course_title=course.title,role=course_member.course_role_id,repository=repository))
    
    return GitlabSignupResponse(courses=signup_courses)