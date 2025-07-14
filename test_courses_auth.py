#!/usr/bin/env python3
"""
Quick test to verify courses endpoint with SSO authentication
"""

import requests
import sys

def test_courses_endpoint(token):
    """Test the courses endpoint with Bearer token"""
    
    # API endpoint
    url = "http://localhost:8000/courses"
    
    # Headers with Bearer token
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"Testing courses endpoint with token: {token[:20]}...")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! Courses data:")
            print(response.json())
        elif response.status_code == 401:
            print("Unauthorized - Token may be invalid or expired")
            print("Response:", response.text)
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

def main():
    print("After logging in via SSO, copy the token from the redirect URL")
    print("URL format: http://localhost:8000/auth/success?...&token=YOUR_TOKEN")
    print("\nEnter your token: ", end="")
    
    token = input().strip()
    
    if not token:
        print("No token provided!")
        sys.exit(1)
    
    test_courses_endpoint(token)

if __name__ == "__main__":
    main()