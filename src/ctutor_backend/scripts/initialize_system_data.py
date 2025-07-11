#!/usr/bin/env python3
"""
Initialize system data including essential roles and reference data.
This script should be run after database migrations to set up the system.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # ctutor_backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))  # src

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env.dev"
load_dotenv(env_path)

from database import get_db
from model.role import Role, UserRole
from model.course import CourseRole, CourseContentKind
from model.execution import ExecutionBackend
from interface.tokens import encrypt_api_key
from model.auth import User


def initialize_system_roles(db: Session):
    """Initialize essential system roles."""
    print("🔧 Initializing system roles...")
    
    system_roles = [
        {
            'id': '_admin',
            'title': 'Administrator',
            'description': 'Full system permissions.',
            'builtin': True
        },
        {
            'id': '_user_manager',
            'title': 'User Manager',
            'description': 'Manage user accounts and permissions.',
            'builtin': True
        },
        {
            'id': '_organization_manager',
            'title': 'Organization Manager',
            'description': 'Manage organizations and their members.',
            'builtin': True
        }
    ]
    
    for role_data in system_roles:
        existing_role = db.query(Role).filter(Role.id == role_data['id']).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            print(f"   ✅ Created system role: {role_data['id']}")
        else:
            print(f"   ⚠️  System role already exists: {role_data['id']}")
    
    db.commit()


def initialize_course_roles(db: Session):
    """Initialize essential course roles."""
    print("🎓 Initializing course roles...")
    
    course_roles = [
        {
            'id': '_student',
            'title': 'Student',
            'description': 'Course participant with basic permissions.',
            'builtin': True
        },
        {
            'id': '_tutor',
            'title': 'Tutor',
            'description': 'Course teaching assistant with elevated permissions.',
            'builtin': True
        },
        {
            'id': '_lecturer',
            'title': 'Lecturer',
            'description': 'Course instructor with full course permissions.',
            'builtin': True
        },
        {
            'id': '_maintainer',
            'title': 'Maintainer',
            'description': 'Course maintainer with administrative permissions.',
            'builtin': True
        },
        {
            'id': '_owner',
            'title': 'Owner',
            'description': 'Course owner with full control.',
            'builtin': True
        }
    ]
    
    for role_data in course_roles:
        existing_role = db.query(CourseRole).filter(CourseRole.id == role_data['id']).first()
        if not existing_role:
            role = CourseRole(**role_data)
            db.add(role)
            print(f"   ✅ Created course role: {role_data['id']}")
        else:
            print(f"   ⚠️  Course role already exists: {role_data['id']}")
    
    db.commit()


def initialize_course_content_kinds(db: Session):
    """Initialize course content kinds."""
    print("📚 Initializing course content kinds...")
    
    content_kinds = [
        {
            'id': 'assignment',
            'title': 'Assignment',
            'description': 'Programming assignments for students',
            'has_ascendants': True,
            'has_descendants': False,
            'submittable': True
        },
        {
            'id': 'unit',
            'title': 'Unit',
            'description': 'Learning units and modules',
            'has_ascendants': True,
            'has_descendants': True,
            'submittable': False
        }
    ]
    
    for kind_data in content_kinds:
        existing_kind = db.query(CourseContentKind).filter(CourseContentKind.id == kind_data['id']).first()
        if not existing_kind:
            kind = CourseContentKind(**kind_data)
            db.add(kind)
            print(f"   ✅ Created content kind: {kind_data['id']}")
        else:
            print(f"   ⚠️  Content kind already exists: {kind_data['id']}")
    
    db.commit()


def initialize_execution_backends(db: Session):
    """Initialize default execution backends."""
    print("⚙️  Initializing execution backends...")
    
    backends = [
        {
            'slug': 'prefect_builtin',
            'type': 'prefect_builtin',
            'properties': {
                'url': 'http://prefect:4200/api',
                'deployment': 'test-assignment/system'
            }
        }
    ]
    
    for backend_data in backends:
        existing_backend = db.query(ExecutionBackend).filter(ExecutionBackend.slug == backend_data['slug']).first()
        if not existing_backend:
            backend = ExecutionBackend(**backend_data)
            db.add(backend)
            print(f"   ✅ Created execution backend: {backend_data['slug']}")
        else:
            print(f"   ⚠️  Execution backend already exists: {backend_data['slug']}")
    
    db.commit()


def create_admin_user(db: Session):
    """Create the default admin user."""
    print("👤 Creating admin user...")
    
    # Check if admin user already exists
    existing_user = db.query(User).filter(User.username == 'admin').first()
    if existing_user:
        print("   ⚠️  Admin user already exists")
        return
    
    # Create admin user
    admin_user = User(
        given_name='System',
        family_name='Administrator',
        email='admin@system.local',
        username='admin',
        password=encrypt_api_key('admin'),
        user_type='user'
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Assign admin role
    admin_role = UserRole(
        user_id=admin_user.id,
        role_id='_admin'
    )
    
    db.add(admin_role)
    db.commit()
    
    print("   ✅ Created admin user (username: admin, password: admin)")


def main():
    """Initialize all system data."""
    print("🚀 System Data Initialization")
    print("=" * 50)
    
    try:
        with next(get_db()) as db:
            # Initialize in dependency order
            initialize_system_roles(db)
            initialize_course_roles(db)
            initialize_course_content_kinds(db)
            initialize_execution_backends(db)
            create_admin_user(db)
            
        print("=" * 50)
        print("✅ System initialization completed successfully!")
        print("\n📋 What was initialized:")
        print("   • System roles: _admin, _user_manager, _organization_manager")
        print("   • Course roles: _student, _tutor, _lecturer, _maintainer, _owner")
        print("   • Content kinds: assignment, lecture, exercise, exam, unit")
        print("   • Execution backends: prefect_builtin")
        print("   • Admin user: username 'admin', password 'admin'")
        print("\n🎯 You can now start the application!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        raise


if __name__ == "__main__":
    main()