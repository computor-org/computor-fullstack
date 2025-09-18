# VSCode Extension Update Guide: New Example Deployment Architecture

## Overview
The backend has refactored how examples are deployed to course contents. Instead of storing deployment information directly on `CourseContent`, we now use a separate `CourseContentDeployment` model for better separation of concerns.

## Key Changes

### 1. Data Model Changes

#### OLD Structure (Deprecated):
```typescript
interface CourseContent {
  id: string;
  example_id?: string;
  example_version?: string;
  deployment_status?: 'pending' | 'deployed' | 'failed';
  deployed_at?: string;
  deployment_path?: string;
  deployment_metadata?: any;
}
```

Important: the "example_version" was not the ID of a database object, it was the version_tag which is defined in the meta.yaml of an example (filesystem, git).

#### NEW Structure:
```typescript
interface CourseContent {
  id: string;
  example_id?: string;        // Still exists for reference
  example_version?: string;    // Still exists for reference
  is_submittable: boolean;
  // Deployment info moved to separate model
  deployment?: CourseContentDeployment;  // Optional, loaded via include=deployment
}

interface CourseContentDeployment {
  id: string;
  course_content_id: string;
  example_version_id: string;  // Now uses version ID, not example ID
  deployment_status: 'pending' | 'in_progress' | 'deployed' | 'failed';
  deployment_path?: string;
  deployed_at?: string;
  last_attempt_at?: string;
  deployment_message?: string;
  deployment_metadata?: Record<string, any>;
  // Relationships (when included)
  example_version?: ExampleVersion;
  course_content?: CourseContent;
}

interface DeploymentHistory {
  id: string;
  deployment_id: string;
  action: 'assigned' | 'reassigned' | 'deployed' | 'failed' | 'unassigned' | 'updated';
  action_details?: string;
  example_version_id?: string;
  previous_example_version_id?: string;
  meta?: Record<string, any>;
  workflow_id?: string;
  created_at: string;
  created_by?: string;
}
```

### 2. API Endpoint Changes

#### Fetching Course Contents with Deployment Info:
```typescript
// OLD
GET /course-contents/{id}

// NEW - Include deployment info explicitly
GET /course-contents/{id}?include=deployment
GET /course-contents?course_id={courseId}&include=deployment
```

#### Assigning/Updating Example Deployments:
```typescript
// OLD
PUT /course-contents/{id}
{
  "example_id": "...",
  "example_version": "v1.0"
}

// NEW - Dedicated endpoint
POST /course-contents/{id}/assign-example
{
  "example_version_id": "uuid-of-version"  // Note: Now uses version ID
}
```

#### Getting Deployment Status:
```typescript
// NEW - Dedicated deployment endpoints
GET /course-contents/{id}/deployment
GET /course-contents/{id}/deployment/history
```

#### Triggering Deployment:
```typescript
// NEW
POST /course-contents/{id}/deploy
{
  "force": boolean  // Optional, force re-deployment
}
```

### 3. Important Workflow Changes

#### Creating Course Content with Examples (NEW):
The workflow has changed from a single-step to a two-step process:

**OLD Workflow (deprecated):**
1. Create course content with `example_id` and `example_version` in the POST body

**NEW Workflow:**
1. Create course content WITHOUT example fields
2. If the content is submittable, assign an example using the separate `/assign-example` endpoint

**Why the change?**
- Cleaner separation of concerns
- Better tracking of deployment history
- Only submittable content can have examples assigned
- More flexible deployment management

### 4. Implementation Notes for Extension

#### When displaying course contents:
- Always include `?include=deployment` when fetching course contents that need deployment status
- Check `is_submittable` flag - only submittable content has deployments
- Deployment info is now nested under `deployment` field

#### When showing deployment status:
```typescript
// OLD
const status = courseContent.deployment_status;
const deployedAt = courseContent.deployed_at;

// NEW
const status = courseContent.deployment?.deployment_status;
const deployedAt = courseContent.deployment?.deployed_at;
const versionId = courseContent.deployment?.example_version_id;
```

#### When assigning examples:
```typescript
// OLD
await updateCourseContent(contentId, {
  example_id: exampleId,
  example_version: versionTag
});

// NEW
// First, find the version ID from example versions
const version = example.versions.find(v => v.version_tag === selectedVersion);
await assignExample(contentId, {
  example_version_id: version.id
});
```

#### Type guards for deployment data:
```typescript
function hasDeployment(content: CourseContent): boolean {
  return content.is_submittable && content.deployment !== undefined;
}

function isDeployed(content: CourseContent): boolean {
  return hasDeployment(content) && 
         content.deployment?.deployment_status === 'deployed';
}

function getDeploymentStatus(content: CourseContent): string | undefined {
  return content.deployment?.deployment_status;
}

function getDeployedVersion(content: CourseContent): ExampleVersion | undefined {
  return content.deployment?.example_version;
}
```

