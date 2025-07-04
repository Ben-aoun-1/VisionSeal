#!/usr/bin/env python3
"""
Simple test of Supabase Auth signup functionality
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

sys.path.insert(0, str(os.path.dirname(__file__) + '/src'))

from core.database.supabase_client import supabase_manager

def test_auth_simple():
    """Test Supabase Auth signup and signin"""
    print("🧪 TESTING SUPABASE AUTH SYSTEM")
    print("=" * 40)
    
    test_email = "test@visionseal.com"
    test_password = "testpass123"
    
    try:
        # Test 1: Sign up
        print("1. Testing user signup...")
        
        signup_response = supabase_manager.client.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        print(f"   Signup response type: {type(signup_response)}")
        
        if hasattr(signup_response, 'user') and signup_response.user:
            print(f"   ✅ User created: {signup_response.user.email}")
            print(f"   User ID: {signup_response.user.id}")
            print(f"   Email confirmed: {signup_response.user.email_confirmed_at}")
            
            if hasattr(signup_response, 'session') and signup_response.session:
                print(f"   ✅ Session created immediately")
            else:
                print(f"   ⚠️ No session - email confirmation required")
        else:
            print(f"   ❌ No user created")
            print(f"   Response: {signup_response}")
            
        # Test 2: List auth users (using service key)
        print("\n2. Checking auth users...")
        try:
            # Use REST API to check users
            import requests
            headers = {
                'Authorization': f'Bearer {os.getenv("SUPABASE_SERVICE_KEY")}',
                'apikey': os.getenv("SUPABASE_SERVICE_KEY")
            }
            response = requests.get(
                f'{os.getenv("SUPABASE_URL")}/auth/v1/admin/users',
                headers=headers
            )
            if response.status_code == 200:
                users = response.json().get('users', [])
                print(f"   Total users: {len(users)}")
                for user in users:
                    print(f"   - {user.get('email')} (ID: {user.get('id', '')[:8]}...)")
            else:
                print(f"   ❌ Failed to list users: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ Could not list users: {e}")
            
        # Test 3: Try sign in
        print("\n3. Testing user signin...")
        signin_response = supabase_manager.client.auth.sign_in_with_password({
            "email": test_email,
            "password": test_password
        })
        
        if hasattr(signin_response, 'session') and signin_response.session:
            print(f"   ✅ Sign in successful")
            print(f"   Session user: {signin_response.session.user.email}")
        else:
            print(f"   ❌ Sign in failed")
            if hasattr(signin_response, 'error'):
                print(f"   Error: {signin_response.error}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth_simple()