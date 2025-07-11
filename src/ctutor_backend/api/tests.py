import os
import shutil
import tempfile
from typing import Annotated, Optional
from fastapi import Depends, APIRouter, BackgroundTasks
from gitlab import Gitlab
from gitlab.v4.objects import Project
from sqlalchemy import func
from sqlalchemy.orm import Session
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.crud import create_db
from ctutor_backend.api.exceptions import BadRequestException, InternalServerException, NotFoundException, NotImplementedException
from ctutor_backend.api.permissions import check_course_permissions
from ctutor_backend.api.results import get_result_status
from ctutor_backend.client.crud_client import CrudClient
from ctutor_backend.database import get_db
from ctutor_backend.generator.git_helper import checkout_branch, git_repo_commit
from ctutor_backend.interface.course_contents import CourseContentGet
from ctutor_backend.interface.course_members import CourseMemberProperties
from ctutor_backend.interface.courses import CourseProperties
from ctutor_backend.interface.organizations import OrganizationProperties
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.repositories import Repository
from ctutor_backend.interface.results import ResultCreate, ResultGet, ResultInterface, ResultStatus, ResultUpdate
from ctutor_backend.interface.tests import Submission, TestCreate, TestJob
from ctutor_backend.interface.tokens import decrypt_api_key
ntent, CourseContentType, CourseExecutionBackend, CourseMember, CourseSubmissionGroup, CourseSubmissionGroupMember, ExecutionBackend, Result, Course, CourseFamily, Organization, User
from prefect.client.orchestration import PrefectClient
from sqlalchemy_utils import Ltree
from ctutor_backend.settings import settings
from ctutor_backend.utils import get_prefect_client

def handle_merge_request(submission: Submission, branch: str, title: str) -> bool:

  gl = Gitlab(url=submission.provider,private_token=submission.token)

  subm_repo = submission.full_path

  gitlab_projects = gl.projects.list(search=subm_repo, search_namespaces=True)

  if len(gitlab_projects) != 1:
    raise Exception("The project does not exist")
  
  submission_project: Project = gitlab_projects[0]

  found_mrs = submission_project.mergerequests.list(source_branch=branch)

  if len(found_mrs) > 1:
    raise Exception("[handle_merge_request] This is a critical error")
  elif len(found_mrs) == 0:

    merge_request = submission_project.mergerequests.create(
      {
        "id": submission_project.get_id(),
        "source_branch": branch,
        "target_branch": "main",
        "target_project_id": submission_project.get_id(),
        "title": title
      }
    )

    print(f"new merge request created [{branch}]")

    return True

  else:
    merge_request = found_mrs[0]

    if merge_request.state == "merged":

      submission_project.mergerequests.update(merge_request.get_id(),{"state_event": "reopen"})

      print(f"Merge request [{branch}] already merged")

      return False
    else:
      print(f"show merge request [{branch}]")

      return True

def copy_subdirectory(source,destination,directory):
  source_path = os.path.join(source, directory)
  destination_path = os.path.join(destination, directory)

  if os.path.exists(destination_path):
    shutil.rmtree(destination_path)
  os.makedirs(destination_path)

  for item in os.listdir(source_path):
    s_item = os.path.join(source_path, item)
    d_item = os.path.join(destination_path, item)
    if os.path.isdir(s_item):
      shutil.copytree(s_item, d_item)
    else:
      shutil.copy2(s_item, d_item)

def create_submission(submission: Submission):

  if submission == None:
    raise Exception("[create_submission_flow] Submission is None")
  
  assignment_dir = submission.assignment.properties.gitlab.directory

  branch = f"submission/{submission.assignment.path}"
  title = f"Submission: {submission.assignment.path}"

  with tempfile.TemporaryDirectory() as root_path:

    student_work_dir = f"{root_path}/student"
    submission_work_dir = f"{root_path}/submission"

    submission.module.clone(student_work_dir)

    submission.submission.clone(submission_work_dir)


    checkout_branch(submission_work_dir,"main")
  
    checkout_branch(submission_work_dir,branch)

    copy_subdirectory(student_work_dir,submission_work_dir,assignment_dir)

    git_repo_commit(submission_work_dir, f"submission: {submission.assignment.path}", branch)

    accepted = handle_merge_request(submission, branch, title)

    if not accepted:
      raise Exception("Merge request Failed")

  try:
    CrudClient(
        url_base=os.environ.get("EXECUTION_BACKEND_API_URL"),
        auth=(os.environ.get("EXECUTION_BACKEND_API_USER"),os.environ.get("EXECUTION_BACKEND_API_PASSWORD")),
        entity_interface=ResultInterface).update(submission.result_id,ResultUpdate(submit=True))
  except Exception as e:
    print(str(e))
    print("Error in crud client updating submit boolen for result")


