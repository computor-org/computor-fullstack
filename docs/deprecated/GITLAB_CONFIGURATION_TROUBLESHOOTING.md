# GitLab Configuration Troubleshooting

## Problem: "Course missing student-template repository URL"

This error occurs when trying to generate a student template for a course that doesn't have proper GitLab integration configured.

## Root Cause

When a course is created, it needs to have GitLab projects created for it, including:
- A GitLab group for the course
- A `student-template` repository within that group
- Proper configuration stored in the course properties

## Diagnosis

### 1. Check Course GitLab Status
You can check the GitLab configuration status using the API:
```bash
curl -X GET "http://localhost:8000/courses/{course_id}/gitlab-status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Use the Diagnostic Script
```bash
cd scripts
python check_course_gitlab.py {course_id}
```

This will show:
- Whether the course has GitLab configuration
- What specific fields are missing
- Course family GitLab configuration (if applicable)

## Solutions

### Option 1: Recreate the Course with GitLab Integration

If the course was created without GitLab integration, the simplest solution is to recreate it:

1. Delete the existing course (if no important data)
2. Create a new course ensuring GitLab integration is enabled
3. The course creation workflow should automatically create the GitLab projects

### Option 2: Manually Add GitLab Configuration

If you have an existing GitLab group and repositories, you can manually update the course properties:

```python
# Example of what the course properties should contain
course.properties = {
    "gitlab": {
        "group_id": 123,  # GitLab group ID
        "student_template_url": "https://gitlab.example.com/course-path/student-template",
        "projects": {
            "student_template": {
                "path": "student-template",
                "full_path": "course-path/student-template",
                "web_url": "https://gitlab.example.com/course-path/student-template",
                "description": "Template repository for students"
            }
        }
    }
}
```

### Option 3: Run GitLab Project Creation Manually

If the course exists but GitLab projects weren't created, you can trigger the creation:

1. Ensure the course family has GitLab configuration
2. Use the GitLabBuilder to create projects for the course
3. Update the course properties with the created project information

## Prevention

To prevent this issue in the future:

1. **Always create courses through the proper workflow** that includes GitLab integration
2. **Ensure course families have GitLab configuration** before creating courses
3. **Verify GitLab connectivity** before creating courses
4. **Check course properties** after creation to ensure all fields are populated

## Visual Indicators in UI

The Course Detail page now shows:
- A summary of assigned examples at the top
- Visual badges on content items that have examples assigned
- "(has example)" text next to content titles with assignments
- Deployment status chips showing the current state

## Example Assignment Workflow

Even without GitLab configuration, you can still:
1. **Assign examples to course content** - This updates the database only
2. **See assigned examples** in the course content tree
3. **Track deployment status** (will show as "pending_release")

However, to actually generate the student template, you need:
1. Valid GitLab configuration on the course
2. A `student-template` repository created in GitLab
3. Proper authentication to push to the repository

## Related Documentation

- [Example Deployment Strategy](./EXAMPLE_DEPLOYMENT_STRATEGY.md)
- [Frontend Example Assignment](./FRONTEND_EXAMPLE_ASSIGNMENT.md)
- [Temporal Task System](./TEMPORAL_TASK_SYSTEM.md)