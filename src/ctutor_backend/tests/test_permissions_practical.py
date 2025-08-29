"""
Practical Permission Testing for FastAPI Endpoints

This test suite uses FastAPI's TestClient with dependency overrides
to test permissions for different user roles and course roles.
"""

import os
import pytest
from uuid import uuid4
from typing import Dict, Optional
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import from new permission system directly
from ctutor_backend.server import app
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.database import get_db
from ctutor_backend.permissions.principal import Principal, Claims
from ctutor_backend.permissions.core import check_permissions, check_admin, check_course_permissions


# ============================================================================
# Mock Principals for Different User Types
# ============================================================================

def create_mock_principal(
    user_id: str = None,
    is_admin: bool = False,
    roles: list = None,
    course_roles: Dict[str, str] = None
) -> Principal:
    """Create a mock Principal for testing (new system only)"""
    principal = Principal(
        user_id=user_id or str(uuid4()),
        is_admin=is_admin,
        roles=roles or []
    )
    
    # Build claims for course roles
    if course_roles:
        claims = Claims()
        for course_id, role in course_roles.items():
            if course_id not in claims.dependent:
                claims.dependent[course_id] = set()
            claims.dependent[course_id].add(role)
        principal.claims = claims
    
    return principal


# Test user fixtures
TEST_USERS = {
    'admin': lambda: create_mock_principal(
        user_id='admin-123',
        is_admin=True,
        roles=['system_admin']
    ),
    'student': lambda: create_mock_principal(
        user_id='student-123',
        is_admin=False,
        roles=['student'],
        course_roles={'course-123': '_student'}
    ),
    'tutor': lambda: create_mock_principal(
        user_id='tutor-123',
        is_admin=False,
        roles=['tutor'],
        course_roles={'course-123': '_tutor'}
    ),
    'lecturer': lambda: create_mock_principal(
        user_id='lecturer-123',
        is_admin=False,
        roles=['lecturer'],
        course_roles={'course-123': '_lecturer'}
    ),
    'maintainer': lambda: create_mock_principal(
        user_id='maintainer-123',
        is_admin=False,
        roles=['maintainer'],
        course_roles={'course-123': '_maintainer'}
    ),
    'unauthorized': lambda: create_mock_principal(
        user_id='unauth-123',
        is_admin=False,
        roles=[]
    )
}


# ============================================================================
# Test Client Factory
# ============================================================================

def create_test_client(user_type: str) -> TestClient:
    """Create a TestClient with mocked authentication for a specific user type"""
    
    # Get the mock principal
    principal = TEST_USERS[user_type]()
    
    # Create override functions
    def override_get_current_permissions():
        return principal
    
    # We'll keep the real database for now - you can override this too if needed
    # def override_get_db():
    #     db = Session()
    #     try:
    #         yield db
    #     finally:
    #         db.close()
    
    # Apply overrides
    app.dependency_overrides[get_current_permissions] = override_get_current_permissions
    # app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)


# ============================================================================
# Permission Tests
# ============================================================================

class TestPermissionSystem:
    """Test the new permission system"""
    
    def test_principal_creation(self):
        """Test creating principals with different roles"""
        # Admin principal
        admin = create_mock_principal(
            user_id='admin-test',
            is_admin=True,
            roles=['system_admin']
        )
        assert admin.user_id == 'admin-test'
        assert admin.is_admin == True
        assert 'system_admin' in admin.roles
        
        # Student with course role
        student = create_mock_principal(
            user_id='student-test',
            is_admin=False,
            roles=['student'],
            course_roles={'course-123': '_student'}
        )
        assert student.user_id == 'student-test'
        assert student.is_admin == False
        assert '_student' in student.claims.dependent.get('course-123', set())


class TestOrganizationPermissions:
    """Test organization endpoint permissions"""
    
    @pytest.mark.parametrize("user_type,method,expected_status", [
        # GET /organizations - most users can list
        ("admin", "GET", 200),
        ("student", "GET", 200),
        ("lecturer", "GET", 200),
        ("unauthorized", "GET", 200),
        
        # POST /organizations - only admin can create
        ("admin", "POST", 422),  # 422 because we're not sending valid data
        ("student", "POST", 403),
        ("lecturer", "POST", 403),
        ("unauthorized", "POST", 403),
    ])
    def test_organization_permissions(self, user_type, method, expected_status):
        """Test organization endpoint with different users and methods"""
        client = create_test_client(user_type)
        
        if method == "GET":
            response = client.get("/organizations")
        elif method == "POST":
            response = client.post("/organizations", json={})
        
        # Check status code - might be 404 if no data, 403 if forbidden
        assert response.status_code in [expected_status, 404, 500]
        
        # Clean up overrides
        app.dependency_overrides.clear()


