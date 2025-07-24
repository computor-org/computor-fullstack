"""
Tests for Temporal workflow implementations.
"""

import pytest
from datetime import timedelta
from temporalio.testing import WorkflowEnvironment

from ctutor_backend.tasks.temporal_base import WorkflowResult
from ctutor_backend.tasks.temporal_examples import (
    ExampleLongRunningWorkflow,
    ExampleDataProcessingWorkflow,
    ExampleErrorHandlingWorkflow,
    simulate_processing_activity,
    process_data_chunk_activity,
)


class TestTemporalWorkflows:
    """Test cases for Temporal workflow implementations."""

    @pytest.mark.asyncio
    async def test_example_long_running_workflow(self):
        """Test the ExampleLongRunningWorkflow execution."""
        async with WorkflowEnvironment() as env:
            # Define parameters
            params = {
                "duration": 5,
                "message": "Test processing"
            }
            
            # Run workflow
            result = await env.client.execute_workflow(
                ExampleLongRunningWorkflow.run,
                params,
                id="test-long-running",
                task_queue="test-queue",
                retry_policy=None,
            )
            
            # Verify result
            assert isinstance(result, WorkflowResult)
            assert result.status == "completed"
            assert result.result["message"] == "Test processing"
            assert result.result["duration_requested"] == 5
            assert result.metadata["workflow_type"] == "long_running"

    @pytest.mark.asyncio
    async def test_example_long_running_workflow_with_string_duration(self):
        """Test workflow with string duration parameter."""
        async with WorkflowEnvironment() as env:
            # Define parameters with string duration
            params = {
                "duration": "10",
                "message": "String duration test"
            }
            
            # Run workflow
            result = await env.client.execute_workflow(
                ExampleLongRunningWorkflow.run,
                params,
                id="test-string-duration",
                task_queue="test-queue",
            )
            
            # Verify duration was converted to int
            assert result.result["duration_requested"] == 10

    @pytest.mark.asyncio
    async def test_example_data_processing_workflow(self):
        """Test the ExampleDataProcessingWorkflow execution."""
        async with WorkflowEnvironment() as env:
            # Define parameters
            params = {
                "data_size": 50,
                "chunk_size": 10,
                "operation": "sum"
            }
            
            # Run workflow
            result = await env.client.execute_workflow(
                ExampleDataProcessingWorkflow.run,
                params,
                id="test-data-processing",
                task_queue="test-queue",
            )
            
            # Verify result
            assert isinstance(result, WorkflowResult)
            assert result.status == "completed"
            assert result.result["total_items"] == 50
            assert result.result["chunks_processed"] == 5  # 50/10
            assert result.result["operation"] == "sum"
            assert result.result["final_result"] == sum(range(1, 51))  # 1+2+...+50

    @pytest.mark.asyncio
    async def test_example_data_processing_workflow_count_operation(self):
        """Test data processing workflow with count operation."""
        async with WorkflowEnvironment() as env:
            params = {
                "data_size": 30,
                "chunk_size": 5,
                "operation": "count"
            }
            
            result = await env.client.execute_workflow(
                ExampleDataProcessingWorkflow.run,
                params,
                id="test-count-operation",
                task_queue="test-queue",
            )
            
            assert result.result["final_result"] == 30

    @pytest.mark.asyncio
    async def test_example_data_processing_workflow_max_operation(self):
        """Test data processing workflow with max operation."""
        async with WorkflowEnvironment() as env:
            params = {
                "data_size": 20,
                "chunk_size": 4,
                "operation": "max"
            }
            
            result = await env.client.execute_workflow(
                ExampleDataProcessingWorkflow.run,
                params,
                id="test-max-operation",
                task_queue="test-queue",
            )
            
            assert result.result["final_result"] == 20  # Max of 1..20

    @pytest.mark.asyncio
    async def test_example_error_handling_workflow_success(self):
        """Test error handling workflow with successful execution."""
        async with WorkflowEnvironment() as env:
            params = {
                "should_fail": False,
                "retry_count": 0,
                "fail_at_step": 1
            }
            
            result = await env.client.execute_workflow(
                ExampleErrorHandlingWorkflow.run,
                params,
                id="test-error-success",
                task_queue="test-queue",
            )
            
            assert result.status == "completed"
            assert result.result["message"] == "Task completed successfully"
            assert result.result["attempts"] == 1

    @pytest.mark.asyncio
    async def test_example_error_handling_workflow_with_retry(self):
        """Test error handling workflow with retries."""
        async with WorkflowEnvironment() as env:
            params = {
                "should_fail": True,
                "retry_count": 2,
                "fail_at_step": 2  # Fail first time, succeed on second
            }
            
            result = await env.client.execute_workflow(
                ExampleErrorHandlingWorkflow.run,
                params,
                id="test-error-retry",
                task_queue="test-queue",
            )
            
            assert result.status == "completed"
            assert result.result["attempts"] == 2

    @pytest.mark.asyncio
    async def test_example_error_handling_workflow_failure(self):
        """Test error handling workflow with ultimate failure."""
        async with WorkflowEnvironment() as env:
            params = {
                "should_fail": True,
                "retry_count": 1,
                "fail_at_step": 10  # Always fail
            }
            
            result = await env.client.execute_workflow(
                ExampleErrorHandlingWorkflow.run,
                params,
                id="test-error-fail",
                task_queue="test-queue",
            )
            
            assert result.status == "failed"
            assert result.error == "Simulated failure at step 2"
            assert result.metadata["attempts"] == 2

    @pytest.mark.asyncio
    async def test_workflow_metadata(self):
        """Test workflow metadata methods."""
        # Test get_name
        assert ExampleLongRunningWorkflow.get_name() == "example_long_running"
        assert ExampleDataProcessingWorkflow.get_name() == "example_data_processing"
        assert ExampleErrorHandlingWorkflow.get_name() == "example_error_handling"
        
        # Test get_task_queue
        assert ExampleLongRunningWorkflow.get_task_queue() == "computor-tasks"
        assert ExampleDataProcessingWorkflow.get_task_queue() == "computor-tasks"
        assert ExampleErrorHandlingWorkflow.get_task_queue() == "computor-tasks"
        
        # Test get_execution_timeout
        assert ExampleLongRunningWorkflow.get_execution_timeout() == timedelta(minutes=5)
        assert ExampleDataProcessingWorkflow.get_execution_timeout() == timedelta(minutes=10)
        assert ExampleErrorHandlingWorkflow.get_execution_timeout() == timedelta(minutes=10)

    @pytest.mark.asyncio
    async def test_activity_simulate_processing(self):
        """Test the simulate_processing_activity."""
        # Run activity directly
        result = await simulate_processing_activity(2, "Test message")
        
        # Verify result
        assert result["message"] == "Test message"
        assert result["duration_requested"] == 2
        assert "started_at" in result
        assert "completed_at" in result
        assert result["duration_actual"] >= 2  # Should take at least 2 seconds

    @pytest.mark.asyncio
    async def test_activity_process_data_chunk(self):
        """Test the process_data_chunk_activity."""
        # Test sum operation
        result = await process_data_chunk_activity([1, 2, 3, 4, 5], "sum")
        assert result["chunk_size"] == 5
        assert result["operation"] == "sum"
        assert result["result"] == 15
        
        # Test count operation
        result = await process_data_chunk_activity([1, 2, 3], "count")
        assert result["result"] == 3
        
        # Test max operation
        result = await process_data_chunk_activity([10, 5, 20, 15], "max")
        assert result["result"] == 20
        
        # Test max with empty list
        result = await process_data_chunk_activity([], "max")
        assert result["result"] is None
        
        # Test unknown operation
        result = await process_data_chunk_activity([1, 2, 3], "unknown")
        assert result["result"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_workflow_registration(self):
        """Test that workflows are properly registered."""
        from ctutor_backend.tasks.registry import task_registry
        
        # Verify workflows are in registry
        assert task_registry.get("example_long_running") == ExampleLongRunningWorkflow
        assert task_registry.get("example_data_processing") == ExampleDataProcessingWorkflow
        assert task_registry.get("example_error_handling") == ExampleErrorHandlingWorkflow

    @pytest.mark.asyncio
    async def test_workflow_with_custom_queue(self):
        """Test that workflows can use custom queues."""
        # Mock a workflow with custom queue
        class CustomQueueWorkflow(ExampleLongRunningWorkflow):
            @classmethod
            def get_task_queue(cls) -> str:
                return "custom-queue"
        
        assert CustomQueueWorkflow.get_task_queue() == "custom-queue"

    @pytest.mark.asyncio
    async def test_workflow_parameter_validation(self):
        """Test workflow parameter handling and validation."""
        async with WorkflowEnvironment() as env:
            # Test with missing parameters (should use defaults)
            params = {}
            
            result = await env.client.execute_workflow(
                ExampleLongRunningWorkflow.run,
                params,
                id="test-defaults",
                task_queue="test-queue",
            )
            
            # Should use default values
            assert result.result["duration_requested"] == 60  # Default
            assert result.result["message"] == "Processing..."  # Default

    @pytest.mark.asyncio
    async def test_boolean_string_conversion(self):
        """Test boolean string conversion in error handling workflow."""
        async with WorkflowEnvironment() as env:
            # Test various string representations of boolean
            for bool_str in ['true', 'True', '1', 'yes']:
                params = {
                    "should_fail": bool_str,
                    "retry_count": 0,
                    "fail_at_step": 1
                }
                
                result = await env.client.execute_workflow(
                    ExampleErrorHandlingWorkflow.run,
                    params,
                    id=f"test-bool-{bool_str}",
                    task_queue="test-queue",
                )
                
                # Should fail because should_fail was converted to True
                assert result.status == "failed"
            
            # Test false string values
            for bool_str in ['false', 'False', '0', 'no']:
                params = {
                    "should_fail": bool_str,
                    "retry_count": 0,
                    "fail_at_step": 1
                }
                
                result = await env.client.execute_workflow(
                    ExampleErrorHandlingWorkflow.run,
                    params,
                    id=f"test-bool-false-{bool_str}",
                    task_queue="test-queue",
                )
                
                # Should succeed
                assert result.status == "completed"