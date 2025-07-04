#!/usr/bin/env python3
"""
Quick test of web authentication interface
"""
import subprocess
import time
import sys
import os
from pathlib import Path
import webbrowser

def start_web_server():
    """Start the web server for testing"""
    print("🌐 STARTING VISIONSEAL WEB SERVER")
    print("=" * 40)
    
    # Change to web_dashboard directory
    web_dir = Path(__file__).parent / "web_dashboard"
    if not web_dir.exists():
        print(f"❌ Web dashboard directory not found: {web_dir}")
        return None
    
    # Find an available port
    ports_to_try = [8080, 8081, 8082, 8083, 8084]
    
    for port in ports_to_try:
        try:
            print(f"🚀 Trying to start server on port {port}...")
            
            # Start server
            process = subprocess.Popen(
                [sys.executable, "server.py", "--port", str(port)],
                cwd=web_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment to see if it starts successfully
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ Server started successfully on port {port}")
                print(f"🔗 Auth URL: http://localhost:{port}/auth.html")
                print(f"🔗 Dashboard URL: http://localhost:{port}/dashboard.html")
                print(f"🔗 Guest Access: http://localhost:{port}/index.html")
                
                return process, port
            else:
                # Process ended, check output
                stdout, stderr = process.communicate()
                if "already in use" in stderr:
                    print(f"   ⚠️  Port {port} is already in use")
                    continue
                else:
                    print(f"   ❌ Failed to start on port {port}: {stderr}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ Error starting server on port {port}: {e}")
            continue
    
    print("❌ Could not start server on any port")
    return None

def test_auth_urls(port):
    """Test authentication URLs"""
    print(f"\n🧪 TESTING AUTHENTICATION URLS")
    print("=" * 35)
    
    import urllib.request
    import urllib.error
    
    urls_to_test = [
        f"http://localhost:{port}/auth.html",
        f"http://localhost:{port}/dashboard.html",
        f"http://localhost:{port}/index.html"
    ]
    
    for url in urls_to_test:
        try:
            print(f"🔍 Testing: {url}")
            response = urllib.request.urlopen(url, timeout=5)
            if response.getcode() == 200:
                print(f"   ✅ Response: {response.getcode()} - OK")
            else:
                print(f"   ⚠️  Response: {response.getcode()}")
        except urllib.error.URLError as e:
            print(f"   ❌ Error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

def show_testing_instructions(port):
    """Show manual testing instructions"""
    print(f"\n📋 MANUAL TESTING INSTRUCTIONS")
    print("=" * 35)
    
    instructions = f"""
    1. Open your web browser
    2. Visit: http://localhost:{port}/auth.html
    3. Click the "Sign Up" tab
    4. Enter a test email (e.g., test@example.com)
    5. Enter a password (minimum 6 characters)
    6. Confirm the password
    7. Click "Create Account"
    
    Expected Results:
    - ✅ Account creation should succeed
    - ✅ User should be redirected to dashboard
    - ✅ Dashboard should show user email in header
    - ✅ Dashboard should display tender data
    
    If Issues Occur:
    - 🔍 Check browser console for JavaScript errors
    - 🔍 Check Network tab for failed API calls
    - 🔍 Verify Supabase authentication settings
    - 🔍 Check if email confirmation is disabled
    
    Alternative Testing:
    - Try signing in with existing user: test@visionseal.com
    - Test guest access at: http://localhost:{port}/index.html
    - Test dashboard directly: http://localhost:{port}/dashboard.html
    """
    
    print(instructions)

def main():
    """Main testing function"""
    print("🔐 VISIONSEAL WEB AUTHENTICATION TESTER")
    print("This script starts the web server and provides testing guidance")
    print()
    
    # Start web server
    server_info = start_web_server()
    
    if not server_info:
        print("❌ Could not start web server")
        print("💡 Try running manually: python3 web_dashboard/server.py")
        return
    
    process, port = server_info
    
    try:
        # Test URLs
        test_auth_urls(port)
        
        # Show testing instructions
        show_testing_instructions(port)
        
        print(f"\n🌐 WEB SERVER IS RUNNING")
        print("=" * 30)
        print(f"🔗 Main URL: http://localhost:{port}/auth.html")
        print(f"⌨️  Press Ctrl+C to stop the server")
        print()
        
        # Try to open browser automatically
        try:
            webbrowser.open(f"http://localhost:{port}/auth.html")
            print("🌐 Opening browser automatically...")
        except Exception as e:
            print(f"💡 Could not open browser automatically: {e}")
            print(f"   Please open http://localhost:{port}/auth.html manually")
        
        # Keep server running
        print("⏳ Server running... waiting for testing...")
        while True:
            time.sleep(1)
            if process.poll() is not None:
                print("❌ Server process ended unexpectedly")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        process.terminate()
        process.wait()
        print("✅ Server stopped")
    
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()