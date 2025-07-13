"""
Student test execution tasks for the task executor framework.

These tasks replace Prefect flows for handling student test submissions.
"""

import json
import os
import shutil
import yaml
import tempfile
from typing import Any, Dict, Callable, Optional
from datetime import datetime

from ctutor_backend.interface.tests import TestJob
from ctutor_backend.interface.results import ResultUpdate, ResultStatus
from ctutor_backend.client.crud_client import CrudClient
from ctutor_backend.interface.results import ResultInterface, ResultQuery, ResultGet

from .base import BaseTask
from .registry import register_task


@register_task
class StudentTestExecutionTask(BaseTask):
    """
    Task for executing student test submissions.
    
    This task replaces the Prefect-based student test execution flow
    with a Redis Queue implementation that provides better integration
    with FastAPI and more granular control.
    """
    
    @property
    def name(self) -> str:
        return "student_test_execution"
    
    @property
    def timeout(self) -> int:
        return 1800  # 30 minutes for test execution
    
    @property
    def retry_limit(self) -> int:
        return 2  # Allow 2 retries for transient failures
    
    async def execute(self, 
                     test_job_data: Dict[str, Any],
                     execution_backend_callable: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute student test submission.
        
        Args:
            test_job_data: Serialized TestJob data
            execution_backend_callable: Name of execution backend function
            
        Returns:
            Test execution results
        """
        # Deserialize test job
        test_job = TestJob(**test_job_data)
        
        # Execute the test
        result = await self._execute_test(test_job)
        
        # Commit results to API
        success = await self._commit_results(test_job, result)
        
        return {
            "test_job_id": test_job_data.get("id"),
            "execution_result": result.dict() if hasattr(result, 'dict') else result,
            "api_commit_success": success,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    async def _execute_test(self, test_job: TestJob) -> ResultUpdate:
        """
        Execute the actual test logic.
        
        Args:
            test_job: Test job configuration
            
        Returns:
            Test result update
        """
        TEST_FILE_NAME = "test.yaml"
        SPEC_FILE_NAME = "specification.yaml"
        REPORT_FILE_NAME = "testSummary.json"
        
        if test_job.reference is None:
            return self._create_error_result(
                "No reference repository found in job payload."
            )
        
        with tempfile.TemporaryDirectory() as root_path:
            try:
                # Clone reference repository
                try:
                    test_job.reference.clone(f"{root_path}/source")
                except Exception as e:
                    return self._create_git_clone_error_result("reference", e)
                
                # Clone student repository
                try:
                    test_job.module.clone(f"{root_path}/student")
                except Exception as e:
                    return self._create_git_clone_error_result("student", e)
                
                # Set up directory paths
                test_path = f"{root_path}/source/{test_job.reference.path}"
                student_path = f"{root_path}/student/{test_job.module.path}"
                artifacts_path = f"{root_path}/artifacts"
                test_files_path = f"{root_path}/test_files"
                output_path = f"{root_path}/output"
                reference_path = f"{test_path}"
                spec_file_path = f"{root_path}/{SPEC_FILE_NAME}"
                
                # Create specification file
                specfile_json = {
                    "executionDirectory": student_path,
                    "studentDirectory": student_path,
                    "referenceDirectory": reference_path,
                    "outputDirectory": output_path,
                    "testDirectory": test_files_path,
                    "artifactDirectory": artifacts_path,
                    "studentTestCounter": 2,
                }
                
                with open(spec_file_path, 'w') as yaml_file:
                    yaml.dump(specfile_json, yaml_file)
                
                # Read meta information
                meta_info = await self._read_meta_info(reference_path)
                
                # Copy test files
                await self._copy_test_files(meta_info, reference_path, test_files_path)
                
                # Execute testing environment
                # Note: This would need to be implemented based on the specific
                # execution backend (Docker, local, etc.)
                result_report = await self._execute_testing_environment(
                    test_job, f"{test_path}/{TEST_FILE_NAME}", spec_file_path
                )
                
                if result_report is None:
                    # Read results from file
                    try:
                        with open(f"{output_path}/{REPORT_FILE_NAME}", "r") as test_summary_file:
                            result_report = json.load(test_summary_file)
                    except Exception as e:
                        return self._create_error_result(
                            f"Reading report file {REPORT_FILE_NAME} failed"
                        )
                
                # Calculate result value
                try:
                    result_value = result_report["summary"]["passed"] / result_report["summary"]["total"]
                except:
                    result_value = 0.0
                
                return ResultUpdate(
                    result=result_value,
                    result_json=result_report,
                    test_run_id=f"task-{datetime.utcnow().timestamp()}",
                    status=ResultStatus.COMPLETED
                )
                
            except Exception as e:
                return self._create_error_result("Test execution failed", e)
    
    async def _read_meta_info(self, reference_path: str) -> Dict[str, Any]:
        """Read meta.yaml information from reference repository."""
        meta_info = {}
        try:
            meta_filepath = os.path.join(reference_path, "meta.yaml")
            if os.path.exists(meta_filepath):
                with open(meta_filepath, "r") as meta_file:
                    meta_info = yaml.safe_load(meta_file)
        except Exception as e:
            print(f"Could not read meta.yaml, reason: {e}")
        return meta_info
    
    async def _copy_test_files(self, meta_info: Dict[str, Any], 
                              reference_path: str, test_files_path: str) -> None:
        """Copy test files based on meta information."""
        try:
            properties = meta_info.get("properties")
            if properties is not None:
                test_files = properties.get("testFiles")
                if test_files is not None:
                    for test_file in test_files:
                        if not os.path.exists(test_files_path):
                            os.makedirs(test_files_path)
                        shutil.copyfile(
                            os.path.join(reference_path, test_file),
                            os.path.join(test_files_path, test_file)
                        )
        except Exception as e:
            print(f"Could not copy testFiles to destination directory, reason: {e}")
    
    async def _execute_testing_environment(self, 
                                          test_job: TestJob,
                                          test_file_path: str,
                                          spec_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Execute the testing environment.
        
        This is a placeholder that should be implemented based on the specific
        execution backend configuration.
        """
        # This would be implemented based on the execution backend
        # For now, return None to indicate file-based result reading
        return None
    
    async def _commit_results(self, test_job: TestJob, result: ResultUpdate) -> bool:
        """
        Commit test results to the API.
        
        Args:
            test_job: Original test job
            result: Test execution result
            
        Returns:
            True if commit successful, False otherwise
        """
        try:
            EXECUTION_BACKEND_API_URL = os.environ.get("EXECUTION_BACKEND_API_URL")
            EXECUTION_BACKEND_USER = os.environ.get("EXECUTION_BACKEND_API_USER")
            EXECUTION_BACKEND_PASSWORD = os.environ.get("EXECUTION_BACKEND_API_PASSWORD")
            
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
            }
            
            client = CrudClient(
                EXECUTION_BACKEND_API_URL, 
                ResultInterface, 
                auth=(EXECUTION_BACKEND_USER, EXECUTION_BACKEND_PASSWORD), 
                headers=headers
            )
            
            # Find existing result
            query = ResultQuery(
                test_system_id=result.test_run_id,
                execution_backend_id=str(test_job.execution_backend_id),
                course_member_id=str(test_job.course_member_id),
                course_content_id=str(test_job.course_content_id)
            )
            
            results = client.list(query)
            
            if len(results) > 1:
                raise Exception("Found multiple results, database is probably broken.")
            elif len(results) == 0:
                raise Exception("No result found, something went wrong")
            
            result_get = results[0]
            
            # Update result
            response = CrudClient(
                EXECUTION_BACKEND_API_URL, 
                ResultInterface, 
                auth=(EXECUTION_BACKEND_USER, EXECUTION_BACKEND_PASSWORD)
            ).update(str(result_get.id), result)
            
            return isinstance(response, ResultGet)
            
        except Exception as e:
            print(f"Failed to commit results: {str(e)}")
            return False
    
    def _create_error_result(self, message: str, exception: Optional[Exception] = None) -> ResultUpdate:
        """Create error result for failed operations."""
        result_json = {
            "task_exception": message,
            "message": message
        }
        
        if exception is not None:
            result_json["exception_type"] = type(exception).__name__
            # Don't include full exception details for security
        
        return ResultUpdate(
            result_json=result_json,
            test_run_id=f"task-{datetime.utcnow().timestamp()}",
            status=ResultStatus.FAILED
        )
    
    def _create_git_clone_error_result(self, title: str, exception: Optional[Exception] = None) -> ResultUpdate:
        """Create error result for git clone failures."""
        result_json = {
            "task_exception": "git clone failed",
            "message": f"Git clone of {title} repository failed."
        }
        
        return ResultUpdate(
            result_json=result_json,
            test_run_id=f"task-{datetime.utcnow().timestamp()}",
            status=ResultStatus.FAILED
        )
    
    async def on_success(self, result: Any, **kwargs) -> None:
        """Handle successful test execution."""
        print(f"Student test execution completed successfully")
        print(f"Results: {result}")
    
    async def on_failure(self, error: Exception, **kwargs) -> None:
        """Handle test execution failure."""
        print(f"Student test execution failed: {str(error)}")
        # Could implement notification logic here