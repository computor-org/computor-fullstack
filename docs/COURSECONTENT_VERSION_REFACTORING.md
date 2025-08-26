# CourseContent Version Management Refactoring

## Overview
Refactor CourseContent to properly use `example_id` and `example_version` instead of the unused `version_identifier` field.

## Current State

### Database Schema (CourseContent)
- `version_identifier` - String(2048), NOT NULL - **Currently unused/arbitrary**
- `example_id` - UUID, nullable - References Example
- `example_version` - String(64), nullable - Version tag
- `deployment_status` - String(32) - Values: pending, deploying, deployed, failed
- `deployed_at` - DateTime, nullable
- `is_customized` - Boolean - True if modified after deployment
- `last_customized_at` - DateTime, nullable

### Problems
1. `version_identifier` is required but serves no purpose
2. No tracking when example is updated (content becomes outdated)
3. No handling for deleted examples
4. No soft deletion for examples

## Proposed Solution

### Phase 1: Make version_identifier Optional
1. **Database Migration**:
   ```sql
   ALTER TABLE course_content 
   ALTER COLUMN version_identifier DROP NOT NULL;
   ```

2. **Interface Updates**:
   - Make `version_identifier` optional in DTOs
   - Add `example_id` and `example_version` to create/update DTOs

### Phase 2: Enhanced Deployment State Management
1. **New deployment_status values**:
   - `'pending'` - Initial state, no example assigned yet
   - `'deploying'` - Currently being deployed
   - `'deployed'` - Successfully deployed to student-template
   - `'failed'` - Deployment failed
   - `'outdated'` - Example was updated, needs redeployment
   - `'orphaned'` - Example was deleted
   - `'archived'` - Manually archived by instructor

2. **Add tracking fields**:
   ```python
   # CourseContent model additions
   example_deployed_version = Column(String(64), nullable=True)  # Track which version was deployed
   example_deleted_at = Column(DateTime(True), nullable=True)  # When example was deleted
   ```

### Phase 3: Example Lifecycle Management

#### When Example is Assigned:
1. Set `example_id` and `example_version`
2. Set `deployment_status = 'pending'`
3. Trigger student template generation

#### When Example is Updated:
1. Check if `example_version` differs from `example_deployed_version`
2. If different, set `deployment_status = 'outdated'`
3. Notify instructor for review

#### When Example is Deleted:
1. Set `deployment_status = 'orphaned'`
2. Set `example_deleted_at = now()`
3. Keep content in student-template with warning README
4. Allow instructor to:
   - Reassign to different example
   - Archive the content
   - Keep as-is for historical reference

### Phase 4: Student Template Generation Updates

#### Workflow Changes:
1. Track deployed version:
   ```python
   content.example_deployed_version = content.example_version
   content.deployment_status = 'deployed'
   content.deployed_at = datetime.now(timezone.utc)
   ```

2. Handle orphaned content:
   ```python
   if content.deployment_status == 'orphaned':
       # Create README explaining the example was removed
       readme_content = f"""
       # {content.title} - Example Removed
       
       This assignment's example was removed from the library.
       The content below is preserved for reference.
       
       Please contact your instructor for guidance.
       """
   ```

3. Handle outdated content:
   ```python
   if content.deployment_status == 'outdated':
       # Add warning to README about outdated content
       warning = "⚠️ This content may be outdated. Check with instructor."
   ```

## Implementation Steps

### Step 1: Update DTOs
```python
# course_contents.py
class CourseContentCreate(BaseModel):
    # ... existing fields ...
    version_identifier: Optional[str] = None  # Make optional
    example_id: Optional[str] = None
    example_version: Optional[str] = None
```

### Step 2: Database Migration
Create Alembic migration to:
1. Make `version_identifier` nullable
2. Add `example_deployed_version` field
3. Add `example_deleted_at` field

### Step 3: Update API Endpoints
1. Remove requirement for `version_identifier` in create endpoint
2. Add example assignment endpoint
3. Add example lifecycle tracking

### Step 4: Update Student Template Workflow
1. Track deployed versions
2. Handle orphaned/outdated content
3. Generate appropriate READMEs

## Benefits
1. **Clear Versioning**: Track exactly which version is deployed
2. **Lifecycle Management**: Handle updates and deletions gracefully
3. **Instructor Control**: Allow manual intervention when needed
4. **Student Clarity**: Clear communication about content state
5. **Historical Tracking**: Preserve content for reference

## Migration Strategy
1. Deploy code changes with backward compatibility
2. Run migration to make `version_identifier` nullable
3. Update existing records to populate `example_deployed_version`
4. Monitor and handle edge cases
5. Eventually deprecate `version_identifier` completely

## Future Considerations
1. **Automatic Redeployment**: Option to auto-deploy when example updates
2. **Diff Viewing**: Show changes between versions
3. **Rollback Support**: Allow reverting to previous versions
4. **Bulk Operations**: Update multiple contents at once
5. **Notification System**: Alert instructors of outdated content