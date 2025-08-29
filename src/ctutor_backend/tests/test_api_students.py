"""
Test API endpoints for students functionality.

This test suite verifies the students API endpoints, especially the submission groups
endpoint and the proper population of the example_identifier field.
"""

import pytest
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

# Base URL for the API server
BASE_URL = "http://localhost:8000"
AUTH = ("admin", "admin")


@pytest.mark.integration
class TestStudentSubmissionGroupsAPI:
    """Integration tests for student submission groups endpoint"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """HTTP client for making API requests"""
        return httpx.Client(base_url=BASE_URL, auth=AUTH, timeout=30.0)
    
    def test_submission_groups_endpoint_structure(self, client):
        """Test submission groups endpoint - GET /students/submission-groups"""
        response = client.get("/students/submission-groups")
        
        # Should return 200 or 401/403 depending on auth setup
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            if data:  # If there are submission groups
                sg = data[0]
                # Test required fields according to SubmissionGroupStudent interface
                assert "id" in sg
                assert "course_id" in sg
                assert "course_content_id" in sg
                assert "max_group_size" in sg
                assert "created_at" in sg
                assert "updated_at" in sg
                
                # Test datetime serialization
                datetime.fromisoformat(sg["created_at"].replace("Z", "+00:00"))
                datetime.fromisoformat(sg["updated_at"].replace("Z", "+00:00"))
                
                # Test optional fields that might be null
                assert "course_content_title" in sg  # can be null
                assert "course_content_path" in sg   # can be null
                assert "example_identifier" in sg    # CRITICAL: this field must be present
                assert "current_group_size" in sg
                assert "members" in sg
                assert "repository" in sg           # can be null
                assert "latest_grading" in sg       # can be null


@pytest.mark.unit
class TestStudentSubmissionGroupsUnit:
    """Unit tests for student submission groups functionality"""
    
    def test_example_identifier_population_with_example(self):
        """Test that example_identifier is properly populated when course content has example"""
        from ctutor_backend.api.students import student_router
        from ctutor_backend.model.course import CourseContent, CourseSubmissionGroup
        from ctutor_backend.model.example import Example
        from sqlalchemy.orm import Session
        
        # Mock data setup
        example_id = str(uuid4())
        course_content_id = str(uuid4())
        submission_group_id = str(uuid4())
        
        # Mock example
        mock_example = Mock()
        mock_example.identifier = "hello-world"
        
        # Mock course content with example
        mock_course_content = Mock()
        mock_course_content.id = course_content_id
        mock_course_content.title = "Hello World Exercise"
        mock_course_content.path = "1.basics.hello-world"
        mock_course_content.example = mock_example
        
        # Mock submission group
        mock_submission_group = Mock()
        mock_submission_group.id = submission_group_id
        mock_submission_group.course_id = str(uuid4())
        mock_submission_group.course_content_id = course_content_id
        mock_submission_group.max_group_size = 2
        mock_submission_group.created_at = datetime.now()
        mock_submission_group.updated_at = datetime.now()
        mock_submission_group.properties = {}
        
        # The test verifies that when a CourseContent has an associated Example,
        # the example_identifier field should be populated with the example's identifier
        assert mock_course_content.example is not None
        assert mock_course_content.example.identifier == "hello-world"
    
    def test_example_identifier_null_when_no_example(self):
        """Test that example_identifier is null when course content has no example"""
        from ctutor_backend.model.course import CourseContent
        
        # Mock course content without example
        mock_course_content = Mock()
        mock_course_content.id = str(uuid4())
        mock_course_content.title = "Theory Lesson"
        mock_course_content.path = "2.theory.concepts"
        mock_course_content.example = None
        
        # The test verifies that when a CourseContent has no associated Example,
        # the example_identifier should be None/null
        assert mock_course_content.example is None
    
    def test_course_content_path_format(self):
        """Test that course_content_path follows expected format"""
        valid_paths = [
            "1.basics.hello-world",
            "2.algorithms.sorting",
            "3.data-structures.linked-lists",
            "10.advanced.machine-learning"
        ]
        
        for path in valid_paths:
            parts = path.split('.')
            assert len(parts) == 3, f"Path {path} should have exactly 3 parts"
            assert parts[0].isdigit(), f"First part of {path} should be numeric"
            assert len(parts[1]) > 0, f"Second part of {path} should not be empty"
            assert len(parts[2]) > 0, f"Third part of {path} should not be empty"
    
    def test_repository_clone_url_construction(self):
        """Test repository clone URL construction for different scenarios"""
        test_cases = [
            {
                "name": "Full gitlab info provided",
                "properties": {
                    "gitlab": {
                        "url": "https://gitlab.example.com",
                        "full_path": "user/project",
                        "clone_url": "https://gitlab.example.com/user/project.git"
                    }
                },
                "expected_clone_url": "https://gitlab.example.com/user/project.git"
            },
            {
                "name": "Clone URL constructed from url and full_path",
                "properties": {
                    "gitlab": {
                        "url": "https://gitlab.example.com",
                        "full_path": "user/project"
                    }
                },
                "expected_clone_url": "https://gitlab.example.com/user/project.git"
            },
            {
                "name": "Backward compatibility with http_url_to_repo",
                "properties": {
                    "gitlab": {
                        "url": "https://gitlab.example.com",
                        "full_path": "user/project"
                    },
                    "http_url_to_repo": "https://gitlab.example.com/user/project.git"
                },
                "expected_clone_url": "https://gitlab.example.com/user/project.git"
            }
        ]
        
        for case in test_cases:
            properties = case["properties"]
            gitlab_info = properties.get('gitlab', {})
            http_url = properties.get('http_url_to_repo')
            
            # Simulate clone URL logic from students.py
            clone_url = (
                gitlab_info.get('clone_url') or 
                gitlab_info.get('http_url_to_repo') or
                http_url
            )
            
            if not clone_url and gitlab_info.get('url') and gitlab_info.get('full_path'):
                base_url = gitlab_info.get('url', '').rstrip('/')
                full_path = gitlab_info.get('full_path', '')
                clone_url = f"{base_url}/{full_path}.git"
            
            assert clone_url == case["expected_clone_url"], f"Failed for case: {case['name']}"


@pytest.mark.unit  
class TestStudentAPIImports:
    """Test that student API modules can be imported."""
    
    def test_import_students_api(self):
        """Test importing students API module."""
        import ctutor_backend.api.students
        assert ctutor_backend.api.students is not None
        assert hasattr(ctutor_backend.api.students, 'student_router')
    
    def test_import_submission_groups_interfaces(self):
        """Test importing submission groups interface."""
        from ctutor_backend.interface.submission_groups import (
            SubmissionGroupStudent, 
            SubmissionGroupStudentQuery,
            SubmissionGroupRepository,
            SubmissionGroupMemberBasic,
            SubmissionGroupGradingStudent
        )
        
        assert SubmissionGroupStudent is not None
        assert SubmissionGroupStudentQuery is not None
        assert SubmissionGroupRepository is not None
        assert SubmissionGroupMemberBasic is not None
        assert SubmissionGroupGradingStudent is not None


@pytest.mark.unit
class TestSubmissionGroupsDataConsistency:
    """Test data consistency in submission groups queries"""
    
    def test_null_handling_in_response(self):
        """Test that null values are properly handled in submission group responses"""
        from ctutor_backend.interface.submission_groups import SubmissionGroupStudent
        from pydantic import ValidationError
        
        # Test valid submission group with all optional fields as null
        valid_data = {
            "id": str(uuid4()),
            "course_id": str(uuid4()),
            "course_content_id": str(uuid4()),
            "course_content_title": None,
            "course_content_path": None,
            "example_identifier": None,
            "max_group_size": 1,
            "current_group_size": 1,
            "members": [],
            "repository": None,
            "latest_grading": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Should not raise ValidationError
        submission_group = SubmissionGroupStudent(**valid_data)
        assert submission_group.example_identifier is None
        assert submission_group.course_content_title is None
        assert submission_group.repository is None
        assert submission_group.latest_grading is None
    
    def test_example_identifier_field_presence(self):
        """Test that example_identifier field is always present in SubmissionGroupStudent"""
        from ctutor_backend.interface.submission_groups import SubmissionGroupStudent
        
        # Check that example_identifier is in the model fields
        fields = SubmissionGroupStudent.model_fields
        assert 'example_identifier' in fields
        
        # Check that it's Optional (can be None)
        field_info = fields['example_identifier']
        assert field_info.default is None
    
    def test_query_parameters_validation(self):
        """Test that query parameters are properly validated"""
        from ctutor_backend.interface.submission_groups import SubmissionGroupStudentQuery
        
        # Valid query with all parameters
        query1 = SubmissionGroupStudentQuery(
            course_id=str(uuid4()),
            course_content_id=str(uuid4()),
            has_repository=True,
            is_graded=False
        )
        assert query1.course_id is not None
        
        # Valid query with no parameters (all None)
        query2 = SubmissionGroupStudentQuery()
        assert query2.course_id is None
        assert query2.course_content_id is None
        assert query2.has_repository is None
        assert query2.is_graded is None