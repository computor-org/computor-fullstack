from typing import Optional
from uuid import UUID
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from ctutor_backend.api.exceptions import NotFoundException
from ctutor_backend.model.course import CourseSubmissionGroupMember
from ctutor_backend.model.result import Result
from ctutor_backend.model.auth import User
from ctutor_backend.model.course import CourseContent, CourseContentKind, CourseMember, CourseSubmissionGroup

def latest_result_subquery(user_id: UUID | str | None, course_member_id: UUID | str | None, course_content_id: UUID | str | None, db: Session, submission: Optional[bool] = None):

    query = db.query(
                Result.course_content_id,
                func.max(Result.created_at).label("latest_result_date")
            )
    
    if user_id != None:
        query = query.join(CourseMember, CourseMember.user_id == user_id) \
            .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == CourseMember.id)
    elif course_member_id != None:
        query = query.join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == course_member_id)
    
    if course_content_id == None:
        query = query.filter(
            Result.course_submission_group_id == CourseSubmissionGroupMember.course_submission_group_id, 
            Result.status == 0)
    else:
        query = query.filter(
            Result.course_submission_group_id == CourseSubmissionGroupMember.course_submission_group_id, 
            Result.status == 0,
            CourseSubmissionGroupMember.course_content_id == course_content_id)
    
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
        query = query.join(CourseMember, CourseMember.user_id == user_id) \
            .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == CourseMember.id)
    elif course_member_id != None:
        query = query.join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_member_id == course_member_id)

    if course_content_id == None:
        query = query.filter(Result.course_submission_group_id == CourseSubmissionGroupMember.course_submission_group_id, \
                    Result.status == 0)
    else:
        query = query.filter(Result.course_submission_group_id == CourseSubmissionGroupMember.course_submission_group_id, \
                    CourseSubmissionGroupMember.course_content_id == course_content_id, \
                    Result.status == 0)
    
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

