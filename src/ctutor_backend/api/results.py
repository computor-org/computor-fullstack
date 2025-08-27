from typing import Annotated
from uuid import UUID
from fastapi import Depends
from ctutor_backend.api.api_builder import CrudRouter
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.permissions import check_permissions
from ctutor_backend.database import get_db
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.results import ResultInterface, ResultStatus
from ctutor_backend.model.result import Result
from ctutor_backend.tasks import get_task_executor
from sqlalchemy.orm import Session

from ctutor_backend.tasks.base import TaskStatus

# TODO: if result status is missing, ResultStatus.NOT_AVAILABLE should be returned
async def get_result_status(result: Result):
    # Use Temporal task executor
    try:
        task_executor = get_task_executor()
        task_info = await task_executor.get_task_status(result.test_system_id)
        
        # Map task status to result status
        if task_info.status == TaskStatus.QUEUED:
            return ResultStatus.PENDING
        elif task_info.status == TaskStatus.STARTED:
            return ResultStatus.RUNNING
        elif task_info.status == TaskStatus.FINISHED:
            return ResultStatus.COMPLETED
        elif task_info.status == TaskStatus.FAILED:
            return ResultStatus.FAILED
        else:
            return ResultStatus.NOT_AVAILABLE
    except Exception:
        return ResultStatus.NOT_AVAILABLE

async def get_result(result: Result):
    # Use Temporal task executor
    try:
        task_executor = get_task_executor()
        task_result = await task_executor.get_task_result(result.test_system_id)
        
        return {
            "state": task_result.status,
            "result": task_result.result,
            "info": {"error": task_result.error} if task_result.error else {},
            "task_id": result.test_system_id
        }
    except Exception as e:
        return {
            "state": "UNKNOWN",
            "result": None,
            "info": {"error": str(e)},
            "task_id": result.test_system_id
        }

result_router = CrudRouter(ResultInterface)

@result_router.router.get("/{result_id}/status", response_model=ResultStatus)
async def result_status(permissions: Annotated[Principal, Depends(get_current_permissions)], result_id: UUID | str, db: Session = Depends(get_db)):
   
   result = check_permissions(permissions,Result,"get",db).filter(Result.id == result_id).first()

   return await get_result_status(result)