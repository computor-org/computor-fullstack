from typing import Annotated
from uuid import UUID
from fastapi import Depends
from ctutor_backend.api.api_builder import CrudRouter

from ctutor_backend.permissions.auth import get_current_permissions
from ctutor_backend.permissions.core import check_permissions
from ctutor_backend.permissions.principal import Principal
from ctutor_backend.database import get_db
from ctutor_backend.interface.results import ResultInterface
from ctutor_backend.model.result import Result
from ctutor_backend.tasks import get_task_executor
from sqlalchemy.orm import Session

from ctutor_backend.interface.tasks import TaskStatus

async def get_result_status(result: Result) -> TaskStatus:
    # Use Temporal task executor
    try:
        task_executor = get_task_executor()
        task_info = await task_executor.get_task_status(result.test_system_id)
        return task_info.status
    except Exception:
        return TaskStatus.FAILED

# async def get_result(result: Result):
#     # Use Temporal task executor
#     try:
#         task_executor = get_task_executor()
#         task_result = await task_executor.get_task_result(result.test_system_id)
        
#         return {
#             "state": task_result.status,
#             "result": task_result.result,
#             "info": {"error": task_result.error} if task_result.error else {},
#             "task_id": result.test_system_id
#         }
#     except Exception as e:
#         return {
#             "state": "UNKNOWN",
#             "result": None,
#             "info": {"error": str(e)},
#             "task_id": result.test_system_id
#         }

result_router = CrudRouter(ResultInterface)

@result_router.router.get("/{result_id}/status", response_model=TaskStatus)
async def result_status(permissions: Annotated[Principal, Depends(get_current_permissions)], result_id: UUID | str, db: Session = Depends(get_db)):
   
   result = check_permissions(permissions,Result,"get",db).filter(Result.id == result_id).first()

   return await get_result_status(result)