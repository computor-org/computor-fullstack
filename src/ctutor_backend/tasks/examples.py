"""
Example task implementations demonstrating the task execution framework.
"""

import asyncio
from typing import Any, Dict
from datetime import datetime

from .base import BaseTask
from .registry import register_task


@register_task
class ExampleLongRunningTask(BaseTask):
    """Example task that simulates a long-running operation."""
    
    @property
    def name(self) -> str:
        return "example_long_running"
    
    @property
    def timeout(self) -> int:
        return 300  # 5 minutes
    
    async def execute(self, duration: int = 60, message: str = "Processing...") -> Dict[str, Any]:
        """
        Simulate a long-running task.
        
        Args:
            duration: How long to run (seconds)
            message: Status message
            
        Returns:
            Result dictionary with execution details
        """
        start_time = datetime.utcnow()
        
        # Simulate processing in chunks to show progress
        chunk_size = 1  # Process in 1-second chunks
        processed = 0
        
        while processed < duration:
            await asyncio.sleep(chunk_size)
            processed += chunk_size
            
            # In a real implementation, you could update job progress here
            # using job.meta['progress'] = {'completed': processed, 'total': duration}
            
        end_time = datetime.utcnow()
        
        return {
            "message": message,
            "duration_requested": duration,
            "duration_actual": (end_time - start_time).total_seconds(),
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "status": "completed"
        }
    
    async def on_success(self, result: Any, **kwargs) -> None:
        """Handle successful task completion."""
        print(f"Task {self.name} completed successfully: {result}")
    
    async def on_failure(self, error: Exception, **kwargs) -> None:
        """Handle task failure."""
        print(f"Task {self.name} failed with error: {str(error)}")


@register_task
class ExampleDataProcessingTask(BaseTask):
    """Example task for processing data."""
    
    @property
    def name(self) -> str:
        return "example_data_processing"
    
    @property
    def timeout(self) -> int:
        return 600  # 10 minutes
    
    async def execute(self, data_source: str, processing_type: str = "basic") -> Dict[str, Any]:
        """
        Simulate data processing task.
        
        Args:
            data_source: Source of data to process
            processing_type: Type of processing to perform
            
        Returns:
            Processing results
        """
        start_time = datetime.utcnow()
        
        # Simulate different processing types
        if processing_type == "basic":
            await asyncio.sleep(5)
            result_count = 100
        elif processing_type == "advanced":
            await asyncio.sleep(15)
            result_count = 500
        elif processing_type == "complex":
            await asyncio.sleep(30)
            result_count = 1000
        else:
            raise ValueError(f"Unknown processing type: {processing_type}")
        
        end_time = datetime.utcnow()
        
        return {
            "data_source": data_source,
            "processing_type": processing_type,
            "records_processed": result_count,
            "processing_time": (end_time - start_time).total_seconds(),
            "completed_at": end_time.isoformat()
        }


@register_task
class ExampleFailingTask(BaseTask):
    """Example task that demonstrates error handling."""
    
    @property
    def name(self) -> str:
        return "example_failing"
    
    @property
    def retry_limit(self) -> int:
        return 2  # Allow 2 retries
    
    async def execute(self, should_fail: bool = True, error_message: str = "Simulated failure") -> Dict[str, Any]:
        """
        Task that can be configured to fail for testing error handling.
        
        Args:
            should_fail: Whether the task should fail
            error_message: Error message to raise
            
        Returns:
            Success result if should_fail is False
        """
        await asyncio.sleep(2)  # Simulate some work
        
        if should_fail:
            raise Exception(error_message)
        
        return {
            "status": "success",
            "message": "Task completed without errors",
            "completed_at": datetime.utcnow().isoformat()
        }