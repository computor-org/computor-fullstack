"""
Tests for the task execution framework.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime
from redis import Redis
from rq import Queue
from rq.job import Job

from ctutor_backend.tasks import (
    TaskExecutor, 
    BaseTask, 
    TaskStatus, 
    TaskSubmission,
    register_task,
    task_registry
)
from ctutor_backend.tasks.examples import ExampleLongRunningTask


class TestTaskExecutor:
    """Test cases for TaskExecutor."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing."""
        with patch('ctutor_backend.tasks.executor.Redis') as mock_redis_class:
            mock_redis = Mock(spec=Redis)
            mock_redis_class.from_url.return_value = mock_redis
            yield mock_redis
    
    @pytest.fixture
    def task_executor(self, mock_redis):
        """Create TaskExecutor instance for testing."""
        return TaskExecutor()
    
    @pytest.mark.asyncio
    async def test_submit_task_success(self, task_executor):
        """Test successful task submission."""
        # Mock queue enqueue method
        mock_job = Mock()
        mock_job.id = "test-job-123"
        task_executor.default_queue.enqueue = Mock(return_value=mock_job)
        
        submission = TaskSubmission(
            task_name="example_long_running",
            parameters={"duration": 10, "message": "test"}
        )
        
        task_id = await task_executor.submit_task(submission)
        
        assert task_id == "test-job-123"
        task_executor.default_queue.enqueue.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_task_unknown_task(self, task_executor):
        """Test submission of unknown task type."""
        submission = TaskSubmission(
            task_name="nonexistent_task",
            parameters={}
        )
        
        with pytest.raises(KeyError):
            await task_executor.submit_task(submission)
    
    @pytest.mark.asyncio 
    async def test_get_task_status(self, task_executor):
        """Test getting task status."""
        # Mock job fetch
        mock_job = Mock(spec=Job)
        mock_job.id = "test-job-123"
        mock_job.status = "queued"
        mock_job.created_at = datetime.utcnow()
        mock_job.started_at = None
        mock_job.ended_at = None
        mock_job.func_name = "example_task"
        mock_job.meta = {}
        mock_job.exc_info = None
        
        with patch('ctutor_backend.tasks.executor.Job') as mock_job_class:
            mock_job_class.fetch.return_value = mock_job
            
            task_info = await task_executor.get_task_status("test-job-123")
            
            assert task_info.task_id == "test-job-123"
            assert task_info.status == TaskStatus.QUEUED
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_executor):
        """Test task cancellation."""
        mock_job = Mock(spec=Job)
        mock_job.cancel = Mock()
        
        with patch('ctutor_backend.tasks.executor.Job') as mock_job_class:
            mock_job_class.fetch.return_value = mock_job
            
            result = await task_executor.cancel_task("test-job-123")
            
            assert result is True
            mock_job.cancel.assert_called_once()
    
    def test_queue_priority_selection(self, task_executor):
        """Test queue selection based on priority."""
        # High priority
        queue = task_executor._get_queue_by_priority(10)
        assert queue == task_executor.high_priority_queue
        
        # Normal priority
        queue = task_executor._get_queue_by_priority(3)
        assert queue == task_executor.default_queue
        
        # Low priority
        queue = task_executor._get_queue_by_priority(-1)
        assert queue == task_executor.low_priority_queue


class MockTask(BaseTask):
    """Mock task for testing."""
    
    @property
    def name(self) -> str:
        return "mock_task"
    
    async def execute(self, test_param: str = "default") -> dict:
        return {"result": f"processed_{test_param}"}


class TestBaseTask:
    """Test cases for BaseTask."""
    
    def test_task_properties(self):
        """Test task property defaults."""
        task = MockTask()
        
        assert task.name == "mock_task"
        assert task.timeout == 3600  # 1 hour default
        assert task.retry_limit == 3
    
    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Test task execution."""
        task = MockTask()
        result = await task.execute(test_param="hello")
        
        assert result == {"result": "processed_hello"}


class TestTaskRegistry:
    """Test cases for task registry."""
    
    def test_register_task_decorator(self):
        """Test task registration via decorator."""
        @register_task
        class TestRegistryTask(BaseTask):
            @property
            def name(self) -> str:
                return "test_registry_task"
            
            async def execute(self, **kwargs):
                return "test_result"
        
        # Verify task is registered
        assert task_registry.is_registered("test_registry_task")
        
        # Verify we can retrieve it
        retrieved_task_class = task_registry.get_task("test_registry_task")
        assert retrieved_task_class == TestRegistryTask
    
    def test_duplicate_registration_error(self):
        """Test error on duplicate task registration."""
        class DuplicateTask(BaseTask):
            @property
            def name(self) -> str:
                return "duplicate_task"
            
            async def execute(self, **kwargs):
                return "result"
        
        # Register first time - should work
        task_registry.register(DuplicateTask)
        
        # Register second time - should fail
        with pytest.raises(ValueError, match="already registered"):
            task_registry.register(DuplicateTask)


class TestTaskSubmission:
    """Test cases for TaskSubmission model."""
    
    def test_task_submission_defaults(self):
        """Test TaskSubmission default values."""
        submission = TaskSubmission(task_name="test_task")
        
        assert submission.task_name == "test_task"
        assert submission.parameters == {}
        assert submission.priority == 0
        assert submission.delay is None
    
    def test_task_submission_with_parameters(self):
        """Test TaskSubmission with custom parameters."""
        submission = TaskSubmission(
            task_name="test_task",
            parameters={"param1": "value1", "param2": 42},
            priority=5,
            delay=60
        )
        
        assert submission.task_name == "test_task"
        assert submission.parameters == {"param1": "value1", "param2": 42}
        assert submission.priority == 5
        assert submission.delay == 60


class TestExampleTasks:
    """Test cases for example task implementations."""
    
    @pytest.mark.asyncio
    async def test_example_long_running_task(self):
        """Test example long running task."""
        task = ExampleLongRunningTask()
        
        # Test with short duration for quick test
        result = await task.execute(duration=1, message="test message")
        
        assert result["message"] == "test message"
        assert result["duration_requested"] == 1
        assert "started_at" in result
        assert "completed_at" in result
        assert result["status"] == "completed"
    
    def test_example_task_registration(self):
        """Test that example tasks are properly registered."""
        assert task_registry.is_registered("example_long_running")
        assert task_registry.is_registered("example_data_processing")
        assert task_registry.is_registered("example_failing")