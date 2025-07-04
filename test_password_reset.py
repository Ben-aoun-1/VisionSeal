#!/usr/bin/env python3
"""
Test password reset functionality to solve login issues
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(os.path.dirname(__file__) + '/src'))

from core.database.supabase_client import supabase_manager

def test_password_reset():
    """Test password reset to bypass login issues"""
    print("🔐 PASSWORD RESET TEST")
    print("=" * 25)
    
    test_email = "medaminebenaoun@gmail.com"
    
    try:
        print(f"Sending password reset email to: {test_email}")
        
        response = supabase_manager.client.auth.reset_password_email(test_email)
        
        print(f"Reset response: {response}")
        print(f"✅ Password reset email sent!")
        print(f"📧 Check your email for reset link")
        print(f"🔗 After clicking link, you can set a new password")
        
    except Exception as e:
        print(f"❌ Password reset failed: {str(e)}")
        
def create_test_user():
    """Create a new test user with known credentials"""
    print("\n🆕 CREATING TEST USER")
    print("=" * 22)
    
    test_email = "testuser@visionseal.local"
    test_password = "testpass123"
    
    try:
        print(f"Creating test user: {test_email}")
        print(f"Password: {test_password}")
        
        response = supabase_manager.client.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if hasattr(response, 'user') and response.user:
            print(f"✅ Test user created successfully!")
            print(f"User ID: {response.user.id}")
            
            # Try to sign in immediately
            print(f"\n🔐 Testing immediate sign-in...")
            signin_response = supabase_manager.client.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            
            if hasattr(signin_response, 'session') and signin_response.session:
                print(f"✅ Sign-in successful!")
                print(f"🎉 You can now use these credentials in the web interface:")
                print(f"   Email: {test_email}")
                print(f"   Password: {test_password}")
            else:
                print(f"⚠️ Sign-in failed - user needs confirmation")
                print(f"Running auto-confirmation...")
                
                # Auto-confirm the user
                import requests
                headers = {
                    'Authorization': f'Bearer {os.getenv("SUPABASE_SERVICE_KEY")}',
                    'apikey': os.getenv("SUPABASE_SERVICE_KEY"),
                    'Content-Type': 'application/json'
                }
                
                confirm_response = requests.put(
                    f'{os.getenv("SUPABASE_URL")}/auth/v1/admin/users/{response.user.id}',
                    headers=headers,
                    json={'email_confirm': True}
                )
                
                if confirm_response.status_code == 200:
                    print(f"✅ User auto-confirmed!")
                    print(f"🎉 Try signing in with:")
                    print(f"   Email: {test_email}")
                    print(f"   Password: {test_password}")
                else:
                    print(f"❌ Auto-confirmation failed")
        else:
            print(f"❌ Failed to create test user")
            print(f"Response: {response}")
            
    except Exception as e:
        if "User already registered" in str(e):
            print(f"✅ Test user already exists!")
            print(f"🎉 Try signing in with:")
            print(f"   Email: {test_email}")
            print(f"   Password: {test_password}")
        else:
            print(f"❌ Error creating test user: {str(e)}")

if __name__ == "__main__":
    print("🚀 AUTHENTICATION TROUBLESHOOTING")
    print("=" * 35)
    
    print("\nOption 1: Reset password for existing account")
    test_password_reset()
    
    print("\nOption 2: Create new test account")
    create_test_user()
    
    print(f"\n📋 NEXT STEPS:")
    print(f"1. If password reset: Check email and follow reset link")
    print(f"2. If test user created: Use testuser@visionseal.local / testpass123")
    print(f"3. Go to http://localhost:8081/auth.html and try signing in")
    print(f"4. If still issues, check browser console (F12) for errors")