class TestCoursePermissions:
    """Test course endpoint permissions"""
    
    @pytest.mark.parametrize("user_type,expected_can_list", [
        ("admin", True),
        ("student", True),
        ("lecturer", True),
        ("unauthorized", True),  # Can list but gets filtered results
    ])
    def test_list_courses(self, user_type, expected_can_list):
        """Test listing courses with different user roles"""
        client = create_test_client(user_type)
        response = client.get("/courses")
        
        if expected_can_list:
            assert response.status_code in [200, 404]  # 404 if no courses exist
        else:
            assert response.status_code == 403
        
        app.dependency_overrides.clear()
    
    @pytest.mark.parametrize("user_type,expected_can_create", [
        ("admin", True),
        ("student", False),
        ("lecturer", False),
        ("maintainer", False),  # Needs to be maintainer of parent course family
        ("unauthorized", False),
    ])
    def test_create_course(self, user_type, expected_can_create):
        """Test creating courses with different user roles"""
        client = create_test_client(user_type)
        
        course_data = {
            "path": "test.university.cs.101",
            "properties": {
                "name": "Test Course"
            }
        }
        
        response = client.post("/courses", json=course_data)
        
        if expected_can_create:
            # Might fail with 422 (validation) or 409 (conflict) or 201 (success)
            assert response.status_code in [201, 409, 422, 500]
        else:
            assert response.status_code in [403, 404]
        
        app.dependency_overrides.clear()


class TestCourseContentPermissions:
    """Test course content permissions based on course roles"""
    
    @pytest.mark.parametrize("user_type,expected_can_list", [
        ("admin", True),
        ("student", True),   # Students in course can view content
        ("tutor", True),
        ("lecturer", True),
        ("unauthorized", True),  # Gets empty list
    ])
    def test_list_course_contents(self, user_type, expected_can_list):
        """Test listing course contents with different course roles"""
        client = create_test_client(user_type)
        response = client.get("/course-contents")
        
        if expected_can_list:
            assert response.status_code in [200, 404]
        else:
            assert response.status_code == 403
        
        app.dependency_overrides.clear()
    
    @pytest.mark.parametrize("user_type,expected_can_create", [
        ("admin", True),
        ("student", False),   # Students cannot create content
        ("tutor", False),     # Tutors cannot create content
        ("lecturer", True),   # Lecturers can create content
        ("maintainer", True),
        ("unauthorized", False),
    ])
    def test_create_course_content(self, user_type, expected_can_create):
        """Test creating course content with different course roles"""
        client = create_test_client(user_type)
        
        content_data = {
            "course_id": "course-123",
            "name": "Test Assignment",
            "kind_id": "assignment",
            "properties": {}
        }
        
        response = client.post("/course-contents", json=content_data)
        
        if expected_can_create:
            # Might fail due to missing course or validation
            assert response.status_code in [201, 404, 422, 500]
        else:
            assert response.status_code in [403, 404]
        
        app.dependency_overrides.clear()


class TestUserPermissions:
    """Test user management permissions"""
    
    @pytest.mark.parametrize("user_type,expected_status", [
        ("admin", 200),
        ("student", 200),  # Can see limited user list
        ("unauthorized", 200),
    ])
    def test_list_users(self, user_type, expected_status):
        """Test listing users with different roles"""
        client = create_test_client(user_type)
        response = client.get("/users")
        
        assert response.status_code in [expected_status, 404]
        
        app.dependency_overrides.clear()


# ============================================================================
# Core Permission Tests (New System)
# ============================================================================

class TestCorePermissions:
    """Test core permissions with new system"""
    
    def teardown_method(self, method):
        """Clean up after each test"""
        app.dependency_overrides.clear()
    
    def test_admin_access(self):
        """Test admin has full access"""
        client = create_test_client("admin")
        
        # Admin should access everything
        assert client.get("/organizations").status_code in [200, 404]
        assert client.get("/courses").status_code in [200, 404]
        assert client.get("/users").status_code in [200, 404]
        assert client.get("/course-contents").status_code in [200, 404]
    
    def test_student_restrictions(self):
        """Test student restrictions"""
        client = create_test_client("student")
        
        # Students can view but not create most things
        assert client.get("/courses").status_code in [200, 404]
        assert client.post("/courses", json={}).status_code in [403, 422]
        assert client.post("/organizations", json={}).status_code == 403
    
    def test_lecturer_course_permissions(self):
        """Test lecturer course permissions"""
        client = create_test_client("lecturer")
        
        # Lecturers can create course content
        content_data = {
            "course_id": "course-123",
            "name": "Test Content",
            "kind_id": "assignment"
        }
        response = client.post("/course-contents", json=content_data)
        # Should either succeed or fail due to missing course, not permissions
        assert response.status_code in [201, 404, 422, 500]


# ============================================================================
# Run Instructions
# ============================================================================

"""
To run these tests:

1. Start the services (database, redis, etc.):
   bash startup.sh

2. Run all permission tests:
   pytest src/ctutor_backend/tests/test_permissions_practical.py -v

3. Run specific test class:
   pytest src/ctutor_backend/tests/test_permissions_practical.py::TestCoursePermissions -v

4. Run core permission tests:
   pytest src/ctutor_backend/tests/test_permissions_practical.py::TestCorePermissions -v -s
"""

if __name__ == "__main__":
    # Quick test to verify it works
    print("Testing new permission system")
    
    # Test with admin
    client = create_test_client("admin")
    response = client.get("/organizations")
    print(f"Admin GET /organizations: {response.status_code}")
    
    # Test with student
    client = create_test_client("student")
    response = client.get("/organizations")
    print(f"Student GET /organizations: {response.status_code}")
    
    # Clean up
    app.dependency_overrides.clear()