"""
Advanced student testing tasks for Celery execution.

This module implements the actual Celery tasks that replace Prefect flows
for student test execution and submission processing.
"""

import os
import json
import asyncio
import tempfile
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime

from ctutor_backend.tasks.base import BaseTask
from ctutor_backend.tasks.registry import register_task
from ctutor_backend.tasks.celery_app import app
from ctutor_backend.tasks.executor import _execute_task_with_celery
from ctutor_backend.interface.repositories import Repository
from ctutor_backend.interface.tests import TestJob, Submission


@register_task
class StudentTestingTask(BaseTask):
    """
    Execute student testing workflow.
    
    This task handles the complete student testing process including:
    - Repository cloning and setup
    - Test execution in isolated environment
    - Result collection and reporting
    """
    
    @property
    def name(self) -> str:
        return "student_testing"
    
    @property
    def timeout(self) -> int:
        return 1800  # 30 minutes for complex tests
    
    async def execute(self, test_job: Dict[str, Any], execution_backend_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute student testing workflow.
        
        Args:
            test_job: TestJob configuration as dict
            execution_backend_properties: Backend configuration
            
        Returns:
            Test execution results
        """
        started_at = datetime.utcnow()
        
        try:
            # Parse test job configuration
            job_config = TestJob(**test_job)
            
            # Update progress
            await self.update_progress(10, {"status": "initializing", "stage": "setup"})
            
            # Create temporary working directory
            with tempfile.TemporaryDirectory() as work_dir:
                # Clone repositories
                await self.update_progress(20, {"status": "cloning", "stage": "repositories"})
                
                student_repo_path = os.path.join(work_dir, "student")
                reference_repo_path = os.path.join(work_dir, "reference")
                
                await self._clone_repository(job_config.module, student_repo_path)
                await self._clone_repository(job_config.reference, reference_repo_path)
                
                # Setup test environment
                await self.update_progress(40, {"status": "setting_up", "stage": "environment"})
                
                test_results = await self._execute_tests(
                    student_repo_path, 
                    reference_repo_path, 
                    job_config,
                    execution_backend_properties
                )
                
                # Process and validate results
                await self.update_progress(80, {"status": "processing", "stage": "results"})
                
                final_results = await self._process_test_results(test_results, job_config)
                
                await self.update_progress(100, {"status": "completed", "stage": "finished"})
                
                finished_at = datetime.utcnow()
                duration = (finished_at - started_at).total_seconds()
                
                return {
                    "success": True,
                    "results": final_results,
                    "execution_time": duration,
                    "started_at": started_at.isoformat(),
                    "finished_at": finished_at.isoformat(),
                    "user_id": job_config.user_id,
                    "course_member_id": job_config.course_member_id,
                    "course_content_id": job_config.course_content_id
                }
                
        except Exception as e:
            await self.update_progress(100, {
                "status": "failed", 
                "error": str(e),
                "stage": "error"
            })
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.utcnow() - started_at).total_seconds(),
                "started_at": started_at.isoformat(),
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def _clone_repository(self, repository: Repository, target_path: str):
        """Clone a Git repository to target path."""
        try:
            # Use repository's clone method
            repository.clone(target_path)
            
            # Checkout specific commit if provided
            if repository.commit:
                await self._run_git_command(target_path, ["checkout", repository.commit])
                
        except Exception as e:
            raise Exception(f"Failed to clone repository {repository.url}: {str(e)}")
    
    async def _run_git_command(self, repo_path: str, git_args: list) -> str:
        """Run a git command in the specified repository."""
        cmd = ["git", "-C", repo_path] + git_args
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Git command failed: {stderr.decode()}")
                
            return stdout.decode()
            
        except Exception as e:
            raise Exception(f"Failed to run git command {' '.join(cmd)}: {str(e)}")
    
    async def _execute_tests(
        self, 
        student_path: str, 
        reference_path: str, 
        job_config: TestJob,
        backend_properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the actual tests comparing student and reference implementations.
        
        This method would typically:
        1. Run tests defined in the reference repository
        2. Compare student output with expected output
        3. Generate test reports and scores
        """
        await self.update_progress(50, {"status": "executing", "stage": "tests"})
        
        try:
            # Example test execution - replace with actual testing logic
            test_script_path = os.path.join(reference_path, "test_runner.py")
            
            if os.path.exists(test_script_path):
                # Run Python test script
                result = await self._run_python_tests(test_script_path, student_path, reference_path)
            else:
                # Run default comparison tests
                result = await self._run_default_tests(student_path, reference_path)
                
            await self.update_progress(70, {"status": "executing", "stage": "validation"})
            
            return result
            
        except Exception as e:
            raise Exception(f"Test execution failed: {str(e)}")
    
    async def _run_python_tests(self, test_script: str, student_path: str, reference_path: str) -> Dict[str, Any]:
        """Run Python-based test script."""
        try:
            cmd = [
                "python", test_script,
                "--student-path", student_path,
                "--reference-path", reference_path,
                "--format", "json"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=reference_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                try:
                    result = json.loads(stdout.decode())
                    return result
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "score": 100,
                        "output": stdout.decode(),
                        "tests_passed": True
                    }
            else:
                return {
                    "success": False,
                    "score": 0,
                    "error": stderr.decode(),
                    "output": stdout.decode(),
                    "tests_passed": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "score": 0,
                "error": str(e),
                "tests_passed": False
            }
    
    async def _run_default_tests(self, student_path: str, reference_path: str) -> Dict[str, Any]:
        """Run default file comparison tests."""
        try:
            # Simple file comparison example
            # In practice, this would be more sophisticated
            
            student_files = set(os.listdir(student_path))
            reference_files = set(os.listdir(reference_path))
            
            # Check if required files exist
            missing_files = reference_files - student_files
            extra_files = student_files - reference_files
            
            score = 100
            if missing_files:
                score -= len(missing_files) * 20
            if extra_files:
                score -= len(extra_files) * 5
                
            score = max(0, score)  # Don't go below 0
            
            return {
                "success": score > 0,
                "score": score,
                "missing_files": list(missing_files),
                "extra_files": list(extra_files),
                "tests_passed": score >= 60
            }
            
        except Exception as e:
            return {
                "success": False,
                "score": 0,
                "error": str(e),
                "tests_passed": False
            }
    
    async def _process_test_results(self, test_results: Dict[str, Any], job_config: TestJob) -> Dict[str, Any]:
        """Process and format final test results."""
        
        # Calculate final grade/score
        final_score = test_results.get("score", 0)
        tests_passed = test_results.get("tests_passed", False)
        
        # Generate detailed report
        report = {
            "score": final_score,
            "max_score": 100,
            "percentage": final_score,
            "passed": tests_passed,
            "details": test_results,
            "timestamp": datetime.utcnow().isoformat(),
            "job_info": {
                "user_id": job_config.user_id,
                "course_member_id": job_config.course_member_id,
                "course_content_id": job_config.course_content_id,
                "execution_backend_id": job_config.execution_backend_id
            }
        }
        
        return report


@register_task
class SubmissionProcessingTask(BaseTask):
    """
    Process student submissions.
    
    This task handles submission processing including:
    - Git operations for submission
    - Merge request creation
    - Submission validation
    """
    
    @property
    def name(self) -> str:
        return "submission_processing"
    
    @property
    def timeout(self) -> int:
        return 600  # 10 minutes for submission processing
    
    async def execute(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a student submission.
        
        Args:
            submission: Submission configuration as dict
            
        Returns:
            Submission processing results
        """
        started_at = datetime.utcnow()
        
        try:
            # Parse submission configuration
            submission_config = Submission(**submission)
            
            await self.update_progress(20, {"status": "processing", "stage": "submission_setup"})
            
            # Import the original submission processing function
            from ctutor_backend.api.tests_celery import create_submission
            
            # Process the submission
            create_submission(submission_config)
            
            await self.update_progress(100, {"status": "completed", "stage": "submitted"})
            
            finished_at = datetime.utcnow()
            duration = (finished_at - started_at).total_seconds()
            
            return {
                "success": True,
                "submission_processed": True,
                "execution_time": duration,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "user_id": submission_config.user_id,
                "result_id": submission_config.result_id
            }
            
        except Exception as e:
            await self.update_progress(100, {
                "status": "failed", 
                "error": str(e),
                "stage": "error"
            })
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.utcnow() - started_at).total_seconds(),
                "started_at": started_at.isoformat(),
                "failed_at": datetime.utcnow().isoformat()
            }


# Celery task wrappers
@app.task(bind=True, name='ctutor_backend.tasks.student_testing')
def student_testing_celery(self, **kwargs):
    """Celery wrapper for StudentTestingTask."""
    return _execute_task_with_celery(self, StudentTestingTask, **kwargs)


@app.task(bind=True, name='ctutor_backend.tasks.submission_processing')
def submission_processing_celery(self, **kwargs):
    """Celery wrapper for SubmissionProcessingTask."""
    return _execute_task_with_celery(self, SubmissionProcessingTask, **kwargs)