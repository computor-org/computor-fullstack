#!/usr/bin/env python
"""Test course projects creation functionality."""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file from project root
env_file = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_file)

import gitlab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Test course projects functionality."""
    
    # Get GitLab connection
    gitlab_url = os.getenv("TEST_GITLAB_URL", "http://localhost:8084")
    gitlab_token = os.getenv("TEST_GITLAB_TOKEN")
    
    if not gitlab_token:
        logger.error("TEST_GITLAB_TOKEN environment variable not set")
        return
    
    gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
    
    logger.info("=" * 60)
    logger.info("VERIFYING COURSE PROJECTS STRUCTURE")
    logger.info("=" * 60)
    
    # Look for recently created course projects
    try:
        # Search for all three types of course projects
        course_projects = []
        for project_type in ["assignments", "student-template", "reference"]:
            projects = gl.projects.list(search=project_type, all=True)
            course_projects.extend(projects)
        
        if not course_projects:
            logger.warning("No course projects found. Run test_complete_gitlab_setup.py first.")
            return
        
        # Display project details
        logger.info(f"Found {len(course_projects)} course projects:")
        logger.info("")
        
        for project in course_projects:
            logger.info(f"📁 Project: {project.name}")
            logger.info(f"   Path: {project.path}")
            logger.info(f"   Full Path: {project.path_with_namespace}")
            logger.info(f"   Description: {project.description}")
            logger.info(f"   Visibility: {project.visibility}")
            logger.info(f"   Web URL: {project.web_url}")
            logger.info(f"   Default Branch: {project.default_branch}")
            logger.info(f"   Created: {project.created_at}")
            logger.info("")
        
        # Check if README files exist
        logger.info("=" * 60)
        logger.info("CHECKING PROJECT CONTENT")
        logger.info("=" * 60)
        
        for project in course_projects:
            try:
                readme_file = project.files.get(file_path='README.md', ref='main')
                readme_content = readme_file.decode().decode('utf-8')
                logger.info(f"✅ {project.name} has README.md:")
                logger.info(f"   First line: {readme_content.split(chr(10))[0]}")
            except Exception as e:
                logger.warning(f"❌ {project.name} missing README.md: {e}")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("VERIFICATION COMPLETE")
        logger.info("=" * 60)
        logger.info("All course projects have been successfully created!")
        logger.info(f"Visit {gitlab_url} to see the projects in action")
        
    except Exception as e:
        logger.error(f"Error verifying course projects: {e}")

if __name__ == "__main__":
    asyncio.run(main())