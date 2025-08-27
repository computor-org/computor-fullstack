from typing import Any
from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, or_, select
from ctutor_backend.api.exceptions import ForbiddenException
from ctutor_backend.interface import get_all_dtos
from ctutor_backend.interface.accounts import AccountInterface
from ctutor_backend.interface.course_families import CourseFamilyInterface
from ctutor_backend.interface.courses import CourseInterface
from ctutor_backend.interface.organizations import OrganizationInterface
from ctutor_backend.interface.permissions import Principal, allowed_course_role_ids
from ctutor_backend.interface.roles_claims import RoleClaimInterface
from ctutor_backend.interface.user_roles import UserRoleInterface
from ctutor_backend.interface.users import UserInterface
from ctutor_backend.model.auth import Account, User, Profile, StudentProfile, Session
from ctutor_backend.model.course import (
    Course, CourseContent, CourseContentKind, CourseContentType, CourseExecutionBackend, 
    CourseFamily, CourseMemberComment, CourseGroup, CourseMember, CourseRole,
    CourseSubmissionGroup, CourseSubmissionGroupMember, CourseSubmissionGroupGrading
)
from ctutor_backend.model.organization import Organization
from ctutor_backend.model.result import Result
from ctutor_backend.model.execution import ExecutionBackend
from ctutor_backend.model.role import Role, RoleClaim, UserRole
from ctutor_backend.model.group import Group, GroupClaim, UserGroup
from ctutor_backend.model.message import Message, MessageRead
from ctutor_backend.model.example import Example, ExampleRepository, ExampleVersion, ExampleDependency

def check_admin(permissions: Principal):
    if permissions.is_admin == True:
        return True
    return False

def user_courses(user_id: str, course_role_id: str, db: Session):

    cm_self = aliased(CourseMember)

    return (
        db.query(cm_self.course_id)
        .filter(
            cm_self.user_id == user_id,
            cm_self.course_role_id.in_(allowed_course_role_ids(course_role_id))
        )
        .subquery()
    )

