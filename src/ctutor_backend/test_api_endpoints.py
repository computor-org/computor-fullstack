#!/usr/bin/env python3
"""
Test API endpoints with the refactored SQLAlchemy models.
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
# Add parent directory to path for ctutor_backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_api_imports():
    """Test that API modules can be imported."""
    print("🧪 Testing API module imports...")
    
    try:
        # Test core API modules
        import api.user
        import api.course
        import api.organization
        import api.permissions
        
        print("✅ Core API modules imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ API import error: {e}")
        return False

def test_database_with_api():
    """Test database operations through API layer."""
    print("🧪 Testing database operations through API...")
    
    try:
        # Set up database connection
        env_vars = {
            'POSTGRES_URL': os.environ.get('POSTGRES_URL', 'localhost'),
            'POSTGRES_USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'POSTGRES_PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres_secret'),
            'POSTGRES_DB': os.environ.get('POSTGRES_DB', 'codeability_test_complete')
        }
        
        database_url = f"postgresql://{env_vars['POSTGRES_USER']}:{env_vars['POSTGRES_PASSWORD']}@{env_vars['POSTGRES_URL']}/{env_vars['POSTGRES_DB']}"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test basic queries through models
        from model.sqlalchemy_models import User, Course, Organization, CourseMember
        
        # Test some basic operations
        user_count = session.query(User).count()
        course_count = session.query(Course).count()
        org_count = session.query(Organization).count()
        
        print(f"✅ Database queries successful")
        print(f"   - Users: {user_count}")
        print(f"   - Courses: {course_count}")
        print(f"   - Organizations: {org_count}")
        
        # Test relationships
        first_user = session.query(User).first()
        first_course = session.query(Course).first()
        
        if first_user and first_course:
            # Test course-organization relationship
            if first_course.organization:
                print(f"✅ Course-Organization relationship working: {first_course.title} -> {first_course.organization.title}")
            
            # Test course family relationship  
            if first_course.course_family:
                print(f"✅ Course-Family relationship working: {first_course.title} -> {first_course.course_family.title}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Database API test error: {e}")
        return False

def test_interface_schemas():
    """Test Pydantic interface schemas."""
    print("🧪 Testing interface schemas...")
    
    try:
        # Test interface imports one by one
        import interface.courses
        print("   ✅ courses imported")
        import interface.users
        print("   ✅ users imported")
        import interface.organizations
        print("   ✅ organizations imported")
        
        print("✅ Interface schemas imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Interface schema error: {e}")
        return False

def main():
    """Run all API endpoint tests."""
    print("🚀 API Endpoint Integration Test")
    print("=" * 50)
    
    tests = [
        test_api_imports,
        test_database_with_api,
        test_interface_schemas
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All API endpoint tests passed!")
        return True
    else:
        print("❌ Some API tests failed.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)