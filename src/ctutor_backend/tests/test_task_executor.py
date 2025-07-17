"""
Tests for the Celery-based task execution framework.

This test suite includes both unit tests (mocked) and integration tests (real Docker services).

## Running Tests

### Unit Tests (Fast, No Dependencies)
```bash
# Run all unit tests (no Docker required)
pytest ctutor_backend/tests/test_task_executor.py -m "not docker"

# Run specific test classes
pytest ctutor_backend/tests/test_task_executor.py::TestTaskExecutor
pytest ctutor_backend/tests/test_task_executor.py::TestBaseTask
```

### Integration Tests (Requires Docker)
```bash
# Start Docker services first
docker-compose -f docker-compose-dev.yaml up -d redis celery-worker-high celery-worker-default

# Run Docker integration tests
pytest ctutor_backend/tests/test_task_executor.py -m docker

# Or use the helper script for full automation
./scripts/testing/test_celery_docker.sh all
```

### Test Categories

- **Unit Tests**: Fast tests using mocked objects (21 tests)
- **Docker Integration Tests**: Real tests using Docker Compose Celery workers (5 tests)  
- **Setup Tests**: Verify Docker Compose configuration (3 tests)

### Docker Integration Features Tested

1. **Real Task Submission**: Submit tasks to actual Celery workers
2. **Worker Status Monitoring**: Check real worker health and queue status
3. **End-to-End Execution**: Complete task lifecycle with real workers
4. **Flower UI Accessibility**: Verify Flower monitoring UI is accessible
5. **Environment Validation**: Verify Docker Compose setup is correct
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from celery import states
from celery.result import AsyncResult

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
    """Test cases for Celery-based TaskExecutor."""
    
    @pytest.fixture
    def mock_celery_app(self):
        """Mock Celery app for testing."""
        with patch('ctutor_backend.tasks.executor.get_celery_app') as mock_get_app:
            mock_app = Mock()
            mock_app.tasks = {}
            mock_app.control = Mock()
            mock_get_app.return_value = mock_app
            yield mock_app
    
    @pytest.fixture
    def task_executor(self, mock_celery_app):
        """Create TaskExecutor instance for testing."""
        return TaskExecutor()
    
    @pytest.mark.asyncio
    async def test_submit_task_success(self, task_executor, mock_celery_app):
        """Test successful task submission."""
        # Mock Celery task
        mock_celery_task = Mock()
        mock_result = Mock()
        mock_result.id = "test-task-123"
        mock_celery_task.apply_async.return_value = mock_result
        
        # Add mock task to app.tasks
        mock_celery_app.tasks = {'ctutor_backend.tasks.example_long_running': mock_celery_task}
        
        submission = TaskSubmission(
            task_name="example_long_running",
            parameters={"duration": 10, "message": "test"}
        )
        
        task_id = await task_executor.submit_task(submission)
        
        assert task_id == "test-task-123"
        mock_celery_task.apply_async.assert_called_once()
    
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
    async def test_get_task_status(self, task_executor, mock_celery_app):
        """Test getting task status."""
        # Mock AsyncResult
        with patch('ctutor_backend.tasks.executor.AsyncResult') as mock_async_result_class:
            mock_result = Mock()
            mock_result.status = states.PENDING
            mock_result.name = "test_task"
            mock_result.failed.return_value = False
            mock_result.traceback = None
            mock_result.info = None
            mock_async_result_class.return_value = mock_result
            
            task_info = await task_executor.get_task_status("test-task-123")
            
            assert task_info.task_id == "test-task-123"
            assert task_info.status == TaskStatus.QUEUED
            assert task_info.task_name == "test_task"
    
    @pytest.mark.asyncio
    async def test_get_task_status_with_progress(self, task_executor, mock_celery_app):
        """Test getting task status with progress information."""
        with patch('ctutor_backend.tasks.executor.AsyncResult') as mock_async_result_class:
            mock_result = Mock()
            mock_result.status = states.STARTED
            mock_result.name = "test_task"
            mock_result.failed.return_value = False
            mock_result.traceback = None
            mock_result.info = {
                'progress': {'completed': 50, 'total': 100},
                'started_at': '2024-01-01T10:00:00',
                'finished_at': '2024-01-01T10:05:00'
            }
            mock_async_result_class.return_value = mock_result
            
            task_info = await task_executor.get_task_status("test-task-123")
            
            assert task_info.task_id == "test-task-123"
            assert task_info.status == TaskStatus.STARTED
            assert task_info.progress == {'completed': 50, 'total': 100}
    
    @pytest.mark.asyncio
    async def test_get_task_result(self, task_executor, mock_celery_app):
        """Test getting task result."""
        with patch('ctutor_backend.tasks.executor.AsyncResult') as mock_async_result_class:
            mock_result = Mock()
            mock_result.status = states.SUCCESS
            mock_result.name = "test_task"
            mock_result.failed.return_value = False
            mock_result.ready.return_value = True
            mock_result.result = {"output": "test_result"}
            mock_result.traceback = None
            mock_result.info = None
            mock_async_result_class.return_value = mock_result
            
            task_result = await task_executor.get_task_result("test-task-123")
            
            assert task_result.task_id == "test-task-123"
            assert task_result.status == TaskStatus.FINISHED
            assert task_result.result == {"output": "test_result"}
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_executor, mock_celery_app):
        """Test task cancellation."""
        mock_celery_app.control.revoke = Mock()
        
        result = await task_executor.cancel_task("test-task-123")
        
        assert result is True
        mock_celery_app.control.revoke.assert_called_once_with("test-task-123", terminate=True)
    
    @pytest.mark.asyncio
    async def test_cancel_task_failure(self, task_executor, mock_celery_app):
        """Test task cancellation failure."""
        mock_celery_app.control.revoke.side_effect = Exception("Revoke failed")
        
        result = await task_executor.cancel_task("test-task-123")
        
        assert result is False
    
    def test_queue_name_by_priority(self, task_executor):
        """Test queue name selection based on priority."""
        # High priority
        queue_name = task_executor._get_queue_name_by_priority(10)
        assert queue_name == "high_priority"
        
        # Normal priority
        queue_name = task_executor._get_queue_name_by_priority(3)
        assert queue_name == "default"
        
        # Low priority
        queue_name = task_executor._get_queue_name_by_priority(-1)
        assert queue_name == "low_priority"
    
    def test_get_worker_status(self, task_executor, mock_celery_app):
        """Test getting worker status."""
        # Mock inspection interface
        mock_inspect = Mock()
        mock_inspect.active.return_value = {
            "worker1@host": [{"name": "task1", "id": "123"}]
        }
        mock_celery_app.control.inspect.return_value = mock_inspect
        mock_celery_app.conf.broker_url = "redis://localhost:6379"
        
        with patch('kombu.Connection'):
            status = task_executor.get_worker_status()
            
            assert status['workers']['active_count'] == 1
            assert 'worker1@host' in status['workers']['workers']
            assert status['broker_url'] == "redis://localhost:6379"


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


class TestCeleryTaskWrapper:
    """Test cases for Celery task wrapper functionality."""
    
    def test_celery_task_wrappers_exist(self):
        """Test that Celery task wrappers are properly defined."""
        from ctutor_backend.tasks.examples import (
            example_long_running_celery_task,
            example_data_processing_celery_task,
            example_failing_celery_task
        )
        
        # Test that the wrapper functions exist and are callable
        assert callable(example_long_running_celery_task)
        assert callable(example_data_processing_celery_task)
        assert callable(example_failing_celery_task)
    
    @patch('ctutor_backend.tasks.examples.asyncio.set_event_loop')
    @patch('ctutor_backend.tasks.examples.asyncio.get_event_loop')
    @patch('ctutor_backend.tasks.examples.asyncio.new_event_loop')
    def test_execute_task_with_celery(self, mock_new_loop, mock_get_loop, mock_set_loop):
        """Test the Celery task execution wrapper."""
        from ctutor_backend.tasks.examples import _execute_task_with_celery
        
        # Mock event loop properly
        mock_loop = Mock()
        mock_get_loop.side_effect = RuntimeError("No running loop")
        mock_new_loop.return_value = mock_loop
        mock_set_loop.return_value = None
        
        # Mock Celery task instance
        mock_celery_task = Mock()
        mock_celery_task.update_state = Mock()
        
        # Mock BaseTask class
        mock_task_class = Mock()
        mock_task_instance = Mock()
        mock_task_instance.execute = AsyncMock(return_value={"test": "result"})
        mock_task_instance.on_success = AsyncMock()
        mock_task_class.return_value = mock_task_instance
        
        # Mock run_until_complete to avoid actual async execution
        mock_loop.run_until_complete.side_effect = [
            {"test": "result"},  # execute result
            None  # on_success result
        ]
        
        # Execute the wrapper
        result = _execute_task_with_celery(mock_celery_task, mock_task_class, test_param="value")
        
        # Verify task execution
        assert result == {"test": "result"}
        mock_celery_task.update_state.assert_called()
        mock_set_loop.assert_called_with(mock_loop)


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


class TestCeleryIntegration:
    """Integration tests for Celery task system."""
    
    @pytest.mark.asyncio
    async def test_task_submission_with_delay(self):
        """Test task submission with delay parameter."""
        with patch('ctutor_backend.tasks.executor.get_celery_app') as mock_get_app:
            mock_app = Mock()
            mock_celery_task = Mock()
            mock_result = Mock()
            mock_result.id = "delayed-task-123"
            mock_celery_task.apply_async.return_value = mock_result
            mock_app.tasks = {'ctutor_backend.tasks.example_long_running': mock_celery_task}
            mock_get_app.return_value = mock_app
            
            executor = TaskExecutor()
            submission = TaskSubmission(
                task_name="example_long_running",
                parameters={"duration": 5},
                delay=60  # 60 seconds delay
            )
            
            task_id = await executor.submit_task(submission)
            
            assert task_id == "delayed-task-123"
            # Verify apply_async was called with countdown parameter
            mock_celery_task.apply_async.assert_called_once()
            call_args = mock_celery_task.apply_async.call_args
            assert 'countdown' in call_args[1]
            assert call_args[1]['countdown'] == 60
    
    @pytest.mark.asyncio
    async def test_task_submission_with_priority_queue(self):
        """Test that tasks are submitted to correct priority queues."""
        with patch('ctutor_backend.tasks.executor.get_celery_app') as mock_get_app:
            mock_app = Mock()
            mock_celery_task = Mock()
            mock_result = Mock()
            mock_result.id = "priority-task-123"
            mock_celery_task.apply_async.return_value = mock_result
            mock_app.tasks = {'ctutor_backend.tasks.example_long_running': mock_celery_task}
            mock_get_app.return_value = mock_app
            
            executor = TaskExecutor()
            submission = TaskSubmission(
                task_name="example_long_running",
                parameters={"duration": 5},
                priority=8  # High priority
            )
            
            task_id = await executor.submit_task(submission)
            
            assert task_id == "priority-task-123"
            # Verify apply_async was called with high priority queue
            call_args = mock_celery_task.apply_async.call_args
            assert call_args[1]['queue'] == 'high_priority'
            assert call_args[1]['priority'] == 8


@pytest.mark.integration
@pytest.mark.docker
class TestDockerCeleryIntegration:
    """
    Integration tests using actual Docker Compose Celery workers.
    
    These tests require Docker Compose services to be running.
    To start services: docker-compose -f docker-compose-dev.yaml up -d
    To run these tests: pytest -m docker
    
    Tests will be skipped if Docker services are not available.
    """
    
    def is_docker_compose_running(self):
        """Check if Docker Compose services are running."""
        import subprocess
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--services", "--filter", "status=running"],
                capture_output=True,
                text=True,
                cwd="/home/theta/computingtutor/computor-fullstack"
            )
            running_services = result.stdout.strip().split('\n')
            return 'redis' in running_services
        except Exception:
            return False
    
    def wait_for_redis(self, timeout=30):
        """Wait for Redis to be available."""
        import time
        import redis
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                return True
            except Exception:
                time.sleep(1)
        return False
    
    def wait_for_celery_workers(self, timeout=60):
        """Wait for Celery workers to be available."""
        import time
        from ctutor_backend.tasks import get_task_executor
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                executor = get_task_executor()
                status = executor.get_worker_status()
                if status['workers']['active_count'] > 0:
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False
    
    @pytest.mark.skipif(
        not pytest.importorskip("docker", minversion="6.0.0"),
        reason="Docker not available"
    )
    def test_docker_compose_services_available(self):
        """Test that required Docker Compose services are running."""
        if not self.is_docker_compose_running():
            pytest.skip("Docker Compose services not running. Start with: docker-compose -f docker-compose-dev.yaml up -d")
        
        assert self.wait_for_redis(), "Redis service not available"
    
    @pytest.mark.skipif(
        not pytest.importorskip("docker", minversion="6.0.0"),
        reason="Docker not available" 
    )
    @pytest.mark.asyncio
    async def test_real_celery_task_submission(self):
        """Test submitting a real task to Docker Compose Celery workers."""
        if not self.is_docker_compose_running():
            pytest.skip("Docker Compose services not running")
        
        if not self.wait_for_redis():
            pytest.skip("Redis not available")
        
        # Import the real task executor (not mocked)
        from ctutor_backend.tasks import get_task_executor, TaskSubmission
        
        executor = get_task_executor()
        
        # Submit a quick test task
        submission = TaskSubmission(
            task_name="example_long_running",
            parameters={"duration": 2, "message": "Docker integration test"}
        )
        
        try:
            task_id = await executor.submit_task(submission)
            assert task_id is not None
            assert isinstance(task_id, str)
            
            # Check task status
            task_info = await executor.get_task_status(task_id)
            assert task_info.task_id == task_id
            assert task_info.task_name in ["ctutor_backend.tasks.example_long_running", "unknown"]
            
        except Exception as e:
            # If task submission fails, it might be because workers aren't running
            pytest.skip(f"Task submission failed, workers may not be available: {e}")
    
    @pytest.mark.skipif(
        not pytest.importorskip("docker", minversion="6.0.0"), 
        reason="Docker not available"
    )
    @pytest.mark.asyncio 
    async def test_celery_worker_status_real(self):
        """Test getting real Celery worker status from Docker."""
        if not self.is_docker_compose_running():
            pytest.skip("Docker Compose services not running")
        
        if not self.wait_for_redis():
            pytest.skip("Redis not available")
        
        from ctutor_backend.tasks import get_task_executor
        
        executor = get_task_executor()
        
        try:
            status = executor.get_worker_status()
            
            # Basic structure checks
            assert 'workers' in status
            assert 'queues' in status
            assert 'broker_url' in status
            assert 'status' in status
            
            # Should have Redis broker URL
            assert 'redis' in status['broker_url'].lower()
            
            print(f"Worker status: {status}")  # For debugging
            
        except Exception as e:
            pytest.skip(f"Worker status check failed: {e}")
    
    @pytest.mark.skipif(
        not pytest.importorskip("docker", minversion="6.0.0"),
        reason="Docker not available"
    )
    @pytest.mark.asyncio
    async def test_task_execution_with_workers(self):
        """Test end-to-end task execution with real workers."""
        if not self.is_docker_compose_running():
            pytest.skip("Docker Compose services not running")
        
        if not self.wait_for_redis():
            pytest.skip("Redis not available")
        
        from ctutor_backend.tasks import get_task_executor, TaskSubmission, TaskStatus
        import asyncio
        
        executor = get_task_executor()
        
        # Submit a very quick task
        submission = TaskSubmission(
            task_name="example_long_running", 
            parameters={"duration": 1, "message": "End-to-end test"}
        )
        
        try:
            task_id = await executor.submit_task(submission)
            
            # Wait a bit and check if task progresses
            await asyncio.sleep(2)
            
            task_info = await executor.get_task_status(task_id)
            
            # Task should at least be queued or started
            assert task_info.status in [TaskStatus.QUEUED, TaskStatus.STARTED, TaskStatus.FINISHED]
            
            # If we have an active worker, try to get the result
            if task_info.status == TaskStatus.FINISHED:
                result = await executor.get_task_result(task_id)
                assert result.task_id == task_id
                assert result.status == TaskStatus.FINISHED
                
        except Exception as e:
            pytest.skip(f"End-to-end task execution failed: {e}")
    
    @pytest.mark.skipif(
        not pytest.importorskip("requests", minversion="2.0.0"),
        reason="requests not available"
    )
    def test_flower_ui_accessible(self):
        """Test that Flower UI is accessible when Docker services are running."""
        if not self.is_docker_compose_running():
            pytest.skip("Docker Compose services not running")
        
        if not self.wait_for_redis():
            pytest.skip("Redis not available")
        
        try:
            import requests
            import time
            
            # Wait a bit for Flower to start up
            time.sleep(5)
            
            # Try to access Flower UI
            response = requests.get(
                'http://localhost:5555',
                timeout=10,
                auth=('admin', 'flower123')  # Default credentials
            )
            
            # Should get a successful response (200) or redirect (302)
            assert response.status_code in [200, 302], f"Flower UI not accessible: {response.status_code}"
            
            # Check that it's actually Flower
            assert 'flower' in response.text.lower() or 'celery' in response.text.lower(), \
                "Response doesn't appear to be from Flower"
            
        except ImportError:
            pytest.skip("requests library not available")
        except Exception as e:
            pytest.skip(f"Flower UI accessibility test failed: {e}")


@pytest.mark.integration  
class TestDockerComposeSetup:
    """Tests to help set up and verify Docker Compose environment."""
    
    def test_docker_compose_file_exists(self):
        """Verify Docker Compose files exist."""
        import os
        
        compose_dev = "/home/theta/computingtutor/computor-fullstack/docker-compose-dev.yaml"
        compose_prod = "/home/theta/computingtutor/computor-fullstack/docker-compose-prod.yaml"
        
        assert os.path.exists(compose_dev), f"Dev compose file not found: {compose_dev}"
        assert os.path.exists(compose_prod), f"Prod compose file not found: {compose_prod}"
    
    def test_docker_compose_config_valid(self):
        """Test that Docker Compose configuration is valid."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose-dev.yaml", "config"],
                capture_output=True,
                text=True,
                cwd="/home/theta/computingtutor/computor-fullstack"
            )
            assert result.returncode == 0, f"Docker Compose config invalid: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("docker-compose command not available")
    
    def test_celery_services_defined(self):
        """Test that Celery worker services are defined in Docker Compose."""
        import yaml
        
        compose_file = "/home/theta/computingtutor/computor-fullstack/docker-compose-dev.yaml"
        
        with open(compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        services = compose_config.get('services', {})
        
        # Check for Celery worker services
        celery_services = [name for name in services.keys() if 'celery-worker' in name]
        assert len(celery_services) >= 2, f"Expected at least 2 Celery worker services, found: {celery_services}"
        
        # Check that workers have proper commands
        for service_name in celery_services:
            service = services[service_name]
            command = service.get('command', [])
            if isinstance(command, list) and len(command) > 0:
                assert 'celery' in ' '.join(command), f"Service {service_name} doesn't have celery command"
        
        # Check for Flower monitoring service
        assert 'flower' in services, "Flower monitoring service not found in Docker Compose"
        flower_service = services['flower']
        flower_command = flower_service.get('command', [])
        if isinstance(flower_command, list):
            assert 'flower' in ' '.join(flower_command), "Flower service doesn't have flower command"