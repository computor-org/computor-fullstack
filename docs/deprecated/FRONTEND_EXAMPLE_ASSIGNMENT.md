# Frontend Implementation Guide: Two-Step Example Assignment

## Overview

This guide describes how to implement the two-step example assignment process in the frontend. The new workflow separates database assignment from Git deployment, giving instructors more control.

## Two-Step Process

### Step 1: Assign Examples to CourseContent (Database Only)
- Instructors select examples from the Example Library
- Assignments are saved to the database
- No Git operations occur
- Changes are marked as "pending_release"

### Step 2: Generate Student Template (Git Operations)
- Instructors explicitly trigger template generation
- System downloads examples from MinIO
- Processes according to meta.yaml rules
- Commits to student-template repository

## UI Components Needed

### 1. CourseContent Management Page

#### Example Assignment Section
```tsx
interface ExampleAssignment {
  contentId: string;
  exampleId: string;
  exampleVersion: string;
  deploymentStatus: 'pending_release' | 'released' | 'deploying';
}

// Component to assign example to single content
<AssignExampleDialog
  contentId={content.id}
  onAssign={handleAssignExample}
/>

// Bulk assignment for multiple contents
<BulkAssignExamplesDialog
  courseId={courseId}
  contents={selectedContents}
  onAssign={handleBulkAssign}
/>
```

#### Status Indicators
```tsx
// Show deployment status for each content
<Chip 
  label={getStatusLabel(content.deploymentStatus)}
  color={getStatusColor(content.deploymentStatus)}
  icon={getStatusIcon(content.deploymentStatus)}
/>

// Status labels
const statusLabels = {
  pending_release: "Pending Release",
  released: "Released",
  deploying: "Deploying...",
  modified: "Modified"
};
```

### 2. Pending Changes View

```tsx
interface PendingChange {
  type: 'new' | 'update' | 'remove';
  contentId: string;
  path: string;
  title: string;
  exampleName?: string;
  exampleId?: string;
  fromVersion?: string;
  toVersion?: string;
}

<PendingChangesDialog
  courseId={courseId}
  onGenerate={handleGenerateTemplate}
>
  <PendingChangesList changes={pendingChanges} />
  <GenerateTemplateButton 
    disabled={pendingChanges.length === 0}
    onClick={onGenerate}
  />
</PendingChangesDialog>
```

### 3. Generate Template Button

```tsx
// Main action button
<Button
  variant="contained"
  color="primary"
  startIcon={<PublishIcon />}
  onClick={handleGenerateTemplate}
  disabled={!hasPendingChanges}
>
  Generate Student Template
</Button>

// Progress indicator during generation
<GenerateTemplateProgress
  workflowId={workflowId}
  onComplete={handleGenerationComplete}
/>
```

## API Integration

### 1. Assign Example to Content
```typescript
async function assignExample(
  contentId: string, 
  exampleId: string, 
  version: string = 'latest'
): Promise<CourseContentExampleResponse> {
  const response = await api.post(
    `/course-contents/${contentId}/assign-example`,
    { example_id: exampleId, example_version: version }
  );
  return response.data;
}
```

### 2. Get Pending Changes
```typescript
async function getPendingChanges(
  courseId: string
): Promise<PendingChangesResponse> {
  const response = await api.get(
    `/courses/${courseId}/pending-changes`
  );
  return response.data;
}
```

### 3. Generate Student Template
```typescript
async function generateStudentTemplate(
  courseId: string,
  commitMessage?: string
): Promise<GenerateTemplateResponse> {
  const response = await api.post(
    `/courses/${courseId}/generate-student-template`,
    { commit_message: commitMessage }
  );
  return response.data;
}
```

### 4. Get Contents with Examples
```typescript
async function getCourseContentsWithExamples(
  courseId: string
): Promise<CourseContentWithExamples[]> {
  const response = await api.get(
    `/courses/${courseId}/contents-with-examples`
  );
  return response.data.contents;
}
```

## UI Flow

### Typical Workflow

1. **Instructor navigates to Course Content page**
   - Sees list of all course contents
   - Status indicators show current deployment state

2. **Assigns examples to contents**
   - Opens assignment dialog
   - Searches/selects from Example Library
   - Chooses version (default: latest)
   - Saves assignment (database only)

3. **Reviews pending changes**
   - Opens pending changes dialog
   - Sees diff of what will change
   - Can cancel or modify assignments

4. **Generates student template**
   - Clicks "Generate Student Template" button
   - Optionally enters commit message
   - Monitors progress
   - Receives confirmation when complete

### Visual States

```tsx
// Content without example
<ContentRow>
  <ContentInfo />
  <AssignExampleButton />
</ContentRow>

// Content with pending example
<ContentRow highlighted>
  <ContentInfo />
  <ExampleInfo status="pending" />
  <Chip label="Pending Release" color="warning" />
  <EditButton />
  <RemoveButton />
</ContentRow>

// Content with released example
<ContentRow>
  <ContentInfo />
  <ExampleInfo status="released" />
  <Chip label="Released" color="success" />
  <UpdateButton />
</ContentRow>
```

## Error Handling

```typescript
// Handle assignment errors
try {
  await assignExample(contentId, exampleId, version);
  showSuccess('Example assigned successfully');
  refreshContents();
} catch (error) {
  if (error.response?.status === 404) {
    showError('Example or version not found');
  } else if (error.response?.status === 403) {
    showError('You do not have permission to assign examples');
  } else {
    showError('Failed to assign example');
  }
}

// Handle generation errors
try {
  const result = await generateStudentTemplate(courseId);
  showSuccess(`Template generation started: ${result.workflow_id}`);
  startPollingWorkflowStatus(result.workflow_id);
} catch (error) {
  if (error.response?.data?.detail) {
    showError(error.response.data.detail);
  } else {
    showError('Failed to generate template');
  }
}
```

## Permissions

- Only users with course management permissions can:
  - Assign examples to course content
  - Generate student templates
  - View pending changes

## Cache Invalidation

After operations, invalidate relevant caches:

```typescript
// After assigning example
queryClient.invalidateQueries(['course', courseId, 'contents']);
queryClient.invalidateQueries(['course', courseId, 'contents-with-examples']);

// After generating template
queryClient.invalidateQueries(['course', courseId, 'contents']);
queryClient.invalidateQueries(['course', courseId, 'pending-changes']);
```

## Migration from Old System

For existing courses using the old deployment system:

1. **First-time migration**
   - System detects existing assignments repository
   - Offers migration wizard
   - Imports existing assignments as "released" status

2. **Backward compatibility**
   - Old API endpoints remain available
   - Gradual migration path
   - Clear indicators of which system is in use

## Best Practices

1. **Always show deployment status clearly**
   - Use consistent colors/icons
   - Provide tooltips with details
   - Show last deployment time

2. **Batch operations when possible**
   - Allow selecting multiple contents
   - Bulk assignment reduces clicks
   - Bulk status updates

3. **Provide clear feedback**
   - Progress indicators during operations
   - Success/error messages
   - Workflow status monitoring

4. **Enable preview before deployment**
   - Show what will change
   - Allow cancellation
   - Dry-run option for testing

5. **Maintain audit trail**
   - Show who assigned what
   - When changes were made
   - Deployment history