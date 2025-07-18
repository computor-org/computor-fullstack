#!/usr/bin/env python3
"""
Test script for GitLab project initialization with content.

This script tests the new Git operations functionality for initializing
course projects with proper directory structure and content.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URL construction (same as conftest.py)
def get_database_url():
    env_vars = {
        'POSTGRES_HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'POSTGRES_PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'POSTGRES_USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'POSTGRES_PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres_secret'),
        'POSTGRES_DB': os.environ.get('POSTGRES_DB', 'codeability')
    }
    return f"postgresql://{env_vars['POSTGRES_USER']}:{env_vars['POSTGRES_PASSWORD']}@{env_vars['POSTGRES_HOST']}:{env_vars['POSTGRES_PORT']}/{env_vars['POSTGRES_DB']}"
from ctutor_backend.model.organization import Organization
from ctutor_backend.model.course import CourseFamily, Course
from ctutor_backend.generator.gitlab_builder_new import GitLabBuilderNew
from ctutor_backend.interface.deployments import ComputorDeploymentConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_git_operations():
    """Test Git operations for project initialization."""
    
    # Database setup
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Get GitLab configuration
        gitlab_url = os.getenv("GITLAB_URL", "http://localhost:8084")
        gitlab_token = os.getenv("TEST_GITLAB_TOKEN")
        
        if not gitlab_token:
            logger.error("TEST_GITLAB_TOKEN environment variable not set")
            return False
        
        # Initialize GitLab builder
        builder = GitLabBuilderNew(
            db_session=db,
            gitlab_url=gitlab_url,
            gitlab_token=gitlab_token
        )
        
        # Find the most recent course with GitLab projects
        course = db.query(Course).filter(
            Course.properties.op('?')('gitlab')
        ).order_by(Course.created_at.desc()).first()
        
        if not course:
            logger.error("No course with GitLab properties found. Create a course first.")
            return False
        
        gitlab_props = course.properties.get("gitlab", {})
        projects = gitlab_props.get("projects", {})
        
        if not projects:
            logger.error(f"Course {course.title} has no GitLab projects configured")
            return False
        
        logger.info(f"Testing Git operations for course: {course.title}")
        logger.info(f"Available projects: {list(projects.keys())}")
        
        # Create a mock deployment config
        from ctutor_backend.interface.deployments import CourseConfig, OrganizationConfig, CourseFamilyConfig
        
        # Get course family and organization from course
        course_family = course.course_family
        organization = course.organization
        
        organization_config = OrganizationConfig(
            name=organization.title or f"Organization {organization.path}",
            path=str(organization.path),
            description=organization.description or f"Organization {organization.path}",
            gitlab_parent_group_id=10  # Default parent
        )
        
        course_family_config = CourseFamilyConfig(
            name=course_family.title,
            path=str(course_family.path),
            description=course_family.description or f"Course Family {course_family.title}"
        )
        
        course_config = CourseConfig(
            name=course.title,
            path=str(course.path),
            description=course.description or f"Course {course.title}",
            subject="programming"  # Add subject for CodeAbility meta
        )
        
        deployment = ComputorDeploymentConfig(
            organization=organization_config,
            courseFamily=course_family_config,
            course=course_config
        )
        
        # Test the Git operations
        logger.info("🚀 Testing project initialization...")
        result = builder.initialize_course_projects_content(course, deployment)
        
        if result["success"]:
            logger.info("✅ Git operations test successful!")
            logger.info(f"Initialized projects: {result['initialized_projects']}")
            
            # Show what would be created
            logger.info("📁 Project structure that would be created:")
            for project in result['initialized_projects']:
                logger.info(f"  - {project}: Repository structure with README.md, meta.yaml, and content")
            
            return True
        else:
            logger.error(f"❌ Git operations test failed: {result['error']}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        db.close()


def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("🧪 GitLab Git Operations Test")
    logger.info("=" * 60)
    
    success = test_git_operations()
    
    if success:
        logger.info("✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()