import json
import os
import shutil
import yaml
import asyncio
import tempfile
from typing import Callable
from prefect import task
from prefect.runtime import flow_run
from prefect.client.orchestration import get_client
from ctutor_backend.interface.tests import TestJob
from ctutor_backend.interface.results import ResultGet, ResultInterface, ResultQuery, ResultStatus, ResultUpdate
from ctutor_backend.client.crud_client import CrudClient

TEST_FILE_NAME = "test.yaml"
SPEC_FILE_NAME = "specification.yaml"
REPORT_FILE_NAME = "testSummary.json"

async def check_connection():
    print("Trying to connect to prefect server...")
    async with get_client() as client:

        await asyncio.sleep(5)

        for i in range(1,30):
            try:
                await client.hello()
                print(f"Connection attempt {i}: successful!")
                break
            except Exception as e:
                print(f"Connection attempt {i}: {e}")
                await asyncio.sleep(5)

def commit_results(flow_run_id: str, test_job: TestJob, result: ResultUpdate, url: str, username: str, password: str):

  headers = { "accept": "application/json",
              "Content-Type": "application/json" }

  client = CrudClient(url, ResultInterface, auth=(username,password), headers=headers)

  query = ResultQuery(
        test_system_id=flow_run_id,
        execution_backend_id=str(test_job.execution_backend_id),
        course_member_id=str(test_job.course_member_id),
        course_content_id=str(test_job.course_content_id))
  
  print(query)
  results = client.list(query)

  if len(results) > 1:
    raise Exception({"message": f"Found multiple results, database is probably broken."})
  elif len(results) == 0:
    raise Exception({"message": f"No result found, something went wrong"})
  
  result_get = results[0]

  try:
    response = CrudClient(url, ResultInterface, auth=(username,password)).update(str(result_get.id), result)

    return isinstance(response,ResultGet)

  except Exception as e:
    raise Exception({"message": f"Failed to call execution-backend api", "trace": str(e)})

def raise_git_clone_exception_result(title: str, exception: Exception | None = None):

    result_json = { "prefect_exception": "git clone failed", "message": f"Git clone of {title} repository failed." }

    # TODO: make sure that exception does not privide data which is not permitted to the course-member
    # if exception != None:
    #   result_json["exception"] = str(exception)

    return ResultUpdate(
        result_json=result_json,
        test_run_id=flow_run.get_id(),
        status=ResultStatus.FAILED)
    
def raise_exception_with_message_result(e: Exception, message: str):
    return ResultUpdate(
        result_json={ "prefect_exception": str(e), "message": message },
        test_run_id=flow_run.get_id(),
        status=ResultStatus.FAILED)

async def test_execution(
  test_job: TestJob,
  exec_testing_env: Callable
):
  
  if test_job.reference == None:
    return raise_exception_with_message_result({}, "No reference repository found in job payload." )

  with tempfile.TemporaryDirectory() as root_path:

    try:
      test_job.reference.clone(f"{root_path}/source")
    except Exception as e:
      return raise_git_clone_exception_result("reference", e)
    
    try:
      test_job.module.clone(f"{root_path}/student")
    except Exception as e:
      return raise_git_clone_exception_result("student", e)
    
    test_path = f"{root_path}/source/{test_job.reference.path}"
    student_path = f"{root_path}/student/{test_job.module.path}"

    artifacts_path = f"{root_path}/artifacts"
    test_files_path = f"{root_path}/test_files"
    output_path = f"{root_path}/output"
    reference_path = f"{test_path}"
    spec_file_path = f"{root_path}/{SPEC_FILE_NAME}"

    specfile_json = {
        "executionDirectory": student_path,
        "studentDirectory": student_path,
        "referenceDirectory": reference_path,
        "outputDirectory": output_path,
        "testDirectory": test_files_path,
        "artifactDirectory": artifacts_path,
        "studentTestCounter": 2,
        #"testVersion": "v1"
    }
    with open(spec_file_path, 'w') as yaml_file:
      yaml.dump(specfile_json, yaml_file)

    print(f"specification file => {json.dumps(specfile_json,indent=4)}")

    meta_info: dict = {}

    try:
      meta_filepath = os.path.join(reference_path,"meta.yaml")
      if os.path.exists(meta_filepath):
        with open(meta_filepath, "r") as meta_file:
          meta_info = yaml.safe_load(meta_file)
          print(f"meta.yaml => {json.dumps(meta_info,indent=4)}")
      else:
        print("meta.yaml does not exist!")
        raise Exception
    except Exception as e:
      print(f"Could not read meta.yaml, reason: {e}")

    mi_properties = meta_info.get("properties")

    try:
      if mi_properties != None:
        mi_test_files = mi_properties.get("testFiles")

        if mi_test_files != None:
          for test_file in mi_test_files:
            if not os.path.exists(test_files_path):
              os.makedirs(test_files_path)
            shutil.copyfile(os.path.join(reference_path,test_file),os.path.join(test_files_path,test_file))
    except Exception as e:
      print(f"Could not copy testFiles to destination directory, reason: {e}")

    try:
      result_report = await exec_testing_env(test_job,f"{test_path}/{TEST_FILE_NAME}",spec_file_path)
      
    except Exception as e:
      return raise_exception_with_message_result({}, "Testing environment failed" )

    if result_report == None:
      print(f"Read results from file '{output_path}/{REPORT_FILE_NAME}'")
      try:
        with open(f"{output_path}/{REPORT_FILE_NAME}", "r") as test_summary_file:
          result_report = json.load(test_summary_file)
        print(f"test results => {json.dumps(result_report,indent=4)}")
      except Exception as e:
        return raise_exception_with_message_result({}, f"Reading report file {REPORT_FILE_NAME} failed" )
    else:
      print(f"Taking results from function return value")
    
    # TODO: REFACTORING
    try:
      result_value = result_report["summary"]["passed"] / result_report["summary"]["total"]
    except:
      result_value = 0.0

    return ResultUpdate(
      result=result_value,
      result_json=result_report,
      test_run_id=flow_run.get_id(),
      status=ResultStatus.COMPLETED
    )

@task(log_prints=True)
async def student_test_flow(
  test_job: TestJob,
  exec_testing_env: Callable
):

  EXECUTION_BACKEND_API_URL = os.environ.get("EXECUTION_BACKEND_API_URL")
  EXECUTION_BACKEND_USER = os.environ.get("EXECUTION_BACKEND_API_USER")
  EXECUTION_BACKEND_PASSWORD = os.environ.get("EXECUTION_BACKEND_API_PASSWORD")

  try:
    result = await test_execution(
      test_job,
      exec_testing_env
    )
  except Exception as e:
    result = raise_exception_with_message_result({}, "Task sumbission failed")

  try:
    commit_results(
      flow_run.get_id(),
      test_job=test_job,
      result=result,
      url=EXECUTION_BACKEND_API_URL,
      username=EXECUTION_BACKEND_USER,
      password=EXECUTION_BACKEND_PASSWORD)
    return result
  except Exception as e:
    raise Exception(
    {
      "message": "Committing results to API failed",
      "trace": str(e),
      "inner": e
    })