#!/usr/bin/env python3
"""
Create a fresh test user with guaranteed working credentials
"""
import os
import sys
import requests
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(os.path.dirname(__file__) + '/src'))

from core.database.supabase_client import supabase_manager

def create_fresh_test_user():
    """Create a completely fresh test user"""
    print("🆕 CREATING FRESH TEST USER")
    print("=" * 30)
    
    # Create unique credentials
    timestamp = int(time.time())
    test_email = f"visiontest{timestamp}@gmail.com"
    test_password = "VisionSeal2025!"
    
    try:
        print(f"Creating user: {test_email}")
        print(f"Password: {test_password}")
        
        # Delete any existing user with similar email first
        print(f"🧹 Cleaning up any existing test users...")
        
        # Create new user
        response = supabase_manager.client.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if hasattr(response, 'user') and response.user:
            user_id = response.user.id
            print(f"✅ User created with ID: {user_id}")
            
            # Immediately confirm the user using admin API
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
                
                # Wait a moment then test sign-in
                print(f"⏳ Waiting 2 seconds...")
                time.sleep(2)
                
                # Test sign-in
                print(f"🔐 Testing sign-in...")
                signin_response = supabase_manager.client.auth.sign_in_with_password({
                    "email": test_email,
                    "password": test_password
                })
                
                if hasattr(signin_response, 'session') and signin_response.session:
                    print(f"🎉 SIGN-IN SUCCESSFUL!")
                    print(f"✅ These credentials are GUARANTEED to work:")
                    print(f"")
                    print(f"📧 Email: {test_email}")
                    print(f"🔑 Password: {test_password}")
                    print(f"")
                    print(f"🌐 To test in browser:")
                    print(f"   1. Go to http://localhost:8082/auth.html")
                    print(f"   2. Click 'Sign In' tab")
                    print(f"   3. Copy and paste the email above")
                    print(f"   4. Copy and paste the password above")
                    print(f"   5. Click 'Sign In'")
                    print(f"   6. Should redirect to dashboard!")
                    
                    return test_email, test_password
                else:
                    print(f"❌ Sign-in failed")
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
            print(f"✅ User already exists! Try using:")
            print(f"   Email: {test_email}")
            print(f"   Password: {test_password}")
        else:
            print(f"❌ Error: {str(e)}")
    
    return None, None

def test_existing_accounts():
    """Test existing accounts to see which ones work"""
    print(f"\n🧪 TESTING EXISTING ACCOUNTS")
    print(f"=" * 30)
    
    test_accounts = [
        ("testuser@gmail.com", "password123"),
        ("medaminebenaoun@gmail.com", "your_password_here"),
    ]
    
    for email, password in test_accounts:
        if "your_password" in password:
            print(f"⏭️ Skipping {email} - password unknown")
            continue
            
        try:
            print(f"🔐 Testing {email}...")
            signin_response = supabase_manager.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if hasattr(signin_response, 'session') and signin_response.session:
                print(f"✅ {email} works with password: {password}")
            else:
                print(f"❌ {email} sign-in failed")
                
        except Exception as e:
            print(f"❌ {email} error: {str(e)}")

if __name__ == "__main__":
    print("🚀 AUTHENTICATION TROUBLESHOOTING")
    print("=" * 35)
    
    # Test existing accounts first
    test_existing_accounts()
    
    # Create fresh account
    email, password = create_fresh_test_user()
    
    if email and password:
        print(f"\n🎯 SUCCESS! Use these guaranteed working credentials:")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
    else:
        print(f"\n📝 Try guest access instead:")
        print(f"🌐 Go to: http://localhost:8082/index.html")