from typing import Optional
from uuid import UUID
from sqlalchemy import func, case, select
from sqlalchemy.orm import Session
from ctutor_backend.api.exceptions import NotFoundException
from ctutor_backend.model.course import CourseSubmissionGroupMember
from ctutor_backend.model.result import Result
from ctutor_backend.model.auth import User
from ctutor_backend.model.course import Course, CourseContent, CourseContentKind, CourseMember, CourseSubmissionGroup, CourseSubmissionGroupGrading

def latest_result_subquery(user_id: UUID | str | None, course_member_id: UUID | str | None, course_content_id: UUID | str | None, db: Session, submission: Optional[bool] = None):

    query = db.query(
                Result.course_content_id,
                func.max(Result.created_at).label("latest_result_date")
            )
    
    if user_id != None:
        query = query.join(CourseSubmissionGroup, CourseSubmissionGroup.id == Result.course_submission_group_id) \
            .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) \
            .join(CourseMember, CourseMember.id == CourseSubmissionGroupMember.course_member_id) \
            .filter(CourseMember.user_id == user_id)
    elif course_member_id != None:
        query = query.join(CourseSubmissionGroup, CourseSubmissionGroup.id == Result.course_submission_group_id) \
            .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) \
            .filter(CourseSubmissionGroupMember.course_member_id == course_member_id)
    
    query = query.filter(Result.status == 0)
    
    if course_content_id != None:
        query = query.filter(Result.course_content_id == course_content_id)
    
    if submission != None:
        query = query.filter(Result.submit == submission)
    
    return query.group_by(Result.course_content_id).subquery()

def results_count_subquery(user_id: UUID | str | None, course_member_id: UUID | str | None, course_content_id: UUID | str | None, db: Session):

    query = db.query(
                Result.course_content_id,
                func.count(Result.id).label("total_results_count"),
                func.count(case((Result.submit == True, 1))).label("submitted_count")
            )

    if user_id != None:
        query = query.join(CourseSubmissionGroup, CourseSubmissionGroup.id == Result.course_submission_group_id) \
            .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) \
            .join(CourseMember, CourseMember.id == CourseSubmissionGroupMember.course_member_id) \
            .filter(CourseMember.user_id == user_id)
    elif course_member_id != None:
        query = query.join(CourseSubmissionGroup, CourseSubmissionGroup.id == Result.course_submission_group_id) \
            .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) \
            .filter(CourseSubmissionGroupMember.course_member_id == course_member_id)

    query = query.filter(Result.status == 0)
    
    if course_content_id != None:
        query = query.filter(Result.course_content_id == course_content_id)
    
    return query.group_by(Result.course_content_id).subquery()

# def submitted_result(user_id: UUID | str | None, course_member_id: UUID | str | None, course_content_id: UUID | str | None, db: Session,):

#     query = db.query(
#         Result.course_content_id,
#         func.count(Result.id).label("submitted_count")
#     )

#     if user_id != None:
#         query = query.join(CourseMember, CourseMember.user_id == user_id) \
#             .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == CourseMember.id)
#     elif course_member_id != None:
#         query = query.join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == course_member_id)

#     if course_content_id == None:
#         query = query.filter(Result.course_submission_group_id == CourseSubmissionGroupMember.course_submission_group_id, \
#                     Result.status == 0,
#                     Result.submit == True)
#     else:
#         query = query.filter(Result.course_submission_group_id == CourseSubmissionGroupMember.course_submission_group_id, \
#                     CourseSubmissionGroupMember.course_content_id == course_content_id, \
#                     Result.status == 0,
#                     Result.submit == True)

    return query.group_by(Result.course_content_id).subquery()

def latest_grading_subquery(db: Session):
    """
    Get the latest grading for each course submission group.
    Returns a subquery with course_submission_group_id, status, and grading.
    """
    return db.query(
        CourseSubmissionGroupGrading.course_submission_group_id,
        CourseSubmissionGroupGrading.status,
        CourseSubmissionGroupGrading.grading,
        func.row_number().over(
            partition_by=CourseSubmissionGroupGrading.course_submission_group_id,
            order_by=CourseSubmissionGroupGrading.created_at.desc()
        ).label('rn')
    ).subquery()

