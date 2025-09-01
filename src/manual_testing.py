import json
import sys
from typing import Dict, List, Any, Optional, Tuple
from ctutor_backend.client.crud_client import CustomClient

def print_test_header(role: str, user: str):
    """Print a formatted test header"""
    print("\n" + "="*80)
    print(f"Testing as {role.upper()} (user: {user})")
    print("="*80)

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def print_result(description: str, success: bool, details: str = ""):
    """Print a test result with consistent formatting"""
    status = "✓" if success else "✗"
    status_text = "SUCCESS" if success else "FAILED"
    print(f"[{status}] {description}: {status_text}")
    if details:
        print(f"    Details: {details}")

def safe_api_call(func, *args, **kwargs) -> Tuple[bool, Any, str]:
    """
    Safely execute an API call and return success status, result, and error message
    """
    try:
        result = func(*args, **kwargs)
        return True, result, ""
    except Exception as e:
        error_msg = str(e)
        # Check if it's a 403 Forbidden (expected for permission tests)
        if "403" in error_msg:
            return False, None, "Permission denied (403)"
        elif "404" in error_msg:
            return False, None, "Not found (404)"
        else:
            return False, None, error_msg

def test_student_endpoints(client: CustomClient, username: str):
    """Test student-specific endpoints"""
    print_section("Student Endpoints")
    
    # Test 1: List courses (students should see their courses)
    success, courses, error = safe_api_call(client.list, "students/courses")
    print_result(
        "List student courses", 
        success,
        f"Found {len(courses) if courses else 0} courses" if success else error
    )
    
    if success and courses:
        # Test 2: Get specific course details
        course_id = courses[0]["id"]
        success, course, error = safe_api_call(client.get, f"students/courses/{course_id}")
        print_result(
            f"Get course details (ID: {course_id[:8]}...)", 
            success,
            f"Course: {course.get('title', 'N/A')}" if success and course else error
        )
        
        # Test 3: List course contents
        success, contents, error = safe_api_call(client.list, "students/course-contents")
        print_result(
            "List course contents",
            success,
            f"Found {len(contents) if contents else 0} contents" if success else error
        )
        
        if success and contents:
            # Test 4: Get specific course content
            content_id = contents[0]["id"]
            success, content, error = safe_api_call(client.get, f"students/course-contents/{content_id}")
            print_result(
                f"Get course content (ID: {content_id[:8]}...)",
                success,
                f"Content: {content.get('title', 'N/A')}" if success and content else error
            )
    
    # Test 5: Get repositories (GitLab integration)
    success, repos, error = safe_api_call(client.list, "students/repositories")
    print_result(
        "List student repositories",
        success,
        f"Found {len(repos) if repos else 0} repositories" if success else error
    )

def test_tutor_endpoints(client: CustomClient, username: str):
    """Test tutor-specific endpoints"""
    print_section("Tutor Endpoints")
    
    # Test 1: List courses where user is tutor
    success, courses, error = safe_api_call(client.list, "tutors/courses")
    print_result(
        "List tutor courses",
        success,
        f"Found {len(courses) if courses else 0} courses" if success else error
    )
    
    if success and courses:
        course_id = courses[0]["id"]
        
        # Test 2: Get specific course as tutor
        success, course, error = safe_api_call(client.get, f"tutors/courses/{course_id}")
        print_result(
            f"Get course as tutor (ID: {course_id[:8]}...)",
            success,
            f"Course: {course.get('title', 'N/A')}" if success and course else error
        )
        
        # # Test 3: Get current course member info
        # success, member, error = safe_api_call(client.get, f"tutors/courses/{course_id}/current")
        # print_result(
        #     "Get current member info",
        #     success,
        #     f"Role: {member.get('course_role_id', 'N/A')}" if success and member else error
        # )
        
        # Test 4: List course members (students in the course)
        success, members, error = safe_api_call(client.list, "tutors/course-members")
        print_result(
            "List course members",
            success,
            f"Found {len(members) if members else 0} members" if success else error
        )
        
        if success and members:
            # Filter for students only
            students = [m for m in members if m.get("course_role_id") == "_student"]
            if students:
                student_member_id = students[0]["id"]
                
                # Test 5: Get specific course member details
                success, member, error = safe_api_call(client.get, f"tutors/course-members/{student_member_id}")
                print_result(
                    f"Get course member (ID: {student_member_id[:8]}...)",
                    success,
                    f"Member: {member.get('user', {}).get('username', 'N/A')}" if success and member else error
                )
                
                # Test 6: List course contents for a specific student
                success, contents, error = safe_api_call(
                    client.list, 
                    f"tutors/course-members/{student_member_id}/course-contents"
                )
                print_result(
                    "List student's course contents",
                    success,
                    f"Found {len(contents) if contents else 0} contents" if success else error
                )
                
                # Test 7: Post a comment on student's work
                comment_data = {"message": f"Test comment from tutor {username}"}
                success, comments, error = safe_api_call(
                    client.create,
                    f"tutors/course-members/{student_member_id}/comments",
                    comment_data
                )
                print_result(
                    "Post comment on student work",
                    success,
                    "Comment posted" if success else error
                )
                
                # Test 8: List comments
                success, comments, error = safe_api_call(
                    client.list,
                    f"tutors/course-members/{student_member_id}/comments"
                )
                print_result(
                    "List comments on student work",
                    success,
                    f"Found {len(comments) if comments else 0} comments" if success else error
                )