# TODO: REFACTORING
async def prefect_test_job(test_job: TestJob, properties: dict) -> str:
  
    if settings.DEBUG_MODE == "production":
      prefect_url = properties["url"]
    else:
      prefect_url = "http://localhost:4200/api"

    async with PrefectClient(prefect_url) as client:
      
      try:
        deployment = await client.read_deployment_by_name(properties["deployment"])
      except:
        raise NotFoundException(detail=f"Worker [{properties['deployment']}] is currently not available. Please wait a moment!")
      
      try:
        flow_run = await client.create_flow_run_from_deployment(
          deployment_id=deployment.id,
          parameters={
            "test_job": test_job.model_dump(exclude_none=True)
          },
          tags=[f"user:{test_job.user_id}"]
        )

        return str(flow_run.id)

      except:
        raise BadRequestException()

async def submission_job(submission: Submission):

  async with get_prefect_client() as client:

    deployment = await client.read_deployment_by_name("submit-result/system")

    try:
      flow_run = await client.create_flow_run_from_deployment(
        deployment_id=deployment.id,
        parameters={
          "submission": submission.model_dump(exclude_none=True)
        },
        tags=[f"user:{submission.user_id}"]
      )

      return str(flow_run.id)

    except:
      raise BadRequestException()

class TestRunResponse(ResultCreate):
  id: str
  submission_flow_run_id: Optional[str | None] = None

tests_router = APIRouter()

