"""
FastAPI endpoints for task management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any
from celery.exceptions import NotRegistered

from ctutor_backend.tasks import (
    get_task_executor, 
    TaskSubmission, 
    TaskInfo, 
    TaskResult,
    task_registry
)

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


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
    
    except (NotRegistered, KeyError):
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
    
    except (NotRegistered, KeyError):
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
    Get Celery worker and queue status information.
    
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