def test_lecturer_endpoints(client: CustomClient, username: str):
    """Test lecturer-specific endpoints"""
    print_section("Lecturer Endpoints")
    
    # Test 1: List courses where user is lecturer
    success, courses, error = safe_api_call(client.list, "lecturers/courses")
    print_result(
        "List lecturer courses",
        success,
        f"Found {len(courses) if courses else 0} courses" if success else error
    )
    
    if success and courses:
        course_id = courses[0]["id"]
        
        # Test 2: Get specific course as lecturer
        success, course, error = safe_api_call(client.get, f"lecturers/courses/{course_id}")
        print_result(
            f"Get course as lecturer (ID: {course_id[:8]}...)",
            success,
            f"Course: {course.get('title', 'N/A')}" if success and course else error
        )

def test_cross_role_access(clients: Dict[str, CustomClient]):
    """Test cross-role access permissions"""
    print_section("Cross-Role Permission Tests")
    
    # Test 1: Student trying to access tutor endpoints (should fail)
    success, _, error = safe_api_call(clients["student"].list, "tutors/course-members")
    print_result(
        "Student accessing tutor endpoints",
        not success and "403" in error,
        "Correctly denied" if not success and "403" in error else f"Unexpected: {error if error else 'Allowed'}"
    )
    
    # Test 2: Student trying to access lecturer endpoints (should fail)
    success, _, error = safe_api_call(clients["student"].list, "lecturers/courses")
    print_result(
        "Student accessing lecturer endpoints",
        not success and "403" in error,
        "Correctly denied" if not success and "403" in error else f"Unexpected: {error if error else 'Allowed'}"
    )
    
    # Test 3: Tutor accessing student endpoints (should succeed - tutors can see student data)
    success, courses, error = safe_api_call(clients["tutor"].list, "students/courses")
    print_result(
        "Tutor accessing student endpoints",
        success,
        f"Allowed - found {len(courses) if courses else 0} courses" if success else error
    )
    
    # Test 4: Tutor trying to access lecturer endpoints (should fail)
    success, _, error = safe_api_call(clients["tutor"].list, "lecturers/courses")
    print_result(
        "Tutor accessing lecturer endpoints",
        not success and "403" in error,
        "Correctly denied" if not success and "403" in error else f"Unexpected: {error if error else 'Allowed'}"
    )
    
    # Test 5: Lecturer accessing tutor endpoints (should succeed - lecturers can see tutor data)
    success, members, error = safe_api_call(clients["lecturer"].list, "tutors/course-members")
    print_result(
        "Lecturer accessing tutor endpoints",
        success,
        f"Allowed - found {len(members) if members else 0} members" if success else error
    )
    
    # Test 6: Lecturer accessing student endpoints (should succeed - lecturers can see student data)
    success, courses, error = safe_api_call(clients["lecturer"].list, "students/courses")
    print_result(
        "Lecturer accessing student endpoints",
        success,
        f"Allowed - found {len(courses) if courses else 0} courses" if success else error
    )

def test_admin_access(client: CustomClient):
    """Test admin access to all endpoints"""
    print_section("Admin Access Tests")
    
    # Admin should have access to everything
    endpoints_to_test = [
        ("students/courses", "Student courses"),
        ("tutors/courses", "Tutor courses"),
        ("lecturers/courses", "Lecturer courses"),
        ("tutors/course-members", "Course members"),
    ]
    
    for endpoint, description in endpoints_to_test:
        success, data, error = safe_api_call(client.list, endpoint)
        print_result(
            f"Admin accessing {description}",
            success,
            f"Allowed - found {len(data) if data else 0} items" if success else error
        )

