#!/usr/bin/env python3
"""
Test script for Temporal task submission via API.
Demonstrates how to submit tasks and monitor them.
"""

import requests
import json
import time
import sys
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
TEMPORAL_UI_URL = "http://localhost:8088"

# You'll need to set this to a valid auth token
# In development, you might get this from your login endpoint
AUTH_TOKEN = None  # Set this to your actual token


def get_auth_headers():
    """Get authorization headers for API requests."""
    if AUTH_TOKEN:
        return {"Authorization": f"Bearer {AUTH_TOKEN}"}
    return {}


def submit_task(task_name: str, parameters: dict, priority: int = 0) -> Optional[str]:
    """Submit a task and return the task ID."""
    url = f"{API_BASE_URL}/tasks/submit"
    headers = {
        "Content-Type": "application/json",
        **get_auth_headers()
    }
    
    payload = {
        "task_name": task_name,
        "parameters": parameters,
        "priority": priority
    }
    
    print(f"\n📤 Submitting task: {task_name}")
    print(f"   Parameters: {json.dumps(parameters, indent=2)}")
    print(f"   Priority: {priority}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        task_id = result.get("task_id")
        print(f"✅ Task submitted successfully!")
        print(f"   Task ID: {task_id}")
        print(f"   View in Temporal UI: {TEMPORAL_UI_URL}/namespaces/default/workflows/{task_id}")
        
        return task_id
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error submitting task: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def check_task_status(task_id: str):
    """Check the status of a task."""
    url = f"{API_BASE_URL}/tasks/{task_id}"
    headers = get_auth_headers()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        task_info = response.json()
        print(f"\n📊 Task Status:")
        print(f"   Task ID: {task_info['task_id']}")
        print(f"   Status: {task_info['status']}")
        print(f"   Created: {task_info['created_at']}")
        print(f"   Started: {task_info.get('started_at', 'Not started')}")
        print(f"   Finished: {task_info.get('finished_at', 'Not finished')}")
        
        return task_info
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking task status: {e}")
        return None


def get_task_result(task_id: str):
    """Get the result of a completed task."""
    url = f"{API_BASE_URL}/tasks/{task_id}/result"
    headers = get_auth_headers()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n📦 Task Result:")
        print(f"   Status: {result['status']}")
        print(f"   Result: {json.dumps(result.get('result'), indent=2)}")
        print(f"   Error: {result.get('error', 'None')}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting task result: {e}")
        return None


def list_task_types():
    """List all available task types."""
    url = f"{API_BASE_URL}/tasks/types"
    headers = get_auth_headers()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        task_types = response.json()
        print(f"\n📋 Available Task Types:")
        for task_type in task_types:
            print(f"   - {task_type}")
        
        return task_types
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing task types: {e}")
        return []


def demo_long_running_task():
    """Demo: Submit and monitor a long-running task."""
    print("\n" + "="*60)
    print("DEMO: Long Running Task")
    print("="*60)
    
    # Submit task
    task_id = submit_task(
        task_name="example_long_running",
        parameters={
            "duration": 30,
            "message": "Demo task running for 30 seconds"
        },
        priority=0
    )
    
    if not task_id:
        return
    
    # Monitor task
    print("\n⏳ Monitoring task progress...")
    for i in range(10):
        time.sleep(5)
        status = check_task_status(task_id)
        if status and status['status'] in ['FINISHED', 'FAILED']:
            break
    
    # Get result
    get_task_result(task_id)


def demo_high_priority_task():
    """Demo: Submit a high-priority task."""
    print("\n" + "="*60)
    print("DEMO: High Priority Task")
    print("="*60)
    
    task_id = submit_task(
        task_name="example_data_processing",
        parameters={
            "data_size": 100,
            "processing_type": "urgent_transform"
        },
        priority=10  # High priority
    )
    
    if task_id:
        print(f"\n🚀 High priority task submitted to 'computor-high-priority' queue")


def main():
    """Main function to run demos."""
    print("🔧 Temporal Task Testing Script")
    print(f"   API URL: {API_BASE_URL}")
    print(f"   Temporal UI: {TEMPORAL_UI_URL}")
    
    if not AUTH_TOKEN:
        print("\n⚠️  WARNING: No AUTH_TOKEN set. API calls may fail.")
        print("   Set AUTH_TOKEN variable in this script with a valid token.")
    
    # List available tasks
    list_task_types()
    
    # Run demos
    while True:
        print("\n" + "="*60)
        print("Select a demo:")
        print("1. Long running task (30 seconds)")
        print("2. High priority task")
        print("3. List task types")
        print("4. Check specific task status")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-4): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            demo_long_running_task()
        elif choice == "2":
            demo_high_priority_task()
        elif choice == "3":
            list_task_types()
        elif choice == "4":
            task_id = input("Enter task ID: ").strip()
            if task_id:
                check_task_status(task_id)
                get_task_result(task_id)
        else:
            print("Invalid choice")
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()