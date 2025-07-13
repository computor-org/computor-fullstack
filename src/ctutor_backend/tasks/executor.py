"""
Task executor implementation using Redis Queue (RQ).
"""

import os
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from redis import Redis
from rq import Queue, Worker
from rq.job import Job
from rq.exceptions import NoSuchJobError

from .base import BaseTask, TaskStatus, TaskResult, TaskInfo, TaskSubmission
from .registry import task_registry


class TaskExecutor:
    """
    Task executor using Redis Queue for managing long-running operations.
    """
    
    def __init__(self, redis_url: Optional[str] = None, redis_password: Optional[str] = None):
        """
        Initialize task executor.
        
        Args:
            redis_url: Redis connection URL
            redis_password: Redis password
        """
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        self.redis_password = redis_password or os.environ.get("REDIS_PASSWORD")
        
        # Initialize Redis connection
        self.redis_client = Redis.from_url(
            self.redis_url,
            password=self.redis_password,
            decode_responses=True
        )
        
        # Initialize task queues
        self.default_queue = Queue('default', connection=self.redis_client)
        self.high_priority_queue = Queue('high_priority', connection=self.redis_client)
        self.low_priority_queue = Queue('low_priority', connection=self.redis_client)
    
    def _get_queue_by_priority(self, priority: int) -> Queue:
        """Get queue based on task priority."""
        if priority > 5:
            return self.high_priority_queue
        elif priority < 0:
            return self.low_priority_queue
        else:
            return self.default_queue
    
    async def submit_task(self, submission: TaskSubmission) -> str:
        """
        Submit a task for execution.
        
        Args:
            submission: Task submission details
            
        Returns:
            Task ID for tracking
            
        Raises:
            KeyError: If task type is not registered
            Exception: If task submission fails
        """
        # Validate task exists
        task_class = task_registry.get_task(submission.task_name)
        task_instance = task_class()
        
        # Select appropriate queue
        queue = self._get_queue_by_priority(submission.priority)
        
        # Submit job to queue
        job = queue.enqueue(
            self._execute_task_wrapper,
            submission.task_name,
            submission.parameters,
            job_timeout=task_instance.timeout,
            retry_limit=task_instance.retry_limit,
            delay=submission.delay
        )
        
        return job.id
    
    async def get_task_status(self, task_id: str) -> TaskInfo:
        """
        Get task execution status and information.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task information
            
        Raises:
            NoSuchJobError: If task ID doesn't exist
        """
        try:
            job = Job.fetch(task_id, connection=self.redis_client)
            
            status_mapping = {
                'queued': TaskStatus.QUEUED,
                'started': TaskStatus.STARTED,
                'finished': TaskStatus.FINISHED,
                'failed': TaskStatus.FAILED,
                'deferred': TaskStatus.DEFERRED,
                'cancelled': TaskStatus.CANCELLED
            }
            
            return TaskInfo(
                task_id=task_id,
                task_name=job.func_name.split('.')[-1] if job.func_name else "unknown",
                status=status_mapping.get(job.status, TaskStatus.QUEUED),
                created_at=job.created_at or datetime.utcnow(),
                started_at=job.started_at,
                finished_at=job.ended_at,
                progress=job.meta.get('progress'),
                error=str(job.exc_info) if job.exc_info else None
            )
            
        except NoSuchJobError:
            raise NoSuchJobError(f"Task with ID {task_id} not found")
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        """
        Get task execution result.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result
            
        Raises:
            NoSuchJobError: If task ID doesn't exist
        """
        task_info = await self.get_task_status(task_id)
        
        try:
            job = Job.fetch(task_id, connection=self.redis_client)
            
            return TaskResult(
                task_id=task_id,
                status=task_info.status,
                result=job.result,
                error=task_info.error,
                created_at=task_info.created_at,
                started_at=task_info.started_at,
                finished_at=task_info.finished_at,
                progress=task_info.progress
            )
            
        except NoSuchJobError:
            raise NoSuchJobError(f"Task with ID {task_id} not found")
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a queued or running task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        try:
            job = Job.fetch(task_id, connection=self.redis_client)
            job.cancel()
            return True
        except NoSuchJobError:
            return False
    
    def start_worker(self, queues: Optional[list] = None, burst: bool = False):
        """
        Start a worker process for executing tasks.
        
        Args:
            queues: List of queue names to process (defaults to all)
            burst: If True, worker will exit after processing all jobs
        """
        if queues is None:
            queues = [self.high_priority_queue, self.default_queue, self.low_priority_queue]
        
        worker = Worker(queues, connection=self.redis_client)
        worker.work(burst=burst)
    
    @staticmethod
    def _execute_task_wrapper(task_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Wrapper function for executing tasks in RQ worker.
        
        This function runs in the worker process and handles task execution.
        """
        # Get task implementation
        task_class = task_registry.get_task(task_name)
        task_instance = task_class()
        
        # Execute task (note: RQ doesn't directly support async, so we need to handle it)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(task_instance.execute(**parameters))
            loop.run_until_complete(task_instance.on_success(result, **parameters))
            return result
        except Exception as e:
            loop.run_until_complete(task_instance.on_failure(e, **parameters))
            raise
        finally:
            loop.close()


# Global task executor instance
_task_executor: Optional[TaskExecutor] = None


def get_task_executor() -> TaskExecutor:
    """
    Get the global task executor instance.
    
    Returns:
        TaskExecutor instance
    """
    global _task_executor
    if _task_executor is None:
        _task_executor = TaskExecutor()
    return _task_executor