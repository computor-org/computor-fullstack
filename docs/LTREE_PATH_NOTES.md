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

## Working with Ltree Objects in Code

### String Conversion Issues

**Problem**: Ltree objects need to be converted to strings for manipulation.

```python
# ❌ Wrong - will fail with AttributeError
organization_name = course.path.split('.')[0]

# ✅ Correct - convert to string first
course_path_str = str(course.path)
organization_name = course_path_str.split('.')[0]
```

### Database Query Requirements

**Problem**: When querying Ltree fields, you must compare Ltree to Ltree, not Ltree to string.

```python
from sqlalchemy_utils import Ltree

# ❌ Wrong - will cause SQL parameter errors: [parameters: [{}]]
organization = db.query(Organization).filter(
    Organization.path == organization_path  # string
).first()

# ✅ Correct - wrap string in Ltree()
organization = db.query(Organization).filter(
    Organization.path == Ltree(organization_path)  # Ltree object
).first()
```

### Safe String Operations

```python
# ❌ Wrong - Ltree doesn't have .replace()
path_with_slashes = content.path.replace('.', '/')

# ✅ Correct - convert to string first
content_path_str = str(content.path)
path_with_slashes = content_path_str.replace('.', '/')
```

### Common Error Patterns

**AttributeError: 'str' object has no attribute 'path'**
- Usually indicates improper string conversion of Ltree objects
- Check that variables expected to be objects aren't strings

**SQL Parameter Errors: [parameters: [{}]]**
- Indicates comparing Ltree field to string instead of Ltree object
- Fix: Wrap string values with `Ltree()` in queries

### Required Import

When working with Ltree queries, always import:
```python
from sqlalchemy_utils import Ltree
```

### Models Using Ltree

- **Organization**: `path` and `parent_path` fields
- **Course**: `path` field for hierarchical course paths  
- **CourseContent**: `path` field for content organization