def user_course_content_query(user_id: UUID | str, course_content_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(user_id,None,course_content_id,db)
    results_count_sub = results_count_subquery(user_id,None,course_content_id,db)
    # submitted_sub = submitted_result(user_id,None,course_content_id,db)

    course_contents_result = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count
        ) \
        .select_from(User) \
        .filter(User.id == user_id) \
        .join(CourseMember, CourseMember.user_id == User.id) \
        .join(Course,Course.id == CourseMember.course_id) \
        .join(CourseContent,CourseContent.id == course_content_id) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(CourseSubmissionGroupMember,
              CourseSubmissionGroupMember.course_member_id == CourseMember.id) \
        .outerjoin(CourseSubmissionGroup, \
            CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .outerjoin(
            latest_result_sub,
            (CourseContent.id == latest_result_sub.c.course_content_id) & 
            (CourseContent.course_id == Course.id)
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            (CourseContent.id == results_count_sub.c.course_content_id) &
            (CourseContent.course_id == Course.id)
        ).first() # \
        # .outerjoin(
        #     submitted_sub,
        #     CourseContent.id == results_count_sub.c.course_content_id
        # ).first()
        
    if course_contents_result == None:
        raise NotFoundException()

    return course_contents_result

def user_course_content_list_query(user_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(user_id,None,None,db)
    results_count_sub = results_count_subquery(user_id,None,None,db)
    #submitted_sub = submitted_result(user_id,None,None,db)

    query = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count
        ) \
        .select_from(User) \
        .filter(User.id == user_id) \
        .join(CourseMember, CourseMember.user_id == User.id) \
        .join(Course,Course.id == CourseMember.course_id) \
        .join(CourseContent,CourseContent.course_id == Course.id) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(CourseSubmissionGroupMember,
              (CourseSubmissionGroupMember.course_member_id == CourseMember.id) &
              (CourseSubmissionGroupMember.course_content_id == CourseContent.id)) \
        .outerjoin(CourseSubmissionGroup, CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .outerjoin(
            latest_result_sub,
            CourseSubmissionGroupMember.course_content_id == latest_result_sub.c.course_content_id
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            (CourseSubmissionGroupMember.course_content_id == results_count_sub.c.course_content_id)
        ) # \
        # .outerjoin(
        #     submitted_sub,
        #     CourseContent.id == submitted_sub.c.course_content_id
        # )

    return query

def course_member_course_content_query(course_member_id: UUID | str, course_content_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(None,course_member_id,course_content_id,db)
    results_count_sub = results_count_subquery(None,course_member_id,course_content_id,db)
    #submitted_sub = submitted_result(None,course_member_id,None,db)

    course_contents_result = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count
        ) \
        .select_from(CourseMember) \
        .filter(CourseMember.id == course_member_id) \
        .join(Course,Course.id == CourseMember.course_id) \
        .join(CourseContent,CourseContent.id == course_content_id) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(CourseSubmissionGroupMember,
              CourseSubmissionGroupMember.course_member_id == CourseMember.id) \
        .outerjoin(CourseSubmissionGroup, \
            CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .outerjoin(
            latest_result_sub,
            (CourseContent.id == latest_result_sub.c.course_content_id) & 
            (CourseContent.course_id == Course.id)
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            (CourseContent.id == results_count_sub.c.course_content_id) &
            (CourseContent.course_id == Course.id)
        ).first() #\
        # .outerjoin(
        #     submitted_sub,
        #     CourseContent.id == submitted_sub.c.course_content_id
        # ).first()
        
    if course_contents_result == None:
        raise NotFoundException()

    return course_contents_result

def course_member_course_content_list_query(course_member_id: UUID | str, db: Session):

    latest_result_sub = latest_result_subquery(None,course_member_id,None,db,True)
    results_count_sub = results_count_subquery(None,course_member_id,None,db)
    #submitted_sub = submitted_result(None,course_member_id,None,db)

    query = db.query(
            CourseContent,
            results_count_sub.c.total_results_count,
            Result,
            CourseSubmissionGroup,
            results_count_sub.c.submitted_count
        ) \
        .select_from(CourseMember) \
        .filter(CourseMember.id == course_member_id) \
        .join(Course,Course.id == CourseMember.course_id) \
        .join(CourseContent,CourseContent.course_id == Course.id) \
        .join(CourseContentKind, CourseContentKind.id == CourseContent.course_content_kind_id) \
        .outerjoin(CourseSubmissionGroupMember,
              (CourseSubmissionGroupMember.course_member_id == CourseMember.id) &
              (CourseSubmissionGroupMember.course_content_id == CourseContent.id)) \
        .outerjoin(CourseSubmissionGroup, CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .outerjoin(
            latest_result_sub,
            CourseSubmissionGroupMember.course_content_id == latest_result_sub.c.course_content_id
        ).outerjoin(
            Result,
            (Result.course_content_id == latest_result_sub.c.course_content_id) &
            (Result.created_at == latest_result_sub.c.latest_result_date)
        ) \
        .outerjoin(
            results_count_sub,
            (CourseSubmissionGroupMember.course_content_id == results_count_sub.c.course_content_id)
        ) # \
        # .outerjoin(
        #     submitted_sub,
        #     CourseContent.id == submitted_sub.c.course_content_id
        # )

    return query

def course_course_member_list_query(db: Session):

    latest_result_subquery =  db.query(
                    Result.course_content_id,
                    CourseMember.id.label("course_member_id"),
                    func.max(Result.created_at).label("latest_result_date")
                ) \
        .join(CourseContent, CourseContent.id == Result.course_content_id) \
        .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_content_id == CourseContent.id) \
        .join(CourseMember,CourseMember.id == CourseSubmissionGroupMember.course_member_id) \
        .join(CourseSubmissionGroup, CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
        .filter(
                Result.course_submission_group_id == CourseSubmissionGroupMember.course_submission_group_id, 
                Result.status == 0,
                Result.submit == True,
                CourseSubmissionGroup.status == None
        ) \
        .group_by(Result.course_content_id,CourseMember.id).subquery()

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