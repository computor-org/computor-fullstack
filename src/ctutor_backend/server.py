from contextlib import asynccontextmanager
import os
import shutil
from ctutor_backend.api.filesystem import mirror_db_to_filesystem
from ctutor_backend.api.permissions import claims_organization_manager, claims_user_manager, db_apply_roles
from ctutor_backend.interface.roles import RoleInterface
from ctutor_backend.interface.tokens import encrypt_api_key
from ctutor_backend.model.auth import User
from ctutor_backend.model.execution import ExecutionBackend
from ctutor_backend.model.role import UserRole
from ctutor_backend.redis_cache import get_redis_client
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ctutor_backend.api.api_builder import CrudRouter, LookUpRouter
from ctutor_backend.api.tests import tests_router
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.sso import sso_router
from ctutor_backend.plugins.registry import initialize_plugin_registry
from sqlalchemy.orm import Session
from ctutor_backend.database import get_db
from ctutor_backend.interface.deployments import DeploymentFactory
from ctutor_backend.interface.accounts import AccountInterface
from ctutor_backend.interface.deployments import ExecutionBackendConfig
from ctutor_backend.interface.execution_backends import ExecutionBackendInterface
from ctutor_backend.interface.groups import GroupInterface
from ctutor_backend.interface.profiles import ProfileInterface
from ctutor_backend.interface.sessions import SessionInterface
from ctutor_backend.interface.submission_group_members import SubmissionGroupMemberInterface
from ctutor_backend.interface.submission_groups import SubmissionGroupInterface
from ctutor_backend.interface.users import UserInterface
from ctutor_backend.interface.course_families import CourseFamilyInterface
from ctutor_backend.interface.course_groups import CourseGroupInterface
from ctutor_backend.interface.course_roles import CourseRoleInterface
from ctutor_backend.interface.course_content_types import CourseContentTypeInterface
from ctutor_backend.interface.course_content_kind import CourseContentKindInterface
from ctutor_backend.api.course_execution_backend import course_execution_backend_router
from ctutor_backend.api.courses import course_router
from ctutor_backend.api.system import system_router
from ctutor_backend.api.course_contents import course_content_router
from ctutor_backend.settings import settings 
from ctutor_backend.api.students import student_router
from ctutor_backend.api.results import result_router
from ctutor_backend.api.tutor import tutor_router
from ctutor_backend.api.lecturer import lecturer_router
from ctutor_backend.api.signup import signup_router
from ctutor_backend.api.organizations import organization_router
from ctutor_backend.api.course_members import course_member_router
# from ctutor_backend.api.services import services_router
from ctutor_backend.api.user_roles import user_roles_router
from ctutor_backend.api.role_claims import role_claim_router
from ctutor_backend.api.user import user_router
from ctutor_backend.api.info import info_router
from ctutor_backend.api.tasks import tasks_router
from ctutor_backend.api.storage import storage_router
from ctutor_backend.api.examples import examples_router
from ctutor_backend.api.course_content_examples import course_content_examples_router
from ctutor_backend.interface.example import ExampleRepositoryInterface, ExampleInterface

async def init_execution_backend_api(db: Session):

    execution_backends_raw = DeploymentFactory.read_deployment_from_file_raw("data/deployments/system-init.yaml")["execution_backends"]

    for eb in execution_backends_raw:

        execution_backend = ExecutionBackendConfig(**eb)

        eb = db.query(ExecutionBackend).filter(ExecutionBackend.slug == execution_backend.slug).first()

        if eb == None:

            db.add(ExecutionBackend(
                type=execution_backend.type,
                slug=execution_backend.slug,
                properties=execution_backend.settings
            ))
        else:
            eb.properties=execution_backend.settings
        
        db.commit()

