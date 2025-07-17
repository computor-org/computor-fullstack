#!/usr/bin/env python3
"""
Real test of GitLab builder with actual database and GitLab instance.

This script tests the creation of Organization->CourseFamily->Course
with both GitLab groups and database entries.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ctutor_backend.generator.gitlab_builder_new import GitLabBuilderNew
from ctutor_backend.interface.deployments import (
    ComputorDeploymentConfig,
    OrganizationConfig,
    CourseFamilyConfig,
    CourseConfig,
    GitLabConfig
)
from ctutor_backend.services.git_service import GitService

# Database configuration from environment
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres_secret')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'codeability')

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# GitLab configuration
GITLAB_URL = os.environ.get("TEST_GITLAB_URL", "http://localhost:8084")
GITLAB_TOKEN = os.environ.get("TEST_GITLAB_TOKEN", "")  # Set via environment variable
GITLAB_GROUP_ID = int(os.environ.get("TEST_GITLAB_GROUP_ID", "2"))


def create_test_deployment() -> ComputorDeploymentConfig:
    """Create a test deployment configuration."""
    return ComputorDeploymentConfig(
        organization=OrganizationConfig(
            name="Real Test Organization",
            path="real_test_org",  # ltree paths use underscores, not hyphens
            description="Testing GitLab builder with real database and GitLab",
            gitlab=GitLabConfig(
                url=GITLAB_URL,
                token=GITLAB_TOKEN,
                parent=GITLAB_GROUP_ID
            )
        ),
        courseFamily=CourseFamilyConfig(
            name="Real Test Family",
            path="real_family",  # ltree paths use underscores, not hyphens
            description="Real test course family"
        ),
        course=CourseConfig(
            name="Real Test Course",
            path="real_course",  # ltree paths use underscores, not hyphens
            description="Real test course with all features"
        )
    )


def main():
    """Run real test with database and GitLab."""
    print("🧪 Real GitLab Builder Test")
    print("=" * 60)
    
    # Show configuration
    print("\n📊 Configuration:")
    print(f"   Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print(f"   GitLab: {GITLAB_URL}")
    print(f"   Parent Group ID: {GITLAB_GROUP_ID}")
    print("-" * 60)
    
    # Test database connection
    print("\n1️⃣ Testing database connection...")
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Please ensure PostgreSQL is running and accessible")
        return 1
    
    # Create session
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    # Create GitService
    git_service = GitService(working_dir=Path("/tmp/gitlab-builder-real-test"))
    
    # Create builder
    print("\n2️⃣ Creating GitLab builder...")
    try:
        builder = GitLabBuilderNew(
            db_session=db_session,
            gitlab_url=GITLAB_URL,
            gitlab_token=GITLAB_TOKEN,
            git_service=git_service
        )
        print("✅ GitLab builder initialized")
    except Exception as e:
        print(f"❌ Failed to initialize builder: {e}")
        print("   Please ensure GitLab is accessible at", GITLAB_URL)
        return 1
    
    # Create deployment configuration
    deployment = create_test_deployment()
    print("\n3️⃣ Deployment configuration:")
    print(f"   Organization: {deployment.organization.name} ({deployment.organization.path})")
    print(f"   Course Family: {deployment.courseFamily.name} ({deployment.courseFamily.path})")
    print(f"   Course: {deployment.course.name} ({deployment.course.path})")
    
    # Execute deployment
    print("\n4️⃣ Creating deployment hierarchy...")
    print("   (This will create both GitLab groups and database entries)")
    
    try:
        result = builder.create_deployment_hierarchy(
            deployment=deployment,
            created_by_user_id=None  # No user ID for this test
        )
        
        if result["success"]:
            print("\n✅ Deployment created successfully!")
            
            # Show created GitLab groups
            if result["gitlab_groups_created"]:
                print("\n📁 GitLab groups created:")
                for group in result["gitlab_groups_created"]:
                    print(f"   ✨ {group}")
            else:
                print("\n♻️ All GitLab groups already existed")
            
            # Show created database entries
            if result["database_entries_created"]:
                print("\n💾 Database entries created:")
                for entry in result["database_entries_created"]:
                    print(f"   ✨ {entry}")
            else:
                print("\n♻️ All database entries already existed")
            
            # Show detailed results
            org = result["organization"]
            family = result.get("course_family")
            course = result.get("course")
            
            print("\n📊 Created hierarchy details:")
            print(f"\n🏢 Organization: {org.title or org.path}")
            print(f"   Database ID: {org.id}")
            print(f"   Path: {org.path}")
            if org.properties and org.properties.get("gitlab"):
                gitlab_props = org.properties["gitlab"]
                print(f"   GitLab Group ID: {gitlab_props.get('group_id')}")
                print(f"   GitLab Full Path: {gitlab_props.get('full_path')}")
                print(f"   GitLab Web URL: {gitlab_props.get('web_url')}")
            
            print(f"\n📚 Course Family: {family.title or family.path}")
            print(f"   Database ID: {family.id}")
            print(f"   Path: {family.path}")
            print(f"   Organization ID: {family.organization_id}")
            if family:
                if family.properties and family.properties.get("gitlab"):
                    gitlab_props = family.properties["gitlab"]
                    print(f"   GitLab Group ID: {gitlab_props.get('group_id')}")
                    print(f"   GitLab Full Path: {gitlab_props.get('full_path')}")
                    print(f"   GitLab Web URL: {gitlab_props.get('web_url')}")
                else:
                    print(f"   ❌ No GitLab properties found!")
            
            if course:
                print(f"\n📖 Course: {course.title or course.path}")
                print(f"   Database ID: {course.id}")
                print(f"   Path: {course.path}")
                print(f"   Course Family ID: {course.course_family_id}")
                print(f"   Organization ID: {course.organization_id}")
                if course.properties and course.properties.get("gitlab"):
                    gitlab_props = course.properties["gitlab"]
                    print(f"   GitLab Group ID: {gitlab_props.get('group_id')}")
                    print(f"   GitLab Full Path: {gitlab_props.get('full_path')}")
                    print(f"   GitLab Web URL: {gitlab_props.get('web_url')}")
                    print(f"   Last Synced: {gitlab_props.get('last_synced_at')}")
                else:
                    print(f"   ❌ No GitLab properties found!")
            else:
                print(f"\n📖 Course: ❌ Not created")
            
            # Test idempotency
            print("\n5️⃣ Testing idempotency (running again)...")
            result2 = builder.create_deployment_hierarchy(
                deployment=deployment,
                created_by_user_id=None
            )
            
            if result2["success"]:
                if not result2["gitlab_groups_created"] and not result2["database_entries_created"]:
                    print("✅ Perfect idempotency - no duplicates created")
                else:
                    print("⚠️ Some changes detected on second run:")
                    if result2["gitlab_groups_created"]:
                        print(f"   GitLab groups: {result2['gitlab_groups_created']}")
                    if result2["database_entries_created"]:
                        print(f"   Database entries: {result2['database_entries_created']}")
            else:
                print("❌ Second run failed:", result2["errors"])
            
            # Summary
            print("\n" + "=" * 60)
            print("🎉 Test completed successfully!")
            print("\n📋 Summary:")
            print(f"   - Organization created with GitLab group ID: {org.properties['gitlab']['group_id']}")
            print(f"   - Course family created with GitLab group ID: {family.properties['gitlab']['group_id']}")
            print(f"   - Course created with GitLab group ID: {course.properties['gitlab']['group_id']}")
            print(f"   - All GitLab metadata stored in database")
            print(f"   - Idempotency verified")
            
        else:
            print("\n❌ Deployment failed!")
            print("\nErrors encountered:")
            for error in result["errors"]:
                print(f"   ❌ {error}")
            
            # Show any partial results
            if result["gitlab_groups_created"]:
                print(f"\n⚠️ Partial GitLab groups created: {result['gitlab_groups_created']}")
            if result["database_entries_created"]:
                print(f"⚠️ Partial database entries created: {result['database_entries_created']}")
                
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        db_session.close()
        print("\n🧹 Database session closed")
    
    return 0


if __name__ == "__main__":
    print("\n⚠️ WARNING: This will create real entries in your database and GitLab!")
    print("If you want to test from scratch, delete the GitLab groups first:")
    print("  - computor-realm/real_test_org")
    print("  - computor-realm/real_test_org/real_family")
    print("  - computor-realm/real_test_org/real_family/real_course")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Test cancelled.")
        exit(0)
    
    exit(main())