def test_rest_operations(client: CustomClient, role: str):
    """Test REST operations (GET, LIST, CREATE, UPDATE, DELETE) based on role"""
    print_section(f"REST Operations for {role}")
    
    # The operations available depend on the role and endpoint
    # This is a simplified test - expand based on actual API capabilities
    
    if role == "_student":
        # Students typically have read-only access
        success, courses, _ = safe_api_call(client.list, "students/courses")
        print_result("LIST operation", success, "Read access granted" if success else "Access denied")
        
        if success and courses:
            course_id = courses[0]["id"]
            success, _, _ = safe_api_call(client.get, f"students/courses/{course_id}")
            print_result("GET operation", success, "Read access granted" if success else "Access denied")
    
    elif role == "_tutor":
        # Tutors can read and update certain resources
        success, members, _ = safe_api_call(client.list, "tutors/course-members")
        print_result("LIST operation", success, "Read access granted" if success else "Access denied")
        
        if success and members:
            students = [m for m in members if m.get("course_role_id") == "_student"]
            if students:
                member_id = students[0]["id"]
                
                # Try to update (PATCH) - this might be allowed for grading
                update_data = {"grading": 85}
                success, _, error = safe_api_call(
                    client.update, 
                    f"tutors/course-members/{member_id}",
                    update_data
                )
                print_result(
                    "UPDATE operation (grading)",
                    success or "not found" in error.lower(),
                    "Update allowed" if success else error
                )
    
    elif role == "_lecturer":
        # Lecturers have broader permissions
        success, courses, _ = safe_api_call(client.list, "lecturers/courses")
        print_result("LIST operation", success, "Read access granted" if success else "Access denied")
        
        if success and courses:
            course_id = courses[0]["id"]
            success, _, _ = safe_api_call(client.get, f"lecturers/courses/{course_id}")
            print_result("GET operation", success, "Read access granted" if success else "Access denied")

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("COMPUTOR PERMISSION SYSTEM TEST SUITE")
    print("Testing Role-Based Access Control and REST Operations")
    print("="*80)
    
    # Track all test results for summary
    failed_tests = []
    unexpected_access = []
    
    def track_result(role, endpoint, expected_fail, actual_success, error_msg=""):
        """Track test results for summary"""
        if expected_fail and actual_success:
            # Should have failed but succeeded - unexpected access
            unexpected_access.append({
                "role": role,
                "endpoint": endpoint,
                "issue": "Should be denied but was allowed"
            })
        elif not expected_fail and not actual_success:
            # Should have succeeded but failed
            failed_tests.append({
                "role": role,
                "endpoint": endpoint,
                "error": error_msg
            })
    
    # Define test users with their roles and credentials
    test_users = [
        ("_student", ("jdoe", "password")),          # John Doe - student
        ("_student", ("ajohnson", "password")),      # Alice Johnson - student
        ("_tutor", ("ta_assistant", "password")),    # Teaching Assistant - tutor
        ("_tutor", ("smiller", "password")),         # Sarah Miller - tutor (also student)
        ("_lecturer", ("course_manager", "password")), # Course Manager - lecturer
        ("_lecturer", ("dbrown", "password")),       # David Brown - lecturer
        ("_maintainer", ("manderson", "password")),  # Michael Anderson - maintainer
        ("_owner", ("edavis", "password")),          # Emily Davis - owner
        ("_admin", ("admin", "admin")),              # Admin user
    ]
    
    # Create clients for specific test scenarios
    clients = {
        "student": CustomClient(url_base="http://localhost:8000", auth=("jdoe", "password")),
        "tutor": CustomClient(url_base="http://localhost:8000", auth=("ta_assistant", "password")),
        "lecturer": CustomClient(url_base="http://localhost:8000", auth=("course_manager", "password")),
        "admin": CustomClient(url_base="http://localhost:8000", auth=("admin", "admin")),
    }
    
    # Test 1: Individual role endpoint access
    for role, auth in test_users[:6]:  # Test first 6 users
        client = CustomClient(url_base="http://localhost:8000", auth=auth)
        print_test_header(role, auth[0])
        
        if role == "_student":
            test_student_endpoints(client, auth[0])
        elif role == "_tutor":
            test_tutor_endpoints(client, auth[0])
        elif role == "_lecturer":
            test_lecturer_endpoints(client, auth[0])
        
        # Test REST operations for each role
        test_rest_operations(client, role)
    
    # Test 2: Cross-role permission tests
    print_test_header("CROSS-ROLE PERMISSIONS", "Multiple Users")
    print_section("Cross-Role Permission Tests")
    
    # Test with tracking
    # Student -> Tutor (should fail)
    success, _, error = safe_api_call(clients["student"].list, "tutors/course-members")
    track_result("student", "tutors/course-members", True, success, error)
    print_result(
        "Student accessing tutor endpoints",
        not success and "403" in error,
        "Correctly denied" if not success and "403" in error else f"Unexpected: {error if error else 'Allowed'}"
    )
    
    # Student -> Lecturer (should fail)
    success, _, error = safe_api_call(clients["student"].list, "lecturers/courses")
    track_result("student", "lecturers/courses", True, success, error)
    print_result(
        "Student accessing lecturer endpoints",
        not success and "403" in error,
        "Correctly denied" if not success and "403" in error else f"Unexpected: {error if error else 'Allowed'}"
    )
    
    # Tutor -> Student (should succeed)
    success, courses, error = safe_api_call(clients["tutor"].list, "students/courses")
    track_result("tutor", "students/courses", False, success, error)
    print_result(
        "Tutor accessing student endpoints",
        success,
        f"Allowed - found {len(courses) if courses else 0} courses" if success else error
    )
    
    # Tutor -> Lecturer (should fail)
    success, _, error = safe_api_call(clients["tutor"].list, "lecturers/courses")
    track_result("tutor", "lecturers/courses", True, success, error)
    print_result(
        "Tutor accessing lecturer endpoints",
        not success and "403" in error,
        "Correctly denied" if not success and "403" in error else f"Unexpected: {error if error else 'Allowed'}"
    )
    
    # Lecturer -> Tutor (should succeed)
    success, members, error = safe_api_call(clients["lecturer"].list, "tutors/course-members")
    track_result("lecturer", "tutors/course-members", False, success, error)
    print_result(
        "Lecturer accessing tutor endpoints",
        success,
        f"Allowed - found {len(members) if members else 0} members" if success else error
    )
    
    # Lecturer -> Student (should succeed)
    success, courses, error = safe_api_call(clients["lecturer"].list, "students/courses")
    track_result("lecturer", "students/courses", False, success, error)
    print_result(
        "Lecturer accessing student endpoints",
        success,
        f"Allowed - found {len(courses) if courses else 0} courses" if success else error
    )
    
    # Test 3: Admin access test
    print_test_header("ADMIN", "admin")
    test_admin_access(clients["admin"])
    
    # Test 4: Hierarchy validation
    print_test_header("ROLE HIERARCHY", "System Test")
    print_section("Role Hierarchy Validation")
    
    # Test maintainer (should have lecturer + tutor + student access)
    maintainer_client = CustomClient(url_base="http://localhost:8000", auth=("manderson", "password"))
    for endpoint, description in [
        ("students/courses", "Student endpoints"),
        ("tutors/courses", "Tutor endpoints"),
        ("lecturers/courses", "Lecturer endpoints")
    ]:
        success, _, error = safe_api_call(maintainer_client.list, endpoint)
        track_result("maintainer", endpoint, False, success, error)
        print_result(
            f"Maintainer accessing {description}",
            success,
            "Access granted (hierarchy working)" if success else error
        )
    
    # Test owner (should have all course-level access)
    owner_client = CustomClient(url_base="http://localhost:8000", auth=("edavis", "password"))
    for endpoint, description in [
        ("students/courses", "Student endpoints"),
        ("tutors/courses", "Tutor endpoints"),
        ("lecturers/courses", "Lecturer endpoints")
    ]:
        success, _, error = safe_api_call(owner_client.list, endpoint)
        track_result("owner", endpoint, False, success, error)
        print_result(
            f"Owner accessing {description}",
            success,
            "Access granted (hierarchy working)" if success else error
        )
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80)
    
    # Print permission issues summary
    if unexpected_access or failed_tests:
        print("\n" + "="*80)
        print("PERMISSION ISSUES DETECTED")
        print("="*80)
        
        if unexpected_access:
            print("\n🔴 CRITICAL: Unexpected Access Granted (Should be denied):")
            print("-" * 60)
            for item in unexpected_access:
                print(f"  • Role: {item['role']:<15} Endpoint: {item['endpoint']:<30}")
                print(f"    Issue: {item['issue']}")
        
        if failed_tests:
            print("\n⚠️  Failed Access (Should be allowed):")
            print("-" * 60)
            for item in failed_tests:
                print(f"  • Role: {item['role']:<15} Endpoint: {item['endpoint']:<30}")
                print(f"    Error: {item['error']}")
    else:
        print("\n✅ All permission checks passed correctly!")
    
    print("\n" + "="*80)
    print("EXPECTED PERMISSION HIERARCHY:")
    print("-" * 60)
    print("  - Students: Can only access /students/* endpoints")
    print("  - Tutors: Can access /students/* and /tutors/* endpoints")
    print("  - Lecturers: Can access /students/*, /tutors/*, and /lecturers/* endpoints")
    print("  - Maintainers: Higher than lecturer, full course management")
    print("  - Owners: Highest course role, complete control")
    print("  - Admin: Universal access to all endpoints")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)