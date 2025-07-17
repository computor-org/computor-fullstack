# PostgreSQL ltree Path Restrictions

## Important: Valid Characters for ltree Paths

PostgreSQL's ltree extension has strict rules for path components:

### ✅ Allowed Characters:
- Letters: `a-z`, `A-Z`
- Numbers: `0-9`
- Underscore: `_`

### ❌ NOT Allowed:
- Hyphens: `-` 
- Spaces: ` `
- Special characters: `!@#$%^&*()`

### Examples:
```
✅ Valid ltree paths:
- organization_name
- course_2024
- test_org.test_family.test_course
- CS101_programming

❌ Invalid ltree paths:
- organization-name    (hyphen not allowed)
- course 2024         (space not allowed)
- test-org.test-family (hyphens not allowed)
```

## GitLab vs Database Path Differences

GitLab allows hyphens in group paths, but our database ltree does not. This creates a mismatch:

- **Database path** (ltree): `test_org.test_family.test_course`
- **GitLab path**: Can be `test-org/test-family/test-course`

## Solution in GitLabBuilder

The builder handles this by:
1. Using underscores in database paths (ltree compatible)
2. GitLab groups can use either underscores or hyphens
3. The GitLab `group_id` is stored for direct lookups (avoiding path issues)

## Best Practice

Always use underscores in path configurations:
```python
OrganizationConfig(
    path="my_organization",  # ✅ Good
    # path="my-organization", # ❌ Bad - will fail with ltree
)
```