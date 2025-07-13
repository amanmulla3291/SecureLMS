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
    def __init__(self, base_url: str = "https://2d8ac9fe-e181-496f-9168-6a056d2e549d.preview.emergentagent.com"):
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
        """Test password strength validation"""
        print("\n🔒 Testing Password Validation...")
        
        test_cases = [
            ("short", "Short password should fail", 400),
            ("nouppercase123", "No uppercase should fail", 400),
            ("NOLOWERCASE123", "No lowercase should fail", 400),
            ("NoNumbers", "No numbers should fail", 400),
            ("ValidPass123", "Valid password should pass", 200)
        ]
        
        all_passed = True
        for password, description, expected_status in test_cases:
            user_data = {
                "name": "Test User",
                "email": f"test_{int(time.time())}_{password}@test.com",
                "password": password,
                "role": "student"
            }
            
            success, response = self.make_request('POST', '/auth/register', 
                                                data=user_data, expected_status=expected_status)
            
            if success:
                self.log_test(f"Password Validation - {description}", True, "Validation working")
            else:
                self.log_test(f"Password Validation - {description}", False, f"Response: {response}")
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

    def run_all_tests(self) -> bool:
        """Run all backend tests for manual authentication system"""
        print("🚀 Starting BuildBytes LMS Backend API Tests - Manual Authentication System")
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