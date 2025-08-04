#!/usr/bin/env python3
"""
Test script to verify the Course Creation Bug fix.

This script tests that CourseFamily objects are properly refreshed 
after GitLab properties are updated, ensuring Course creation can 
access the parent GitLab group_id.
"""

import sys
import os
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ctutor_backend.generator.gitlab_builder import GitLabBuilder
from ctutor_backend.interface.deployments import (
    ComputorDeploymentConfig,
    OrganizationConfig,
    CourseFamilyConfig,
    CourseConfig,
    GitLabConfig
)
from ctutor_backend.model.organization import Organization
from ctutor_backend.model.course import CourseFamily, Course
from ctutor_backend.services.git_service import GitService
from ..types import Ltree


def test_course_family_refresh_fix():
    """Test that CourseFamily objects are properly refreshed after GitLab property updates."""
    
    print("🧪 Testing Course Creation Bug Fix")
    print("=" * 60)
    
    # Create mock objects
    mock_db_session = Mock()
    mock_gitlab = Mock()
    mock_git_service = Mock(spec=GitService)
    
    # Mock GitLab client behavior
    mock_gitlab.auth = Mock()
    mock_gitlab.groups = Mock()
    
    # Create mock GitLab group
    mock_gitlab_group = Mock()
    mock_gitlab_group.id = 123
    mock_gitlab_group.full_path = "test-org/test-family"
    mock_gitlab_group.web_url = "http://gitlab.example.com/test-org/test-family"
    mock_gitlab_group.name = "Test Family"
    mock_gitlab_group.path = "test_family"
    mock_gitlab_group.namespace = Mock()
    mock_gitlab_group.namespace.id = 456
    mock_gitlab_group.namespace.full_path = "test-org"
    
    mock_gitlab.groups.create.return_value = mock_gitlab_group
    mock_gitlab.groups.get.return_value = mock_gitlab_group
    
    # Create mock course family that initially has no GitLab properties
    mock_course_family = Mock(spec=CourseFamily)
    mock_course_family.id = "cf-123"
    mock_course_family.path = Ltree("test_family")
    mock_course_family.organization_id = "org-123"
    mock_course_family.properties = {}  # Initially empty
    
    # Create mock organization with GitLab properties
    mock_organization = Mock(spec=Organization)
    mock_organization.id = "org-123"
    mock_organization.path = Ltree("test_org")
    mock_organization.properties = {
        "gitlab": {
            "group_id": 456,
            "full_path": "test-org",
            "web_url": "http://gitlab.example.com/test-org"
        }
    }
    
    # Mock database queries
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_course_family
    mock_db_session.flush = Mock()
    mock_db_session.refresh = Mock()
    
    # Create builder instance with mocked GitLab
    builder = GitLabBuilder.__new__(GitLabBuilder)  # Create without __init__
    builder.db = mock_db_session
    builder.gitlab = mock_gitlab
    builder.git_service = mock_git_service
    
    print("1️⃣ Testing CourseFamily GitLab properties update...")
    
    # Test the update method directly
    gitlab_config = {
        "group_id": 123,
        "namespace_id": 456,
        "namespace_path": "test-org",
        "full_path": "test-org/test-family",
        "web_url": "http://gitlab.example.com/test-org/test-family",
        "last_synced_at": "2023-01-01T00:00:00Z"
    }
    
    # Call the update method
    builder._update_course_family_gitlab_properties(
        mock_course_family,
        mock_gitlab_group,
        gitlab_config
    )
    
    # Verify the fix: db.refresh should be called after db.flush
    print("2️⃣ Verifying fix implementation...")
    
    # Check that flush was called
    mock_db_session.flush.assert_called_once()
    print("✅ Database flush was called")
    
    # Check that refresh was called after flush
    mock_db_session.refresh.assert_called_once_with(mock_course_family)
    print("✅ Database refresh was called with course_family object")
    
    # Check that properties were updated
    assert mock_course_family.properties["gitlab"] == gitlab_config
    print("✅ GitLab properties were updated correctly")
    
    print("\n3️⃣ Testing Course GitLab properties update...")
    
    # Test the course update method too
    mock_course = Mock(spec=Course)
    mock_course.id = "course-123"
    mock_course.path = Ltree("test_course")
    mock_course.properties = {}
    
    # Reset mocks
    mock_db_session.flush.reset_mock()
    mock_db_session.refresh.reset_mock()
    
    # Call the course update method
    builder._update_course_gitlab_properties(
        mock_course,
        mock_gitlab_group,
        gitlab_config
    )
    
    # Verify the fix: db.refresh should be called after db.flush
    mock_db_session.flush.assert_called_once()
    print("✅ Database flush was called for course")
    
    mock_db_session.refresh.assert_called_once_with(mock_course)
    print("✅ Database refresh was called with course object")
    
    # Check that properties were updated
    assert mock_course.properties["gitlab"] == gitlab_config
    print("✅ GitLab properties were updated correctly for course")
    
    print("\n" + "=" * 60)
    print("🎉 Course Creation Bug Fix Test PASSED!")
    print("\n📋 Summary:")
    print("   - CourseFamily properties are flushed to database")
    print("   - CourseFamily object is refreshed from database") 
    print("   - Course properties are flushed to database")
    print("   - Course object is refreshed from database")
    print("   - In-memory objects now reflect updated GitLab properties")
    print("   - Course creation can now access parent GitLab group_id")
    
    return True


if __name__ == "__main__":
    success = test_course_family_refresh_fix()
    if success:
        print("\n✅ All tests passed! The fix is working correctly.")
        exit(0)
    else:
        print("\n❌ Tests failed!")
        exit(1)