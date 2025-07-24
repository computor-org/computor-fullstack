"""
Tests for Temporal task executor implementation.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4
from temporalio.client import WorkflowExecutionStatus

from ctutor_backend.tasks.temporal_executor import TemporalTaskExecutor
from ctutor_backend.tasks.base import TaskSubmission, TaskStatus, TaskInfo, TaskResult
from ctutor_backend.tasks.registry import task_registry


class MockWorkflow:
    """Mock workflow for testing."""
    
    @classmethod
    def get_name(cls):
        return "test_workflow"
    
    @classmethod
    def get_task_queue(cls):
        return "test-queue"


class TestTemporalTaskExecutor:
    """Test cases for TemporalTaskExecutor."""

    @pytest.fixture
    def executor(self):
        """Create a TemporalTaskExecutor instance."""
        return TemporalTaskExecutor()

    @pytest.fixture
    def mock_client(self):
        """Create a mock Temporal client."""
        return AsyncMock()

    @pytest.fixture
    def task_submission(self):
        """Create a sample task submission."""
        return TaskSubmission(
            task_name="test_workflow",
            parameters={"key": "value"},
            queue="test-queue"
        )

    @pytest.mark.asyncio
    async def test_submit_task_success(self, executor, mock_client, task_submission):
        """Test successful task submission."""
        # Setup mocks
        workflow_handle = MagicMock()
        workflow_handle.id = "test-workflow-id"
        mock_client.start_workflow.return_value = workflow_handle
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            with patch.object(task_registry, 'get_task', return_value=MockWorkflow):
                # Submit task
                task_id = await executor.submit_task(task_submission)
                
                # Verify workflow was started
                mock_client.start_workflow.assert_called_once()
                call_args = mock_client.start_workflow.call_args
                
                # Check workflow type
                assert call_args[0][0] == MockWorkflow
                
                # Check parameters
                assert call_args[1]['arg'] == task_submission.parameters
                assert call_args[1]['id'] == task_id
                assert call_args[1]['task_queue'] == "test-queue"

    @pytest.mark.asyncio
    async def test_submit_task_with_default_queue(self, executor, mock_client):
        """Test task submission with default queue from workflow."""
        # Task submission without queue specified
        submission = TaskSubmission(
            task_name="test_workflow",
            parameters={"key": "value"}
        )
        
        workflow_handle = MagicMock()
        workflow_handle.id = "test-workflow-id"
        mock_client.start_workflow.return_value = workflow_handle
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            with patch.object(task_registry, 'get_task', return_value=MockWorkflow):
                # Submit task
                task_id = await executor.submit_task(submission)
                
                # Should use workflow's default queue
                call_args = mock_client.start_workflow.call_args
                assert call_args[1]['task_queue'] == "test-queue"

    @pytest.mark.asyncio
    async def test_submit_task_workflow_not_found(self, executor, mock_client):
        """Test task submission with non-existent workflow."""
        submission = TaskSubmission(
            task_name="non_existent_workflow",
            parameters={}
        )
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            with patch.object(task_registry, 'get_task', side_effect=KeyError("Task not found")):
                # Should raise ValueError
                with pytest.raises(ValueError, match="Workflow 'non_existent_workflow' not found"):
                    await executor.submit_task(submission)

    @pytest.mark.asyncio
    async def test_get_task_status_running(self, executor, mock_client):
        """Test getting status of a running task."""
        task_id = str(uuid4())
        
        # Mock workflow handle with async describe
        workflow_handle = MagicMock()
        workflow_handle.id = task_id
        workflow_handle.describe = AsyncMock()
        
        # Mock describe result
        describe_result = MagicMock()
        describe_result.status = WorkflowExecutionStatus.RUNNING
        describe_result.task_queue = "test-queue"
        describe_result.start_time = datetime.utcnow()
        describe_result.close_time = None
        describe_result.most_recent_execution_run_id = "test-run-id"
        describe_result.history_length = 10
        
        workflow_handle.describe.return_value = describe_result
        mock_client.get_workflow_handle.return_value = workflow_handle
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            # Get status
            status = await executor.get_task_status(task_id)
            
            # Verify
            assert isinstance(status, TaskInfo)
            assert status.task_id == task_id
            assert status.status == TaskStatus.STARTED
            assert status.queue == "test-queue"

    @pytest.mark.asyncio
    async def test_get_task_status_completed(self, executor, mock_client):
        """Test getting status of a completed task."""
        task_id = str(uuid4())
        
        # Mock workflow handle with async describe
        workflow_handle = MagicMock()
        workflow_handle.id = task_id
        workflow_handle.describe = AsyncMock()
        
        # Mock describe result
        describe_result = MagicMock()
        describe_result.status = WorkflowExecutionStatus.COMPLETED
        describe_result.task_queue = "test-queue"
        describe_result.start_time = datetime.utcnow()
        describe_result.close_time = datetime.utcnow()
        describe_result.most_recent_execution_run_id = "test-run-id"
        describe_result.history_length = 20
        
        workflow_handle.describe.return_value = describe_result
        mock_client.get_workflow_handle.return_value = workflow_handle
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            # Get status
            status = await executor.get_task_status(task_id)
            
            # Verify
            assert status.status == TaskStatus.FINISHED
            assert status.finished_at is not None

    @pytest.mark.asyncio
    async def test_get_task_result_success(self, executor, mock_client):
        """Test getting result of a successful task."""
        task_id = str(uuid4())
        from ctutor_backend.tasks.temporal_base import WorkflowResult
        expected_result = WorkflowResult(status="completed", result={"data": "test"})
        
        # Mock workflow handle
        workflow_handle = MagicMock()
        workflow_handle.id = task_id
        workflow_handle.result = AsyncMock(return_value=expected_result)
        workflow_handle.describe = AsyncMock()
        
        mock_client.get_workflow_handle.return_value = workflow_handle
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            # Get result
            result = await executor.get_task_result(task_id)
            
            # Verify
            assert isinstance(result, TaskResult)
            assert result.task_id == task_id
            assert result.status == TaskStatus.FINISHED
            assert result.result == expected_result.result

    @pytest.mark.asyncio
    async def test_get_task_result_failed(self, executor, mock_client):
        """Test getting result of a failed task."""
        task_id = str(uuid4())
        
        # Mock workflow handle that raises exception
        workflow_handle = MagicMock()
        workflow_handle.id = task_id
        workflow_handle.result = AsyncMock(side_effect=Exception("Workflow failed"))
        
        # Mock describe for fallback
        describe_result = MagicMock()
        describe_result.status = WorkflowExecutionStatus.FAILED
        describe_result.close_time = datetime.utcnow()
        workflow_handle.describe = AsyncMock(return_value=describe_result)
        
        mock_client.get_workflow_handle.return_value = workflow_handle
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            # Get result
            result = await executor.get_task_result(task_id)
            
            # Verify
            assert result.status == TaskStatus.FAILED
            assert "Workflow failed" in result.error

    @pytest.mark.asyncio
    async def test_cancel_task(self, executor, mock_client):
        """Test cancelling a task."""
        task_id = str(uuid4())
        
        # Mock workflow handle
        workflow_handle = MagicMock()
        workflow_handle.id = task_id
        workflow_handle.cancel = AsyncMock()
        
        mock_client.get_workflow_handle.return_value = workflow_handle
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            # Cancel task
            await executor.cancel_task(task_id)
            
            # Verify workflow was cancelled
            workflow_handle.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task_not_implemented(self, executor):
        """Test that delete_task raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Temporal doesn't support direct deletion"):
            await executor.delete_task("any-task-id")

    @pytest.mark.asyncio
    async def test_get_worker_status(self, executor, mock_client):
        """Test getting workers status."""
        # Mock worker service
        mock_worker_service = MagicMock()
        mock_client.worker_service = mock_worker_service
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            # Get workers status
            status = await executor.get_worker_status()
            
            # Verify
            assert "workers" in status
            assert "backend" in status
            assert status["backend"] == "temporal"

    @pytest.mark.asyncio
    async def test_list_tasks(self, executor, mock_client):
        """Test listing tasks."""
        # Mock workflow executions
        mock_execution = MagicMock()
        mock_execution.workflow_id = "test-id"
        mock_execution.workflow_type = MagicMock()
        mock_execution.workflow_type.name = "test_workflow"
        mock_execution.status = WorkflowExecutionStatus.RUNNING
        mock_execution.start_time = datetime.utcnow()
        mock_execution.task_queue = "test-queue"
        
        # Create async iterator for list_workflows
        async def mock_list_workflows(**kwargs):
            yield mock_execution
        
        mock_client.list_workflows = mock_list_workflows
        
        with patch('ctutor_backend.tasks.temporal_executor.get_temporal_client', return_value=mock_client):
            # List tasks
            result = await executor.list_tasks(limit=10, status="RUNNING")
            tasks = result.get("tasks", [])
            
            # Verify
            assert len(tasks) == 1
            assert tasks[0]["task_id"] == "test-id"
            assert tasks[0]["task_name"] == "test_workflow"
            assert tasks[0]["status"] == "STARTED"

    @pytest.mark.asyncio
    async def test_status_mapping(self, executor):
        """Test Temporal status to TaskStatus mapping."""
        mappings = {
            WorkflowExecutionStatus.RUNNING: TaskStatus.STARTED,
            WorkflowExecutionStatus.COMPLETED: TaskStatus.FINISHED,
            WorkflowExecutionStatus.FAILED: TaskStatus.FAILED,
            WorkflowExecutionStatus.CANCELED: TaskStatus.CANCELLED,
            WorkflowExecutionStatus.TERMINATED: TaskStatus.CANCELLED,
            WorkflowExecutionStatus.TIMED_OUT: TaskStatus.FAILED,
        }
        
        for temporal_status, expected_status in mappings.items():
            # Test status mapping using the internal mapping dict
            mapped_status = executor._status_mapping.get(temporal_status, TaskStatus.QUEUED)
            assert mapped_status == expected_status