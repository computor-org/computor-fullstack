# GitLab Properties Update Strategy

## Current Issue
The `GitLabConfig` in deployments.py is missing critical fields that would help avoid unnecessary API calls:
- `group_id`: The GitLab group ID (currently only has `parent` for parent ID)
- Better validation to detect when GitLab properties need updating

## Proposed Enhancement

### 1. Enhanced GitLabConfig Structure
```python
class GitLabConfigGet(RepositoryConfig):
    url: Optional[str] = None
    full_path: Optional[str] = None
    group_id: Optional[int] = None  # NEW: Store the actual group ID
    parent_id: Optional[int] = None  # Renamed from 'parent' for clarity
    namespace_id: Optional[int] = None  # NEW: Store namespace ID
    namespace_path: Optional[str] = None  # NEW: Store namespace path
    web_url: Optional[str] = None  # NEW: Store complete web URL
    directory: Optional[str] = None
    registry: Optional[str] = None
    last_synced_at: Optional[str] = None  # NEW: Track when last synced
```

### 2. Benefits
- **Avoid API Calls**: Use stored `group_id` instead of searching by path
- **Change Detection**: Compare stored values with GitLab to detect changes
- **Performance**: Drastically reduce GitLab API calls
- **Audit Trail**: Track when properties were last synced

### 3. Validation Strategy
When creating/updating groups:
1. Check if stored properties match current GitLab state
2. If mismatch detected, update database properties
3. Log any changes for audit purposes

### 4. Implementation Plan
1. Update `GitLabConfig` model in deployments.py
2. Create property validator/updater in gitlab_builder
3. Store complete GitLab metadata after group creation
4. Use stored IDs for all subsequent operations