async def init_admin_user(db: Session):

    username = os.environ.get("EXECUTION_BACKEND_API_USER")
    password = os.environ.get("EXECUTION_BACKEND_API_PASSWORD")

    admin = db.query(User).filter(User.username == username).first()

    if admin != None:
        return
    
    try:
        admin_user = User(
            given_name="Admin",
            family_name="System",
            username=username,
            password=encrypt_api_key(password)
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        db.add(
            UserRole(
                user_id=admin_user.id,
                role_id="_admin"
            )
        )
        db.commit()

    except:
        print("[CRITICAL BUG] Admin user could not be created. The backend is shutting down.")
        quit(1)

async def startup_logic():

    with next(get_db()) as db:
        db_apply_roles("_user_manager",claims_user_manager(),db)
        db_apply_roles("_organization_manager",claims_organization_manager(),db)

        repo_dirs = os.path.join(settings.API_LOCAL_STORAGE_DIR,"repositories")
        if os.path.exists(repo_dirs):
            shutil.rmtree(repo_dirs)

        await init_admin_user(db)
        await init_execution_backend_api(db)
        await mirror_db_to_filesystem(db)
    
    # Initialize plugin registry
    await initialize_plugin_registry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # redis_client = await get_redis_client()
    # RedisCache(redis_client)

    if settings.DEBUG_MODE == "production":
        await startup_logic()
    else:
        # Initialize plugin registry in development mode
        await initialize_plugin_registry()
    
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

CrudRouter(UserInterface).register_routes(app)
CrudRouter(AccountInterface).register_routes(app)
CrudRouter(GroupInterface).register_routes(app)
CrudRouter(ProfileInterface).register_routes(app)
CrudRouter(SessionInterface).register_routes(app)
course_router.register_routes(app)
organization_router.register_routes(app)
CrudRouter(CourseFamilyInterface).register_routes(app)
CrudRouter(CourseGroupInterface).register_routes(app)
course_member_router.register_routes(app)
LookUpRouter(CourseRoleInterface).register_routes(app)
LookUpRouter(RoleInterface).register_routes(app)
CrudRouter(ExecutionBackendInterface).register_routes(app)
CrudRouter(ExampleRepositoryInterface).register_routes(app)
# CrudRouter(ExampleInterface).register_routes(app) # Examples should only be created via upload

CrudRouter(SubmissionGroupInterface).register_routes(app)
CrudRouter(SubmissionGroupMemberInterface).register_routes(app)

app.include_router(
    course_execution_backend_router,
    prefix="/course-execution-backends",
    tags=["course execution backends"],
    dependencies=[Depends(get_current_permissions)]
)

CrudRouter(CourseContentKindInterface).register_routes(app)
CrudRouter(CourseContentTypeInterface).register_routes(app)

course_content_router.register_routes(app)

result_router.register_routes(app)

app.include_router(
    system_router,
    prefix="/system",
    tags=["system"],
    dependencies=[Depends(get_current_permissions),Depends(get_redis_client)]
)

app.include_router(
    tests_router,
    prefix="/tests",
    tags=["tests"],
    dependencies=[Depends(get_current_permissions)]
)

app.include_router(
    student_router,
    prefix="/students",
    tags=["students"],
    dependencies=[Depends(get_current_permissions),Depends(get_redis_client)]
)

app.include_router(
    tutor_router,
    prefix="/tutors",
    tags=["tutors"],
    dependencies=[Depends(get_current_permissions),Depends(get_redis_client)]
)

app.include_router(
    lecturer_router,
    prefix="/lecturer",
    tags=["lecturers"],
    dependencies=[Depends(get_current_permissions),Depends(get_redis_client)]
)

app.include_router(
    signup_router,
    prefix="/signup",
    tags=["signup","gitlab"]
)

# app.include_router(
#     services_router,
#     prefix="/services",
#     tags=["services"]
# )

app.include_router(
    user_roles_router,
    prefix="/user-roles",
    tags=["user","roles"]
)

app.include_router(
    role_claim_router,
    prefix="/role-claims",
    tags=["roles", "claims"]
)

app.include_router(
    user_router,
    prefix="/user",
    tags=["user", "me"]
)

app.include_router(
    info_router,
    prefix="/info",
    tags=["info"]
)

app.include_router(
    tasks_router,
    tags=["tasks"],
    dependencies=[Depends(get_current_permissions)]
)

app.include_router(
    sso_router,
    tags=["sso", "authentication"]
)

app.include_router(
    storage_router,
    tags=["storage"],
    dependencies=[Depends(get_current_permissions), Depends(get_redis_client)]
)

app.include_router(
    examples_router,
    tags=["examples"],
    dependencies=[Depends(get_current_permissions), Depends(get_redis_client)]
)

app.include_router(
    course_content_examples_router,
    tags=["course-content-examples"],
    dependencies=[Depends(get_current_permissions), Depends(get_redis_client)]
)

@app.head("/", status_code=204)
def get_status_head():
    return