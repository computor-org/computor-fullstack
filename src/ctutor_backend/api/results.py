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
from celery.result import AsyncResult
from ctutor_backend.tasks.celery_app import app as celery_app
from sqlalchemy.orm import Session

# TODO: if result status is missing, ResultStatus.NOT_AVAILABLE should be returned
async def get_result_status(result: Result):
    # Use Celery AsyncResult instead of Prefect
    task_result = AsyncResult(result.test_system_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        return ResultStatus.PENDING
    elif task_result.state == 'PROGRESS':
        return ResultStatus.RUNNING
    elif task_result.state == 'SUCCESS':
        return ResultStatus.COMPLETED
    elif task_result.state == 'FAILURE':
        return ResultStatus.FAILED
    else:
        return ResultStatus.NOT_AVAILABLE

async def get_result(result: Result):
    # Use Celery AsyncResult instead of Prefect
    task_result = AsyncResult(result.test_system_id, app=celery_app)
    
    return {
        "state": task_result.state,
        "result": task_result.result if task_result.successful() else None,
        "info": task_result.info,
        "task_id": result.test_system_id
    }

result_router = CrudRouter(ResultInterface)

@result_router.router.get("/{result_id}/status", response_model=ResultStatus)
async def result_status(permissions: Annotated[Principal, Depends(get_current_permissions)], result_id: UUID | str, db: Session = Depends(get_db)):
   
   result = check_permissions(permissions,Result,"get",db).filter(Result.id == result_id).first()

   return await get_result_status(result)