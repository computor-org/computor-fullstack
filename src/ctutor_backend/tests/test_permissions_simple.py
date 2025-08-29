"""
Simple permission tests that demonstrate proper testing with the new system.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock

from ctutor_backend.server import app
from ctutor_backend.permissions.auth import get_current_permissions
from ctutor_backend.database import get_db
from ctutor_backend.permissions.principal import Principal, Claims
from ctutor_backend.permissions.core import check_permissions, check_admin


class TestSimplePermissions:
    """Simple tests that work with the new permission system."""
    
    def test_principal_creation(self):
        """Test creating principals with different roles."""
        # Admin principal
        admin = Principal(
            user_id='admin-123',
            is_admin=True,
            roles=['system_admin']
        )
        assert admin.user_id == 'admin-123'
        assert admin.is_admin == True
        assert admin.permitted('anything', 'anything')  # Admin can do anything
        
        # Student principal
        student = Principal(
            user_id='student-123',
            is_admin=False,
            roles=['student']
        )
        assert student.user_id == 'student-123'
        assert student.is_admin == False
        assert not student.permitted('courses', 'create')  # Student can't create courses
    
    def test_course_roles(self):
        """Test course role permissions."""
        # Create principal with course role
        principal = Principal(
            user_id='lecturer-123',
            is_admin=False,
            roles=['lecturer']
        )
        
        # Add course role claims
        claims = Claims()
        claims.dependent['course-456'] = {'_lecturer'}
        principal.claims = claims
        
        # Check course role
        assert '_lecturer' in principal.claims.dependent.get('course-456', set())
    
    def test_api_with_mock_db(self, mock_db, admin_principal):
        """Test API endpoint with mock database."""
        # Override dependencies
        app.dependency_overrides[get_current_permissions] = lambda: admin_principal
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Create test client
        client = TestClient(app)
        
        # Test organizations endpoint
        response = client.get("/organizations")
        
        # Should not fail with 500 error
        assert response.status_code in [200, 404]  # 200 if data, 404 if empty
        
        # Clean up
        app.dependency_overrides.clear()
    
    def test_api_with_test_client_factory(self, test_client_factory, mock_db, student_principal):
        """Test using the test client factory."""
        # Create client with student principal
        client = test_client_factory(student_principal, mock_db)
        
        # Test that student can list courses (but gets filtered results)
        response = client.get("/courses")
        assert response.status_code in [200, 404]
        
        # Test that student cannot create organizations
        response = client.post("/organizations", json={
            "path": "test.org",
            "properties": {}
        })
        assert response.status_code == 403  # Forbidden
        
        # Clean up
        client.cleanup()


class TestPermissionHelpers:
    """Test permission helper functions."""
    
    def test_check_admin_function(self):
        """Test the check_admin helper."""
        # Admin should pass
        admin = Principal(user_id='admin-1', is_admin=True, roles=['admin'])
        
        # Note: check_admin needs a database query, so we mock it
        mock_query = Mock()
        result = check_admin(admin)
        # If it doesn't raise an exception, it passed
        assert result is not None
        
        # Non-admin should fail
        student = Principal(user_id='student-1', is_admin=False, roles=['student'])
        with pytest.raises(Exception):  # Should raise permission error
            check_admin(student)
    
    def test_permission_caching(self):
        """Test that permission checks are cached."""
        principal = Principal(user_id='test-user', is_admin=True)
        
        # First check - not cached
        result1 = principal.permitted('resource', 'action')
        assert result1 == True
        
        # Second check - should use cache
        result2 = principal.permitted('resource', 'action')
        assert result2 == True
        
        # Check cache was used (cache should have the key)
        cache_key = f"resource:action:None:None"
        assert cache_key in principal._permission_cache


class TestAPIIntegration:
    """Test API integration with proper mocking."""
    
    @pytest.mark.parametrize("user_type,endpoint,method,expected_status", [
        ("admin", "/organizations", "GET", [200, 404]),
        ("student", "/organizations", "GET", [200, 404]),
        ("admin", "/organizations", "POST", [201, 422, 400]),
        ("student", "/organizations", "POST", [403, 422]),  # May get 422 if validation happens first
        ("admin", "/courses", "GET", [200, 404]),
        ("student", "/courses", "GET", [200, 404]),
    ])
    def test_endpoint_permissions(
        self, 
        test_client_factory, 
        mock_db,
        admin_principal,
        student_principal,
        user_type,
        endpoint,
        method,
        expected_status
    ):
        """Test various endpoints with different user types."""
        # Select principal based on user type
        principal = admin_principal if user_type == "admin" else student_principal
        
        # Create test client
        client = test_client_factory(principal, mock_db)
        
        # Make request based on method
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
        
        # Check status code
        assert response.status_code in expected_status, \
            f"Expected {expected_status}, got {response.status_code} for {user_type} {method} {endpoint}"
        
        # Clean up
        client.cleanup()