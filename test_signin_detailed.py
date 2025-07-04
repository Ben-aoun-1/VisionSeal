#!/usr/bin/env python3
"""
Detailed test of sign-in process to identify the exact issue
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(os.path.dirname(__file__) + '/src'))

from core.database.supabase_client import supabase_manager

def test_signin_detailed():
    """Test sign-in with detailed error reporting"""
    print("🔍 DETAILED SIGN-IN TESTING")
    print("=" * 35)
    
    # Test with the confirmed email
    test_email = "medaminebenaoun@gmail.com"
    
    print(f"Testing sign-in with: {test_email}")
    print("Please enter the password you used for this account:")
    
    # Get password from user
    import getpass
    test_password = getpass.getpass("Password: ")
    
    if not test_password:
        print("❌ No password entered")
        return
    
    try:
        print(f"\n🔐 Attempting sign-in...")
        print(f"Email: {test_email}")
        print(f"Password: {'*' * len(test_password)}")
        
        # Attempt sign-in
        response = supabase_manager.client.auth.sign_in_with_password({
            "email": test_email,
            "password": test_password
        })
        
        print(f"\n📋 Response details:")
        print(f"Response type: {type(response)}")
        
        if hasattr(response, 'user') and response.user:
            print(f"✅ User object found:")
            print(f"   Email: {response.user.email}")
            print(f"   ID: {response.user.id}")
            print(f"   Email confirmed: {response.user.email_confirmed_at}")
        else:
            print(f"❌ No user in response")
            
        if hasattr(response, 'session') and response.session:
            print(f"✅ Session object found:")
            print(f"   Access token: {response.session.access_token[:20]}...")
            print(f"   User ID: {response.session.user.id}")
            print(f"   Expires: {response.session.expires_at}")
        else:
            print(f"❌ No session in response")
            
        if hasattr(response, 'error') and response.error:
            print(f"❌ Error in response:")
            print(f"   Error: {response.error}")
        
        print(f"\n🧪 TESTING WEB INTERFACE...")
        print(f"If sign-in worked above, try these steps:")
        print(f"1. Go to http://localhost:8081/auth.html")
        print(f"2. Use email: {test_email}")
        print(f"3. Use the same password you just entered")
        print(f"4. Check browser console (F12) for any JavaScript errors")
        
    except Exception as e:
        print(f"❌ Sign-in failed with error:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        
        if "Invalid login credentials" in str(e):
            print(f"\n💡 DIAGNOSIS: Invalid credentials error")
            print(f"   This means either:")
            print(f"   1. Password is incorrect")
            print(f"   2. Email is not exactly correct")
            print(f"   3. Account exists but has a different password")
            
            print(f"\n🔧 SOLUTIONS:")
            print(f"   1. Try different password variations")
            print(f"   2. Reset password using forgot password")
            print(f"   3. Create a new account with known password")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_signin_detailed()