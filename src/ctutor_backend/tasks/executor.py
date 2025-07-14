"""
Task executor implementation using Celery.
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional
from celery import states
from celery.result import AsyncResult

from .celery_app import app, get_celery_app
from .base import BaseTask, TaskStatus, TaskResult, TaskInfo, TaskSubmission
from .registry import task_registry


class TaskExecutor:
    """
    Task executor using Celery for managing long-running operations.
    """
    
    def __init__(self):
        """
        Initialize task executor with Celery app.
        """
        self.app = get_celery_app()
        
        # Status mapping from Celery to our TaskStatus
        self._status_mapping = {
            states.PENDING: TaskStatus.QUEUED,
            states.STARTED: TaskStatus.STARTED,
            states.SUCCESS: TaskStatus.FINISHED,
            states.FAILURE: TaskStatus.FAILED,
            states.RETRY: TaskStatus.QUEUED,
            states.REVOKED: TaskStatus.CANCELLED
        }
    
    def _get_queue_name_by_priority(self, priority: int) -> str:
        """Get queue name based on task priority."""
        if priority > 5:
            return 'high_priority'
        elif priority < 0:
            return 'low_priority'
        else:
            return 'default'
    
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
        
        # Get queue name based on priority
        queue_name = self._get_queue_name_by_priority(submission.priority)
        
        # Get the Celery task function
        celery_task = self.app.tasks.get(f'ctutor_backend.tasks.{submission.task_name}')
        if not celery_task:
            # Register the task dynamically if not found
            celery_task = self._register_celery_task(submission.task_name, task_class)
        
        # Submit task to Celery
        options = {
            'queue': queue_name,
            'priority': submission.priority,
        }
        
        if submission.delay:
            # Schedule for later execution
            result = celery_task.apply_async(
                kwargs=submission.parameters,
                countdown=submission.delay,
                **options
            )
        else:
            # Execute immediately
            result = celery_task.apply_async(
                kwargs=submission.parameters,
                **options
            )
        
        return result.id
    
    async def get_task_status(self, task_id: str) -> TaskInfo:
        """
        Get task execution status and information.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task information
            
        Raises:
            Exception: If task ID doesn't exist
        """
        result = AsyncResult(task_id, app=self.app)
        
        # Get task status
        status = self._status_mapping.get(result.status, TaskStatus.QUEUED)
        
        # Get task information
        task_info = TaskInfo(
            task_id=task_id,
            task_name=result.name or "unknown",
            status=status,
            created_at=datetime.utcnow(),  # Celery doesn't store creation time by default
            started_at=None,
            finished_at=None,
            progress=None,
            error=str(result.traceback) if result.failed() else None
        )
        
        # Get additional info if available
        if hasattr(result, 'info') and result.info:
            if isinstance(result.info, dict):
                task_info.progress = result.info.get('progress')
                if 'started_at' in result.info:
                    task_info.started_at = datetime.fromisoformat(result.info['started_at'])
                if 'finished_at' in result.info:
                    task_info.finished_at = datetime.fromisoformat(result.info['finished_at'])
        
        return task_info
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        """
        Get task execution result.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result
            
        Raises:
            Exception: If task ID doesn't exist
        """
        task_info = await self.get_task_status(task_id)
        result = AsyncResult(task_id, app=self.app)
        
        return TaskResult(
            task_id=task_id,
            status=task_info.status,
            result=result.result if result.ready() else None,
            error=task_info.error,
            created_at=task_info.created_at,
            started_at=task_info.started_at,
            finished_at=task_info.finished_at,
            progress=task_info.progress
        )
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a queued or running task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        try:
            self.app.control.revoke(task_id, terminate=True)
            return True
        except Exception:
            return False
    
    def start_worker(self, queues: Optional[list] = None, burst: bool = False) -> None:
        """
        Start a Celery worker to process tasks.
        
        Args:
            queues: List of queue names to process. If None, processes all queues.
            burst: If True, worker exits after processing all available jobs.
        """
        import subprocess
        import sys
        
        # Build celery worker command
        cmd = [sys.executable, '-m', 'celery', '-A', 'ctutor_backend.tasks.celery_app', 'worker']
        
        # Add queue specification
        if queues:
            cmd.extend(['--queues', ','.join(queues)])
        else:
            cmd.extend(['--queues', 'high_priority,default,low_priority'])
        
        # Add burst mode if requested
        if burst:
            cmd.append('--purge')  # Clear any existing messages before starting
            cmd.extend(['--max-tasks-per-child', '1'])
        
        # Add logging configuration
        cmd.extend(['--loglevel', 'info'])
        
        # Start the worker process
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to start Celery worker: {e}")
    
    def get_worker_status(self) -> Dict[str, Any]:
        """
        Get status information about Celery workers and queues.
        
        Returns:
            Dictionary containing worker and queue status information
        """
        try:
            # Get Celery inspection interface
            inspect = self.app.control.inspect()
            
            # Get active workers
            active_workers = inspect.active() or {}
            
            # Get queue lengths
            queue_lengths = {}
            try:
                from kombu import Connection
                with Connection(self.app.conf.broker_url) as conn:
                    for queue_name in ['high_priority', 'default', 'low_priority']:
                        try:
                            queue = conn.SimpleQueue(queue_name)
                            queue_lengths[queue_name] = queue.qsize()
                            queue.close()
                        except Exception:
                            queue_lengths[queue_name] = 'unknown'
            except Exception:
                queue_lengths = {'high_priority': 'unknown', 'default': 'unknown', 'low_priority': 'unknown'}
            
            return {
                'workers': {
                    'active_count': len(active_workers),
                    'workers': active_workers
                },
                'queues': queue_lengths,
                'broker_url': self.app.conf.broker_url,
                'status': 'connected' if active_workers or True else 'disconnected'  # Basic connection test
            }
            
        except Exception as e:
            return {
                'workers': {'active_count': 0, 'workers': {}},
                'queues': {'high_priority': 'error', 'default': 'error', 'low_priority': 'error'},
                'broker_url': self.app.conf.broker_url,
                'status': 'error',
                'error': str(e)
            }

    def _register_celery_task(self, task_name: str, task_class: type) -> Any:
        """
        Register a task class with Celery.
        
        Args:
            task_name: Name of the task
            task_class: Task class to register
            
        Returns:
            Celery task function
        """
        @self.app.task(bind=True, name=f'ctutor_backend.tasks.{task_name}')
        def celery_task_wrapper(celery_task, **kwargs):
            # Create task instance
            task_instance = task_class()
            
            # Update task state to STARTED
            celery_task.update_state(
                state=states.STARTED,
                meta={'started_at': datetime.utcnow().isoformat()}
            )
            
            try:
                # Execute task
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(task_instance.execute(**kwargs))
                    loop.run_until_complete(task_instance.on_success(result, **kwargs))
                    
                    # Update final state
                    celery_task.update_state(
                        state=states.SUCCESS,
                        meta={
                            'started_at': datetime.utcnow().isoformat(),
                            'finished_at': datetime.utcnow().isoformat()
                        }
                    )
                    
                    return result
                finally:
                    loop.close()
                    
            except Exception as e:
                # Handle failure
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    loop.run_until_complete(task_instance.on_failure(e, **kwargs))
                finally:
                    loop.close()
                
                raise e
        
        return celery_task_wrapper


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


def _execute_task_with_celery(celery_task, task_class, **kwargs):
    """
    Execute a BaseTask implementation within Celery.
    
    This utility function bridges Celery's synchronous execution model
    with the async BaseTask interface used throughout the framework.
    
    Args:
        celery_task: The Celery task instance (self)
        task_class: The BaseTask class to execute
        **kwargs: Task parameters
        
    Returns:
        Task execution result
    """
    # Create task instance
    task_instance = task_class()
    
    # Update task state to STARTED
    celery_task.update_state(
        state=states.STARTED,
        meta={
            'started_at': datetime.utcnow().isoformat(),
            'progress': {'status': 'started'}
        }
    )
    
    try:
        # Execute task in asyncio event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Execute the task
            result = loop.run_until_complete(task_instance.execute(**kwargs))
            
            # Call success hook
            loop.run_until_complete(task_instance.on_success(result, **kwargs))
            
            # Update final state
            celery_task.update_state(
                state=states.SUCCESS,
                meta={
                    'started_at': datetime.utcnow().isoformat(),
                    'finished_at': datetime.utcnow().isoformat(),
                    'progress': {'status': 'completed'}
                }
            )
            
            return result
            
        except Exception as e:
            # Call failure hook
            try:
                loop.run_until_complete(task_instance.on_failure(e, **kwargs))
            except Exception:
                pass  # Don't let failure hook errors mask the original error
            
            # Re-raise the original exception
            raise e
            
    except Exception as e:
        # Update error state
        celery_task.update_state(
            state=states.FAILURE,
            meta={
                'started_at': datetime.utcnow().isoformat(),
                'finished_at': datetime.utcnow().isoformat(),
                'error': str(e),
                'progress': {'status': 'failed'}
            }
        )
        raise e