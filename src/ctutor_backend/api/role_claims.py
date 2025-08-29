from typing import Annotated
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from ctutor_backend.permissions.integration import adaptive_check_permissions as check_permissions, Principal
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.database import get_db
from ctutor_backend.interface.roles_claims import RoleClaimList, RoleClaimQuery, role_claim_search
from ctutor_backend.model.role import RoleClaim
role_claim_router = APIRouter()

@role_claim_router.get("", response_model=list[RoleClaimList])
async def list_role_claim(permissions: Annotated[Principal, Depends(get_current_permissions)], role_claim_query: RoleClaimQuery = Depends(), db: Session = Depends(get_db)):

    query = check_permissions(permissions,RoleClaim,"get",db)

    return role_claim_search(db,query,role_claim_query).all()