### 5. Migration Period
- Old fields (`deployment_status`, `deployed_at`, etc.) are deprecated but still present
- Use new `deployment` relationship for all new code
- Backend returns both during transition, but prefer new structure
- Plan to remove deprecated fields in future release

### 6. Error Handling
- Non-submittable content won't have deployment records (returns 404 on deployment endpoints)
- Handle cases where `deployment` is null even for submittable content (not yet assigned)
- Version IDs are now required instead of version tags
- Always check `is_submittable` before attempting deployment operations

### 7. Quick Reference Table

| Action | Old Approach | New Approach |
|--------|-------------|--------------|
| Check deployment status | `content.deployment_status` | `content.deployment?.deployment_status` |
| Assign example | Use `example_id` + `example_version` | Use `example_version_id` |
| Get deployment info | Included in content | Request with `?include=deployment` |
| Update deployment | PUT to course-content | POST to `/assign-example` endpoint |
| Check if deployed | `content.deployment_status === 'deployed'` | `content.deployment?.deployment_status === 'deployed'` |
| Get deployed path | `content.deployment_path` | `content.deployment?.deployment_path` |
| Get deployment time | `content.deployed_at` | `content.deployment?.deployed_at` |

### 8. Example Usage Patterns

#### Fetching course content tree with deployment status:
```typescript
async function getCourseContentTree(courseId: string) {
  const response = await fetch(
    `/course-contents?course_id=${courseId}&include=deployment`
  );
  const contents: CourseContent[] = await response.json();
  
  return contents.map(content => ({
    ...content,
    hasDeployment: content.is_submittable && content.deployment !== undefined,
    isDeployed: content.deployment?.deployment_status === 'deployed',
    deploymentStatus: content.deployment?.deployment_status ?? 'not_assigned'
  }));
}
```

#### Creating course content and assigning an example (NEW workflow):
```typescript
async function createCourseContentWithExample(
  courseId: string,
  contentData: {
    title: string;
    path: string;
    course_content_type_id: string;
    position?: number;
  },
  exampleId: string,
  versionTag: string
) {
  // Step 1: Create the course content first
  const contentResponse = await fetch('/course-contents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...contentData,
      course_id: courseId,
      // Note: Do NOT include example_id or example_version here anymore
    })
  });
  
  const newContent = await contentResponse.json();
  
  // Step 2: If content is submittable, assign the example
  if (newContent.is_submittable && exampleId) {
    // Get the example with versions
    const exampleResponse = await fetch(`/examples/${exampleId}?include=versions`);
    const example = await exampleResponse.json();
    
    // Find the specific version
    const version = example.versions.find(v => v.version_tag === versionTag);
    if (!version) {
      throw new Error(`Version ${versionTag} not found`);
    }
    
    // Assign the example to the content
    const deploymentResponse = await fetch(
      `/course-contents/${newContent.id}/assign-example`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          example_version_id: version.id
        })
      }
    );
    
    const deployment = await deploymentResponse.json();
    
    // Return content with deployment info
    return {
      ...newContent,
      deployment
    };
  }
  
  return newContent;
}
```

#### Assigning a new example version to existing content:
```typescript
async function assignExampleVersion(
  contentId: string, 
  exampleId: string, 
  versionTag: string
) {
  // First get the example with versions
  const exampleResponse = await fetch(`/examples/${exampleId}?include=versions`);
  const example = await exampleResponse.json();
  
  // Find the specific version
  const version = example.versions.find(v => v.version_tag === versionTag);
  if (!version) {
    throw new Error(`Version ${versionTag} not found`);
  }
  
  // Assign using the version ID
  const response = await fetch(`/course-contents/${contentId}/assign-example`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      example_version_id: version.id
    })
  });
  
  return response.json();
}
```

#### Checking deployment history:
```typescript
async function getDeploymentHistory(contentId: string) {
  const response = await fetch(`/course-contents/${contentId}/deployment/history`);
  const history: DeploymentHistory[] = await response.json();
  
  return history.map(entry => ({
    action: entry.action,
    timestamp: entry.created_at,
    details: entry.action_details,
    versionId: entry.example_version_id
  }));
}
```

### 9. Testing Checklist

- [ ] Extension correctly fetches deployment info using `include=deployment`
- [ ] UI properly displays deployment status from nested `deployment` object
- [ ] Assignment uses `example_version_id` instead of `example_id` + `example_version`
- [ ] Non-submittable content doesn't show deployment options
- [ ] Deployment history displays correctly
- [ ] Error handling for missing deployments
- [ ] Backwards compatibility with deprecated fields (if needed during transition)

## Summary

The main change is that deployment information is now stored in a separate `CourseContentDeployment` model linked to `CourseContent`. This provides better data integrity, clearer relationships with `ExampleVersion`, and a complete audit trail through `DeploymentHistory`. The frontend needs to:

1. Use `include=deployment` when fetching course contents
2. Access deployment data through `content.deployment` instead of direct fields
3. Use `example_version_id` when assigning examples
4. Check `is_submittable` before showing deployment features