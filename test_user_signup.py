#!/usr/bin/env python3
"""
Test user signup after applying fixes
"""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(os.path.dirname(__file__) + '/src'))

from core.database.supabase_client import supabase_manager

def test_user_signup():
    """Test complete user signup flow"""
    print("🧪 TESTING USER SIGNUP FLOW")
    print("=" * 35)
    
    # Create unique test user
    timestamp = int(time.time())
    test_email = f"newuser{timestamp}@test.com"
    test_password = "TestPass123!"
    
    try:
        print(f"📧 Testing signup for: {test_email}")
        
        # Step 1: Sign up new user
        response = supabase_manager.client.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if hasattr(response, 'user') and response.user:
            print(f"✅ User created in auth.users: {response.user.id}")
            
            # Step 2: Check if auto-confirmation worked
            if hasattr(response, 'session') and response.session:
                print(f"✅ User auto-confirmed with session!")
                
                # Step 3: Test immediate signin
                signin_response = supabase_manager.client.auth.sign_in_with_password({
                    "email": test_email,
                    "password": test_password
                })
                
                if hasattr(signin_response, 'session') and signin_response.session:
                    print(f"✅ Immediate signin works!")
                    
                    # Step 4: Check if profile was created automatically
                    print(f"🔍 Checking if user profile was created...")
                    profile_check = supabase_manager.client.table('users').select('*').eq('email', test_email).execute()
                    
                    if profile_check.data:
                        print(f"✅ User profile created automatically!")
                        print(f"   Profile: {profile_check.data[0]}")
                        
                        print(f"\n🎉 SUCCESS! User signup flow is working:")
                        print(f"   ✅ User registration")
                        print(f"   ✅ Auto-confirmation") 
                        print(f"   ✅ Immediate signin")
                        print(f"   ✅ Automatic profile creation")
                        print(f"\n💡 Users can now signup at: http://localhost:8082/auth.html")
                        
                        return True
                    else:
                        print(f"❌ User profile NOT created automatically")
                        print(f"💡 Database trigger might not be set up")
                        
                else:
                    print(f"❌ Immediate signin failed")
                    if hasattr(signin_response, 'error'):
                        print(f"   Error: {signin_response.error}")
            else:
                print(f"⚠️ User created but needs email confirmation")
                print(f"💡 Auto-confirmation not enabled in Supabase settings")
                
        else:
            print(f"❌ User creation failed")
            if hasattr(response, 'error'):
                print(f"   Error: {response.error}")
                
    except Exception as e:
        print(f"❌ Signup test error: {str(e)}")
        return False
    
    return False

if __name__ == "__main__":
    print("🚀 USER SIGNUP TESTING")
    print("Testing complete signup flow after fixes")
    print()
    
    if test_user_signup():
        print(f"\n✅ All fixes applied successfully!")
        print(f"Users can now create accounts normally")
    else:
        print(f"\n❌ Fixes still needed:")
        print(f"1. Disable email confirmation in Supabase Dashboard")
        print(f"2. Run fix_user_registration.sql in Supabase SQL Editor")