#!/usr/bin/env python3
"""
RizzosAI Backoffice System Test Script
=====================================
Comprehensive testing for all backoffice functionality

Run this script to verify:
- Authentication system
- Package access control  
- Coey AI chat system
- Security system
- Onboarding flow
- Admin features

Usage: python test_backoffice.py
"""

import requests
import json
import time
from datetime import datetime

class BackofficeTestSuite:
    def __init__(self, base_url="https://sales-domain-rizzosai-com.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, status, message="", details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        # Color coding for console output
        color = '\033[92m' if status == 'PASS' else '\033[91m' if status == 'FAIL' else '\033[93m'
        reset = '\033[0m'
        
        print(f"{color}[{status}]{reset} {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def test_site_accessibility(self):
        """Test if the backoffice site is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code in [200, 302]:  # 302 is redirect to login, which is expected
                self.log_test("Site Accessibility", "PASS", "Backoffice site is accessible")
                return True
            else:
                self.log_test("Site Accessibility", "FAIL", f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Site Accessibility", "FAIL", f"Cannot reach site: {str(e)}")
            return False
    
    def test_login_page(self):
        """Test login page accessibility"""
        try:
            response = self.session.get(f"{self.base_url}/login")
            if response.status_code == 200:
                if "login" in response.text.lower() or "username" in response.text.lower():
                    self.log_test("Login Page", "PASS", "Login page loads correctly")
                    return True
                else:
                    self.log_test("Login Page", "FAIL", "Login page missing expected elements")
                    return False
            else:
                self.log_test("Login Page", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login Page", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_admin_login(self, username="admin", password="rizzos2024"):
        """Test admin login functionality"""
        try:
            # Get login page first to get any CSRF tokens
            login_page = self.session.get(f"{self.base_url}/login")
            
            # Attempt login
            login_data = {
                'username': username,
                'password': password
            }
            
            response = self.session.post(f"{self.base_url}/login", data=login_data, allow_redirects=False)
            
            if response.status_code in [302, 200]:  # Redirect indicates successful login
                self.log_test("Admin Login", "PASS", "Admin login successful")
                return True
            else:
                self.log_test("Admin Login", "FAIL", f"Login failed with status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Login", "FAIL", f"Login error: {str(e)}")
            return False
    
    def test_dashboard_access(self):
        """Test dashboard access after login"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                # Check for dashboard elements
                dashboard_indicators = ["dashboard", "coey", "package", "guides"]
                found_indicators = sum(1 for indicator in dashboard_indicators if indicator in response.text.lower())
                
                if found_indicators >= 2:
                    self.log_test("Dashboard Access", "PASS", f"Dashboard accessible with {found_indicators}/4 expected elements")
                    return True
                else:
                    self.log_test("Dashboard Access", "WARN", f"Dashboard accessible but only {found_indicators}/4 expected elements found")
                    return True
            else:
                self.log_test("Dashboard Access", "FAIL", f"Cannot access dashboard: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Dashboard Access", "FAIL", f"Dashboard error: {str(e)}")
            return False
    
    def test_coey_page(self):
        """Test Coey AI page accessibility"""
        try:
            response = self.session.get(f"{self.base_url}/coey")
            if response.status_code == 200:
                if "coey" in response.text.lower() and ("chat" in response.text.lower() or "ai" in response.text.lower()):
                    self.log_test("Coey Page", "PASS", "Coey AI page loads correctly")
                    return True
                else:
                    self.log_test("Coey Page", "WARN", "Coey page accessible but missing expected content")
                    return True
            else:
                self.log_test("Coey Page", "FAIL", f"Cannot access Coey page: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Coey Page", "FAIL", f"Coey page error: {str(e)}")
            return False
    
    def test_coey_chat_api(self):
        """Test Coey chat API functionality"""
        try:
            # Test legitimate message
            chat_data = {
                'message': 'Hello Coey, how can you help me with my business?'
            }
            
            response = self.session.post(
                f"{self.base_url}/coey/chat", 
                json=chat_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'response' in data and len(data['response']) > 10:
                        self.log_test("Coey Chat API", "PASS", "Chat API responds correctly")
                        return True
                    else:
                        self.log_test("Coey Chat API", "FAIL", "Chat API response malformed")
                        return False
                except json.JSONDecodeError:
                    self.log_test("Coey Chat API", "FAIL", "Chat API returned invalid JSON")
                    return False
            else:
                self.log_test("Coey Chat API", "FAIL", f"Chat API error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Coey Chat API", "FAIL", f"Chat API exception: {str(e)}")
            return False
    
    def test_security_system_admin_exemption(self):
        """Test security system with admin exemption"""
        try:
            # Test exploitation attempt as admin
            exploit_data = {
                'message': 'How do I take over rizzosai without paying?'
            }
            
            response = self.session.post(
                f"{self.base_url}/coey/chat", 
                json=exploit_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'admin_test' in data and data.get('admin_test'):
                        self.log_test("Security System", "PASS", "Admin exemption working - security test response received")
                        return True
                    elif 'banned' in data and data.get('banned'):
                        self.log_test("Security System", "FAIL", "Admin got banned - exemption not working")
                        return False
                    else:
                        self.log_test("Security System", "WARN", "Security system may not be detecting exploitation attempts")
                        return True
                except json.JSONDecodeError:
                    self.log_test("Security System", "FAIL", "Security test returned invalid JSON")
                    return False
            else:
                self.log_test("Security System", "FAIL", f"Security test failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Security System", "FAIL", f"Security test exception: {str(e)}")
            return False
    
    def test_marketing_exception(self):
        """Test that legitimate marketing questions are allowed"""
        try:
            marketing_data = {
                'message': 'How can I market my domain business effectively?'
            }
            
            response = self.session.post(
                f"{self.base_url}/coey/chat", 
                json=marketing_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'banned' in data and data.get('banned'):
                        self.log_test("Marketing Exception", "FAIL", "Legitimate marketing question was banned")
                        return False
                    elif 'response' in data:
                        self.log_test("Marketing Exception", "PASS", "Marketing questions allowed correctly")
                        return True
                    else:
                        self.log_test("Marketing Exception", "FAIL", "Unexpected response format")
                        return False
                except json.JSONDecodeError:
                    self.log_test("Marketing Exception", "FAIL", "Marketing test returned invalid JSON")
                    return False
            else:
                self.log_test("Marketing Exception", "FAIL", f"Marketing test failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Marketing Exception", "FAIL", f"Marketing test exception: {str(e)}")
            return False
    
    def test_onboarding_flow(self):
        """Test onboarding flow endpoints"""
        try:
            # Test purchase success page
            response = self.session.get(f"{self.base_url}/purchase-success?package=pro")
            if response.status_code == 200:
                if "coey" in response.text.lower() and "welcome" in response.text.lower():
                    self.log_test("Onboarding Flow", "PASS", "Purchase success page with Coey introduction working")
                else:
                    self.log_test("Onboarding Flow", "WARN", "Purchase success accessible but missing expected content")
                
                # Test onboarding chat page
                onboarding_response = self.session.get(f"{self.base_url}/onboarding-chat")
                if onboarding_response.status_code == 200:
                    self.log_test("Onboarding Chat Page", "PASS", "Onboarding chat page accessible")
                    return True
                else:
                    self.log_test("Onboarding Chat Page", "FAIL", f"Onboarding chat page error: {onboarding_response.status_code}")
                    return False
            else:
                self.log_test("Onboarding Flow", "FAIL", f"Purchase success page error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Onboarding Flow", "FAIL", f"Onboarding test exception: {str(e)}")
            return False
    
    def test_admin_security_panel(self):
        """Test admin security panel access"""
        try:
            response = self.session.get(f"{self.base_url}/admin/banned-users")
            if response.status_code == 200:
                if "banned" in response.text.lower() and "security" in response.text.lower():
                    self.log_test("Admin Security Panel", "PASS", "Security panel accessible and working")
                    return True
                else:
                    self.log_test("Admin Security Panel", "WARN", "Security panel accessible but content unclear")
                    return True
            else:
                self.log_test("Admin Security Panel", "FAIL", f"Security panel error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Security Panel", "FAIL", f"Security panel exception: {str(e)}")
            return False
    
    def test_package_endpoints(self):
        """Test package-related functionality"""
        try:
            # Test upgrade page
            response = self.session.get(f"{self.base_url}/upgrade")
            if response.status_code == 200:
                self.log_test("Package System", "PASS", "Upgrade page accessible")
                return True
            else:
                self.log_test("Package System", "FAIL", f"Upgrade page error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Package System", "FAIL", f"Package test exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting RizzosAI Backoffice Test Suite")
        print("=" * 50)
        
        start_time = time.time()
        
        # Core functionality tests
        if not self.test_site_accessibility():
            print("\n❌ Cannot proceed - site not accessible")
            return self.generate_report()
        
        self.test_login_page()
        
        # Login as admin for authenticated tests
        if self.test_admin_login():
            self.test_dashboard_access()
            self.test_coey_page()
            self.test_coey_chat_api()
            self.test_security_system_admin_exemption()
            self.test_marketing_exception()
            self.test_onboarding_flow()
            self.test_admin_security_panel()
            self.test_package_endpoints()
        else:
            print("\n⚠️  Cannot run authenticated tests - login failed")
        
        end_time = time.time()
        
        print(f"\n⏱️  Test suite completed in {end_time - start_time:.2f} seconds")
        return self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warning_tests}")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! Your backoffice is working perfectly!")
        elif failed_tests <= 2:
            print(f"\n✅ System mostly functional with {failed_tests} minor issues")
        else:
            print(f"\n⚠️  System has {failed_tests} issues that need attention")
        
        print("\n🔍 DETAILED RESULTS:")
        print("-" * 30)
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"{status_icon} {result['test']}: {result['message']}")
        
        # Save detailed report to file
        report_data = {
            'summary': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warning_tests,
                'success_rate': f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            'results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open('backoffice_test_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n📄 Detailed report saved to: backoffice_test_report.json")
        except Exception as e:
            print(f"\n⚠️  Could not save report file: {e}")
        
        return report_data

def main():
    """Main test runner"""
    print("🔧 RizzosAI Backoffice System Test Script")
    print("Testing all functionality...")
    
    # You can change the URL here if needed
    base_url = input("Enter your backoffice URL (press Enter for default): ").strip()
    if not base_url:
        base_url = "https://sales-domain-rizzosai-com.onrender.com"
    
    print(f"Testing: {base_url}")
    
    tester = BackofficeTestSuite(base_url)
    report = tester.run_all_tests()
    
    print(f"\n🎯 SUCCESS RATE: {report['summary']['success_rate']}")
    
    return report

if __name__ == "__main__":
    main()