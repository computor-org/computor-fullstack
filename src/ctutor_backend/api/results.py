from typing import Annotated
from uuid import UUID
from fastapi import Depends
from ctutor_backend.api.api_builder import CrudRouter
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.permissions import check_permissions
from ctutor_backend.database import get_db
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.interface.results import ResultInterface, ResultStatus
from ctutor_backend.model.sqlalchemy_models.result import Result
from ctutor_backend.helpers import get_prefect_client
from sqlalchemy.orm import Session

# TODO: if result status is missing, ResultStatus.NOT_AVAILABLE should be returned
async def get_result_status(result: Result):
   async with get_prefect_client() as client:
      response = (await client.read_flow_run(result.test_system_id)).dict()
     
      return ResultStatus[response["state_type"]]

async def get_result(result: Result):
   async with get_prefect_client() as client:
      response = (await client.read_flow_run(result.test_system_id)).dict()
     
      return response

result_router = CrudRouter(ResultInterface)

@result_router.router.get("/{result_id}/status", response_model=ResultStatus)
async def result_status(permissions: Annotated[Principal, Depends(get_current_permissions)], result_id: UUID | str, db: Session = Depends(get_db)):
   
   result = check_permissions(permissions,Result,"get",db).filter(Result.id == result_id).first()

   return await get_result_status(result)