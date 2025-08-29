# Testing FastAPI Endpoints with Permissions

## Overview

This guide explains how to properly test FastAPI endpoints with different user roles and permissions in the Computor backend.

## Key Concepts

### 1. FastAPI TestClient

FastAPI provides a `TestClient` that allows you to test your API without running a server:

```python
from fastapi.testclient import TestClient
from ctutor_backend.server import app

client = TestClient(app)
response = client.get("/organizations")
```

### 2. Dependency Injection & Overrides

FastAPI's dependency injection system allows you to override dependencies during testing:

```python
from ctutor_backend.api.auth import get_current_permissions

def mock_get_permissions():
    return mock_principal

app.dependency_overrides[get_current_permissions] = mock_get_permissions
```

### 3. Principal Object

The `Principal` object represents the authenticated user and their permissions:

- `user_id`: User's unique identifier
- `is_admin`: Boolean flag for admin privileges
- `roles`: List of system-wide roles
- `claims`: Permission claims (general and course-dependent)

## Testing Patterns

### Pattern 1: Basic Permission Testing

```python
def test_admin_can_create_organization():
    # Create admin principal
    admin_principal = create_mock_principal(is_admin=True)
    
    # Override authentication
    app.dependency_overrides[get_current_permissions] = lambda: admin_principal
    
    # Create test client
    client = TestClient(app)
    
    # Test the endpoint
    response = client.post("/organizations", json={...})
    assert response.status_code == 201
    
    # Clean up
    app.dependency_overrides.clear()
```

### Pattern 2: Course Role Testing

```python
def test_lecturer_can_create_content():
    # Create lecturer principal with course role
    lecturer = create_mock_principal(
        user_id="lecturer-123",
        course_roles={"course-123": "_lecturer"}
    )
    
    app.dependency_overrides[get_current_permissions] = lambda: lecturer
    client = TestClient(app)
    
    response = client.post("/course-contents", json={
        "course_id": "course-123",
        "title": "Assignment 1"
    })
    assert response.status_code == 201
```

### Pattern 3: Parametrized Testing

```python
@pytest.mark.parametrize("user_type,expected_status", [
    ("admin", 200),
    ("student", 403),
    ("lecturer", 200),
])
def test_endpoint_permissions(user_type, expected_status):
    principal = TEST_USERS[user_type]()
    app.dependency_overrides[get_current_permissions] = lambda: principal
    
    client = TestClient(app)
    response = client.get("/course-members")
    assert response.status_code == expected_status
```

## Role Hierarchy

The system implements a course role hierarchy:

```
_student → _tutor → _lecturer → _maintainer → _owner
```

Each role inherits permissions from the roles before it:
- **_student**: Can view course content
- **_tutor**: Can view + grade assignments
- **_lecturer**: Can create/modify content
- **_maintainer**: Can manage course members
- **_owner**: Full course control

## Test Data Setup

### Creating Mock Principals

```python
def create_mock_principal(user_id=None, is_admin=False, roles=None, course_roles=None):
    """Create a mock Principal for testing"""
    
    principal = Principal()
    principal.user_id = user_id or str(uuid4())
    principal.is_admin = is_admin
    principal.roles = roles or []
    
    # Add course-specific roles
    if course_roles:
        for course_id, role in course_roles.items():
            # Add to claims.dependent
            principal.claims.dependent[course_id] = {role}
    
    return principal
```

### Standard Test Users

```python
TEST_USERS = {
    'admin': lambda: create_mock_principal(is_admin=True),
    'student': lambda: create_mock_principal(
        course_roles={'course-123': '_student'}
    ),
    'lecturer': lambda: create_mock_principal(
        course_roles={'course-123': '_lecturer'}
    ),
    # ... more user types
}
```

## Testing Both Permission Systems

The codebase supports two permission systems (old and new). Test both:

```python
@pytest.mark.parametrize("system", ["OLD", "NEW"])
def test_with_both_systems(system):
    # Set the system
    os.environ["USE_NEW_PERMISSION_SYSTEM"] = "true" if system == "NEW" else "false"
    toggle_system(system == "NEW")
    
    # Run your tests
    client = create_test_client("admin")
    response = client.get("/organizations")
    assert response.status_code == 200
```

## Common Test Scenarios

### 1. Admin Operations
```python
def test_admin_operations():
    admin = create_mock_principal(is_admin=True)
    # Admin should be able to:
    # - Create/modify/delete any resource
    # - Access all endpoints
    # - Override course-specific permissions
```

