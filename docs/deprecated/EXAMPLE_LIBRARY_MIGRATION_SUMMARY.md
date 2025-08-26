# Example Library Migration Summary

## Overview

This document summarizes the migration from the old three-repository system (assignments, student-template, reference) to the new Example Library paradigm where examples are first-class entities stored in MinIO.

## Key Changes

### 1. Repository Structure Simplification

**Before:**
- `assignments/` - Storage for assignment templates
- `student-template/` - Generated from assignments
- `reference/` - Storage for solutions and instructor materials

**After:**
- `student-template/` - Only repository needed, generated directly from Example Library
- Examples stored in MinIO object storage
- No intermediate Git repositories

### 2. Two-Step Deployment Process

The new system separates database operations from Git operations:

**Step 1: Assign Examples (Database Only)**
- Instructors assign examples to CourseContent
- Changes tracked in database with `deployment_status`
- No Git operations occur
- Multiple assignments can be made and reviewed

**Step 2: Generate Student Template (Git Operations)**
- Explicitly triggered by instructor
- Downloads examples from MinIO
- Processes according to meta.yaml rules
- Commits to student-template repository

### 3. API Changes

#### New Endpoints
```
POST   /api/v1/course-contents/{content_id}/assign-example
POST   /api/v1/courses/{course_id}/assign-examples (bulk)
DELETE /api/v1/course-contents/{content_id}/example
GET    /api/v1/courses/{course_id}/pending-changes
POST   /api/v1/courses/{course_id}/generate-student-template
GET    /api/v1/courses/{course_id}/contents-with-examples
```

#### Deprecated Endpoints
```
POST   /api/v1/courses/{course_id}/deploy-examples (old workflow)
```

### 4. Workflow Changes

#### New Workflow
- `GenerateStudentTemplateWorkflowV2` - Pulls directly from MinIO
- `generate_student_template_v2` activity - Processes examples without Git intermediaries

#### Deprecated Workflow
- `DeployExamplesToCourseWorkflow` - No longer needed
- All related activities removed from worker

### 5. GitLab Builder Changes

`GitLabBuilder` now only creates:
- Course group
- Students subgroup
- `student-template` repository

The `assignments` and `reference` repositories are no longer created.

### 6. Database Schema Updates

CourseContent model enhanced with:
- `example_id` - Links to Example entity
- `example_version` - Specific version deployed
- `deployment_status` - Tracks release state
- `deployed_at` - Timestamp of last deployment

### 7. Benefits

1. **Simpler Architecture**
   - Fewer repositories to manage
   - Direct path from Example Library to students
   - No synchronization issues

2. **Better Control**
   - Instructors can preview changes before releasing
   - Bulk operations supported
   - Clear deployment status tracking

3. **Version Management**
   - Examples versioned in MinIO
   - Easy rollback capabilities
   - Clear audit trail

4. **Performance**
   - No intermediate Git operations
   - Parallel example processing
   - Efficient bulk updates

## Migration Path

For existing courses:

1. Examples already in MinIO remain unchanged
2. Old repositories can be archived
3. First template generation imports existing assignments
4. Future updates use the new two-step process

## Implementation Status

✅ **Completed:**
- Temporal worker fixes for sandbox restrictions
- MinIO Docker networking fixes
- New API endpoints implementation
- GenerateStudentTemplateWorkflowV2 workflow
- GitLabBuilder modifications
- Documentation updates
- Deprecated file cleanup

🔄 **Pending:**
- Frontend UI implementation (see `FRONTEND_EXAMPLE_ASSIGNMENT.md`)
- Testing with production data
- Migration scripts for existing courses

## Code Locations

- **New API**: `src/ctutor_backend/api/course_content_examples.py`
- **New Workflow**: `src/ctutor_backend/tasks/temporal_student_template_v2.py`
- **Modified Builder**: `src/ctutor_backend/generator/gitlab_builder.py`
- **Frontend Guide**: `docs/FRONTEND_EXAMPLE_ASSIGNMENT.md`

## Testing

Use the provided test script `test_new_api.py` to verify the new endpoints:

```bash
python test_new_api.py
```

Update the script with actual IDs from your system before running.

## Security Considerations

- Example assignments require course management permissions
- Template generation requires elevated permissions
- All operations logged for audit trail
- No direct MinIO access from frontend

## Future Enhancements

1. **Dry-run mode** - Preview template generation without committing
2. **Diff view** - Show exact changes before deployment
3. **Rollback** - Revert to previous template state
4. **Scheduling** - Automated template updates
5. **Notifications** - Alert students of new content