def user_course_content_query(user_id: UUID | str, course_content_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(user_id,None,course_content_id,db)
    results_count_sub = results_count_subquery(user_id,None,course_content_id,db)
    latest_grading_sub = latest_grading_subquery(db)

    # Subquery to get only the user's submission groups
    # Use select() explicitly to avoid SQLAlchemy warning
    user_submission_groups = select(CourseSubmissionGroup.id).select_from(
        CourseSubmissionGroup
    ).join(
        CourseSubmissionGroupMember,
        CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id
    ).join(
        CourseMember,
        CourseSubmissionGroupMember.course_member_id == CourseMember.id
    ).where(
        CourseMember.user_id == user_id
    ).subquery()

    # Query specific course content including those without submission groups
    course_contents_result = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count,
            latest_grading_sub.c.status,
            latest_grading_sub.c.grading
        ) \
        .select_from(User) \
        .filter(User.id == user_id) \
        .join(CourseMember, CourseMember.user_id == User.id) \
        .join(Course, Course.id == CourseMember.course_id) \
        .join(CourseContent, (CourseContent.course_id == Course.id) & (CourseContent.id == course_content_id)) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(CourseSubmissionGroup, 
                   (CourseSubmissionGroup.course_content_id == CourseContent.id) &
                   (CourseSubmissionGroup.id.in_(select(user_submission_groups.c.id)))) \
        .outerjoin(CourseSubmissionGroupMember, 
                   (CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) &
                   (CourseSubmissionGroupMember.course_member_id == CourseMember.id)) \
        .outerjoin(
            latest_result_sub,
            CourseContent.id == latest_result_sub.c.course_content_id
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            CourseContent.id == results_count_sub.c.course_content_id
        ).outerjoin(
            latest_grading_sub,
            (latest_grading_sub.c.course_submission_group_id == CourseSubmissionGroup.id) &
            (latest_grading_sub.c.rn == 1)
        ).distinct().first()
        
    if course_contents_result == None:
        raise NotFoundException()

    return course_contents_result

def user_course_content_list_query(user_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(user_id,None,None,db)
    results_count_sub = results_count_subquery(user_id,None,None,db)
    latest_grading_sub = latest_grading_subquery(db)

    # Subquery to get only the user's submission groups
    # Use select() explicitly to avoid SQLAlchemy warning
    user_submission_groups = select(CourseSubmissionGroup.id).select_from(
        CourseSubmissionGroup
    ).join(
        CourseSubmissionGroupMember,
        CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id
    ).join(
        CourseMember,
        CourseSubmissionGroupMember.course_member_id == CourseMember.id
    ).where(
        CourseMember.user_id == user_id
    ).subquery()

    # Query ALL course contents where the user is a member, including those without submission groups
    query = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count,
            latest_grading_sub.c.status,
            latest_grading_sub.c.grading
        ) \
        .select_from(User) \
        .filter(User.id == user_id) \
        .join(CourseMember, CourseMember.user_id == User.id) \
        .join(Course, Course.id == CourseMember.course_id) \
        .join(CourseContent, CourseContent.course_id == Course.id) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(CourseSubmissionGroup, 
                   (CourseSubmissionGroup.course_content_id == CourseContent.id) &
                   (CourseSubmissionGroup.id.in_(select(user_submission_groups.c.id)))) \
        .outerjoin(CourseSubmissionGroupMember, 
                   (CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) &
                   (CourseSubmissionGroupMember.course_member_id == CourseMember.id)) \
        .outerjoin(
            latest_result_sub,
            CourseContent.id == latest_result_sub.c.course_content_id
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            CourseContent.id == results_count_sub.c.course_content_id
        ).outerjoin(
            latest_grading_sub,
            (latest_grading_sub.c.course_submission_group_id == CourseSubmissionGroup.id) &
            (latest_grading_sub.c.rn == 1)
        ).distinct()

    return query

