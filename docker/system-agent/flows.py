import os
import asyncio
import tempfile
from prefect import flow, task
from prefect.deployments import Deployment
from ctutor_backend.api.system import ReleaseStudentsCreate
from ctutor_backend.api.tests import create_submission
from ctutor_backend.api.utils import collect_sub_path_positions_if_meta_exists
from ctutor_backend.flows.utils import check_connection
from ctutor_backend.interface.deployments import CodeabilityReleaseBuilder
from ctutor_backend.generator.gitlab_builder import CodeabilityGitlabBuilder
from ctutor_backend.interface.deployments import ApiConfig, ComputorDeploymentConfig
from ctutor_backend.interface.tests import Submission

DEPLOYMENT_NAME = "system"
DEPLOYMENT_STORAGE = None
WORK_QUEUE_NAME = os.environ.get("PREFECT_WORK_QUEUE","system-queue")
INFRA_OVERRIDES = {}

EXECUTION_BACKEND_API_URL = os.environ.get("EXECUTION_BACKEND_API_URL")
EXECUTION_BACKEND_API_USER = os.environ.get("EXECUTION_BACKEND_API_USER")
EXECUTION_BACKEND_API_PASSWORD = os.environ.get("EXECUTION_BACKEND_API_PASSWORD")

def convert_to_gitlab_paths(release_dir_list: list[str]) -> list[str]:
    gitlab_paths = []

    for path in release_dir_list:
        converted_path = path.replace("\\", "/")
        
        if path[1:3] == ":\\":
            raise ValueError(f"Invalid path: {path} - Path cannot start with a drive letter.")

        path = path.lstrip("\\/")

        gitlab_paths.append(path.replace("\\", "/"))

    return gitlab_paths

def get_worker_api_deployment():

    return ApiConfig(url=EXECUTION_BACKEND_API_URL,user=EXECUTION_BACKEND_API_USER,password=EXECUTION_BACKEND_API_PASSWORD)

def get_builder(deployment: ComputorDeploymentConfig, work_dir: str) -> CodeabilityReleaseBuilder:

    if deployment.organization.gitlab != None:
        return CodeabilityGitlabBuilder(get_worker_api_deployment(), deployment, work_dir)

    # elif deployment.organization.github != None:
    #     raise NotImplementedError()

    else:
        raise NotImplementedError()

@task(log_prints=True)
async def release_student_task(deployment: ComputorDeploymentConfig, payload: ReleaseStudentsCreate):

    with tempfile.TemporaryDirectory() as tmp:
        builder = get_builder(deployment,tmp)

        for student in payload.students:
            try:
                course_member = await builder.create_student_project(student.user,student.course_group_id,student.role)

                print(f"imported student => {course_member.model_dump_json(indent=4)}")

            except Exception as e:
                print(f"imported student failed => {course_member.model_dump_json(indent=4)}")
                print(e)

@flow(name="release-student", log_prints=True, persist_result=True)
async def release_student_flow(deployment: ComputorDeploymentConfig, payload: ReleaseStudentsCreate):

    await release_student_task.submit(deployment,payload)

@flow(name="release-course", log_prints=True, persist_result=True)
def release_course_flow(deployment: ComputorDeploymentConfig, release_dir: str | None = None, ascendants: bool = False, descendants: bool = False, release_dir_list: list[str] = []):

    with tempfile.TemporaryDirectory() as tmp:
        builder = get_builder(deployment,tmp)

        if len(release_dir_list) > 0:

            release_dir_list = convert_to_gitlab_paths(release_dir_list)

            error_log = []    
            if any(len(s) == 0 for s in release_dir_list):
                error_log.extend(builder.create_course_release())
                release_dir_list.remove("")

                if len(error_log) > 0:
                    raise Exception(error_log)
    
            for dir in release_dir_list:
                error_log.extend(builder.create_release(dir))

                if len(error_log) > 0:
                    raise Exception(error_log)
            
            return True

        else:
            # CASE: course-content
            if release_dir != None:
                if ascendants == True:
                    parts = release_dir.split("/")
                    past_part = None
                    
                    for part in parts:
                        if past_part == None:
                            past_part = part
                        else:
                            past_part = f"{past_part}/{part}"
                        error_log = builder.create_release(past_part)

                error_log = builder.create_release(release_dir)

                if descendants == True:

                    path_desc = builder.get_directory_testing()

                    data = collect_sub_path_positions_if_meta_exists(os.path.join(path_desc,release_dir))

                    for d in data:
                        error_log = builder.create_release(os.path.join(release_dir,d[0]))

            # CASE: course
            else:
                error_log = builder.create_course_release()

                if descendants == True:
                    data = collect_sub_path_positions_if_meta_exists(builder.get_directory_testing())

                    for d in data:
                        error_log = builder.create_release(d[0])

            if len(error_log) > 0:
                raise Exception(error_log)
            else:
                return True

@task(log_prints=True)
def submit_result_task(submission: Submission):
    create_submission(submission)

@flow(name="submit-result", log_prints=True, persist_result=True)
def submit_result_flow(submission: Submission):
    submit_result_task.submit(submission)

if __name__ ==  '__main__':
    asyncio.run(check_connection())

    system_flows = [release_student_flow, release_course_flow,submit_result_flow]

    for system_flow in system_flows:
        Deployment.build_from_flow(
            name=DEPLOYMENT_NAME,
            flow=system_flow,
            work_queue_name=WORK_QUEUE_NAME,
            infra_overrides=INFRA_OVERRIDES,
            storage=DEPLOYMENT_STORAGE
        ).apply()

    print(f"Deployment successful!")