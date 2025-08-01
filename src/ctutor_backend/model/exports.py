import numpy as np
import pandas as pd
import random
from faker import Faker
from datetime import timedelta
from ctutor_backend.database import get_db
from ctutor_backend.model.course import Course, CourseContent, CourseContentType, CourseGroup, CourseMember, CourseMemberComment
from ctutor_backend.model.auth import User
from ctutor_backend.model.course import CourseSubmissionGroup, CourseSubmissionGroupMember
from ctutor_backend.model.result import Result
from sqlalchemy.orm import Session
from sqlalchemy import func

def db_export_course_member_grading(db: Session, course_member_id: str | None = None) -> pd.DataFrame:

    data = db.query(
        Course.id,
        CourseMember.id,
        CourseContent.path,
        CourseContentType.slug,
        CourseSubmissionGroup.grading,
        CourseSubmissionGroup.status,
        User.given_name,
        User.family_name
    ) \
    .select_from(CourseSubmissionGroup) \
    .join(CourseSubmissionGroupMember,CourseSubmissionGroup.id == CourseSubmissionGroupMember.course_submission_group_id) \
    .join(CourseMember,CourseMember.id == CourseSubmissionGroupMember.course_member_id) \
    .join(CourseContent,CourseContent.id == CourseSubmissionGroup.course_content_id) \
    .join(Course,Course.id == CourseContent.course_id) \
    .join(CourseContentType,CourseContentType.id == CourseContent.course_content_type_id) \
    .join(User,User.id == CourseMember.user_id)
    
    if course_member_id != None:
        data = data.filter(CourseMember.id == course_member_id)
    
    data = data.all()

    data_typed = []
    for d in data:
        data_typed.append({
            "course_id": d[0],
            "course_member_id": d[1],
            "assignment_path": str(d[2]),
            "type": d[3],
            "grading": d[4],
            "status": d[5],
            "given_name": d[6],
            "family_name": d[7]
        })
    
    return pd.DataFrame(data_typed, columns=["course_id","course_member_id","assignment_path","type","grading","status","given_name","family_name"])

def db_export_course_member_results(db: Session, course_member_id: str | None = None) -> pd.DataFrame:
        
    data = db.query(
        Course.id,
        CourseMember.id,
        CourseContent.path,
        CourseContentType.slug,
        Result.result,
        Result.submit,
        Result.created_at,
        CourseGroup.title,
        User.given_name,
        User.family_name
    ) \
    .select_from(Result) \
    .join(CourseContent,CourseContent.id == Result.course_content_id) \
    .join(Course,Course.id == CourseContent.course_id) \
    .join(CourseContentType,CourseContentType.id == CourseContent.course_content_type_id) \
    .join(CourseSubmissionGroup, Result.course_submission_group_id == CourseSubmissionGroup.id) \
    .join(CourseSubmissionGroupMember, CourseSubmissionGroupMember.course_submission_group_id == CourseSubmissionGroup.id) \
    .join(CourseMember,CourseMember.id == CourseSubmissionGroupMember.course_member_id) \
    .join(CourseGroup,CourseGroup.id == CourseMember.course_group_id) \
    .join(User,User.id == CourseMember.user_id)
    
    if course_member_id != None:
        data = data.filter(CourseMember.id == course_member_id)
    
    data = data.group_by(
        Course.id,
        CourseMember.id,
        CourseContent.path,
        CourseContentType.slug,
        Result.result,
        Result.submit,
        Result.created_at,
        CourseGroup.title,
        User.given_name,
        User.family_name
    ) \
    .all()

    data_typed = []
    for d in data:
        data_typed.append({
            "course_id": d[0],
            "course_member_id": d[1],
            "assignment_path": str(d[2]),
            "type": d[3],
            "result": d[4],
            "submit": d[5],
            "timestamp": d[6],
            "group_name": d[7],
            "given_name": d[8],
            "family_name": d[9]
        })

    return pd.DataFrame(data_typed, columns=["course_id","course_member_id","assignment_path","type","result","submit","timestamp","group_name","given_name","family_name"])