def course_member_course_content_query(course_member_id: UUID | str, course_content_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(None,course_member_id,course_content_id,db)
    results_count_sub = results_count_subquery(None,course_member_id,course_content_id,db)
    latest_grading_sub = latest_grading_subquery(db)

    course_contents_result = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count,
            latest_grading_sub.c.status,
            latest_grading_sub.c.grading
        ) \
        .select_from(CourseMember) \
        .filter(CourseMember.id == course_member_id) \
        .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == CourseMember.id) \
        .join(CourseSubmissionGroup, CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .join(CourseContent, (CourseContent.id == CourseSubmissionGroup.course_content_id) & (CourseContent.id == course_content_id)) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(
            latest_result_sub,
            CourseContent.id == latest_result_sub.c.course_content_id
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            CourseContent.id == results_count_sub.c.course_content_id
        ).outerjoin(
            latest_grading_sub,
            (latest_grading_sub.c.course_submission_group_id == CourseSubmissionGroup.id) &
            (latest_grading_sub.c.rn == 1)
        ).first()
        
    if course_contents_result == None:
        raise NotFoundException()

    return course_contents_result

def course_member_course_content_list_query(course_member_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(None,course_member_id,None,db,True)
    results_count_sub = results_count_subquery(None,course_member_id,None,db)
    latest_grading_sub = latest_grading_subquery(db)

    # Subquery to get the member's submission groups
    member_submission_groups = select(CourseSubmissionGroup).select_from(
        CourseSubmissionGroup
    ).join(
        CourseSubmissionGroupMember,
        CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id
    ).where(
        CourseSubmissionGroupMember.course_member_id == course_member_id
    ).subquery()

    # Query ALL course contents for the course where the user is a member
    query = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count,
            latest_grading_sub.c.status,
            latest_grading_sub.c.grading
        ) \
        .select_from(CourseMember) \
        .filter(CourseMember.id == course_member_id) \
        .join(Course, Course.id == CourseMember.course_id) \
        .join(CourseContent, CourseContent.course_id == Course.id) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(CourseSubmissionGroup,
                   (CourseSubmissionGroup.course_content_id == CourseContent.id) &
                   (CourseSubmissionGroup.id.in_(select(member_submission_groups.c.id)))) \
        .outerjoin(
            latest_result_sub,
            CourseContent.id == latest_result_sub.c.course_content_id
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            CourseContent.id == results_count_sub.c.course_content_id
        ).outerjoin(
            latest_grading_sub,
            (latest_grading_sub.c.course_submission_group_id == CourseSubmissionGroup.id) &
            (latest_grading_sub.c.rn == 1)
        )

    return query

def course_course_member_list_query(db: Session):

    latest_result_subquery =  db.query(
                    Result.course_content_id,
                    CourseMember.id.label("course_member_id"),
                    func.max(Result.created_at).label("latest_result_date")
                ) \
        .join(CourseSubmissionGroup, CourseSubmissionGroup.id == Result.course_submission_group_id) \
        .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) \
        .join(CourseMember, CourseMember.id == CourseSubmissionGroupMember.course_member_id) \
        .filter(
                Result.status == 0,
                Result.submit == True
        ) \
        .group_by(Result.course_content_id, CourseMember.id).subquery()

    latest_result_per_member = db.query(
        latest_result_subquery.c.course_member_id,
        func.max(latest_result_subquery.c.latest_result_date).label("latest_result_date")
    ) \
        .group_by(latest_result_subquery.c.course_member_id) \
        .subquery()

    course_member_results = db.query(
            CourseMember,
            latest_result_per_member.c.latest_result_date
        ) \
        .select_from(CourseMember) \
        .outerjoin(latest_result_per_member,latest_result_per_member.c.course_member_id == CourseMember.id)

    return course_member_results