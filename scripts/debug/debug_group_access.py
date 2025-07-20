#!/usr/bin/env python
"""Debug GitLab group access."""

import os
from pathlib import Path
from dotenv import load_dotenv
import gitlab

# Load environment variables
env_file = Path(__file__).parent / ".env"
load_dotenv(env_file)

gitlab_url = os.getenv("TEST_GITLAB_URL", "http://localhost:8084")
gitlab_token = os.getenv("TEST_GITLAB_TOKEN")
parent_group_id = os.getenv("TEST_GITLAB_GROUP_ID")

print(f"GitLab URL: {gitlab_url}")
print(f"Token: {gitlab_token[:20]}...")
print(f"Parent Group ID: {parent_group_id}")

if not gitlab_token:
    print("❌ No GitLab token found")
    exit(1)

gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)

print("\n=== Testing GitLab API Access ===")

try:
    # Test basic authentication
    version = gl.version()
    print(f"✅ Authentication successful: {version}")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    exit(1)

try:
    # List all groups we can access
    groups = gl.groups.list(all=True)
    print(f"✅ Can access {len(groups)} groups:")
    for group in groups:
        print(f"  - ID: {group.id}, Path: {group.full_path}, Name: {group.name}")
except Exception as e:
    print(f"❌ Cannot list groups: {e}")

if parent_group_id:
    try:
        # Test access to specific parent group
        parent_group = gl.groups.get(parent_group_id)
        print(f"✅ Can access parent group {parent_group_id}: {parent_group.full_path}")
    except Exception as e:
        print(f"❌ Cannot access parent group {parent_group_id}: {e}")
        print("This is likely why the test is failing!")

print("\n=== Testing Group Creation ===")

try:
    # Test creating a simple group at root level
    test_group_data = {
        'name': 'Test Group',
        'path': 'test-group-debug',
        'description': 'Test group for debugging',
        'visibility': 'private'
    }
    
    test_group = gl.groups.create(test_group_data)
    print(f"✅ Can create groups at root level: {test_group.full_path}")
    
    # Clean up
    test_group.delete()
    print("✅ Test group deleted")
    
except Exception as e:
    print(f"❌ Cannot create groups at root level: {e}")
    
print("\n=== Recommendations ===")
print("1. If parent group access fails, create groups at root level (parent=None)")
print("2. If group creation fails, check token scopes (needs 'api' scope)")
print("3. If token is project-scoped, it may not have group creation permissions")