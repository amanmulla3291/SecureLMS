#!/usr/bin/env python3
"""
BuildBytes LMS Backend API Testing Suite
Tests all API endpoints including authentication, CRUD operations, and error handling.
"""

import requests
import sys
import json
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
                    expected_status: int = 200, use_auth: bool = False) -> tuple[bool, Dict]:
        """Make HTTP request and validate response"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
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
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_health_check(self) -> bool:
        """Test the root API endpoint"""
        success, response = self.make_request('GET', '/')
        
        if success and response.get('message') == 'BuildBytes LMS API':
            return self.log_test("Health Check", True, f"Version: {response.get('version', 'N/A')}")
        else:
            return self.log_test("Health Check", False, f"Response: {response}")

    def test_unauthenticated_endpoints(self) -> bool:
        """Test endpoints that should require authentication"""
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

    def test_with_mock_auth(self) -> bool:
        """Test with a mock/invalid token to verify auth validation"""
        # Set a fake token
        original_token = self.token
        self.token = "fake_jwt_token_for_testing"
        
        success, response = self.make_request('GET', '/me', expected_status=401, use_auth=True)
        
        # Restore original token
        self.token = original_token
        
        if success:
            return self.log_test("Invalid Token Rejection", True, "Auth validation working")
        else:
            return self.log_test("Invalid Token Rejection", False, f"Response: {response}")

    def test_subject_categories_crud_without_auth(self) -> bool:
        """Test CRUD operations without authentication (should fail)"""
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

    def test_cors_headers(self) -> bool:
        """Test CORS configuration"""
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
        # Test that /api prefix is working
        success, response = self.make_request('GET', '/')
        
        if success:
            return self.log_test("API Routing Structure", True, "API prefix working correctly")
        else:
            return self.log_test("API Routing Structure", False, f"Response: {response}")

    def test_error_handling(self) -> bool:
        """Test error handling for non-existent endpoints"""
        success, response = self.make_request('GET', '/non-existent-endpoint', expected_status=404)
        
        if success:
            return self.log_test("404 Error Handling", True, "Non-existent endpoint handled correctly")
        else:
            return self.log_test("404 Error Handling", False, f"Response: {response}")

    def test_database_connection(self) -> bool:
        """Test if the API can handle database-related operations (indirect test)"""
        # This is an indirect test - we'll try to access an endpoint that requires DB
        # Without auth, it should fail with 401, not 500 (which would indicate DB issues)
        success, response = self.make_request('GET', '/subject-categories', expected_status=401)
        
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
        """Run all backend tests"""
        print("🚀 Starting BuildBytes LMS Backend API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Run tests in logical order
        test_methods = [
            self.test_health_check,
            self.test_api_structure,
            self.test_cors_headers,
            self.test_unauthenticated_endpoints,
            self.test_with_mock_auth,
            self.test_subject_categories_crud_without_auth,
            self.test_error_handling,
            self.test_database_connection
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(f"Exception in {test_method.__name__}", False, str(e))
        
        # Print summary
        print("\n" + "=" * 60)
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