@tests_router.post("", response_model=TestRunResponse)
async def create_test(test_create: TestCreate, background_tasks: BackgroundTasks, permissions: Annotated[Principal, Depends(get_current_permissions)], db: Session = Depends(get_db)):

  user_id = permissions.user_id

  if test_create.provider_url == None or test_create.project == None:
    course_member = db.query(CourseMember).join(User, User.id == CourseMember.user_id).filter(User.id == user_id).first()

  else:
    course_member = check_course_permissions(permissions,CourseMember,"_student",db) \
      .filter(
        CourseMember.properties["gitlab"].op("->>")("url") == test_create.provider_url,
        CourseMember.properties["gitlab"].op("->>")("full_path") == test_create.project
      ).first()

  course_member_id = course_member.id
  course_member_properties = CourseMemberProperties(**course_member.properties)

  results_count_subquery = (
      db.query(
          Result.course_content_id,
          func.count(Result.id).label("total_results_count")
      )
      .group_by(Result.course_content_id)
      .subquery()
  )

  joined_query = db.query(CourseContent,Course,Organization,CourseSubmissionGroup.max_submissions,results_count_subquery.c.total_results_count) \
      .join(CourseContentType, CourseContentType.id == CourseContent.course_content_type_id) \
        .join(Course,Course.id == CourseContent.course_id) \
          .join(CourseMember, CourseMember.course_id == Course.id) \
            .join(CourseFamily, CourseFamily.id == Course.course_family_id) \
              .join(Organization, Organization.id == CourseFamily.organization_id) \
                .join(CourseExecutionBackend, CourseExecutionBackend.course_id == CourseContent.course_id) \
                  .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == CourseMember.id) \
                    .join(CourseSubmissionGroup, CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
                  .outerjoin(
                    results_count_subquery,
                    (CourseContent.id == results_count_subquery.c.course_content_id)
                  ).filter(Course.id == course_member.course_id, CourseMember.id == course_member_id)

  if test_create.course_content_id != None:

    query_result = joined_query.filter(CourseContent.id == test_create.course_content_id, CourseContentType.course_content_kind_id == "assignment").first()

  elif test_create.course_content_path != None:

    query_result = joined_query.filter(CourseContent.path == Ltree(test_create.course_content_path), CourseContentType.course_content_kind_id == "assignment").first()

  elif test_create.directory != None:

    # new_parts = []
    
    # for part in test_create.directory.split("/"):
    #   new_parts.append(position_directory_to_db_path(part))
    query_result = joined_query.filter(
      CourseContent.properties["gitlab"].op("->>")("directory") == test_create.directory, 
      CourseContentType.course_content_kind_id == "assignment"
    ).first()
    # query_result = joined_query.filter(CourseContent.path == Ltree(".".join(new_parts)), CourseContentType.course_content_kind_id == "assignment").first()
  
  submissions = query_result[4] if query_result[4] != None else 0
  allowed_max_submissions = query_result[3]

  if allowed_max_submissions is not None and submissions >= allowed_max_submissions:
    raise BadRequestException(detail="Reached max submissions for this course_content")

  try:
    assignment = CourseContentGet(**query_result[0].__dict__)
    print(assignment.model_dump_json(indent=4))
  except:
    raise BadRequestException(detail="CourseContent of kind 'unit' could not be released.")

  course = query_result[1]
  organization = query_result[2]
  
  organization_properties = OrganizationProperties(**organization.properties)
  course_properties = CourseProperties(**course.properties)
  assignment_properties = assignment.properties
  execution_backend_id = assignment.execution_backend_id

  commit = test_create.version_identifier

  if commit == None:
    raise BadRequestException(detail="commit is None")

  results = db.query(Result) \
      .select_from(CourseSubmissionGroup) \
        .join(CourseContent, CourseContent.id == CourseSubmissionGroup.course_content_id) \
          .join(Result,Result.course_content_id == CourseSubmissionGroup.course_content_id) \
            .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) \
  .filter(
      CourseSubmissionGroupMember.course_member_id == course_member_id,
      CourseContent.id == assignment.id,
      Result.version_identifier == commit
    ).all()

  course_submission_group_id = db.query(CourseSubmissionGroup.id) \
      .join(CourseSubmissionGroupMember,CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .filter(CourseSubmissionGroupMember.course_member_id == course_member_id, CourseSubmissionGroupMember.course_content_id == assignment.id).scalar()

  if len(results) > 1:
    raise InternalServerException(f"More than one Result with commit [{commit}] for this Assignment. This is a critical database error, please inform your admin.")

  # if gitlab
  if course_member_properties.gitlab != None:

    provider = organization_properties.gitlab.url
    full_path_course = course_properties.gitlab.full_path
    assignment_directory = assignment_properties.gitlab.directory
    token = decrypt_api_key(organization_properties.gitlab.token)

    full_path_module = course_member_properties.gitlab.full_path
    full_path_reference = f"{full_path_course}/assignments"
    
    gitlab_path_module = f"{provider}/{full_path_module}.git"
    gitlab_path_reference = f"{provider}/{full_path_reference}.git"

    student_repository = Repository(
        url=gitlab_path_module,
        path=assignment_directory,
        token=token,
        commit=commit
    )
    reference_repository = Repository(
        url=gitlab_path_reference,
        path=assignment_directory,
        token=token,
        commit=assignment.version_identifier
    )

    def create_submission(assignment, result_id: str):
      full_path_submission = course_member_properties.gitlab.full_path_submission

      if full_path_submission == None:
        raise BadRequestException(detail=f"CourseMember has no submission repository.")

      gitlab_path_submission = f"{provider}/{full_path_submission}.git"

      return Submission(
        assignment=assignment,
        submission=Repository(
          url=gitlab_path_submission,
          token=token,
        ),
        provider=provider,
        full_path=full_path_submission,
        token=token,
        module=student_repository,
        result_id=result_id,
        user_id=user_id
      )


    job = TestJob(
      user_id=user_id,
      course_member_id=str(course_member_id),
      course_content_id=str(assignment.id),
      execution_backend_id=str(execution_backend_id),
      module=student_repository,
      reference=reference_repository
    )
  else:
    raise NotImplementedException()

  ##
  
  submission_flow_run_id = None

  if len(results) == 1:
    result: Result = results[0]

    if ResultStatus(result.status) != ResultStatus.COMPLETED:
      try:
        status = await get_result_status(results[0])
      except:
        status = ResultStatus.NOT_AVAILABLE
      
      result.status = status.value
      if ResultStatus(status) in [ResultStatus.FAILED,ResultStatus.CRASHED,ResultStatus.CANCELLING,ResultStatus.CANCELLED,ResultStatus.NOT_AVAILABLE]:
        result.version_identifier = f"{result.version_identifier}:{status}"

      db.commit()
      db.refresh(result)

    status = result.status

    if ResultStatus(status) in [ResultStatus.PENDING,ResultStatus.SCHEDULED,ResultStatus.RUNNING,ResultStatus.PAUSED]:
      return TestRunResponse(**result.__dict__)

    if ResultStatus(status) == ResultStatus.COMPLETED:
      if result.submit == True and test_create.submit == True:
        return TestRunResponse(**result.__dict__)

      elif result.submit == False and test_create.submit == True and result.status == 0:
        submission_flow_run_id = await submission_job(create_submission(assignment,str(result.id)))

      return TestRunResponse(submission_flow_run_id=submission_flow_run_id,**result.__dict__)

  ##

  execution_backend = db.query(ExecutionBackend) \
    .filter(ExecutionBackend.id == execution_backend_id).first()

  if execution_backend.type == "prefect_builtin":
    test_system_id = await prefect_test_job(job, execution_backend.properties) # TODO: why not using course_execution_backend.properties?
  else:
    raise BadRequestException("execution_backend type not supported!")
    
  try:
    # print("[ResultCreate] start ")
    result_create = Result(
        submit=0,
        course_member_id=course_member_id,
        course_submission_group_id=course_submission_group_id,
        course_content_id=assignment.id,
        execution_backend_id=execution_backend.id,
        test_system_id=test_system_id,
        result=0,
        result_json=None,
        properties=None,
        status=ResultStatus.SCHEDULED,
        version_identifier=commit
    )

    db.add(result_create)
    db.commit()

    if test_create.submit == True:
      submission_flow_run_id = await submission_job(create_submission(assignment,str(result_create.id)))

    return TestRunResponse(
      submission_flow_run_id=submission_flow_run_id,
        id = result_create.id,
        submit=result_create.submit,
        course_member_id=result_create.course_member_id,
        course_submission_group_id=result_create.course_submission_group_id,
        course_content_id=result_create.course_content_id,
        execution_backend_id=result_create.execution_backend_id,
        test_system_id=result_create.test_system_id,
        result=result_create.result,
        result_json=result_create.result_json,
        properties=result_create.properties,
        status=result_create.status,
        version_identifier=result_create.version_identifier
    )
  
  except Exception as e:
    print(e.with_traceback(None))
    print(f"[ResultCreate] {e.args}")
    raise e