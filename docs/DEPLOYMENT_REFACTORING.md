# Course Content Deployment Refactoring

## Overview

This document describes the refactoring of the course content deployment system to separate deployment concerns from the hierarchical course structure.

## Problem Statement

The original implementation had several architectural issues:

1. **Data Redundancy**: Both `example_id` and `example_version_id` stored in `CourseContent`
2. **Misplaced Concerns**: Deployment fields on all content types, not just assignments
3. **Poor Separation**: Mixing hierarchical structure (ltree) with deployment logic
4. **Weak Audit Trail**: Deployment history stored in JSON instead of proper tables

## Solution: Separate Deployment Tables

### New Architecture

```
CourseContent (hierarchical structure)
    └── CourseContentDeployment (1:1, only for submittable content)
            └── DeploymentHistory (1:N, audit log)
```

### New Tables

#### `course_content_deployment`
- Tracks deployment of example versions to course content
- Only exists for submittable content (assignments)
- One deployment record per course content
- Stores deployment status, timestamps, and metadata

#### `deployment_history`
- Audit log of all deployment actions
- Immutable records of assignments, deployments, failures
- Tracks workflow IDs for Temporal integration

### Benefits

1. **Clean Separation**: Course structure vs deployment concerns
2. **Better Validation**: Database enforces only assignments have deployments
3. **Proper Audit Trail**: Full history of deployment actions
4. **Reduced Redundancy**: No duplicate foreign keys
5. **Easier Querying**: Dedicated deployment queries and reporting

## Migration Path

### Phase 1: Add New Tables (Current)
- ✅ Created `course_content_deployment` table
- ✅ Created `deployment_history` table
- ✅ Migrated existing deployment data
- ✅ Added validation triggers
- ✅ Created new APIs and DTOs

### Phase 2: Update Application Code
- ✅ Refactored API endpoints to use new tables
- 🔄 Update Temporal workflows (in progress)
- ⏳ Update frontend to use new endpoints

### Phase 3: Clean Up (Future)
- Remove deprecated columns from `course_content`:
  - `example_id`
  - `example_version_id`
  - `deployment_status`
  - `deployed_at`
- Remove old API endpoints
- Update documentation

## API Changes

### Old Endpoints (Deprecated)
```
POST /course-contents/{id}/assign-example
  Body: { example_id, example_version }
  
GET /course-contents/{id}
  Returns: { ..., example_id, deployment_status, ... }
```

### New Endpoints
```
POST /course-contents/{id}/assign-example
  Body: { example_version_id, deployment_message? }
  Returns: DeploymentWithHistory
  
GET /course-contents/{id}/deployment
  Returns: DeploymentWithHistory | null
  
GET /courses/{course_id}/deployment-summary
  Returns: DeploymentSummary
```

## Temporal Workflow Updates

### Current Implementation
```python
# Direct update of CourseContent
content.deployment_status = 'deployed'
content.deployed_at = datetime.now()
```

### New Implementation
```python
# Update via CourseContentDeployment
deployment = db.query(CourseContentDeployment).filter(
    CourseContentDeployment.course_content_id == content.id
).first()

if deployment:
    deployment.set_deployed(
        path=str(content.example.identifier),
        metadata={'workflow_id': workflow.info.workflow_id}
    )
    
    # Add history entry
    history = DeploymentHistory(
        deployment_id=deployment.id,
        action='deployed',
        workflow_id=workflow.info.workflow_id
    )
```

## Database Triggers

### Validation Trigger
Ensures only submittable content can have deployments:

```sql
CREATE TRIGGER trg_validate_deployment_submittable
BEFORE INSERT ON course_content_deployment
FOR EACH ROW
EXECUTE FUNCTION validate_deployment_submittable();
```

## Usage Examples

### Assigning an Example
```python
# Create or update deployment
deployment = CourseContentDeployment(
    course_content_id=content_id,
    example_version_id=version_id,
    deployment_status='pending'
)
db.add(deployment)

# Add history
history = DeploymentHistory(
    deployment_id=deployment.id,
    action='assigned',
    example_version_id=version_id
)
db.add(history)
```

### Querying Deployments
```python
# Get all deployments for a course
deployments = db.query(CourseContentDeployment).join(
    CourseContent
).filter(
    CourseContent.course_id == course_id
).all()

# Get deployment history
history = db.query(DeploymentHistory).filter(
    DeploymentHistory.deployment_id == deployment.id
).order_by(DeploymentHistory.created_at.desc()).all()
```

## Backwards Compatibility

During the transition period:
1. Old columns remain but are marked as deprecated
2. Migration populates new tables from old data
3. Both old and new APIs work (with deprecation warnings)
4. Frontend can gradually migrate to new endpoints

## Future Enhancements

1. **Deployment Versions**: Track multiple deployment attempts
2. **Rollback Support**: Revert to previous deployments
3. **Batch Operations**: Deploy multiple examples at once
4. **Deployment Templates**: Reusable deployment configurations
5. **Advanced Reporting**: Deployment analytics and metrics

## Testing

### Unit Tests Required
- Deployment creation and updates
- History tracking
- Validation triggers
- Migration of existing data

### Integration Tests Required
- Full deployment workflow via Temporal
- API endpoint functionality
- Permission checking
- Cache invalidation

## Rollback Plan

If issues arise:
1. Migration includes full downgrade path
2. Old columns still present for fallback
3. Can revert to old API endpoints
4. Data is preserved in both locations during transition