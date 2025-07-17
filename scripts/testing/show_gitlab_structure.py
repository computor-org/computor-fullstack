#!/usr/bin/env python
"""Show the GitLab structure that would be created."""
import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def main():
    """Show the GitLab structure."""
    gitlab_url = os.getenv("GITLAB_URL", "http://localhost:8084")
    
    print("\n" + "="*60)
    print("GITLAB STRUCTURE TO BE CREATED")
    print("="*60)
    
    print("\n📁 demo-university (Organization)")
    print("   └── 📁 cs-2024 (Course Family)")
    print("       └── 📁 intro-programming (Course)")
    print("           └── 📁 students (Students Group)")
    
    print("\n" + "="*60)
    print("GITLAB GROUPS AND PERMISSIONS")
    print("="*60)
    
    print("\n1. Organization Group: demo-university")
    print("   - Type: GitLab Group")
    print("   - Visibility: Private")
    print("   - Members: Organization admins (Owner access)")
    
    print("\n2. Course Family Group: demo-university/cs-2024")
    print("   - Type: GitLab Subgroup")
    print("   - Visibility: Private")
    print("   - Members: Course family coordinators (Maintainer access)")
    
    print("\n3. Course Group: demo-university/cs-2024/intro-programming")
    print("   - Type: GitLab Subgroup")
    print("   - Visibility: Private")
    print("   - Members: Lecturers (Maintainer access)")
    
    print("\n4. Students Group: demo-university/cs-2024/intro-programming/students")
    print("   - Type: GitLab Subgroup")
    print("   - Visibility: Private")
    print("   - Members: Students (Developer access)")
    
    print("\n" + "="*60)
    print("MEMBER MANAGEMENT")
    print("="*60)
    
    print("\nStudents:")
    print("  - Added to: intro-programming/students group")
    print("  - Access level: Developer (can create projects, push code)")
    print("  - Cannot: Modify course structure, see other students' private projects")
    
    print("\nLecturers:")
    print("  - Added to: intro-programming group")
    print("  - Access level: Maintainer (can manage course)")
    print("  - Can: Create course projects, manage students, view all submissions")
    
    print("\n" + "="*60)
    print("NEXT FEATURES TO IMPLEMENT")
    print("="*60)
    
    print("\n1. Course Projects:")
    print("   - intro-programming/tests (test suite project)")
    print("   - intro-programming/student-template (starter code)")
    print("   - intro-programming/reference (reference solution)")
    
    print("\n2. Student Projects:")
    print("   - students/<username>-submissions (per-student project)")
    
    print("\n3. Git Operations:")
    print("   - Initialize projects with README")
    print("   - Push starter code to student-template")
    print("   - Set up CI/CD for automatic testing")
    
    print(f"\nGitLab URL: {gitlab_url}")
    print("Default login: root / topsecret123")
    print("\n")

if __name__ == "__main__":
    main()