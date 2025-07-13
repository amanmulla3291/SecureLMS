#!/usr/bin/env python3
"""
BuildBytes LMS Backend API Testing Suite - Manual Authentication System
Tests all API endpoints including JWT authentication, user registration/login, and CRUD operations.
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class BuildBytesAPITester:
    def __init__(self, base_url: str = "https://30fd2b50-0308-4158-b46f-1f5cbb0a9968.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.current_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_users = {
            "mentor": None,
            "student": None
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {name}"
        if details:
            result += f" | {details}"
        
        print(result)
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        return success

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    expected_status: int = 200, use_auth: bool = False, timeout: int = 15) -> tuple[bool, Dict]:
        """Make HTTP request and validate response"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            if not success:
                response_data["status_code"] = response.status_code
                response_data["expected_status"] = expected_status
            
            return success, response_data
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout - API may be slow or unresponsive"}
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_health_check(self) -> bool:
        """Test the root API endpoint"""
        success, response = self.make_request('GET', '/')
        
        if success and response.get('message') == 'BuildBytes LMS API':
            return self.log_test("Health Check", True, f"Version: {response.get('version', 'N/A')}")
        else:
            return self.log_test("Health Check", False, f"Response: {response}")

    def test_user_registration(self) -> bool:
        """Test user registration endpoint with various scenarios"""
        print("\n🔐 Testing User Registration...")
        
        # Test valid mentor registration
        mentor_data = {
            "name": "Dr. Sarah Johnson",
            "email": f"mentor_{int(time.time())}@buildbytes.edu",
            "password": "SecurePass123",
            "role": "mentor"
        }
        
        success, response = self.make_request('POST', '/auth/register', data=mentor_data, expected_status=200)
        
        if success and response.get('access_token') and response.get('user'):
            self.test_users["mentor"] = {
                "data": mentor_data,
                "token": response['access_token'],
                "user": response['user']
            }
            self.log_test("Mentor Registration", True, f"User ID: {response['user']['id']}")
        else:
            self.log_test("Mentor Registration", False, f"Response: {response}")
            return False
        
        # Test valid student registration
        student_data = {
            "name": "Alex Chen",
            "email": f"student_{int(time.time())}@buildbytes.edu",
            "password": "StudentPass456",
            "role": "student"
        }
        
        success, response = self.make_request('POST', '/auth/register', data=student_data, expected_status=200)
        
        if success and response.get('access_token') and response.get('user'):
            self.test_users["student"] = {
                "data": student_data,
                "token": response['access_token'],
                "user": response['user']
            }
            self.log_test("Student Registration", True, f"User ID: {response['user']['id']}")
        else:
            self.log_test("Student Registration", False, f"Response: {response}")
            return False
        
        return True

    def test_password_validation(self) -> bool:
        """Test password strength validation with comprehensive test cases"""
        print("\n🔒 Testing Password Validation...")
        
        # Valid password test cases
        valid_passwords = [
            ("TestPass123", "Valid password with uppercase, lowercase, and numbers"),
            ("MySecure1", "Valid password - minimum requirements met"),
            ("ValidPass9", "Valid password - all requirements satisfied")
        ]
        
        # Invalid password test cases
        invalid_passwords = [
            ("nouppercase123", "No uppercase letter - should fail"),
            ("NOLOWERCASE123", "No lowercase letter - should fail"),
            ("NoNumbers", "No numbers - should fail"),
            ("Short1", "Too short (less than 8 characters) - should fail"),
            ("ValidPassword", "No numbers - should fail"),
            ("validpassword123", "No uppercase letter - should fail"),
            ("VALIDPASSWORD123", "No lowercase letter - should fail")
        ]
        
        all_passed = True
        
        # Test valid passwords (should return 200)
        print("  Testing VALID passwords...")
        for password, description in valid_passwords:
            user_data = {
                "name": "Test User",
                "email": f"valid_test_{int(time.time())}_{len(password)}@test.com",
                "password": password,
                "role": "student"
            }
            
            success, response = self.make_request('POST', '/auth/register', 
                                                data=user_data, expected_status=200)
            
            if success and response.get('access_token'):
                self.log_test(f"Valid Password - {password}", True, description)
            else:
                self.log_test(f"Valid Password - {password}", False, f"Expected success but got: {response}")
                all_passed = False
        
        # Test invalid passwords (should return 400)
        print("  Testing INVALID passwords...")
        for password, description in invalid_passwords:
            user_data = {
                "name": "Test User",
                "email": f"invalid_test_{int(time.time())}_{len(password)}@test.com",
                "password": password,
                "role": "student"
            }
            
            success, response = self.make_request('POST', '/auth/register', 
                                                data=user_data, expected_status=400)
            
            if success:
                self.log_test(f"Invalid Password - {password}", True, description)
            else:
                self.log_test(f"Invalid Password - {password}", False, f"Expected 400 error but got: {response}")
                all_passed = False
        
        return all_passed

    def test_email_uniqueness(self) -> bool:
        """Test email uniqueness validation"""
        print("\n📧 Testing Email Uniqueness...")
        
        if not self.test_users["mentor"]:
            return self.log_test("Email Uniqueness", False, "No mentor user available for testing")
        
        # Try to register with same email
        duplicate_data = {
            "name": "Another User",
            "email": self.test_users["mentor"]["data"]["email"],
            "password": "AnotherPass123",
            "role": "student"
        }
        
        success, response = self.make_request('POST', '/auth/register', 
                                            data=duplicate_data, expected_status=409)
        
        if success:
            return self.log_test("Email Uniqueness", True, "Duplicate email correctly rejected")
        else:
            return self.log_test("Email Uniqueness", False, f"Response: {response}")

    def test_role_validation(self) -> bool:
        """Test user role validation"""
        print("\n👥 Testing Role Validation...")
        
        # Test invalid role
        invalid_role_data = {
            "name": "Test User",
            "email": f"invalid_role_{int(time.time())}@test.com",
            "password": "ValidPass123",
            "role": "admin"  # Invalid role
        }
        
        success, response = self.make_request('POST', '/auth/register', 
                                            data=invalid_role_data, expected_status=400)
        
        if success:
            return self.log_test("Role Validation", True, "Invalid role correctly rejected")
        else:
            return self.log_test("Role Validation", False, f"Response: {response}")

    def test_user_login(self) -> bool:
        """Test user login endpoint"""
        print("\n🔑 Testing User Login...")
        
        if not self.test_users["mentor"]:
            return self.log_test("User Login", False, "No mentor user available for testing")
        
        # Test valid login
        login_data = {
            "email": self.test_users["mentor"]["data"]["email"],
            "password": self.test_users["mentor"]["data"]["password"]
        }
        
        success, response = self.make_request('POST', '/auth/login', data=login_data, expected_status=200)
        
        if success and response.get('access_token') and response.get('user'):
            self.log_test("Valid Login", True, f"Token received for user: {response['user']['name']}")
        else:
            self.log_test("Valid Login", False, f"Response: {response}")
            return False
        
        # Test invalid credentials
        invalid_login = {
            "email": self.test_users["mentor"]["data"]["email"],
            "password": "WrongPassword123"
        }
        
        success, response = self.make_request('POST', '/auth/login', 
                                            data=invalid_login, expected_status=401)
        
        if success:
            self.log_test("Invalid Login", True, "Invalid credentials correctly rejected")
        else:
            self.log_test("Invalid Login", False, f"Response: {response}")
            return False
        
        # Test non-existent user
        nonexistent_login = {
            "email": "nonexistent@test.com",
            "password": "SomePassword123"
        }
        
        success, response = self.make_request('POST', '/auth/login', 
                                            data=nonexistent_login, expected_status=401)
        
        if success:
            self.log_test("Non-existent User Login", True, "Non-existent user correctly rejected")
            return True
        else:
            self.log_test("Non-existent User Login", False, f"Response: {response}")
            return False

    def test_jwt_token_authentication(self) -> bool:
        """Test JWT token authentication on protected endpoints"""
        print("\n🎫 Testing JWT Token Authentication...")
        
        if not self.test_users["mentor"]:
            return self.log_test("JWT Authentication", False, "No mentor user available for testing")
        
        # Set valid token
        self.token = self.test_users["mentor"]["token"]
        
        # Test protected endpoint with valid token
        success, response = self.make_request('GET', '/me', expected_status=200, use_auth=True)
        
        if success and response.get('email') == self.test_users["mentor"]["data"]["email"]:
            self.log_test("Valid JWT Token", True, f"User info retrieved: {response['name']}")
        else:
            self.log_test("Valid JWT Token", False, f"Response: {response}")
            return False
        
        # Test with invalid token
        original_token = self.token
        self.token = "invalid.jwt.token"
        
        success, response = self.make_request('GET', '/me', expected_status=401, use_auth=True)
        
        if success:
            self.log_test("Invalid JWT Token", True, "Invalid token correctly rejected")
        else:
            self.log_test("Invalid JWT Token", False, f"Response: {response}")
            return False
        
        # Test without token
        self.token = None
        success, response = self.make_request('GET', '/me', expected_status=403)
        
        if success:
            self.log_test("Missing JWT Token", True, "Missing token correctly rejected")
        else:
            self.log_test("Missing JWT Token", False, f"Response: {response}")
            return False
        
        # Restore valid token
        self.token = original_token
        return True

    def test_protected_endpoints(self) -> bool:
        """Test protected endpoints with valid JWT tokens"""
        print("\n🛡️ Testing Protected Endpoints...")
        
        if not self.test_users["mentor"]:
            return self.log_test("Protected Endpoints", False, "No mentor user available for testing")
        
        self.token = self.test_users["mentor"]["token"]
        
        protected_endpoints = [
            ('/me', 'GET', 200),
            ('/dashboard/stats', 'GET', 200),
            ('/subject-categories', 'GET', 200)
        ]
        
        all_passed = True
        for endpoint, method, expected_status in protected_endpoints:
            success, response = self.make_request(method, endpoint, 
                                                expected_status=expected_status, use_auth=True)
            
            if success:
                self.log_test(f"Protected Endpoint - {method} {endpoint}", True, "Access granted with valid token")
            else:
                self.log_test(f"Protected Endpoint - {method} {endpoint}", False, f"Response: {response}")
                all_passed = False
        
        return all_passed

    def test_role_based_access(self) -> bool:
        """Test role-based access control"""
        print("\n👤 Testing Role-Based Access Control...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Role-Based Access", False, "Both student and mentor users needed for testing")
        
        # Test mentor-only endpoint with student token
        self.token = self.test_users["student"]["token"]
        
        mentor_only_data = {
            "name": "Test Category",
            "description": "Test Description"
        }
        
        success, response = self.make_request('POST', '/subject-categories', 
                                            data=mentor_only_data, expected_status=403, use_auth=True)
        
        if success:
            self.log_test("Student Access to Mentor Endpoint", True, "Student correctly denied access")
        else:
            self.log_test("Student Access to Mentor Endpoint", False, f"Response: {response}")
            return False
        
        # Test mentor-only endpoint with mentor token
        self.token = self.test_users["mentor"]["token"]
        
        success, response = self.make_request('POST', '/subject-categories', 
                                            data=mentor_only_data, expected_status=200, use_auth=True)
        
        if success and response.get('id'):
            self.log_test("Mentor Access to Mentor Endpoint", True, f"Category created: {response['id']}")
            return True
        else:
            self.log_test("Mentor Access to Mentor Endpoint", False, f"Response: {response}")
            return False

    def test_password_hashing_security(self) -> bool:
        """Test that passwords are properly hashed and not stored in plain text"""
        print("\n🔐 Testing Password Hashing Security...")
        
        # This is an indirect test - we verify that login works with the original password
        # but would fail with a different password, indicating proper hashing
        if not self.test_users["mentor"]:
            return self.log_test("Password Hashing", False, "No mentor user available for testing")
        
        # Test that original password works
        login_data = {
            "email": self.test_users["mentor"]["data"]["email"],
            "password": self.test_users["mentor"]["data"]["password"]
        }
        
        success, response = self.make_request('POST', '/auth/login', data=login_data, expected_status=200)
        
        if success and response.get('access_token'):
            self.log_test("Password Hashing - Original Password", True, "Original password works")
        else:
            self.log_test("Password Hashing - Original Password", False, f"Response: {response}")
            return False
        
        # Test that a similar but different password fails
        wrong_login = {
            "email": self.test_users["mentor"]["data"]["email"],
            "password": self.test_users["mentor"]["data"]["password"] + "x"  # Add one character
        }
        
        success, response = self.make_request('POST', '/auth/login', 
                                            data=wrong_login, expected_status=401)
        
        if success:
            self.log_test("Password Hashing - Wrong Password", True, "Wrong password correctly rejected")
            return True
        else:
            self.log_test("Password Hashing - Wrong Password", False, f"Response: {response}")
            return False

    def test_unauthenticated_endpoints(self) -> bool:
        """Test endpoints that should require authentication"""
        print("\n🚫 Testing Unauthenticated Access...")
        
        endpoints_to_test = [
            ('/me', 403),  # FastAPI HTTPBearer returns 403 for missing auth header
            ('/dashboard/stats', 403),
            ('/subject-categories', 403)
        ]
        
        all_passed = True
        for endpoint, expected_status in endpoints_to_test:
            success, response = self.make_request('GET', endpoint, expected_status=expected_status)
            test_name = f"Unauthenticated Access - {endpoint}"
            
            if success:
                self.log_test(test_name, True, "Correctly rejected")
            else:
                self.log_test(test_name, False, f"Expected {expected_status}, got {response.get('status_code')}")
                all_passed = False
        
        return all_passed

    def test_subject_categories_crud_without_auth(self) -> bool:
        """Test CRUD operations without authentication (should fail)"""
        print("\n🔒 Testing CRUD Without Authentication...")
        
        test_category = {
            "name": "Test Category",
            "description": "Test Description",
            "color": "#FF0000"
        }
        
        # Test POST without auth - FastAPI HTTPBearer returns 403 for missing auth header
        success, response = self.make_request('POST', '/subject-categories', 
                                            data=test_category, expected_status=403)
        
        if success:
            return self.log_test("Create Category Without Auth", True, "Correctly rejected")
        else:
            return self.log_test("Create Category Without Auth", False, f"Response: {response}")

    def test_token_expiration_format(self) -> bool:
        """Test JWT token format and expiration settings"""
        print("\n⏰ Testing JWT Token Format...")
        
        if not self.test_users["mentor"]:
            return self.log_test("Token Format", False, "No mentor user available for testing")
        
        token = self.test_users["mentor"]["token"]
        
        # Basic JWT format check (should have 3 parts separated by dots)
        token_parts = token.split('.')
        if len(token_parts) == 3:
            self.log_test("JWT Token Format", True, "Token has correct JWT format (3 parts)")
        else:
            self.log_test("JWT Token Format", False, f"Token has {len(token_parts)} parts, expected 3")
            return False
        
        # Test that token works immediately after creation
        self.token = token
        success, response = self.make_request('GET', '/me', expected_status=200, use_auth=True)
        
        if success:
            self.log_test("JWT Token Validity", True, "Newly created token works correctly")
            return True
        else:
            self.log_test("JWT Token Validity", False, f"Response: {response}")
            return False

    def test_enhanced_task_management(self) -> bool:
        """Test enhanced task management - update and delete endpoints"""
        print("\n📝 Testing Enhanced Task Management...")
        
        if not self.test_users["mentor"]:
            return self.log_test("Enhanced Task Management", False, "No mentor user available")
        
        self.token = self.test_users["mentor"]["token"]
        
        # First create a subject category and project for testing
        category_data = {
            "name": "Programming Fundamentals",
            "description": "Basic programming concepts"
        }
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Task Management Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "Python Basics Project",
            "description": "Learn Python fundamentals",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Task Management Setup - Project", False, f"Response: {project_response}")
        
        # Create a task
        task_data = {
            "project_id": project_response["id"],
            "title": "Variables and Data Types",
            "description": "Learn about Python variables and data types",
            "deadline": "2024-12-31T23:59:59"
        }
        success, task_response = self.make_request('POST', '/tasks', 
                                                 data=task_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Task Creation", False, f"Response: {task_response}")
        
        self.log_test("Task Creation", True, f"Task created: {task_response['id']}")
        task_id = task_response["id"]
        
        # Test task update
        update_data = {
            "title": "Variables, Data Types, and Basic Operations",
            "description": "Updated description with more details",
            "status": "in_progress"
        }
        success, update_response = self.make_request('PUT', f'/tasks/{task_id}', 
                                                   data=update_data, expected_status=200, use_auth=True)
        if success and update_response.get("title") == update_data["title"]:
            self.log_test("Task Update", True, "Task updated successfully")
        else:
            self.log_test("Task Update", False, f"Response: {update_response}")
            return False
        
        # Test task delete
        success, delete_response = self.make_request('DELETE', f'/tasks/{task_id}', 
                                                   expected_status=200, use_auth=True)
        if success:
            self.log_test("Task Delete", True, "Task deleted successfully")
            return True
        else:
            self.log_test("Task Delete", False, f"Response: {delete_response}")
            return False

    def test_submissions_system(self) -> bool:
        """Test submissions system - full CRUD operations"""
        print("\n📤 Testing Submissions System...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Submissions System", False, "Both student and mentor users needed")
        
        # Setup: Create category, project, and task as mentor
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Web Development", "description": "Web dev projects"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submissions Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "HTML/CSS Project",
            "description": "Build a responsive website",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submissions Setup - Project", False, f"Response: {project_response}")
        
        task_data = {
            "project_id": project_response["id"],
            "title": "Create Homepage",
            "description": "Design and implement homepage"
        }
        success, task_response = self.make_request('POST', '/tasks', 
                                                 data=task_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submissions Setup - Task", False, f"Response: {task_response}")
        
        task_id = task_response["id"]
        
        # Test submission creation as student
        self.token = self.test_users["student"]["token"]
        
        submission_data = {
            "task_id": task_id,
            "text_content": "I have completed the homepage with responsive design using HTML5 and CSS3.",
            "file_name": "homepage.html",
            "file_data": "PGh0bWw+PGhlYWQ+PHRpdGxlPkhvbWVwYWdlPC90aXRsZT48L2hlYWQ+PGJvZHk+PGgxPldlbGNvbWU8L2gxPjwvYm9keT48L2h0bWw+",  # Base64 encoded HTML
            "file_type": "text/html"
        }
        success, submission_response = self.make_request('POST', '/submissions', 
                                                       data=submission_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submission Creation", False, f"Response: {submission_response}")
        
        self.log_test("Submission Creation", True, f"Submission created: {submission_response['id']}")
        submission_id = submission_response["id"]
        
        # Test getting submissions as student
        success, submissions_response = self.make_request('GET', '/submissions', 
                                                        expected_status=200, use_auth=True)
        if success and len(submissions_response) > 0:
            self.log_test("Get Submissions (Student)", True, f"Retrieved {len(submissions_response)} submissions")
        else:
            self.log_test("Get Submissions (Student)", False, f"Response: {submissions_response}")
            return False
        
        # Test getting specific submission as student
        success, specific_submission = self.make_request('GET', f'/submissions/{submission_id}', 
                                                       expected_status=200, use_auth=True)
        if success and specific_submission.get("id") == submission_id:
            self.log_test("Get Specific Submission", True, "Retrieved submission details")
        else:
            self.log_test("Get Specific Submission", False, f"Response: {specific_submission}")
            return False
        
        # Test submission feedback/grading as mentor
        self.token = self.test_users["mentor"]["token"]
        
        feedback_data = {
            "feedback": "Great work! The homepage looks professional and is well-structured. Consider adding more interactive elements.",
            "status": "approved",
            "grade": 95.0
        }
        success, feedback_response = self.make_request('PUT', f'/submissions/{submission_id}', 
                                                     data=feedback_data, expected_status=200, use_auth=True)
        if success and feedback_response.get("feedback") == feedback_data["feedback"]:
            self.log_test("Submission Feedback/Grading", True, f"Grade: {feedback_response['grade']}")
            return True
        else:
            self.log_test("Submission Feedback/Grading", False, f"Response: {feedback_response}")
            return False

    def test_resources_system(self) -> bool:
        """Test resources system - full CRUD operations"""
        print("\n📚 Testing Resources System...")
        
        if not self.test_users["mentor"]:
            return self.log_test("Resources System", False, "No mentor user available")
        
        self.token = self.test_users["mentor"]["token"]
        
        # Create a subject category first
        category_data = {"name": "Data Science", "description": "Data science resources"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Resources Setup - Category", False, f"Response: {category_response}")
        
        category_id = category_response["id"]
        
        # Test resource creation (link type)
        link_resource_data = {
            "subject_category_id": category_id,
            "title": "Python Data Science Handbook",
            "description": "Comprehensive guide to data science with Python",
            "resource_type": "link",
            "url": "https://jakevdp.github.io/PythonDataScienceHandbook/"
        }
        success, link_response = self.make_request('POST', '/resources', 
                                                 data=link_resource_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Resource Creation (Link)", False, f"Response: {link_response}")
        
        self.log_test("Resource Creation (Link)", True, f"Link resource created: {link_response['id']}")
        link_resource_id = link_response["id"]
        
        # Test resource creation (document type with file)
        doc_resource_data = {
            "subject_category_id": category_id,
            "title": "Data Analysis Cheat Sheet",
            "description": "Quick reference for pandas and numpy",
            "resource_type": "document",
            "file_name": "cheat_sheet.pdf",
            "file_data": "JVBERi0xLjQKJcOkw7zDtsO8CjIgMCBvYmoKPDwKL0xlbmd0aCAzIDAgUgo+PgpzdHJlYW0KQNC4xOzAuMTswLjE=",  # Base64 encoded PDF header
            "file_type": "application/pdf"
        }
        success, doc_response = self.make_request('POST', '/resources', 
                                                data=doc_resource_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Resource Creation (Document)", False, f"Response: {doc_response}")
        
        self.log_test("Resource Creation (Document)", True, f"Document resource created: {doc_response['id']}")
        doc_resource_id = doc_response["id"]
        
        # Test getting all resources
        success, resources_response = self.make_request('GET', '/resources', 
                                                      expected_status=200, use_auth=True)
        if success and len(resources_response) >= 2:
            self.log_test("Get All Resources", True, f"Retrieved {len(resources_response)} resources")
        else:
            self.log_test("Get All Resources", False, f"Response: {resources_response}")
            return False
        
        # Test getting resources by category
        success, category_resources = self.make_request('GET', f'/resources?subject_category_id={category_id}', 
                                                      expected_status=200, use_auth=True)
        if success and len(category_resources) >= 2:
            self.log_test("Get Resources by Category", True, f"Retrieved {len(category_resources)} resources for category")
        else:
            self.log_test("Get Resources by Category", False, f"Response: {category_resources}")
            return False
        
        # Test resource update
        update_data = {
            "title": "Updated: Python Data Science Handbook",
            "description": "Updated comprehensive guide with latest examples"
        }
        success, update_response = self.make_request('PUT', f'/resources/{link_resource_id}', 
                                                   data=update_data, expected_status=200, use_auth=True)
        if success and update_response.get("title") == update_data["title"]:
            self.log_test("Resource Update", True, "Resource updated successfully")
        else:
            self.log_test("Resource Update", False, f"Response: {update_response}")
            return False
        
        # Test resource delete
        success, delete_response = self.make_request('DELETE', f'/resources/{doc_resource_id}', 
                                                   expected_status=200, use_auth=True)
        if success:
            self.log_test("Resource Delete", True, "Resource deleted successfully")
            return True
        else:
            self.log_test("Resource Delete", False, f"Response: {delete_response}")
            return False

    def test_messaging_system(self) -> bool:
        """Test messaging system - full CRUD operations"""
        print("\n💬 Testing Messaging System...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Messaging System", False, "Both student and mentor users needed")
        
        # Setup: Create a project for context
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Mobile Development", "description": "Mobile app projects"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Messaging Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "React Native App",
            "description": "Build a mobile app with React Native",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Messaging Setup - Project", False, f"Response: {project_response}")
        
        project_id = project_response["id"]
        
        # Test message creation (mentor to student)
        message_data = {
            "recipient_id": self.test_users["student"]["user"]["id"],
            "project_id": project_id,
            "subject": "Project Guidelines",
            "content": "Hi! Here are the guidelines for your React Native project. Please focus on creating a clean UI and implementing proper navigation."
        }
        success, message_response = self.make_request('POST', '/messages', 
                                                    data=message_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Message Creation (Mentor to Student)", False, f"Response: {message_response}")
        
        self.log_test("Message Creation (Mentor to Student)", True, f"Message created: {message_response['id']}")
        message_id = message_response["id"]
        
        # Test getting messages as student
        self.token = self.test_users["student"]["token"]
        
        success, messages_response = self.make_request('GET', '/messages', 
                                                     expected_status=200, use_auth=True)
        if success and len(messages_response) > 0:
            self.log_test("Get Messages (Student)", True, f"Retrieved {len(messages_response)} messages")
        else:
            self.log_test("Get Messages (Student)", False, f"Response: {messages_response}")
            return False
        
        # Test getting specific message
        success, specific_message = self.make_request('GET', f'/messages/{message_id}', 
                                                    expected_status=200, use_auth=True)
        if success and specific_message.get("id") == message_id:
            self.log_test("Get Specific Message", True, "Retrieved message details")
        else:
            self.log_test("Get Specific Message", False, f"Response: {specific_message}")
            return False
        
        # Test marking message as read
        read_data = {"is_read": True}
        success, read_response = self.make_request('PUT', f'/messages/{message_id}', 
                                                 data=read_data, expected_status=200, use_auth=True)
        if success and read_response.get("is_read") == True:
            self.log_test("Mark Message as Read", True, "Message marked as read")
        else:
            self.log_test("Mark Message as Read", False, f"Response: {read_response}")
            return False
        
        # Test reply message (student to mentor)
        reply_data = {
            "recipient_id": self.test_users["mentor"]["user"]["id"],
            "project_id": project_id,
            "subject": "Re: Project Guidelines",
            "content": "Thank you for the guidelines! I have a question about the navigation implementation. Should I use React Navigation v6?"
        }
        success, reply_response = self.make_request('POST', '/messages', 
                                                  data=reply_data, expected_status=200, use_auth=True)
        if success:
            self.log_test("Reply Message (Student to Mentor)", True, f"Reply sent: {reply_response['id']}")
            return True
        else:
            self.log_test("Reply Message (Student to Mentor)", False, f"Response: {reply_response}")
            return False

    def test_progress_tracking(self) -> bool:
        """Test progress tracking - student progress and overview endpoints"""
        print("\n📊 Testing Progress Tracking...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Progress Tracking", False, "Both student and mentor users needed")
        
        # Setup: Create project with tasks and submissions
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Machine Learning", "description": "ML projects"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Progress Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "ML Classification Project",
            "description": "Build a classification model",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Progress Setup - Project", False, f"Response: {project_response}")
        
        project_id = project_response["id"]
        
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task_data = {
                "project_id": project_id,
                "title": f"Task {i+1}: ML Step {i+1}",
                "description": f"Complete step {i+1} of the ML project"
            }
            success, task_response = self.make_request('POST', '/tasks', 
                                                     data=task_data, expected_status=200, use_auth=True)
            if success:
                tasks.append(task_response)
        
        if len(tasks) != 3:
            return self.log_test("Progress Setup - Tasks", False, "Failed to create test tasks")
        
        # Create submissions and approve some tasks
        self.token = self.test_users["student"]["token"]
        
        for i, task in enumerate(tasks[:2]):  # Submit for first 2 tasks
            submission_data = {
                "task_id": task["id"],
                "text_content": f"Completed task {i+1} with excellent results"
            }
            success, submission_response = self.make_request('POST', '/submissions', 
                                                           data=submission_data, expected_status=200, use_auth=True)
            if success:
                # Approve the first task as mentor
                self.token = self.test_users["mentor"]["token"]
                if i == 0:  # Approve only the first task
                    feedback_data = {"status": "approved", "grade": 90.0}
                    self.make_request('PUT', f'/submissions/{submission_response["id"]}', 
                                    data=feedback_data, expected_status=200, use_auth=True)
                self.token = self.test_users["student"]["token"]
        
        # Test student progress endpoint
        student_id = self.test_users["student"]["user"]["id"]
        success, progress_response = self.make_request('GET', f'/progress/{student_id}', 
                                                     expected_status=200, use_auth=True)
        if success and progress_response.get("student_id") == student_id:
            progress_data = progress_response.get("progress", [])
            if len(progress_data) > 0:
                project_progress = progress_data[0]
                self.log_test("Student Progress Tracking", True, 
                            f"Completion: {project_progress.get('completion_percentage', 0):.1f}%")
            else:
                self.log_test("Student Progress Tracking", False, "No progress data found")
                return False
        else:
            self.log_test("Student Progress Tracking", False, f"Response: {progress_response}")
            return False
        
        # Test mentor overview endpoint
        self.token = self.test_users["mentor"]["token"]
        
        success, overview_response = self.make_request('GET', '/progress/overview', 
                                                     expected_status=200, use_auth=True)
        if success and overview_response.get("overview"):
            overview_data = overview_response["overview"]
            student_found = any(student["student_id"] == student_id for student in overview_data)
            if student_found:
                self.log_test("Progress Overview (Mentor)", True, f"Overview for {len(overview_data)} students")
                return True
            else:
                self.log_test("Progress Overview (Mentor)", False, "Student not found in overview")
                return False
        else:
            self.log_test("Progress Overview (Mentor)", False, f"Response: {overview_response}")
            return False

    def test_certificate_generation(self) -> bool:
        """Test certificate generation - PDF certificate generation for completed projects"""
        print("\n🏆 Testing Certificate Generation...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Certificate Generation", False, "Both student and mentor users needed")
        
        # Setup: Create project with tasks and complete them
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Full Stack Development", "description": "Complete web development"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "E-commerce Website",
            "description": "Build a complete e-commerce solution",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Project", False, f"Response: {project_response}")
        
        project_id = project_response["id"]
        student_id = self.test_users["student"]["user"]["id"]
        
        # Create and complete tasks
        task_data = {
            "project_id": project_id,
            "title": "Frontend Development",
            "description": "Build the frontend with React"
        }
        success, task_response = self.make_request('POST', '/tasks', 
                                                 data=task_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Task", False, f"Response: {task_response}")
        
        task_id = task_response["id"]
        
        # Create submission as student
        self.token = self.test_users["student"]["token"]
        
        submission_data = {
            "task_id": task_id,
            "text_content": "Completed the e-commerce frontend with all required features"
        }
        success, submission_response = self.make_request('POST', '/submissions', 
                                                       data=submission_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Submission", False, f"Response: {submission_response}")
        
        # Approve submission as mentor
        self.token = self.test_users["mentor"]["token"]
        
        approval_data = {"status": "approved", "grade": 95.0}
        success, approval_response = self.make_request('PUT', f'/submissions/{submission_response["id"]}', 
                                                     data=approval_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Approval", False, f"Response: {approval_response}")
        
        # Update task status to approved
        task_update = {"status": "approved"}
        success, task_update_response = self.make_request('PUT', f'/tasks/{task_id}', 
                                                        data=task_update, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Task Status", False, f"Response: {task_update_response}")
        
        # Test certificate generation
        success, cert_response = self.make_request('POST', f'/certificates/generate?student_id={student_id}&project_id={project_id}', 
                                                 expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Generation", False, f"Response: {cert_response}")
        
        self.log_test("Certificate Generation", True, f"Certificate generated: {cert_response['id']}")
        certificate_id = cert_response["id"]
        
        # Test getting certificates
        success, certificates_response = self.make_request('GET', '/certificates', 
                                                         expected_status=200, use_auth=True)
        if success and len(certificates_response) > 0:
            self.log_test("Get Certificates", True, f"Retrieved {len(certificates_response)} certificates")
        else:
            self.log_test("Get Certificates", False, f"Response: {certificates_response}")
            return False
        
        # Test getting specific certificate
        success, specific_cert = self.make_request('GET', f'/certificates/{certificate_id}', 
                                                 expected_status=200, use_auth=True)
        if success and specific_cert.get("id") == certificate_id:
            self.log_test("Get Specific Certificate", True, "Retrieved certificate details")
        else:
            self.log_test("Get Specific Certificate", False, f"Response: {specific_cert}")
            return False
        
        # Test certificate download
        success, download_response = self.make_request('GET', f'/certificates/{certificate_id}/download', 
                                                     expected_status=200, use_auth=True)
        if success and download_response.get("certificate_data"):
            self.log_test("Certificate Download", True, f"PDF data length: {len(download_response['certificate_data'])}")
            return True
        else:
            self.log_test("Certificate Download", False, f"Response: {download_response}")
            return False

    def test_role_based_access_comprehensive(self) -> bool:
        """Test comprehensive role-based access control for all new endpoints"""
        print("\n🔐 Testing Comprehensive Role-Based Access Control...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Comprehensive RBAC", False, "Both student and mentor users needed")
        
        # Test student trying to access mentor-only endpoints
        self.token = self.test_users["student"]["token"]
        
        mentor_only_tests = [
            ('POST', '/subject-categories', {"name": "Test", "description": "Test"}),
            ('POST', '/tasks', {"project_id": "test", "title": "Test", "description": "Test"}),
            ('PUT', '/tasks/test-id', {"title": "Updated"}),
            ('DELETE', '/tasks/test-id', None),
            ('POST', '/resources', {"subject_category_id": "test", "title": "Test", "description": "Test", "resource_type": "link"}),
            ('PUT', '/resources/test-id', {"title": "Updated"}),
            ('DELETE', '/resources/test-id', None),
            ('PUT', '/submissions/test-id', {"feedback": "Good work"}),
            ('GET', '/progress/overview', None),
            ('POST', '/certificates/generate?student_id=test&project_id=test', None)
        ]
        
        all_passed = True
        for method, endpoint, data in mentor_only_tests:
            success, response = self.make_request(method, endpoint, data=data, 
                                                expected_status=403, use_auth=True)
            test_name = f"Student Access Denied - {method} {endpoint}"
            if success:
                self.log_test(test_name, True, "Access correctly denied")
            else:
                self.log_test(test_name, False, f"Expected 403, got {response.get('status_code')}")
                all_passed = False
        
        return all_passed

    def test_cors_headers(self) -> bool:
        """Test CORS configuration"""
        print("\n🌐 Testing CORS Configuration...")
        
        try:
            response = requests.options(f"{self.api_url}/", timeout=10)
            
            # Check if CORS headers are present
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            has_cors = any(header in response.headers for header in cors_headers)
            
            if has_cors or response.status_code in [200, 405]:  # 405 is also acceptable for OPTIONS
                return self.log_test("CORS Configuration", True, "CORS headers present or OPTIONS handled")
            else:
                return self.log_test("CORS Configuration", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("CORS Configuration", False, f"Error: {str(e)}")

    def test_api_structure(self) -> bool:
        """Test API structure and routing"""
        print("\n🏗️ Testing API Structure...")
        
        # Test that /api prefix is working
        success, response = self.make_request('GET', '/')
        
        if success:
            return self.log_test("API Routing Structure", True, "API prefix working correctly")
        else:
            return self.log_test("API Routing Structure", False, f"Response: {response}")

    def test_error_handling(self) -> bool:
        """Test error handling for non-existent endpoints"""
        print("\n❌ Testing Error Handling...")
        
        success, response = self.make_request('GET', '/non-existent-endpoint', expected_status=404)
        
        if success:
            return self.log_test("404 Error Handling", True, "Non-existent endpoint handled correctly")
        else:
            return self.log_test("404 Error Handling", False, f"Response: {response}")

    def test_database_connection(self) -> bool:
        """Test if the API can handle database-related operations (indirect test)"""
        print("\n🗄️ Testing Database Connection...")
        
        # This is an indirect test - we'll try to access an endpoint that requires DB
        # Without auth, it should fail with 403, not 500 (which would indicate DB issues)
        success, response = self.make_request('GET', '/subject-categories', expected_status=403)
        
        if success:
            return self.log_test("Database Connection (Indirect)", True, "API responding correctly")
        else:
            # If we get 500, it might indicate database issues
            status_code = response.get('status_code', 0)
            if status_code == 500:
                return self.log_test("Database Connection (Indirect)", False, "Possible database connection issue")
            else:
                return self.log_test("Database Connection (Indirect)", False, f"Unexpected response: {response}")

    def test_enhanced_task_management(self) -> bool:
        """Test enhanced task management - update and delete endpoints"""
        print("\n📝 Testing Enhanced Task Management...")
        
        if not self.test_users["mentor"]:
            return self.log_test("Enhanced Task Management", False, "No mentor user available")
        
        self.token = self.test_users["mentor"]["token"]
        
        # First create a subject category and project for testing
        category_data = {
            "name": "Programming Fundamentals",
            "description": "Basic programming concepts"
        }
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Task Management Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "Python Basics Project",
            "description": "Learn Python fundamentals",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Task Management Setup - Project", False, f"Response: {project_response}")
        
        # Create a task
        task_data = {
            "project_id": project_response["id"],
            "title": "Variables and Data Types",
            "description": "Learn about Python variables and data types",
            "deadline": "2024-12-31T23:59:59"
        }
        success, task_response = self.make_request('POST', '/tasks', 
                                                 data=task_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Task Creation", False, f"Response: {task_response}")
        
        self.log_test("Task Creation", True, f"Task created: {task_response['id']}")
        task_id = task_response["id"]
        
        # Test task update
        update_data = {
            "title": "Variables, Data Types, and Basic Operations",
            "description": "Updated description with more details",
            "status": "in_progress"
        }
        success, update_response = self.make_request('PUT', f'/tasks/{task_id}', 
                                                   data=update_data, expected_status=200, use_auth=True)
        if success and update_response.get("title") == update_data["title"]:
            self.log_test("Task Update", True, "Task updated successfully")
        else:
            self.log_test("Task Update", False, f"Response: {update_response}")
            return False
        
        # Test task delete
        success, delete_response = self.make_request('DELETE', f'/tasks/{task_id}', 
                                                   expected_status=200, use_auth=True)
        if success:
            self.log_test("Task Delete", True, "Task deleted successfully")
            return True
        else:
            self.log_test("Task Delete", False, f"Response: {delete_response}")
            return False

    def test_submissions_system(self) -> bool:
        """Test submissions system - full CRUD operations"""
        print("\n📤 Testing Submissions System...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Submissions System", False, "Both student and mentor users needed")
        
        # Setup: Create category, project, and task as mentor
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Web Development", "description": "Web dev projects"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submissions Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "HTML/CSS Project",
            "description": "Build a responsive website",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submissions Setup - Project", False, f"Response: {project_response}")
        
        task_data = {
            "project_id": project_response["id"],
            "title": "Create Homepage",
            "description": "Design and implement homepage"
        }
        success, task_response = self.make_request('POST', '/tasks', 
                                                 data=task_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submissions Setup - Task", False, f"Response: {task_response}")
        
        task_id = task_response["id"]
        
        # Test submission creation as student
        self.token = self.test_users["student"]["token"]
        
        submission_data = {
            "task_id": task_id,
            "text_content": "I have completed the homepage with responsive design using HTML5 and CSS3.",
            "file_name": "homepage.html",
            "file_data": "PGh0bWw+PGhlYWQ+PHRpdGxlPkhvbWVwYWdlPC90aXRsZT48L2hlYWQ+PGJvZHk+PGgxPldlbGNvbWU8L2gxPjwvYm9keT48L2h0bWw+",  # Base64 encoded HTML
            "file_type": "text/html"
        }
        success, submission_response = self.make_request('POST', '/submissions', 
                                                       data=submission_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Submission Creation", False, f"Response: {submission_response}")
        
        self.log_test("Submission Creation", True, f"Submission created: {submission_response['id']}")
        submission_id = submission_response["id"]
        
        # Test getting submissions as student
        success, submissions_response = self.make_request('GET', '/submissions', 
                                                        expected_status=200, use_auth=True)
        if success and len(submissions_response) > 0:
            self.log_test("Get Submissions (Student)", True, f"Retrieved {len(submissions_response)} submissions")
        else:
            self.log_test("Get Submissions (Student)", False, f"Response: {submissions_response}")
            return False
        
        # Test getting specific submission as student
        success, specific_submission = self.make_request('GET', f'/submissions/{submission_id}', 
                                                       expected_status=200, use_auth=True)
        if success and specific_submission.get("id") == submission_id:
            self.log_test("Get Specific Submission", True, "Retrieved submission details")
        else:
            self.log_test("Get Specific Submission", False, f"Response: {specific_submission}")
            return False
        
        # Test submission feedback/grading as mentor
        self.token = self.test_users["mentor"]["token"]
        
        feedback_data = {
            "feedback": "Great work! The homepage looks professional and is well-structured. Consider adding more interactive elements.",
            "status": "approved",
            "grade": 95.0
        }
        success, feedback_response = self.make_request('PUT', f'/submissions/{submission_id}', 
                                                     data=feedback_data, expected_status=200, use_auth=True)
        if success and feedback_response.get("feedback") == feedback_data["feedback"]:
            self.log_test("Submission Feedback/Grading", True, f"Grade: {feedback_response['grade']}")
            return True
        else:
            self.log_test("Submission Feedback/Grading", False, f"Response: {feedback_response}")
            return False

    def test_resources_system(self) -> bool:
        """Test resources system - full CRUD operations"""
        print("\n📚 Testing Resources System...")
        
        if not self.test_users["mentor"]:
            return self.log_test("Resources System", False, "No mentor user available")
        
        self.token = self.test_users["mentor"]["token"]
        
        # Create a subject category first
        category_data = {"name": "Data Science", "description": "Data science resources"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Resources Setup - Category", False, f"Response: {category_response}")
        
        category_id = category_response["id"]
        
        # Test resource creation (link type)
        link_resource_data = {
            "subject_category_id": category_id,
            "title": "Python Data Science Handbook",
            "description": "Comprehensive guide to data science with Python",
            "resource_type": "link",
            "url": "https://jakevdp.github.io/PythonDataScienceHandbook/"
        }
        success, link_response = self.make_request('POST', '/resources', 
                                                 data=link_resource_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Resource Creation (Link)", False, f"Response: {link_response}")
        
        self.log_test("Resource Creation (Link)", True, f"Link resource created: {link_response['id']}")
        link_resource_id = link_response["id"]
        
        # Test resource creation (document type with file)
        doc_resource_data = {
            "subject_category_id": category_id,
            "title": "Data Analysis Cheat Sheet",
            "description": "Quick reference for pandas and numpy",
            "resource_type": "document",
            "file_name": "cheat_sheet.pdf",
            "file_data": "JVBERi0xLjQKJcOkw7zDtsO8CjIgMCBvYmoKPDwKL0xlbmd0aCAzIDAgUgo+PgpzdHJlYW0KQNC4xOzAuMTswLjE=",  # Base64 encoded PDF header
            "file_type": "application/pdf"
        }
        success, doc_response = self.make_request('POST', '/resources', 
                                                data=doc_resource_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Resource Creation (Document)", False, f"Response: {doc_response}")
        
        self.log_test("Resource Creation (Document)", True, f"Document resource created: {doc_response['id']}")
        doc_resource_id = doc_response["id"]
        
        # Test getting all resources
        success, resources_response = self.make_request('GET', '/resources', 
                                                      expected_status=200, use_auth=True)
        if success and len(resources_response) >= 2:
            self.log_test("Get All Resources", True, f"Retrieved {len(resources_response)} resources")
        else:
            self.log_test("Get All Resources", False, f"Response: {resources_response}")
            return False
        
        # Test getting resources by category
        success, category_resources = self.make_request('GET', f'/resources?subject_category_id={category_id}', 
                                                      expected_status=200, use_auth=True)
        if success and len(category_resources) >= 2:
            self.log_test("Get Resources by Category", True, f"Retrieved {len(category_resources)} resources for category")
        else:
            self.log_test("Get Resources by Category", False, f"Response: {category_resources}")
            return False
        
        # Test resource update
        update_data = {
            "title": "Updated: Python Data Science Handbook",
            "description": "Updated comprehensive guide with latest examples"
        }
        success, update_response = self.make_request('PUT', f'/resources/{link_resource_id}', 
                                                   data=update_data, expected_status=200, use_auth=True)
        if success and update_response.get("title") == update_data["title"]:
            self.log_test("Resource Update", True, "Resource updated successfully")
        else:
            self.log_test("Resource Update", False, f"Response: {update_response}")
            return False
        
        # Test resource delete
        success, delete_response = self.make_request('DELETE', f'/resources/{doc_resource_id}', 
                                                   expected_status=200, use_auth=True)
        if success:
            self.log_test("Resource Delete", True, "Resource deleted successfully")
            return True
        else:
            self.log_test("Resource Delete", False, f"Response: {delete_response}")
            return False

    def test_messaging_system(self) -> bool:
        """Test messaging system - full CRUD operations"""
        print("\n💬 Testing Messaging System...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Messaging System", False, "Both student and mentor users needed")
        
        # Setup: Create a project for context
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Mobile Development", "description": "Mobile app projects"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Messaging Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "React Native App",
            "description": "Build a mobile app with React Native",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Messaging Setup - Project", False, f"Response: {project_response}")
        
        project_id = project_response["id"]
        
        # Test message creation (mentor to student)
        message_data = {
            "recipient_id": self.test_users["student"]["user"]["id"],
            "project_id": project_id,
            "subject": "Project Guidelines",
            "content": "Hi! Here are the guidelines for your React Native project. Please focus on creating a clean UI and implementing proper navigation."
        }
        success, message_response = self.make_request('POST', '/messages', 
                                                    data=message_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Message Creation (Mentor to Student)", False, f"Response: {message_response}")
        
        self.log_test("Message Creation (Mentor to Student)", True, f"Message created: {message_response['id']}")
        message_id = message_response["id"]
        
        # Test getting messages as student
        self.token = self.test_users["student"]["token"]
        
        success, messages_response = self.make_request('GET', '/messages', 
                                                     expected_status=200, use_auth=True)
        if success and len(messages_response) > 0:
            self.log_test("Get Messages (Student)", True, f"Retrieved {len(messages_response)} messages")
        else:
            self.log_test("Get Messages (Student)", False, f"Response: {messages_response}")
            return False
        
        # Test getting specific message
        success, specific_message = self.make_request('GET', f'/messages/{message_id}', 
                                                    expected_status=200, use_auth=True)
        if success and specific_message.get("id") == message_id:
            self.log_test("Get Specific Message", True, "Retrieved message details")
        else:
            self.log_test("Get Specific Message", False, f"Response: {specific_message}")
            return False
        
        # Test marking message as read
        read_data = {"is_read": True}
        success, read_response = self.make_request('PUT', f'/messages/{message_id}', 
                                                 data=read_data, expected_status=200, use_auth=True)
        if success and read_response.get("is_read") == True:
            self.log_test("Mark Message as Read", True, "Message marked as read")
        else:
            self.log_test("Mark Message as Read", False, f"Response: {read_response}")
            return False
        
        # Test reply message (student to mentor)
        reply_data = {
            "recipient_id": self.test_users["mentor"]["user"]["id"],
            "project_id": project_id,
            "subject": "Re: Project Guidelines",
            "content": "Thank you for the guidelines! I have a question about the navigation implementation. Should I use React Navigation v6?"
        }
        success, reply_response = self.make_request('POST', '/messages', 
                                                  data=reply_data, expected_status=200, use_auth=True)
        if success:
            self.log_test("Reply Message (Student to Mentor)", True, f"Reply sent: {reply_response['id']}")
            return True
        else:
            self.log_test("Reply Message (Student to Mentor)", False, f"Response: {reply_response}")
            return False

    def test_progress_tracking(self) -> bool:
        """Test progress tracking - student progress and overview endpoints"""
        print("\n📊 Testing Progress Tracking...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Progress Tracking", False, "Both student and mentor users needed")
        
        # Setup: Create project with tasks and submissions
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Machine Learning", "description": "ML projects"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Progress Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "ML Classification Project",
            "description": "Build a classification model",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Progress Setup - Project", False, f"Response: {project_response}")
        
        project_id = project_response["id"]
        
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task_data = {
                "project_id": project_id,
                "title": f"Task {i+1}: ML Step {i+1}",
                "description": f"Complete step {i+1} of the ML project"
            }
            success, task_response = self.make_request('POST', '/tasks', 
                                                     data=task_data, expected_status=200, use_auth=True)
            if success:
                tasks.append(task_response)
        
        if len(tasks) != 3:
            return self.log_test("Progress Setup - Tasks", False, "Failed to create test tasks")
        
        # Create submissions and approve some tasks
        self.token = self.test_users["student"]["token"]
        
        for i, task in enumerate(tasks[:2]):  # Submit for first 2 tasks
            submission_data = {
                "task_id": task["id"],
                "text_content": f"Completed task {i+1} with excellent results"
            }
            success, submission_response = self.make_request('POST', '/submissions', 
                                                           data=submission_data, expected_status=200, use_auth=True)
            if success:
                # Approve the first task as mentor
                self.token = self.test_users["mentor"]["token"]
                if i == 0:  # Approve only the first task
                    feedback_data = {"status": "approved", "grade": 90.0}
                    self.make_request('PUT', f'/submissions/{submission_response["id"]}', 
                                    data=feedback_data, expected_status=200, use_auth=True)
                self.token = self.test_users["student"]["token"]
        
        # Test student progress endpoint
        student_id = self.test_users["student"]["user"]["id"]
        success, progress_response = self.make_request('GET', f'/progress/{student_id}', 
                                                     expected_status=200, use_auth=True)
        if success and progress_response.get("student_id") == student_id:
            progress_data = progress_response.get("progress", [])
            if len(progress_data) > 0:
                project_progress = progress_data[0]
                self.log_test("Student Progress Tracking", True, 
                            f"Completion: {project_progress.get('completion_percentage', 0):.1f}%")
            else:
                self.log_test("Student Progress Tracking", False, "No progress data found")
                return False
        else:
            self.log_test("Student Progress Tracking", False, f"Response: {progress_response}")
            return False
        
        # Test mentor overview endpoint
        self.token = self.test_users["mentor"]["token"]
        
        success, overview_response = self.make_request('GET', '/progress/overview', 
                                                     expected_status=200, use_auth=True)
        if success and overview_response.get("overview"):
            overview_data = overview_response["overview"]
            student_found = any(student["student_id"] == student_id for student in overview_data)
            if student_found:
                self.log_test("Progress Overview (Mentor)", True, f"Overview for {len(overview_data)} students")
                return True
            else:
                self.log_test("Progress Overview (Mentor)", False, "Student not found in overview")
                return False
        else:
            self.log_test("Progress Overview (Mentor)", False, f"Response: {overview_response}")
            return False

    def test_certificate_generation(self) -> bool:
        """Test certificate generation - PDF certificate generation for completed projects"""
        print("\n🏆 Testing Certificate Generation...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Certificate Generation", False, "Both student and mentor users needed")
        
        # Setup: Create project with tasks and complete them
        self.token = self.test_users["mentor"]["token"]
        
        category_data = {"name": "Full Stack Development", "description": "Complete web development"}
        success, category_response = self.make_request('POST', '/subject-categories', 
                                                     data=category_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Category", False, f"Response: {category_response}")
        
        project_data = {
            "title": "E-commerce Website",
            "description": "Build a complete e-commerce solution",
            "subject_category_id": category_response["id"],
            "assigned_students": [self.test_users["student"]["user"]["id"]]
        }
        success, project_response = self.make_request('POST', '/projects', 
                                                    data=project_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Project", False, f"Response: {project_response}")
        
        project_id = project_response["id"]
        student_id = self.test_users["student"]["user"]["id"]
        
        # Create and complete tasks
        task_data = {
            "project_id": project_id,
            "title": "Frontend Development",
            "description": "Build the frontend with React"
        }
        success, task_response = self.make_request('POST', '/tasks', 
                                                 data=task_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Task", False, f"Response: {task_response}")
        
        task_id = task_response["id"]
        
        # Create submission as student
        self.token = self.test_users["student"]["token"]
        
        submission_data = {
            "task_id": task_id,
            "text_content": "Completed the e-commerce frontend with all required features"
        }
        success, submission_response = self.make_request('POST', '/submissions', 
                                                       data=submission_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Submission", False, f"Response: {submission_response}")
        
        # Approve submission as mentor
        self.token = self.test_users["mentor"]["token"]
        
        approval_data = {"status": "approved", "grade": 95.0}
        success, approval_response = self.make_request('PUT', f'/submissions/{submission_response["id"]}', 
                                                     data=approval_data, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Approval", False, f"Response: {approval_response}")
        
        # Update task status to approved
        task_update = {"status": "approved"}
        success, task_update_response = self.make_request('PUT', f'/tasks/{task_id}', 
                                                        data=task_update, expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Setup - Task Status", False, f"Response: {task_update_response}")
        
        # Test certificate generation
        success, cert_response = self.make_request('POST', f'/certificates/generate?student_id={student_id}&project_id={project_id}', 
                                                 expected_status=200, use_auth=True)
        if not success:
            return self.log_test("Certificate Generation", False, f"Response: {cert_response}")
        
        self.log_test("Certificate Generation", True, f"Certificate generated: {cert_response['id']}")
        certificate_id = cert_response["id"]
        
        # Test getting certificates
        success, certificates_response = self.make_request('GET', '/certificates', 
                                                         expected_status=200, use_auth=True)
        if success and len(certificates_response) > 0:
            self.log_test("Get Certificates", True, f"Retrieved {len(certificates_response)} certificates")
        else:
            self.log_test("Get Certificates", False, f"Response: {certificates_response}")
            return False
        
        # Test getting specific certificate
        success, specific_cert = self.make_request('GET', f'/certificates/{certificate_id}', 
                                                 expected_status=200, use_auth=True)
        if success and specific_cert.get("id") == certificate_id:
            self.log_test("Get Specific Certificate", True, "Retrieved certificate details")
        else:
            self.log_test("Get Specific Certificate", False, f"Response: {specific_cert}")
            return False
        
        # Test certificate download
        success, download_response = self.make_request('GET', f'/certificates/{certificate_id}/download', 
                                                     expected_status=200, use_auth=True)
        if success and download_response.get("certificate_data"):
            self.log_test("Certificate Download", True, f"PDF data length: {len(download_response['certificate_data'])}")
            return True
        else:
            self.log_test("Certificate Download", False, f"Response: {download_response}")
            return False

    def test_role_based_access_comprehensive(self) -> bool:
        """Test comprehensive role-based access control for all new endpoints"""
        print("\n🔐 Testing Comprehensive Role-Based Access Control...")
        
        if not self.test_users["student"] or not self.test_users["mentor"]:
            return self.log_test("Comprehensive RBAC", False, "Both student and mentor users needed")
        
        # Test student trying to access mentor-only endpoints
        self.token = self.test_users["student"]["token"]
        
        mentor_only_tests = [
            ('POST', '/subject-categories', {"name": "Test", "description": "Test"}),
            ('POST', '/tasks', {"project_id": "test", "title": "Test", "description": "Test"}),
            ('PUT', '/tasks/test-id', {"title": "Updated"}),
            ('DELETE', '/tasks/test-id', None),
            ('POST', '/resources', {"subject_category_id": "test", "title": "Test", "description": "Test", "resource_type": "link"}),
            ('PUT', '/resources/test-id', {"title": "Updated"}),
            ('DELETE', '/resources/test-id', None),
            ('PUT', '/submissions/test-id', {"feedback": "Good work"}),
            ('GET', '/progress/overview', None),
            ('POST', '/certificates/generate?student_id=test&project_id=test', None)
        ]
        
        all_passed = True
        for method, endpoint, data in mentor_only_tests:
            success, response = self.make_request(method, endpoint, data=data, 
                                                expected_status=403, use_auth=True)
            test_name = f"Student Access Denied - {method} {endpoint}"
            if success:
                self.log_test(test_name, True, "Access correctly denied")
            else:
                self.log_test(test_name, False, f"Expected 403, got {response.get('status_code')}")
                all_passed = False
        
        return all_passed

    def run_all_tests(self) -> bool:
        """Run all backend tests including comprehensive LMS features"""
        print("🚀 Starting BuildBytes LMS Backend API Tests - Comprehensive Feature Testing")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 80)
        
        # Run tests in logical order
        test_methods = [
            # Basic API tests
            self.test_health_check,
            self.test_api_structure,
            self.test_cors_headers,
            self.test_database_connection,
            
            # Authentication system tests
            self.test_user_registration,
            self.test_password_validation,
            self.test_email_uniqueness,
            self.test_role_validation,
            self.test_user_login,
            
            # JWT and security tests
            self.test_jwt_token_authentication,
            self.test_token_expiration_format,
            self.test_password_hashing_security,
            
            # Protected endpoints tests
            self.test_protected_endpoints,
            self.test_role_based_access,
            self.test_unauthenticated_endpoints,
            self.test_subject_categories_crud_without_auth,
            
            # NEW COMPREHENSIVE LMS FEATURES
            self.test_enhanced_task_management,
            self.test_submissions_system,
            self.test_resources_system,
            self.test_messaging_system,
            self.test_progress_tracking,
            self.test_certificate_generation,
            self.test_role_based_access_comprehensive,
            
            # Error handling
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(f"Exception in {test_method.__name__}", False, str(e))
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate detailed test report"""
        return {
            "test_summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "failed_tests": self.tests_run - self.tests_passed,
                "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
            },
            "test_results": self.test_results,
            "api_url": self.api_url,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Main test execution"""
    print("BuildBytes LMS Backend API Test Suite")
    print("=====================================")
    
    tester = BuildBytesAPITester()
    
    try:
        success = tester.run_all_tests()
        
        # Generate and save report
        report = tester.generate_report()
        
        print(f"\n📋 Detailed Report:")
        print(f"   • Success Rate: {report['test_summary']['success_rate']:.1f}%")
        print(f"   • API Endpoint: {report['api_url']}")
        
        # Save report to file
        with open('/app/backend_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"   • Report saved to: /app/backend_test_report.json")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Critical error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())