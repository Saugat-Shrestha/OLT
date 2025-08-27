#!/usr/bin/env python3
"""
Test script for ONT Registration System
This script tests the complete ONT registration flow
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
TEST_CREDENTIALS = {
    "username": "admin",  # Replace with actual OLT credentials
    "password": "admin"   # Replace with actual OLT credentials
}

def test_olt_login():
    """Test OLT login functionality"""
    print("=== Testing OLT Login ===")
    
    try:
        response = requests.post(
            f"{BASE_URL}/olt-login",
            json=TEST_CREDENTIALS,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ OLT Login successful")
            return True
        else:
            print("❌ OLT Login failed")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False

def test_ont_autofind():
    """Test ONT autofind functionality"""
    print("\n=== Testing ONT Autofind ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/ont-autofind",
            cookies=requests.Session().cookies
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ ONT Autofind successful")
            return True
        else:
            print("❌ ONT Autofind failed")
            return False
            
    except Exception as e:
        print(f"❌ Autofind error: {str(e)}")
        return False

def test_ont_registration():
    """Test ONT registration functionality"""
    print("\n=== Testing ONT Registration ===")
    
    # Test data - replace with actual ONT data
    test_ont_data = {
        "boardId": "0/0",
        "portId": "5",
        "ontId": "1",
        "serialNumber": "45485443BA058ED8",  # Replace with actual serial number
        "description": "test_ont",
        "lineProfileId": "10",
        "serviceProfileId": "10"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ont-register",
            json=test_ont_data,
            headers={'Content-Type': 'application/json'},
            cookies=requests.Session().cookies
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ ONT Registration successful")
            return True
        else:
            print("❌ ONT Registration failed")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return False

def test_ont_verification():
    """Test ONT verification functionality"""
    print("\n=== Testing ONT Verification ===")
    
    # Test data - should match registration data
    test_verify_data = {
        "boardId": "0/0",
        "portId": "5",
        "ontId": "1",
        "serialNumber": "45485443BA058ED8"  # Replace with actual serial number
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ont-verify",
            json=test_verify_data,
            headers={'Content-Type': 'application/json'},
            cookies=requests.Session().cookies
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ ONT Verification successful")
            return True
        else:
            print("❌ ONT Verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        return False

def test_board_status():
    """Test board status functionality"""
    print("\n=== Testing Board Status ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/board-status",
            cookies=requests.Session().cookies
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Board Status successful")
            return True
        else:
            print("❌ Board Status failed")
            return False
            
    except Exception as e:
        print(f"❌ Board Status error: {str(e)}")
        return False

def test_olt_logout():
    """Test OLT logout functionality"""
    print("\n=== Testing OLT Logout ===")
    
    try:
        response = requests.post(
            f"{BASE_URL}/olt-logout",
            headers={'Content-Type': 'application/json'},
            cookies=requests.Session().cookies
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ OLT Logout successful")
            return True
        else:
            print("❌ OLT Logout failed")
            return False
            
    except Exception as e:
        print(f"❌ Logout error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("ONT Registration System Test Suite")
    print("=" * 50)
    
    # Test results
    results = []
    
    # Run tests
    results.append(("OLT Login", test_olt_login()))
    time.sleep(1)  # Small delay between tests
    
    results.append(("ONT Autofind", test_ont_autofind()))
    time.sleep(1)
    
    results.append(("ONT Registration", test_ont_registration()))
    time.sleep(1)
    
    results.append(("ONT Verification", test_ont_verification()))
    time.sleep(1)
    
    results.append(("Board Status", test_board_status()))
    time.sleep(1)
    
    results.append(("OLT Logout", test_olt_logout()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! ONT Registration System is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the system configuration and OLT connectivity.")

if __name__ == "__main__":
    main() 