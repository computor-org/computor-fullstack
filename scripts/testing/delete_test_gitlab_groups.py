#!/usr/bin/env python3
"""
Script to delete test GitLab groups for testing purposes.
"""

from gitlab import Gitlab
from gitlab.exceptions import GitlabDeleteError, GitlabGetError

# GitLab configuration
import os
GITLAB_URL = os.environ.get("TEST_GITLAB_URL", "http://localhost:8084")
GITLAB_TOKEN = os.environ.get("TEST_GITLAB_TOKEN", "")  # Set via environment variable

# Test group paths to delete
TEST_GROUP_PATHS = [
    # Groups with underscores (valid ltree paths)
    "computor-realm/real_test_org/real_family/real_course",
    "computor-realm/real_test_org/real_family",
    "computor-realm/real_test_org",
    # Groups with hyphens (GitLab allows but ltree doesn't)
    "computor-realm/real-test-org/real-family/real-course",
    "computor-realm/real-test-org/real-family",
    "computor-realm/real-test-org",
    "computor-realm/refactor-test/test-family/python-basics",
    "computor-realm/refactor-test/test-family",
    "computor-realm/refactor-test",
    "computor-realm/builder-test-org/builder-family/builder-course",
    "computor-realm/builder-test-org/builder-family",
    "computor-realm/builder-test-org",
]


def main():
    """Delete test GitLab groups."""
    print("🧹 GitLab Test Group Cleanup")
    print("=" * 60)
    
    # Connect to GitLab
    print(f"\n📡 Connecting to GitLab at {GITLAB_URL}...")
    try:
        gl = Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
        gl.auth()
        print("✅ Connected to GitLab")
    except Exception as e:
        print(f"❌ Failed to connect to GitLab: {e}")
        return 1
    
    # Get all groups
    print("\n🔍 Searching for test groups...")
    all_groups = gl.groups.list(all=True)
    
    # Find test groups
    test_groups = []
    for path in TEST_GROUP_PATHS:
        for group in all_groups:
            if group.full_path == path:
                test_groups.append(group)
                break
    
    if not test_groups:
        print("✅ No test groups found to delete")
        return 0
    
    # Show groups to delete
    print(f"\n📋 Found {len(test_groups)} test groups to delete:")
    for group in test_groups:
        print(f"   - {group.full_path} (ID: {group.id})")
    
    # Confirm deletion
    print("\n⚠️ WARNING: This will permanently delete these groups!")
    response = input("Do you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Deletion cancelled.")
        return 0
    
    # Delete groups (in reverse order to delete children first)
    print("\n🗑️ Deleting groups...")
    deleted_count = 0
    for group in reversed(test_groups):
        try:
            full_group = gl.groups.get(group.id)
            full_group.delete()
            print(f"✅ Deleted: {group.full_path}")
            deleted_count += 1
        except GitlabDeleteError as e:
            print(f"❌ Failed to delete {group.full_path}: {e}")
        except GitlabGetError:
            print(f"⚠️ Group {group.full_path} no longer exists")
    
    print(f"\n✅ Deleted {deleted_count} groups")
    
    # Also check database
    print("\n💡 Note: Database entries may still exist.")
    print("   The GitLab builder will handle this by:")
    print("   - Detecting missing GitLab groups")
    print("   - Recreating them automatically")
    print("   - Updating stored properties")
    
    return 0


if __name__ == "__main__":
    exit(main())