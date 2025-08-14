#!/usr/bin/env python3
"""
Troubleshooting script for web initialization issues.
Run this to identify why the page is stuck on "Initializing Healthcare AI"
"""

import sys
import os
import requests
import json
from pathlib import Path

def check_server():
    """Check if the server is running and responding."""
    print("🔍 Checking server status...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            data = response.json()
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Environment: {data.get('environment', 'Unknown')}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def check_endpoints():
    """Check various API endpoints."""
    print("\n🔍 Checking API endpoints...")
    
    endpoints = [
        ("/health", "Health Check"),
        ("/debug", "Debug Info"),
        ("/", "Main Page"),
        ("/emergency", "Emergency Page")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"   {status} {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: {e}")

def check_files():
    """Check if required frontend files exist."""
    print("\n🔍 Checking frontend files...")
    
    required_files = [
        "frontend/static/index.html",
        "frontend/static/script.js",
        "frontend/static/styles.css"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING!")

def check_html_content():
    """Check HTML content for potential issues."""
    print("\n🔍 Checking HTML content...")
    
    html_file = Path("frontend/static/index.html")
    if not html_file.exists():
        print("   ❌ HTML file not found!")
        return
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            'id="loadingScreen"',
            'id="app"',
            'id="recordBtn"',
            'id="chatMessages"'
        ]
        
        for element in required_elements:
            if element in content:
                print(f"   ✅ {element}")
            else:
                print(f"   ❌ {element} - MISSING!")
        
        # Check for script loading
        if 'script.js' in content:
            print("   ✅ script.js is referenced")
        else:
            print("   ❌ script.js is NOT referenced!")
            
    except Exception as e:
        print(f"   ❌ Error reading HTML: {e}")

def check_console_errors():
    """Provide instructions for checking browser console."""
    print("\n🔍 Browser Console Check:")
    print("   1. Open the main page: http://localhost:8000")
    print("   2. Press F12 to open Developer Tools")
    print("   3. Go to Console tab")
    print("   4. Look for any red error messages")
    print("   5. Copy any errors you see")

def main():
    """Main troubleshooting function."""
    print("🚨 Healthcare Voice AI - Web Troubleshooting")
    print("=" * 60)
    
    # Check server
    server_ok = check_server()
    
    if server_ok:
        # Check endpoints
        check_endpoints()
        
        # Check files
        check_files()
        
        # Check HTML content
        check_html_content()
        
        # Browser console instructions
        check_console_errors()
        
        print("\n" + "=" * 60)
        print("📋 Troubleshooting Summary:")
        print("✅ Server is running")
        print("🔍 Check the file status above")
        print("🔍 Check browser console for JavaScript errors")
        print("🔍 Try the emergency page: http://localhost:8000/emergency")
        
        print("\n🚀 Quick Fixes:")
        print("   1. Clear browser cache (Ctrl+Shift+R)")
        print("   2. Check browser console (F12)")
        print("   3. Try emergency page: /emergency")
        print("   4. Restart server: python main.py")
        
    else:
        print("\n❌ Server is not running!")
        print("Start the server with: python main.py")

if __name__ == "__main__":
    main()