def check_permissions(permissions: Principal, entity: Any, action: str, db: Session):

    if permissions.is_admin == True:
        return db.query(entity)
    
    permitted_user = permissions.user_id
    
    if entity == User:

        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get"]:
            # TODO: this line should be used soon
            # query = db.query(User).filter(User.id == permitted_user)
            
            cm_other = aliased(CourseMember)

            query = (
                db.query(User) \
                    .outerjoin(cm_other, cm_other.user_id == User.id)
                    .filter( 
                        or_(
                            User.id == permitted_user, \
                            cm_other.course_id.in_(select(user_courses(permitted_user,"_tutor",db)))
                        )
                    )
                    .distinct()
            )
            
            return query
        
        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})
    
    elif entity == Account:

        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get"]:
            query = db.query(Account).join(User, User.id == Account.user_id).filter(User.id == permitted_user)

        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})

        return query
    
    elif entity == Profile:

        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get","update"]:
            # Users can view and edit their own profile
            query = db.query(Profile).filter(Profile.user_id == permitted_user)

        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})

        return query
    
    elif entity == ExecutionBackend:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)

        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})
    
    elif entity == Organization:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        else:

            actions_mapper = {
                "get": "_student",
                "list": "_student"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(Course,cm_other.course_id == Course.id)
                .outerjoin(entity,entity.id == Course.organization_id)
                .filter(
                    cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db)))
                )                              
            )

            return query

    elif entity == CourseFamily:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        else:

            actions_mapper = {
                "get": "_student",
                "list": "_student"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(Course,cm_other.course_id == Course.id)
                .outerjoin(entity,entity.id == Course.course_family_id)
                .filter(
                    cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db)))
                )                              
            )

            return query

    elif entity == Course:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        else:

            actions_mapper = {
                "get": "_student",
                "list": "_student",
                "update": "_maintainer"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(entity,entity.id == cm_other.course_id)
                .filter(
                    cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db)))
                )                              
            )

            return query
    
    elif entity == CourseContent:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)

        else:

            actions_mapper = {
                "get": "_student",
                "list": "_student"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(entity,entity.course_id == cm_other.course_id)
                .filter(
                    cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db)))
                )                              
            )

            return query

    elif entity == CourseContentType:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)

        else:

            actions_mapper = {
                "get": "_student",
                "list": "_student",
                "update": "_maintainer"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(entity,entity.course_id == cm_other.course_id)
                .filter(
                    cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db)))
                )                              
            )

            return query

    elif entity == CourseContentKind:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get"]:
            query = db.query(entity)
        
        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})
        
        return query

    elif entity == CourseGroup:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)

        else:

            actions_mapper = {
                "get": "_tutor",
                "list": "_tutor",
                "update": "_maintainer"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(entity,entity.course_id == cm_other.course_id)
                .filter(
                    or_(
                        cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db))),
                        and_(
                            User.id == permitted_user,
                            cm_other.course_role_id == "_student",
                            action in ["get","list"],
                            entity.id == cm_other.course_group_id
                        )
                    )
                )
            )

            return query

    elif entity == CourseExecutionBackend:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)

        else:

            actions_mapper = {
                "get": "_tutor",
                "list": "_tutor",
                "update": "_maintainer"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(entity,entity.course_id == cm_other.course_id)
                .filter(
                    cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db)))
                )                              
            )

            return query

    elif entity == Result:
        actions_mapper = {
            "get": "_tutor",
            "list": "_tutor"
        }

        cm_other = aliased(CourseMember)

        query = (
            db.query(entity)
            .select_from(User)
            .outerjoin(cm_other, cm_other.user_id == User.id)
            .outerjoin(CourseContent,CourseContent.course_id == cm_other.course_id)
            .outerjoin(entity,entity.course_content_id == CourseContent.id)
            .filter(
                or_(
                    cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db))),
                    and_(
                        User.id == permitted_user,
                        cm_other.course_role_id == "_student",
                        action in ["get","list"],
                        cm_other.id == entity.course_member_id
                    )
                )
            )
        )

        return query

    elif entity == CourseMember:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)

        else:

            actions_mapper = {
                "get": "_tutor",
                "list": "_tutor",
                "update": "_maintainer"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(entity,entity.course_id == cm_other.course_id)
                .filter(
                    or_(
                        cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db))),
                        and_(
                            User.id == permitted_user,
                            cm_other.course_role_id == "_student",
                            action in ["get","list"],
                            entity.id == cm_other.id
                        )
                    )
                )
            )

            return query

    elif entity == CourseMemberComment:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)

        else:

            actions_mapper = {
                "get": "_tutor",
                "list": "_tutor"
            }

            cm_other = aliased(CourseMember)

            query = (
                db.query(entity)
                .select_from(User)
                .outerjoin(cm_other, cm_other.user_id == User.id)
                .outerjoin(entity,entity.course_id == cm_other.course_id)
                .filter(cm_other.course_id.in_(select(user_courses(permitted_user,actions_mapper[action],db))))
            )

            return query

    elif entity == Example:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get"]:
            query = db.query(entity)
        
        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})
        
        return query

    elif entity == ExampleRepository:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get"]:
            query = db.query(entity)
        
        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})
        
        return query

    elif entity == ExampleVersion:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get"]:
            query = db.query(entity)
        
        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})
        
        return query

    elif entity == ExampleDependency:
        resource = entity.__tablename__

        if permissions.permitted(resource,action):
            return db.query(entity)
        
        elif action in ["list","get","create"]:
            query = db.query(entity)
        
        else:
            raise ForbiddenException(detail={"entity": entity.__tablename__})
        
        return query

    else:
        print(f"Type: {entity} is something else")

    raise ForbiddenException(detail={"entity": entity.__tablename__})

