# Test GitLab Instance Configuration

## Overview

This document describes how to configure a local GitLab instance for testing the GitLab refactoring.

## GitLab Instance Setup

To test the GitLab integration, you need to set up a local GitLab instance with:

- **Web URL**: Your GitLab instance URL
- **Group Token**: A GitLab group access token with appropriate permissions
- **Group ID**: The ID of the test group

## Usage

This GitLab instance can be used to test:
- GitService operations (clone, push, pull, etc.)
- GitLab API integration
- Repository pattern with real GitLab data
- End-to-end workflow testing

## Environment Variables for Testing

Add these to your test environment:

```bash
# Test GitLab Configuration
TEST_GITLAB_URL=http://your-gitlab-instance:port
TEST_GITLAB_TOKEN=your-group-access-token
TEST_GITLAB_GROUP_ID=your-group-id
```

## Integration Test Examples

### GitService with Real GitLab

```python
import asyncio
from pathlib import Path
from ctutor_backend.services.git_service import GitService

async def test_real_gitlab():
    git_service = GitService(Path("/tmp/test"))
    
    # Clone a repository from test instance
    repo = await git_service.clone(
        url="http://your-gitlab-instance:port/group/repo.git",
        token="your-access-token",
        directory=Path("/tmp/test/cloned_repo")
    )
    
    # Test other operations...
```

### GitLab API Testing

```python
from gitlab import Gitlab

def test_gitlab_api():
    gl = Gitlab(
        url="http://your-gitlab-instance:port",
        private_token="your-access-token"
    )
    
    # Get group
    group = gl.groups.get(your_group_id)
    print(f"Group name: {group.name}")
    
    # List projects
    projects = group.projects.list()
    print(f"Projects: {[p.name for p in projects]}")
```

## Security Note

⚠️ **Important**: This configuration is for testing purposes only. Never commit real production tokens to the repository.

## Test Data Setup

Use this GitLab instance to create test data for:
- Organizations (mapped to GitLab groups)
- Course families (mapped to GitLab subgroups)
- Courses (mapped to GitLab projects)
- Student repositories
- Assignment templates

This allows us to test the complete GitLab integration workflow without affecting production systems.