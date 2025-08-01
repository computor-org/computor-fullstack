"""
FastAPI endpoints for task management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, List, Any, Optional

from ctutor_backend.tasks import (
    get_task_executor, 
    TaskSubmission, 
    TaskInfo, 
    TaskResult,
    task_registry
)

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get("", response_model=Dict[str, Any])
async def list_tasks(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    status: Optional[str] = Query(None, description="Filter by task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED)")
):
    """
    List tasks with optional filtering and pagination.
    
    Args:
        limit: Maximum number of tasks to return (1-1000)
        offset: Number of tasks to skip for pagination
        status: Optional status filter
        
    Returns:
        Dictionary containing:
        - tasks: List of task information
        - total: Total number of tasks
        - limit: Applied limit
        - offset: Applied offset
        - has_more: Whether more tasks are available
        
    Example:
        GET /tasks?limit=10&offset=0&status=SUCCESS
    """
    try:
        task_executor = get_task_executor()
        result = await task_executor.list_tasks(limit=limit, offset=offset, status=status)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tasks: {str(e)}"
        )


@tasks_router.post("/submit", response_model=Dict[str, str])
async def submit_task(submission: TaskSubmission):
    """
    Submit a task for asynchronous execution.
    
    Args:
        submission: Task submission details
        
    Returns:
        Dictionary containing task_id and status
        
    Raises:
        HTTPException: If task type is not registered or submission fails
    """
    try:
        task_executor = get_task_executor()
        task_id = await task_executor.submit_task(submission)
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"Task '{submission.task_name}' submitted successfully"
        }
    
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task type: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit task: {str(e)}"
        )


@tasks_router.get("/{task_id}", response_model=TaskInfo)
async def get_task(task_id: str):
    """
    Get task information by ID.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task information including status, timestamps, and metadata
        
    Raises:
        HTTPException: If task is not found
    """
    return await get_task_status(task_id)


@tasks_router.get("/{task_id}/status", response_model=TaskInfo)
async def get_task_status(task_id: str):
    """
    Get task execution status and information.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task information including status and progress
        
    Raises:
        HTTPException: If task is not found
    """
    try:
        task_executor = get_task_executor()
        task_info = await task_executor.get_task_status(task_id)
        return task_info
    
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@tasks_router.get("/{task_id}/result", response_model=TaskResult)
async def get_task_result(task_id: str):
    """
    Get task execution result.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task result including output data and any errors
        
    Raises:
        HTTPException: If task is not found
    """
    try:
        task_executor = get_task_executor()
        task_result = await task_executor.get_task_result(task_id)
        return task_result
    
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task result: {str(e)}"
        )


@tasks_router.delete("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    Cancel a queued or running task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Cancellation status
        
    Raises:
        HTTPException: If cancellation fails
    """
    try:
        task_executor = get_task_executor()
        cancelled = await task_executor.cancel_task(task_id)
        
        if cancelled:
            return {
                "task_id": task_id,
                "status": "cancelled",
                "message": "Task cancelled successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found or cannot be cancelled"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )


@tasks_router.delete("/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a task from the database.
    
    Note: Temporal doesn't support direct deletion of workflow history.
    Use cancellation or retention policies instead.
    
    Args:
        task_id: Task ID to delete
        
    Returns:
        Error message explaining limitation
        
    Raises:
        HTTPException: Always returns 501 Not Implemented for Temporal
    """
    try:
        task_executor = get_task_executor()
        deleted = await task_executor.delete_task(task_id)
        
        if deleted:
            return {
                "task_id": task_id,
                "status": "deleted",
                "message": "Task deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )
    
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=str(e)
        )
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete task: {str(e)}"
        )


@tasks_router.get("/types", response_model=List[str])
async def list_task_types():
    """
    Get list of available task types.
    
    Returns:
        List of registered task names
    """
    try:
        registered_tasks = task_registry.list_tasks()
        return list(registered_tasks.keys())
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list task types: {str(e)}"
        )


@tasks_router.get("/workers/status", response_model=Dict[str, Any])
async def get_worker_status():
    """
    Get Temporal worker and queue status information.
    
    Returns:
        Dictionary containing worker status, queue information, and connection details
    """
    try:
        task_executor = get_task_executor()
        status_info = task_executor.get_worker_status()
        return status_info
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get worker status: {str(e)}"
        )