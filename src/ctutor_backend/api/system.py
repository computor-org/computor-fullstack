from collections import defaultdict
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Annotated, Optional
from fastapi import BackgroundTasks, Depends, APIRouter, File, UploadFile
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.crud import get_id_db
from ctutor_backend.api.exceptions import BadRequestException, NotFoundException
from ctutor_backend.api.filesystem import mirror_entity_to_filesystem
from ctutor_backend.api.permissions import check_admin, check_course_permissions, get_permitted_course_ids
from ctutor_backend.api.utils import get_course_id_from_url, sync_dependent_items
from ctutor_backend.database import get_db
from ctutor_backend.interface.course_groups import CourseGroupCreate
from ctutor_backend.interface.course_members import CourseMemberCreate, CourseMemberInterface, CourseMemberProperties
from ctutor_backend.interface.courses import CourseInterface, CourseUpdate
from ctutor_backend.interface.deployments import ComputorDeploymentConfig, CourseConfig, CourseFamilyConfig, GitLabConfig, OrganizationConfig
from ctutor_backend.interface.organizations import OrganizationProperties
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.course_content_types import CourseContentTypeCreate
from ctutor_backend.interface.student_profile import StudentProfileCreate
from ctutor_backend.interface.tokens import decrypt_api_key
from ctutor_backend.interface.users import UserCreate, UserGet, UserTypeEnum
from ctutor_backend.model.sqlalchemy_models.course import CourseContent, CourseContentType, CourseFamily, CourseGroup, CourseMember, Organization, StudentProfile, User
from ctutor_backend.utils import get_prefect_client
from ctutor_backend.redis import get_redis_client
from aiocache import BaseCache
from prefect.client.schemas.filters import FlowRunFilter, FlowRunFilterTags,FlowRunFilterId

system_router = APIRouter()

def get_computor_deployment_from_course_id_db(course_id: UUID | str, db: Session) -> ComputorDeploymentConfig: # TODO: REFACTORING

    query = db.query(Course,CourseFamily,Organization) \
                .join(CourseFamily,CourseFamily.id == Course.course_family_id) \
                    .join(Organization, Organization.id == Course.organization_id) \
            .filter(Course.id == course_id).first()

    course: Course = query[0]
    course_family: CourseFamily = query[1]
    organization: Organization = query[2]

    deployment = ComputorDeploymentConfig(
        organization=OrganizationConfig(
            name=organization.title,
            path=organization.path.path,
            description=organization.description,
            settings=organization.properties
        ),
        courseFamily=CourseFamilyConfig(
            name=course_family.title,
            path=course_family.path.path,
            description=course_family.description,
            settings=course_family.properties
        ),
        course=CourseConfig(
            name=course.title,
            path=course.path.path,
            description=course.description,
            settings=course.properties
        )
    )

    properties = OrganizationProperties(**organization.properties)

    if properties.gitlab != None:

        deployment.organization.gitlab = GitLabConfig(
            url=properties.gitlab.url,
            full_path=properties.gitlab.full_path,
            token=decrypt_api_key(properties.gitlab.token),
            parent=properties.gitlab.parent
        )

    else:
        raise NotImplementedError()

    return deployment

class StudentCreate(BaseModel):
    user_id: Optional[UUID | str] = None
    user: Optional[UserGet] = None
    course_group_id: Optional[UUID | str] = None
    course_group_title: Optional[str] = None
    role: Optional[str] = None

class ReleaseStudentsCreate(BaseModel):
   students: list[StudentCreate] = []
   course_id: UUID | str