def permitted_course_subquery(permissions: Principal, course_role_id: str, db: Session):

    cm_other = aliased(CourseMember)
    c_other = aliased(Course)
    u_other = aliased(User)

    return (
        db.query(c_other.id).select_from(u_other).filter(u_other.id == permissions.get_user_id_or_throw())
        .join(cm_other, cm_other.user_id == u_other.id)
        .join(c_other, c_other.id == cm_other.course_id)
        .filter(cm_other.course_role_id.in_(allowed_course_role_ids(course_role_id)))
    )

def get_permitted_course_ids(permissions: Principal, course_role_id: str, db: Session):
    # TODO: cache
    return [id for id, in permitted_course_subquery(permissions,course_role_id,db).all()]

def check_course_permissions(permissions: Principal, entity: Any, course_role_id: str, db: Session):

    if permissions.is_admin == True:
        return db.query(entity)

    subquery = permitted_course_subquery(permissions,course_role_id,db).subquery()

    query = db.query(entity)

    table_keys = entity.__table__.columns.keys()

    if "course_id" in table_keys:
        query = query.join(Course, Course.id == entity.course_id)

    elif "course_content_id" in table_keys:
        query = query.join(CourseContent, CourseContent.id == entity.course_content_id) \
                    .join(Course, Course.id == CourseContent.course_id)

    elif "course_member_id" in table_keys:
        query = query.join(CourseMember, CourseMember.id == entity.course_member_id) \
                    .join(Course, Course.id == CourseMember.course_id)
    
    query = query.filter(Course.id.in_(select(subquery)))
        
    return query


def get_all_claim_values():
    for j in get_all_dtos():
        for c in j().claim_values():
            yield c

def claims_user_manager():
    claims = []

    claims.extend(UserInterface().claim_values())
    claims.extend(AccountInterface().claim_values())
    claims.extend(RoleClaimInterface().claim_values())
    claims.extend(UserRoleInterface().claim_values())

    return claims

def claims_organization_manager():
    claims = []

    claims.extend(OrganizationInterface().claim_values())
    claims.extend(CourseFamilyInterface().claim_values())
    claims.extend(CourseInterface().claim_values())

    return claims

def db_apply_roles(role_id: str, claims: list[str], db: Session):

    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(RoleClaim).values([
        {"role_id": role_id, "claim_type": ct, "claim_value": cv}
        for ct, cv in claims
    ])

    stmt = stmt.on_conflict_do_nothing(
        index_elements=["role_id", "claim_type", "claim_value"]
    )
    db.execute(stmt)
    db.commit()

def db_get_roles_claims(user_id: str, db: Session):
    
    values = db.query(RoleClaim.role_id,RoleClaim.claim_type,RoleClaim.claim_value) \
                .select_from(User) \
                    .join(UserRole,UserRole.user_id == User.id) \
                        .join(Role,Role.id == UserRole.role_id) \
                            .join(RoleClaim,RoleClaim.role_id == Role.id) \
                                .filter(User.id == user_id).all()

    role_ids = list({row.role_id for row in values})
    claim_values = [(row.claim_type, row.claim_value) for row in values]

    return role_ids, claim_values

def db_get_claims(user_id: str, db: Session):
    
    values = (
        db.query(RoleClaim.claim_type,RoleClaim.claim_value)
        .select_from(User)
        .join(UserRole,UserRole.user_id == User.id)
        .join(Role,Role.id == UserRole.role_id)
        .join(RoleClaim,RoleClaim.role_id == Role.id)
        .filter(User.id == user_id)
        .distinct(RoleClaim.claim_type,RoleClaim.claim_value)
        .all()
    )

    return values

def db_get_course_claims(user_id: str, db: Session):
    
    course_members = (
        db.query(
            CourseMember.course_id,
            CourseMember.course_role_id
        )
        .select_from(User)
        .join(
            CourseMember,
            CourseMember.user_id == User.id
        ).filter(
            User.id == user_id
        ).all()
    )

    course_claims = []

    for course_id, course_role_id in course_members:
        course_claims.append(("permissions",f"{Course.__tablename__}:{course_role_id}:{course_id}"))

    return course_claims
