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
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from ctutor_backend.database import get_db
from ctutor_backend.model.role import Role, UserRole
from ctutor_backend.model.course import CourseRole, CourseContentKind
from ctutor_backend.model.execution import ExecutionBackend
from ctutor_backend.interface.tokens import encrypt_api_key
from ctutor_backend.model.auth import User, Account
from ctutor_backend.auth.keycloak_admin import KeycloakAdminClient, KeycloakUser
import asyncio


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
            'type': 'prefect',
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


async def sync_admin_with_keycloak(admin_username: str, admin_password: str, admin_email: str = 'admin@system.local'):
    """Sync admin user with Keycloak."""
    try:
        keycloak_admin = KeycloakAdminClient()
        
        # Check if admin user exists in Keycloak
        if await keycloak_admin.user_exists(admin_username):
            print(f"   ⚠️  Admin user already exists in Keycloak: {admin_username}")
            # Get user ID to update password
            user_id = await keycloak_admin._get_user_id_by_username(admin_username)
            # Update password to ensure it matches
            await keycloak_admin.set_user_password(user_id, admin_password, temporary=False)
            print(f"   ✅ Updated admin password in Keycloak")
            return user_id
        
        # Create admin user in Keycloak
        keycloak_user = KeycloakUser(
            username=admin_username,
            email=admin_email,
            firstName='System',
            lastName='Administrator',
            enabled=True,
            emailVerified=True,
            credentials=[{
                "type": "password",
                "value": admin_password,
                "temporary": False
            }],
            attributes={
                "system_role": "admin"
            }
        )
        
        provider_user_id = await keycloak_admin.create_user(keycloak_user)
        print(f"   ✅ Created admin user in Keycloak (ID: {provider_user_id})")
        return provider_user_id
        
    except Exception as e:
        print(f"   ⚠️  Failed to sync with Keycloak: {e}")
        print("   ℹ️  Admin user will be created locally only")
        return None


def create_admin_user(db: Session):
    """Create the default admin user and sync with Keycloak."""
    print("👤 Creating admin user...")
    
    # Get credentials from environment variables
    admin_username = os.environ.get('EXECUTION_BACKEND_API_USER', 'admin')
    admin_password = os.environ.get('EXECUTION_BACKEND_API_PASSWORD', 'admin')
    admin_email = 'admin@system.local'
    
    # Check if admin user already exists
    existing_user = db.query(User).filter(User.username == admin_username).first()
    if existing_user:
        print(f"   ⚠️  Admin user already exists locally: {admin_username}")
        
        # Check if Keycloak account exists
        keycloak_account = db.query(Account).filter(
            Account.user_id == existing_user.id,
            Account.provider == "keycloak"
        ).first()
        
        if not keycloak_account:
            # Sync with Keycloak
            provider_user_id = asyncio.run(sync_admin_with_keycloak(admin_username, admin_password, admin_email))
            if provider_user_id:
                # Create account linking
                account = Account(
                    provider="keycloak",
                    type="oidc",
                    provider_account_id=provider_user_id,
                    user_id=existing_user.id,
                    properties={
                        "email": admin_email,
                        "username": admin_username,
                        "system_admin": True
                    }
                )
                db.add(account)
                db.commit()
                print(f"   ✅ Linked existing admin user to Keycloak")
        else:
            # Update password in Keycloak
            asyncio.run(sync_admin_with_keycloak(admin_username, admin_password, admin_email))
        return
    
    # Sync with Keycloak first
    provider_user_id = asyncio.run(sync_admin_with_keycloak(admin_username, admin_password, admin_email))
    
    # Create admin user locally
    admin_user = User(
        given_name='System',
        family_name='Administrator',
        email=admin_email,
        username=admin_username,
        password=encrypt_api_key(admin_password),
        user_type='user'
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Create Keycloak account if sync was successful
    if provider_user_id:
        account = Account(
            provider="keycloak",
            type="oidc",
            provider_account_id=provider_user_id,
            user_id=admin_user.id,
            properties={
                "email": admin_email,
                "username": admin_username,
                "system_admin": True
            }
        )
        db.add(account)
    
    # Assign admin role
    admin_role = UserRole(
        user_id=admin_user.id,
        role_id='_admin'
    )
    
    db.add(admin_role)
    db.commit()
    
    print(f"   ✅ Created admin user (username: {admin_username}, password: ****)")


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
        print("   • Execution backends: prefect")
        print(f"   • Admin user: username '{os.environ.get('EXECUTION_BACKEND_API_USER', 'admin')}', password '{os.environ.get('EXECUTION_BACKEND_API_PASSWORD', 'admin')}'")
        print("\n🎯 You can now start the application!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        raise


if __name__ == "__main__":
    main()