def db_obscurity(df: pd.DataFrame):
    df['course_member_id'], course_member_id_mapping = pd.factorize(df['course_member_id'])

    df['course_member_id'] = "student_" + df['course_member_id'].astype(str)

    segment_set = set()
    for path in df['assignment_path']:
        segments = path.split('.')
        segment_set.update(segments)


    fake = Faker()
    Faker.seed(42) 

    if 'group_name' in df.columns:
        unique_groups = df['group_name'].dropna().unique()

        group_mapping = {group: f"group_{fake.last_name()}" for group in unique_groups}

        df['group_name'] = df['group_name'].map(group_mapping)

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        def random_shift(dt, max_hours=10):
            delta = timedelta(hours=random.randint(-max_hours, max_hours))
            return dt + delta

        df['timestamp'] = df['timestamp'].apply(lambda ts: random_shift(ts, max_hours=24))
    
    if 'grading' in df.columns:
        df['grading'] = np.random.uniform(0,1,size=len(df))
    
    # if 'status' in df.columns:
    #     status_list = [None,"corrected", "correction_necessary", "improvement_possible"]

    #     def chooser(g):
    #         if g > 0.9:
    #             return "corrected"
    #         elif g < 0.2:
    #             return None
    #         elif g < 0.5:
    #             return "correction necessary"
    #         elif g < 0.7:
    #             return "improvement_possible"
    #         else:
    #             return random.choice(status_list)

    #     df['status'] = df['grading'].apply(chooser)

    return df

def db_export_types(db: Session, course_id: str | None = None) -> pd.DataFrame:

    data = db.query(
        Course.id,
        CourseContentType.id,
        CourseContentType.slug,
        CourseContentType.course_content_kind_id,
        CourseContentType.color,
        CourseContentType.properties,
        func.count(CourseContent.id).label("content_count")
    ).select_from(Course).join(CourseContentType,CourseContentType.course_id == Course.id) \
     .outerjoin(CourseContent, CourseContent.course_content_type_id == CourseContentType.id)
    
    if course_id != None:
        data = data.filter(Course.id == course_id)

    data = data.group_by(
        Course.id,
        CourseContentType.id,
        CourseContentType.slug,
        CourseContentType.course_content_kind_id,
        CourseContentType.color,
        CourseContentType.properties
    ) \
    .all()

    data_typed = []
    for d in data:
        data_typed.append({
            "course_id": d[0],
            "id": d[1],
            "slug": str(d[2]),
            "kind_id": d[3],
            "color": d[4],
            "properties": d[5],
            "count": d[6]
        })

    return pd.DataFrame(data_typed, columns=["course_id","id","slug","kind_id","color","properties","count"])

def db_export_assignments(db: Session, course_id: str | None = None) -> pd.DataFrame:

    data = db.query(
        Course.id,
        CourseContent.path,
        CourseContentType.slug,
        CourseContentType.color,
    ).select_from(Course) \
        .join(CourseContent, Course.id == CourseContent.course_id) \
        .join(CourseContentType,CourseContentType.course_id == Course.id) \
        .filter(CourseContent.course_content_kind_id == "assignment")
    
    if course_id != None:
        data = data.filter(Course.id == course_id)

    data = data.group_by(
        Course.id,
        CourseContent.path,
        CourseContentType.slug,
        CourseContentType.color
    ) \
    .all()

    data_typed = []
    for d in data:
        data_typed.append({
            "course_id": d[0],
            "assignment_path": str(d[1]),
            "type": d[2],
            "color": d[3]
        })

    return pd.DataFrame(data_typed, columns=["course_id","assignment_path","type","color","properties"])

def db_export_comments(db: Session, course_id: str | None = None) -> pd.DataFrame:

    data = db.query(
        CourseMemberComment.message,
        CourseMemberComment.course_member_id,
        CourseMember.course_id,
        CourseMemberComment.created_at
    ).select_from(CourseMemberComment) \
        .join(CourseMember, CourseMemberComment.course_member_id == CourseMember.id) \
    
    if course_id != None:
        data = data.filter(Course.id == course_id)

    data = data.group_by(
        CourseMemberComment.message,
        CourseMemberComment.course_member_id,
        CourseMember.course_id,
        CourseMemberComment.created_at
    ) \
    .all()

    data_typed = []
    for d in data:
        data_typed.append({
            "message": d[0],
            "course_member_id": str(d[1]),
            "course_id": d[2],
            "created_at": d[3]
        })

    return pd.DataFrame(data_typed, columns=["message","course_member_id","course_id","created_at"])
        
def create_grading_all(db: Session):

    courses = db.query(Course.id).all()
    
    for course_id in courses:

        course_members = db.query(CourseMember.id).filter(CourseMember.course_id == course_id[0]).all()
        
        for course_member_id in course_members:
            result_df = db_export_course_member_results(str(course_member_id[0]))
            grading_df = db_export_course_member_grading(str(course_member_id[0]))
            
            print(result_df)
            print(grading_df)