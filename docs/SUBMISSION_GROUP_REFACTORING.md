# Submission Group Refactoring Documentation

## Overview
This document describes the refactoring of the submission group system to properly track grading and submission repositories.

## Database Changes

### 1. New Table: `CourseSubmissionGroupGrading`
Tracks who graded what, when, and the result:
- `id`: UUID primary key
- `course_submission_group_id`: References the submission group
- `graded_by_course_member_id`: References the CourseMember who performed the grading
- `grading`: Float (0.0 to 1.0) representing the grade
- `status`: String field for grading status:
  - `"corrected"` - Grading is complete
  - `"correction_necessary"` - Needs regrading
  - `"correction_possible"` - Can be regraded
  - `null` - Not yet graded
- `created_at`: When the grading was performed
- `updated_at`: Last update time

**Note**: Originally planned `feedback` and `properties` fields were removed due to SQLAlchemy 'metadata' reserved attribute conflict.

### 2. Modified: `CourseSubmissionGroup`
- **Removed fields:**
  - `grading` - Moved to CourseSubmissionGroupGrading
  - `status` - Moved to CourseSubmissionGroupGrading
  
- **Properties field structure:**
```json
{
  "gitlab": {
    "url": "https://gitlab.example.com",
    "full_path": "course-2024/students/john-doe/assignment-1",
    "project_id": 12345,
    "clone_url": "https://gitlab.example.com/course-2024/students/john-doe/assignment-1.git",
    "web_url": "https://gitlab.example.com/course-2024/students/john-doe/assignment-1"
  }
}
```

### 3. Modified: `CourseSubmissionGroupMember`
- **Removed fields:**
  - `course_content_id` - Relationship is through CourseSubmissionGroup
  - `grading` - Moved to CourseSubmissionGroupGrading
  
- **Removed constraint:**
  - `course_submission_group_course_content_key` - Invalid constraint

## Usage Examples

### Creating a Submission Group for a Solo Student
```python
# Create submission group for a student working alone
submission_group = CourseSubmissionGroup(
    course_id=course.id,
    course_content_id=assignment.id,  # The assignment/exercise
    max_group_size=1,
    properties={
        "gitlab": {
            "url": "https://gitlab.example.com",
            "full_path": f"course-{course.path}/students/{student.username}/assignment-{assignment.path}",
            "clone_url": f"https://gitlab.example.com/course-{course.path}/students/{student.username}/assignment-{assignment.path}.git"
        }
    }
)

# Add the student as the only member
member = CourseSubmissionGroupMember(
    course_id=course.id,
    course_submission_group_id=submission_group.id,
    course_member_id=student_course_member.id
)
```

### Creating a Submission Group for a Team
```python
# Create submission group for a team
submission_group = CourseSubmissionGroup(
    course_id=course.id,
    course_content_id=assignment.id,
    max_group_size=3,
    properties={
        "gitlab": {
            "url": "https://gitlab.example.com",
            "full_path": f"course-{course.path}/teams/team-{team_id}/assignment-{assignment.path}",
            "clone_url": f"https://gitlab.example.com/course-{course.path}/teams/team-{team_id}/assignment-{assignment.path}.git"
        }
    }
)

# Add team members
for member_id in team_member_ids:
    member = CourseSubmissionGroupMember(
        course_id=course.id,
        course_submission_group_id=submission_group.id,
        course_member_id=member_id
    )
```

### Recording a Grade
```python
# Grade a submission
grading = CourseSubmissionGroupGrading(
    course_submission_group_id=submission_group.id,
    graded_by_course_member_id=tutor.id,  # The tutor/lecturer doing the grading
    grading=0.85,  # 85%
    status="corrected",
    feedback="Good implementation, but missing error handling in the main function.",
    properties={
        "rubric": {
            "functionality": 0.9,
            "code_quality": 0.8,
            "documentation": 0.85
        }
    }
)
```

### Querying Grades
```python
# Get latest grade for a submission group
latest_grade = session.query(CourseSubmissionGroupGrading)\
    .filter_by(course_submission_group_id=submission_group.id)\
    .order_by(CourseSubmissionGroupGrading.created_at.desc())\
    .first()

# Get all grades given by a specific tutor
tutor_grades = session.query(CourseSubmissionGroupGrading)\
    .filter_by(graded_by_course_member_id=tutor.id)\
    .all()

# Get submission groups that need grading
ungraded = session.query(CourseSubmissionGroup)\
    .outerjoin(CourseSubmissionGroupGrading)\
    .filter(CourseSubmissionGroupGrading.id == None)\
    .all()
```

## Migration Path

The migration (`366a83771631_refactor_submission_groups_add_grading_.py`) handles:
1. Creating the new grading table
2. Migrating existing grading data from CourseSubmissionGroup to the new table
3. Removing deprecated fields
4. Setting up proper indexes and constraints

## Benefits

1. **Audit Trail**: Complete history of who graded what and when
2. **Multiple Gradings**: Support for regrading and tracking grade changes
3. **Proper Relationships**: CourseContent relationship is through CourseSubmissionGroup
4. **Repository Tracking**: Clear structure for storing GitLab/Git repository information
5. **Flexibility**: JSONB properties allow for custom metadata without schema changes

## API Implications

### New Endpoints Needed
- `POST /course-submission-groups/{id}/gradings` - Record a new grade
- `GET /course-submission-groups/{id}/gradings` - Get grading history
- `GET /course-members/{id}/gradings` - Get all grades given by a member
- `PATCH /course-submission-group-gradings/{id}` - Update a grade

### Modified Responses
- CourseSubmissionGroup responses should include:
  - Latest grading information (joined from grading table)
  - Repository URLs from properties field
  - Member list with their details

## Frontend Implications

### Student View
- Show latest grade and status
- Display feedback from grader
- Link to submission repository

### Lecturer/Tutor View
- Grade submission interface
- View grading history
- Filter by grading status
- Batch grading support

## Next Steps

1. Run the migration: `alembic upgrade head`
2. Update API endpoints to use new grading table
3. Create DTOs for CourseSubmissionGroupGrading
4. Update frontend to display grading information
5. Implement repository creation workflow when creating submission groups