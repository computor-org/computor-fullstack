"""
Task executor implementation using Celery.
"""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from celery import states
from celery.result import AsyncResult
from sqlalchemy import text
from sqlalchemy.orm import Session

from .celery_app import app, get_celery_app
from .base import BaseTask, TaskStatus, TaskResult, TaskInfo, TaskSubmission
from .registry import task_registry
from ctutor_backend.database import get_db


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
        Get task execution status and information from PostgreSQL.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task information
            
        Raises:
            Exception: If task ID doesn't exist
        """
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Query task from celery_taskmeta table
            query = text("""
                SELECT task_id, status, result, date_done, traceback, name, args, kwargs, worker, retries, queue
                FROM celery_taskmeta
                WHERE task_id = :task_id
            """)
            
            result = db.execute(query, {"task_id": task_id}).fetchone()
            
            if not result:
                raise KeyError(f"Task with ID {task_id} not found")
            
            # Parse result JSON if available
            task_data = None
            if result.result:
                try:
                    # Handle memoryview objects from database
                    if isinstance(result.result, memoryview):
                        try:
                            result_data = bytes(result.result).decode('utf-8')
                        except UnicodeDecodeError:
                            # If UTF-8 decoding fails, try latin-1 which accepts all byte values
                            result_data = bytes(result.result).decode('latin-1')
                    else:
                        result_data = result.result
                    
                    task_data = json.loads(result_data)
                except Exception:
                    # If JSON parsing fails, handle as binary data
                    if isinstance(result.result, memoryview):
                        # For binary data, we'll just indicate it exists but not try to decode it
                        task_data = {"_binary_data": True, "_size": len(result.result)}
                    else:
                        task_data = str(result.result) if result.result else None
            
            # Map Celery status to our TaskStatus
            status = self._status_mapping.get(result.status, TaskStatus.QUEUED)
            
            # Extract progress and timestamps from task data
            progress = None
            started_at = None
            finished_at = None
            
            if isinstance(task_data, dict):
                # Check for metadata in result
                if 'progress' in task_data:
                    progress = task_data.get('progress', {}).get('percentage')
                if 'started_at' in task_data:
                    started_at = datetime.fromisoformat(task_data['started_at'])
                if 'finished_at' in task_data:
                    finished_at = datetime.fromisoformat(task_data['finished_at'])
            
            # Use date_done from database for finished_at if not in metadata
            if not finished_at and result.date_done:
                finished_at = result.date_done
            
            # Parse args and kwargs if available
            args = None
            kwargs = None
            if result.args:
                try:
                    if isinstance(result.args, memoryview):
                        args_str = bytes(result.args).decode('utf-8')
                        args = json.loads(args_str)
                    else:
                        args = json.loads(result.args) if isinstance(result.args, str) else result.args
                except:
                    args = None
                    
            if result.kwargs:
                try:
                    if isinstance(result.kwargs, memoryview):
                        kwargs_str = bytes(result.kwargs).decode('utf-8')
                        kwargs = json.loads(kwargs_str)
                    else:
                        kwargs = json.loads(result.kwargs) if isinstance(result.kwargs, str) else result.kwargs
                except:
                    kwargs = None
            
            # Create task info with additional fields
            task_info = TaskInfo(
                task_id=task_id,
                task_name=result.name or "unknown",
                status=status,
                created_at=datetime.now(timezone.utc),  # Not stored in celery_taskmeta
                started_at=started_at,
                finished_at=finished_at,
                progress=progress,
                error=result.traceback,
                worker=result.worker,
                queue=result.queue,
                retries=result.retries,
                args=args,
                kwargs=kwargs
            )
            
            return task_info
            
        finally:
            db_gen.close()
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        """
        Get task execution result from PostgreSQL.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result
            
        Raises:
            Exception: If task ID doesn't exist
        """
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Query task from celery_taskmeta table
            query = text("""
                SELECT task_id, status, result, date_done, traceback, name, args, kwargs, worker, retries, queue
                FROM celery_taskmeta
                WHERE task_id = :task_id
            """)
            
            result_row = db.execute(query, {"task_id": task_id}).fetchone()
            
            if not result_row:
                raise KeyError(f"Task with ID {task_id} not found")
            
            # Parse result JSON if available
            task_result = None
            if result_row.result:
                try:
                    # Handle memoryview objects from database
                    if isinstance(result_row.result, memoryview):
                        try:
                            result_data = bytes(result_row.result).decode('utf-8')
                        except UnicodeDecodeError:
                            # If UTF-8 decoding fails, try latin-1 which accepts all byte values
                            result_data = bytes(result_row.result).decode('latin-1')
                    else:
                        result_data = result_row.result
                    
                    task_result = json.loads(result_data)
                except Exception:
                    # If JSON parsing fails, handle as binary data
                    if isinstance(result_row.result, memoryview):
                        # For binary data, we'll just indicate it exists but not try to decode it
                        task_result = {"_binary_data": True, "_size": len(result_row.result)}
                    else:
                        task_result = str(result_row.result) if result_row.result else None
            
            # Map Celery status to our TaskStatus
            status = self._status_mapping.get(result_row.status, TaskStatus.QUEUED)
            
            # Extract timestamps from metadata or use database values
            started_at = None
            finished_at = result_row.date_done
            progress = None
            
            if isinstance(task_result, dict) and 'started_at' in task_result:
                started_at = datetime.fromisoformat(task_result['started_at'])
            if isinstance(task_result, dict) and 'finished_at' in task_result:
                finished_at = datetime.fromisoformat(task_result['finished_at'])
            if isinstance(task_result, dict) and 'progress' in task_result:
                progress = task_result.get('progress', {}).get('percentage')
            
            return TaskResult(
                task_id=task_id,
                status=status,
                result=task_result,
                error=result_row.traceback,
                created_at=datetime.now(timezone.utc),  # Not stored in celery_taskmeta
                started_at=started_at,
                finished_at=finished_at,
                progress=progress
            )
            
        finally:
            db_gen.close()
    
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
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the database.
        
        This permanently removes the task record from celery_taskmeta table.
        Note: This does not cancel a running task, only removes the database record.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was deleted, False if not found
            
        Raises:
            Exception: If database operation fails
        """
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Check if task exists first
            check_query = text("SELECT 1 FROM celery_taskmeta WHERE task_id = :task_id")
            result = db.execute(check_query, {"task_id": task_id}).fetchone()
            
            if not result:
                return False
            
            # Delete the task
            delete_query = text("DELETE FROM celery_taskmeta WHERE task_id = :task_id")
            db.execute(delete_query, {"task_id": task_id})
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db_gen.close()
    
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

    async def list_tasks(self, limit: int = 100, offset: int = 0, status: Optional[str] = None) -> Dict[str, Any]:
        """
        List tasks from PostgreSQL celery_taskmeta table.
        
        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            status: Optional status filter (PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED)
            
        Returns:
            Dictionary containing task list and pagination info
        """
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Build the query
            base_query = """
                SELECT task_id, status, result, date_done, traceback, name, args, kwargs, worker, retries, queue
                FROM celery_taskmeta
            """
            
            count_query = "SELECT COUNT(*) FROM celery_taskmeta"
            
            # Add status filter if provided
            if status:
                base_query += " WHERE status = :status"
                count_query += " WHERE status = :status"
            
            # Add ordering and pagination
            base_query += " ORDER BY date_done DESC NULLS LAST LIMIT :limit OFFSET :offset"
            
            # Execute count query
            if status:
                total_result = db.execute(text(count_query), {"status": status})
            else:
                total_result = db.execute(text(count_query))
            total = total_result.scalar()
            
            # Execute main query
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            
            result = db.execute(text(base_query), params)
            
            # Process results
            tasks = []
            for row in result:
                # Parse result JSON if available
                result_data = None
                if row.result:
                    try:
                        # Handle memoryview objects from database
                        if isinstance(row.result, memoryview):
                            try:
                                result_str = bytes(row.result).decode('utf-8')
                            except UnicodeDecodeError:
                                # If UTF-8 decoding fails, try latin-1 which accepts all byte values
                                result_str = bytes(row.result).decode('latin-1')
                        else:
                            result_str = row.result
                        
                        result_data = json.loads(result_str)
                    except Exception:
                        # If JSON parsing fails, handle as binary data
                        if isinstance(row.result, memoryview):
                            # For binary data, we'll just indicate it exists but not try to decode it
                            result_data = {"_binary_data": True, "_size": len(row.result)}
                        else:
                            result_data = str(row.result) if row.result else None
                
                task_info = {
                    'task_id': row.task_id,
                    'task_name': row.name or 'unknown',
                    'status': row.status,
                    'date_done': row.date_done.isoformat() if row.date_done else None,
                    'worker': row.worker,
                    'retries': row.retries,
                    'queue': row.queue,
                    'has_result': result_data is not None,
                    'has_error': row.traceback is not None
                }
                tasks.append(task_info)
            
            return {
                'tasks': tasks,
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }
            
        except Exception as e:
            return {
                'tasks': [],
                'total': 0,
                'limit': limit,
                'offset': offset,
                'has_more': False,
                'error': str(e)
            }
        finally:
            db_gen.close()

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
                meta={'started_at': datetime.now(timezone.utc).isoformat()}
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
                            'started_at': datetime.now(timezone.utc).isoformat(),
                            'finished_at': datetime.now(timezone.utc).isoformat()
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
    
    # Store task metadata in the backend
    # This ensures name, worker, and queue are properly recorded
    from celery import current_task
    if hasattr(current_task.request, 'id'):
        # Update the backend with task metadata
        backend = celery_task.backend
        task_id = current_task.request.id
        
        # Store initial metadata
        backend.store_result(
            task_id,
            None,
            states.STARTED,
            request={
                'name': celery_task.name,
                'args': [],
                'kwargs': kwargs,
                'worker': current_task.request.hostname if hasattr(current_task.request, 'hostname') else None,
                'queue': current_task.request.delivery_info.get('routing_key') if hasattr(current_task.request, 'delivery_info') else None,
            }
        )
    
    # Inject progress update method
    async def update_progress(percentage: int, metadata: dict = None):
        """Update task progress via Celery."""
        celery_task.update_state(
            state=states.STARTED,
            meta={
                'started_at': datetime.now(timezone.utc).isoformat(),
                'progress': {
                    'percentage': percentage,
                    'metadata': metadata or {},
                    'status': 'running'
                }
            }
        )
    
    # Override the default update_progress method
    task_instance.update_progress = update_progress
    
    # Update task state to STARTED
    celery_task.update_state(
        state=states.STARTED,
        meta={
            'started_at': datetime.now(timezone.utc).isoformat(),
            'progress': {'status': 'started', 'percentage': 0}
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
                    'started_at': datetime.now(timezone.utc).isoformat(),
                    'finished_at': datetime.now(timezone.utc).isoformat(),
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
                'started_at': datetime.now(timezone.utc).isoformat(),
                'finished_at': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'progress': {'status': 'failed'}
            }
        )
        raise e