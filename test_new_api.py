#!/usr/bin/env python3
"""
Test script for the new two-step example deployment process.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Replace with actual values from your system
COURSE_ID = "your-course-id"
CONTENT_ID = "your-content-id"
EXAMPLE_ID = "your-example-id"
AUTH_TOKEN = "your-auth-token"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_assign_example():
    """Test Step 1: Assign example to course content."""
    print("Testing example assignment...")
    
    response = requests.post(
        f"{BASE_URL}/course-contents/{CONTENT_ID}/assign-example",
        headers=headers,
        json={
            "example_id": EXAMPLE_ID,
            "example_version": "latest"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_pending_changes():
    """Test getting pending changes."""
    print("\nTesting pending changes...")
    
    response = requests.get(
        f"{BASE_URL}/courses/{COURSE_ID}/pending-changes",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_generate_template():
    """Test Step 2: Generate student template."""
    print("\nTesting template generation...")
    
    response = requests.post(
        f"{BASE_URL}/courses/{COURSE_ID}/generate-student-template",
        headers=headers,
        json={
            "commit_message": "Update student template from Example Library"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_contents_with_examples():
    """Test getting course contents with examples."""
    print("\nTesting course contents with examples...")
    
    response = requests.get(
        f"{BASE_URL}/courses/{COURSE_ID}/contents-with-examples",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

if __name__ == "__main__":
    print("=== Testing New Two-Step Example Deployment API ===\n")
    
    print("IMPORTANT: Update the following variables before running:")
    print(f"- COURSE_ID: {COURSE_ID}")
    print(f"- CONTENT_ID: {CONTENT_ID}")
    print(f"- EXAMPLE_ID: {EXAMPLE_ID}")
    print(f"- AUTH_TOKEN: {AUTH_TOKEN}")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    input()
    
    # Run tests
    tests = [
        ("Assign Example", test_assign_example),
        ("Get Pending Changes", test_get_pending_changes),
        ("Generate Template", test_generate_template),
        ("Get Contents with Examples", test_get_contents_with_examples)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"Error: {e}")
            results.append((test_name, "ERROR"))
    
    print("\n=== Test Summary ===")
    for test_name, result in results:
        print(f"{test_name}: {result}")