### 2. Student Access
```python
def test_student_access():
    student = create_mock_principal(
        course_roles={'course-123': '_student'}
    )
    # Student should be able to:
    # - View courses they're enrolled in
    # - View course content
    # - Submit assignments
    # But NOT:
    # - Create/modify course content
    # - View other students' grades
    # - Manage course members
```

### 3. Lecturer Permissions
```python
def test_lecturer_permissions():
    lecturer = create_mock_principal(
        course_roles={'course-123': '_lecturer'}
    )
    # Lecturer should be able to:
    # - Create/modify course content
    # - View all course members
    # - Grade assignments
    # But NOT:
    # - Delete the course
    # - Add/remove course members
```

## Running Tests

### Prerequisites
```bash
# Start required services
bash startup.sh

# Or manually:
docker-compose -f docker-compose-dev.yaml up -d postgres redis
```

### Run All Permission Tests
```bash
# Run comprehensive test suite
pytest src/ctutor_backend/tests/test_permissions_comprehensive.py -v

# Run practical tests
pytest src/ctutor_backend/tests/test_permissions_practical.py -v
```

### Run Specific Tests
```bash
# Test specific class
pytest src/ctutor_backend/tests/test_permissions_practical.py::TestCoursePermissions -v

# Test with specific system
USE_NEW_PERMISSION_SYSTEM=true pytest src/ctutor_backend/tests/test_permissions_practical.py -v
```

### Debug Failed Tests
```bash
# Run with print statements
pytest src/ctutor_backend/tests/test_permissions_practical.py -v -s

# Run with pdb on failure
pytest src/ctutor_backend/tests/test_permissions_practical.py --pdb
```

## Troubleshooting

### Issue: 404 Instead of 403
If you get 404 when expecting 403, it might be because:
- The resource doesn't exist in the test database
- The permission check filters out the resource before checking existence

### Issue: Database Connection Errors
Make sure PostgreSQL is running:
```bash
docker-compose -f docker-compose-dev.yaml up -d postgres
```

### Issue: Import Errors
Ensure you're in the right environment:
```bash
source .venv/bin/activate
pip install -r src/requirements.txt
```

### Issue: Circular Imports
The permission system has been refactored to avoid circular imports. If you encounter them:
1. Check that you're importing from `permissions.integration`
2. Don't import `get_current_permissions` from integration module

## Best Practices

1. **Always clean up overrides**: 
   ```python
   app.dependency_overrides.clear()
   ```

2. **Use fixtures for repeated setup**:
   ```python
   @pytest.fixture
   def admin_client():
       # Setup
       yield client
       # Teardown
       app.dependency_overrides.clear()
   ```

3. **Test both positive and negative cases**:
   - Test what users CAN do
   - Test what users CANNOT do

4. **Use parametrize for multiple scenarios**:
   ```python
   @pytest.mark.parametrize("user,status", [...])
   ```

5. **Mock at the right level**:
   - Mock authentication (Principal)
   - Don't mock the permission logic itself

## Example: Complete Test Case

```python
class TestCourseContentPermissions:
    """Test course content CRUD with different roles"""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up after each test"""
        yield
        app.dependency_overrides.clear()
    
    def test_student_cannot_create_content(self):
        """Students should not be able to create course content"""
        student = create_mock_principal(
            user_id="student-123",
            course_roles={"course-123": "_student"}
        )
        
        app.dependency_overrides[get_current_permissions] = lambda: student
        client = TestClient(app)
        
        response = client.post("/course-contents", json={
            "course_id": "course-123",
            "title": "New Assignment"
        })
        
        assert response.status_code == 403
        assert "permission" in response.json().get("detail", "").lower()
    
    def test_lecturer_can_create_content(self):
        """Lecturers should be able to create course content"""
        lecturer = create_mock_principal(
            user_id="lecturer-123",
            course_roles={"course-123": "_lecturer"}
        )
        
        app.dependency_overrides[get_current_permissions] = lambda: lecturer
        client = TestClient(app)
        
        response = client.post("/course-contents", json={
            "course_id": "course-123",
            "title": "New Assignment",
            "kind_id": "assignment"
        })
        
        # Should succeed or fail due to missing course, not permissions
        assert response.status_code in [201, 404, 422]
```

## Summary

Testing FastAPI endpoints with permissions requires:
1. Creating mock Principal objects with appropriate roles
2. Using dependency injection to override authentication
3. Testing with FastAPI's TestClient
4. Verifying both allowed and forbidden operations
5. Testing both old and new permission systems

The test files provided (`test_permissions_comprehensive.py` and `test_permissions_practical.py`) demonstrate these patterns and can be extended for your specific use cases.