@system_router.post("/release/students", response_model=dict)
async def create_student(payload: ReleaseStudentsCreate, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    course_id = payload.course_id
    students = payload.students

    if check_course_permissions(permissions,Course,"_maintainer",db).filter(Course.id == course_id).first() == None:
       raise NotFoundException()

    for p in students:
      if p.course_group_id != None:
        if db.query(CourseGroup.id).filter(CourseGroup.id == p.course_group_id).count() != 1:
            raise BadRequestException(detail=f"CourseGroup with id {p.course_group_id} does not exist")
      elif p.course_group_title != None:
        course_group_id = db.query(CourseGroup.id).filter(CourseGroup.course_id == course_id,CourseGroup.title == p.course_group_title).scalar()

        if course_group_id == None:
          raise BadRequestException(detail=f"CourseGroup with id {course_group_id} does not exist")

        p.course_group_id = course_group_id
      else:
        if p.role in ["_study_assistant","_maintainer","_owner"]:
          p.course_group_id = None
        else:
          raise BadRequestException(detail=f"Student must be in a course group")   

      if p.user == None:

        if p.user_id == None:
           raise BadRequestException(detail=f"User and user id not in payload")

        user = db.query(User).filter(User.id == p.user_id).first()

        if user == None:
            raise BadRequestException(detail=f"User with id {p.user_id} does not exist")

        p.user = user

    deployment = get_computor_deployment_from_course_id_db(course_id, db)

    async with get_prefect_client() as client:

      deployment_response = await client.read_deployment_by_name("release-student/system")

      try:
        flow_run = await client.create_flow_run_from_deployment(
          deployment_id=deployment_response.id,
          parameters={
            "deployment": deployment.model_dump(),
            "payload": ReleaseStudentsCreate(
              students=students,
              course_id=course_id
            ).model_dump()
          }
        )

        return {"flow_run_id": flow_run.id}

      except Exception as e:
        raise BadRequestException()
  
class TUGStudentExport(BaseModel):
   course_group_title: str
   family_name: str
   given_name: str
   matriculation_number: str
   created_at: str
   email: str

@system_router.post("/release/students/export", response_model=list[TUGStudentExport])
async def create_student_from_export(permissions: Annotated[Principal, Depends(get_current_permissions)], course_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):

    if check_course_permissions(permissions,Course,"_maintainer",db).filter(Course.id == course_id).first() == None and check_admin(permissions) == False:
      raise NotFoundException()

    # course_path_ = str(db.query(Course.path).filter(Course.id == course_id).scalar())

    # course_path_splitted = course_path_.split(".")

    # if len(course_path_splitted) > 1:
    #   course_path = ".".join(course_path_splitted[1:])
    # else:
    #   course_path = course_path_

    import pandas as pd
    from io import StringIO

    content = await file.read()

    csv_string = StringIO(content.decode("utf-8"))

    df = pd.read_csv(csv_string)

    students: list[TUGStudentExport] = []
    for index, row in df.iterrows():
      student = TUGStudentExport(
         course_group_title = str(row["Gruppe"]).rstrip().lstrip(),
         family_name = str(row["Familienname"]).rstrip().lstrip(),
         given_name = str(row["Vorname"]).rstrip().lstrip(),
         matriculation_number = str(row["Matrikelnummer"]).rstrip().lstrip(),
         created_at = str(row["Anmeldedatum"]).rstrip().lstrip(),
         email = str(row["E-Mail"]).rstrip().lstrip())

      #if student.course_group_title.lower().endswith(course_path):
      students.append(student)

    course_groups = defaultdict(list)
    for student in students:
      course_groups[student.course_group_title].append(student)
    
    course_member_create_tasks: list[StudentCreate] = []

    for course_group_title, group in course_groups.items():

      course_group_db = db.query(CourseGroup).filter(CourseGroup.course_id == course_id, CourseGroup.title == course_group_title).first()

      if course_group_db == None:
        course_group_create = CourseGroupCreate(
          title=course_group_title,
          course_id=course_id
        )

        course_group_db = CourseGroup(**course_group_create.model_dump())

        db.add(course_group_db)
        db.commit()
        db.refresh(course_group_db)
      
      for student in group:
        student_profiles_count = (
          db.query(User.id, func.count(StudentProfile.id).label("profile_count"))
          .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
          .group_by(User.id)
          .subquery()
        )
        
        query = db.query(User,StudentProfile).select_from(User) \
          .outerjoin(StudentProfile,StudentProfile.user_id == User.id) \
            .outerjoin(student_profiles_count, student_profiles_count.c.id == User.id) \
              .filter(
                or_(
                    and_(StudentProfile.student_email == student.email,StudentProfile.student_id == student.matriculation_number),
                    and_(User.email == student.email, student_profiles_count.c.profile_count == 0))).first()

        user_db = query[0] if query != None else None
        student_profile_db = query[1] if query != None else None

        if user_db == None:

          user_create = UserCreate(
            given_name=student.given_name,
            family_name=student.family_name,
            user_type=UserTypeEnum.user,
            email=student.email
          )
          
          user_db = User(**user_create.model_dump())

          db.add(user_db)
          db.commit()
          db.refresh(user_db)

          user_id = user_db.id
        else:
          user_id = query[0].id
        
        if student_profile_db == None:
          student_profile = StudentProfileCreate(
            student_id=student.matriculation_number,
            student_email=student.email,
            user_id = user_id
          )

          student_profile_db = StudentProfile(**student_profile.model_dump())

          db.add(student_profile_db)
          db.commit()
          db.refresh(student_profile_db)

        course_member_db = db.query(CourseMember).filter(CourseMember.course_id == course_id, CourseMember.user_id == user_db.id).first()

        if course_member_db == None: 
          course_member_create = CourseMemberCreate(
            user_id=user_db.id,
            course_id=course_id,
            course_group_id=course_group_db.id,
            course_role_id="_student"
          )

          course_member_db = CourseMember(**course_member_create.model_dump())

          db.add(course_member_db)
          db.commit()
          db.refresh(course_member_db)

          CourseMemberInterface.post_create(course_member_db,db)
        else:
          if course_member_db.course_group_id != course_group_db.id:
            course_member_db.course_group_id = course_group_db.id

            db.commit()
            db.refresh(course_member_db)

        props = CourseMemberProperties(**course_member_db.properties) if course_member_db.properties != None else None

        if props == None or props != None and props.gitlab == None:
           course_member_create_tasks.append(StudentCreate(
              user_id=str(user_db.id),
              user=UserGet(**user_db.__dict__),
              course_group_id=str(course_group_db.id),
              role="_student"
           ))

    if len(course_member_create_tasks) > 0:
      deployment = get_computor_deployment_from_course_id_db(course_id, db)

      async with get_prefect_client() as client:

        deployment_response = await client.read_deployment_by_name("release-student/system")

        try:
          flow_run = await client.create_flow_run_from_deployment(
            deployment_id=deployment_response.id,
            parameters={
              "deployment": deployment.model_dump(),
              "payload": ReleaseStudentsCreate(
                students=course_member_create_tasks,
                course_id=course_id
              ).model_dump()
            }
          )
          print(f"Started flow_run {flow_run}")

        except Exception as e:
          raise BadRequestException()

    return students

async def create_course_client(course_id: str | None, deployment: ComputorDeploymentConfig, release_dir: str | None = None, ascendants: bool = False, descendants: bool = False, release_dir_list: list[str] = []):

    async with get_prefect_client() as client:

      deployment_response = await client.read_deployment_by_name("release-course/system")

      tags = []

      if course_id != None:
         tags.append(f"course:{course_id}")

      try:
        flow_run = await client.create_flow_run_from_deployment(
          deployment_id=deployment_response.id,
          parameters={
            "deployment": deployment.model_dump(),
            "release_dir": release_dir,
            "ascendants": ascendants if ascendants else False,
            "descendants": descendants  if descendants else False,
            "release_dir_list": release_dir_list
          },
          tags=tags
        )

        return {"flow_run_id": flow_run.id}

      except Exception as e:
        raise BadRequestException()

class ReleaseCourseCreate(BaseModel):
    course_id: Optional[UUID | str] = None
    gitlab_url: Optional[str] = None
    descendants: Optional[bool] = False
    deployment: Optional[ComputorDeploymentConfig] = None

@system_router.post("/release/courses", response_model=dict)
async def release_course(payload: ReleaseCourseCreate, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):
    if payload.course_id != None:
      course_id = payload.course_id
    elif payload.gitlab_url != None:
      course_id = get_course_id_from_url(payload.gitlab_url,db)
    elif payload.deployment != None:
      if check_admin(permissions) == False:
        raise NotFoundException()
      # TODO: course_id = None is wrong
      return await create_course_client(None,payload.deployment,None,None,payload.descendants)
    else:
      raise BadRequestException()

    if check_course_permissions(permissions,Course,"_maintainer",db).filter(Course.id == course_id).first() == None:
      raise NotFoundException()

    return await create_course_client(course_id,get_computor_deployment_from_course_id_db(course_id, db),None,None,payload.descendants)

class ReleaseCourseContentCreate(BaseModel):
    release_dir: Optional[str] = None
    course_id: Optional[UUID | str] = None
    gitlab_url: Optional[str] = None
    ascendants: bool = False
    descendants: bool = False
    release_dir_list: list[str] = []

@system_router.post("/release/course-contents", response_model=dict)
async def release_course_content(payload: ReleaseCourseContentCreate, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

    if payload.course_id != None:
      course_id = payload.course_id

    elif payload.gitlab_url != None:
      course_id = get_course_id_from_url(payload.gitlab_url,db)

    else:
      raise BadRequestException()

    if check_course_permissions(permissions,Course,"_maintainer",db).filter(Course.id == course_id).first() == None:
      raise NotFoundException()

    return await create_course_client(course_id, get_computor_deployment_from_course_id_db(course_id, db), payload.release_dir, payload.ascendants, payload.descendants,payload.release_dir_list)

class StatusQuery(BaseModel):
   course_id: Optional[str] = None

@system_router.get("/status/{flow_run_id}", response_model=dict)
async def system_job_status(flow_run_id: UUID | str, permissions: Annotated[Principal, Depends(get_current_permissions)], params: StatusQuery = Depends()):

    async with get_prefect_client() as client:
      if permissions.is_admin == True:
        flow_run = (await client.read_flow_run(flow_run_id))
      
      else:
        filter=FlowRunFilter()
        filter_id = FlowRunFilterId()
        filter_id.any_ = [flow_run_id]

        if params.course_id != None:
          with next(get_db()) as db:
            if params.course_id in get_permitted_course_ids(permissions,"_maintainer",db):
              
              filter_tags = FlowRunFilterTags()
              filter_tags.all_ = [f"course:{params.course_id}"]
              filter.tags = filter_tags
              filter.id = filter_id
            
            else:
               raise NotFoundException()
        else:
          filter_tags = FlowRunFilterTags()
          filter_tags.all_ = [f"user:{permissions.user_id}"]
          filter.tags = filter_tags
          filter.id = filter_id

        responses = (await client.read_flow_runs(flow_run_filter=filter))

        if len(responses) == 1:
          flow_run = responses[0]
        else:
          raise NotFoundException()

      response_dict = {"status": flow_run.state_type}

      if flow_run.state != None and flow_run.state.message != None:
        response_dict["message"] = flow_run.state.message

      return response_dict


# SYSTEM RESPONSE ROUTES - NOT CALLABLE FROM NON-SYSTEM CLIENTS

class CourseReleaseUpdate(BaseModel):
   course: Optional[CourseUpdate] = None
   course_content_types: list[CourseContentTypeCreate]

@system_router.patch("/release/courses/{course_id}/callback", response_model=bool)
async def release_course_response(
   background_tasks: BackgroundTasks, 
   course_id: UUID | str, 
   course_release_update: CourseReleaseUpdate, 
   permissions: Annotated[Principal, Depends(get_current_permissions)],
   cache: Annotated[BaseCache, Depends(get_redis_client)],
   db: Session = Depends(get_db)):

    if await get_id_db(permissions,db,course_id,CourseInterface,"update") == None:
       raise NotFoundException()

    ## UPDATE EXISTING COURSE

    course_db = db.query(Course).filter(Course.id == course_id).first()

    if course_db == None:
        raise NotFoundException()
    try:

      if course_release_update.course != None:
        course_update = course_release_update.course

        for key in course_update.model_fields_set:
          setattr(course_db, key, getattr(course_update,key))

      course_content_types = course_release_update.course_content_types

      content_by_kind = defaultdict(list)

      for content in course_content_types:
        kind_id = content.course_content_kind_id
        content_by_kind[kind_id].append(content)

      for kind, contents in content_by_kind.items():
        sync_dependent_items(
          dependents=[("course_id", course_id),("course_content_kind_id", kind)],
          dependent_items=contents,
          dependent_item_type=CourseContentType,
          foreign_key="slug",
          db=db)

      db.commit()

      await cache.clear(Course.__tablename__)
      await cache.clear(CourseContent.__tablename__)
      await cache.clear(CourseContentType.__tablename__)
      await cache.clear(CourseGroup.__tablename__)

      async def event_wrapper():
          try:
              await mirror_entity_to_filesystem(course_id,CourseInterface,db)
          except Exception as e:
              print(e)

      background_tasks.add_task(event_wrapper)

      return True

    except Exception as e:
       db.rollback()
       print(e.args)
       print(e.with_traceback())
       raise BadRequestException(e.args)