#!/usr/bin/env python3
"""
Test authentication system with Supabase
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio

# Load environment variables
load_dotenv()

def test_supabase_auth():
    """Test Supabase authentication"""
    print("🔐 TESTING SUPABASE AUTHENTICATION")
    print("=" * 40)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        print("❌ Missing Supabase environment variables")
        return False
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_anon_key)
    
    # Test user signup
    print("\n📝 Testing user signup...")
    test_email = "test@visionseal.com"
    test_password = "TestPass123!"
    
    try:
        # First, try to sign up a user
        response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if response.user:
            print(f"   ✅ User signed up successfully: {response.user.id}")
            print(f"   📧 Email: {response.user.email}")
            print(f"   ✅ Email confirmed: {response.user.email_confirmed_at is not None}")
            
            # Check if user was created in auth.users table
            print(f"   🔍 User created in auth.users table: {response.user.id}")
            
            # Check if user was created in public.users table
            print("\n🔍 Checking if user profile was created in public.users...")
            try:
                user_profile = supabase.table('users').select('*').eq('id', response.user.id).execute()
                if user_profile.data:
                    print(f"   ✅ User profile found in public.users: {user_profile.data[0]}")
                else:
                    print("   ❌ User profile NOT found in public.users table")
                    print("   💡 This might be the issue - user profile not being created")
            except Exception as profile_error:
                print(f"   ❌ Error checking user profile: {profile_error}")
            
            # Test if we need to manually create the user profile
            print("\n📝 Testing manual user profile creation...")
            try:
                user_data = {
                    'id': response.user.id,
                    'email': response.user.email,
                    'full_name': 'Test User',
                    'subscription_tier': 'FREE'
                }
                
                profile_response = supabase.table('users').insert(user_data).execute()
                if profile_response.data:
                    print(f"   ✅ User profile created manually: {profile_response.data[0]}")
                else:
                    print("   ❌ Failed to create user profile manually")
            except Exception as manual_error:
                print(f"   ❌ Error creating user profile manually: {manual_error}")
                
        else:
            print("   ❌ User signup failed")
            print(f"   Error: {response}")
            
    except Exception as e:
        print(f"   ❌ Signup error: {str(e)}")
        # This might be expected if user already exists
        if "already registered" in str(e):
            print("   💡 User already exists - testing sign in...")
            
            # Test sign in
            try:
                signin_response = supabase.auth.sign_in_with_password({
                    "email": test_email,
                    "password": test_password
                })
                
                if signin_response.user:
                    print(f"   ✅ User signed in successfully: {signin_response.user.id}")
                    print(f"   📧 Email: {signin_response.user.email}")
                else:
                    print("   ❌ Sign in failed")
                    
            except Exception as signin_error:
                print(f"   ❌ Sign in error: {str(signin_error)}")
    
    # Test authentication settings
    print("\n⚙️ Testing authentication settings...")
    try:
        # Get current session
        session = supabase.auth.get_session()
        print(f"   Current session: {session.access_token[:20] if session.access_token else 'None'}...")
        
        # Test if email confirmation is required
        print("\n📧 Checking email confirmation settings...")
        print("   💡 Check your Supabase Auth settings:")
        print("   - Email Confirm: Should be disabled for testing")
        print("   - Email Auth: Should be enabled")
        print("   - Auto-confirm users: Should be enabled for testing")
        
    except Exception as e:
        print(f"   ❌ Session error: {str(e)}")
    
    return True

def check_auth_policies():
    """Check authentication policies"""
    print("\n🛡️ CHECKING AUTHENTICATION POLICIES")
    print("=" * 40)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase service key")
        return False
    
    # Create Supabase client with service key
    supabase: Client = create_client(supabase_url, supabase_service_key)
    
    print("🔍 Checking user table policies...")
    try:
        # Try to read from users table
        users = supabase.table('users').select('*').limit(5).execute()
        print(f"   ✅ Can read users table: {len(users.data)} users found")
        
        # Check if we can create a user
        print("\n📝 Testing user creation with service key...")
        test_user_data = {
            'email': 'servicetest@visionseal.com',
            'full_name': 'Service Test User',
            'subscription_tier': 'FREE'
        }
        
        # This should work with service key
        create_response = supabase.table('users').insert(test_user_data).execute()
        if create_response.data:
            print(f"   ✅ Can create user with service key: {create_response.data[0]}")
        else:
            print("   ❌ Cannot create user with service key")
            
    except Exception as e:
        print(f"   ❌ Policy check error: {str(e)}")
        print("   💡 This might indicate RLS policy issues")
    
    return True

def main():
    """Run all authentication tests"""
    print("🔐 AUTHENTICATION SYSTEM TEST")
    print("Testing VisionSeal authentication with Supabase")
    print()
    
    test_supabase_auth()
    check_auth_policies()
    
    print("\n" + "=" * 50)
    print("🎯 AUTHENTICATION TEST COMPLETE")
    print("=" * 50)
    
    print("\n💡 TROUBLESHOOTING TIPS:")
    print("1. Check Supabase Auth settings in dashboard")
    print("2. Verify email confirmation is disabled for testing")
    print("3. Check if public.users table has proper triggers")
    print("4. Verify RLS policies allow user creation")
    print("5. Check browser console for JavaScript errors")
    
    print(f"\n🌐 Supabase Dashboard: https://supabase.com/dashboard")
    print("   Go to: Authentication > Settings")
    print("   Go to: Authentication > Users")
    print("   Go to: Database > public.users")

if __name__ == "__main__":
    main()