#!/usr/bin/env python3
"""
Create a working test user for authentication testing
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(os.path.dirname(__file__) + '/src'))

from core.database.supabase_client import supabase_manager

def create_working_test_user():
    """Create a test user that definitely works"""
    print("🆕 CREATING WORKING TEST USER")
    print("=" * 30)
    
    test_email = "testuser@gmail.com"  # Use proper email format
    test_password = "password123"      # Simple password
    
    try:
        print(f"Creating user: {test_email}")
        print(f"Password: {test_password}")
        
        # Create user
        response = supabase_manager.client.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if hasattr(response, 'user') and response.user:
            user_id = response.user.id
            print(f"✅ User created with ID: {user_id}")
            
            # Immediately confirm the user
            print(f"🔧 Auto-confirming user...")
            headers = {
                'Authorization': f'Bearer {os.getenv("SUPABASE_SERVICE_KEY")}',
                'apikey': os.getenv("SUPABASE_SERVICE_KEY"),
                'Content-Type': 'application/json'
            }
            
            confirm_response = requests.put(
                f'{os.getenv("SUPABASE_URL")}/auth/v1/admin/users/{user_id}',
                headers=headers,
                json={'email_confirm': True}
            )
            
            if confirm_response.status_code == 200:
                print(f"✅ User confirmed successfully!")
                
                # Test sign-in
                print(f"🔐 Testing sign-in...")
                signin_response = supabase_manager.client.auth.sign_in_with_password({
                    "email": test_email,
                    "password": test_password
                })
                
                if hasattr(signin_response, 'session') and signin_response.session:
                    print(f"🎉 SIGN-IN SUCCESSFUL!")
                    print(f"✅ These credentials work perfectly:")
                    print(f"   📧 Email: {test_email}")
                    print(f"   🔑 Password: {test_password}")
                    print(f"")
                    print(f"🌐 To test in browser:")
                    print(f"   1. Go to http://localhost:8081/auth.html")
                    print(f"   2. Click 'Sign In' tab")
                    print(f"   3. Enter: {test_email}")
                    print(f"   4. Enter: {test_password}")
                    print(f"   5. Should redirect to dashboard!")
                else:
                    print(f"❌ Sign-in still failed")
                    if hasattr(signin_response, 'error'):
                        print(f"Error: {signin_response.error}")
            else:
                print(f"❌ Confirmation failed: {confirm_response.status_code}")
                print(f"Response: {confirm_response.text}")
        else:
            print(f"❌ User creation failed")
            if hasattr(response, 'error'):
                print(f"Error: {response.error}")
                
    except Exception as e:
        if "User already registered" in str(e):
            print(f"✅ User already exists!")
            print(f"🔐 Testing existing user sign-in...")
            
            try:
                signin_response = supabase_manager.client.auth.sign_in_with_password({
                    "email": test_email,
                    "password": test_password
                })
                
                if hasattr(signin_response, 'session') and signin_response.session:
                    print(f"🎉 EXISTING USER SIGN-IN SUCCESSFUL!")
                    print(f"✅ Use these credentials:")
                    print(f"   📧 Email: {test_email}")
                    print(f"   🔑 Password: {test_password}")
                else:
                    print(f"❌ Existing user sign-in failed")
            except Exception as signin_error:
                print(f"❌ Existing user sign-in error: {signin_error}")
        else:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    create_working_test_user()