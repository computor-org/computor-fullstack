#!/usr/bin/env python3
"""
Debug GitLab authentication issue
"""

import os
from gitlab import Gitlab

# Configuration
GITLAB_URL = os.environ.get("TEST_GITLAB_URL", "http://localhost:8084")
GITLAB_TOKEN = os.environ.get("TEST_GITLAB_TOKEN", "")

print(f"Testing GitLab authentication")
print(f"URL: {GITLAB_URL}")

if not GITLAB_TOKEN:
    print("❌ ERROR: TEST_GITLAB_TOKEN environment variable not set!")
    print("Please set it before running this script:")
    print("  export TEST_GITLAB_TOKEN='your-gitlab-token'")
    exit(1)

print(f"Token: {GITLAB_TOKEN[:8]}...")

try:
    # Test different ways of initializing GitLab
    print("\n1. Testing basic GitLab initialization...")
    gl = Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
    print("✅ GitLab object created")
    
    print("\n2. Testing authentication...")
    user = gl.auth()
    print(f"✅ Authentication successful: {user}")
    
    print("\n3. Testing with keep_base_url=True...")
    gl2 = Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN, keep_base_url=True)
    user2 = gl2.auth()
    print(f"✅ Authentication successful with keep_base_url: {user2}")
    
    print("\n4. Testing current user...")
    current_user = gl.user
    print(f"✅ Current user: {current_user.username}")
    
    print("\n5. Testing groups access...")
    groups = gl.groups.list(all=True)
    print(f"✅ Found {len(groups)} groups")
    for group in groups:
        print(f"   - {group.name} (ID: {group.id})")
    
    print("\n🎉 All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()