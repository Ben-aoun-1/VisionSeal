#!/usr/bin/env python3
"""
Debug authentication sign-in issues
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_signin():
    """Debug sign-in issues"""
    print("🔍 DEBUGGING AUTHENTICATION SIGN-IN")
    print("=" * 40)
    
    # Check users in database
    try:
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
            print(f"✅ Found {len(users)} users in database:")
            
            for i, user in enumerate(users, 1):
                email = user.get('email')
                confirmed = user.get('email_confirmed_at')
                last_signin = user.get('last_sign_in_at')
                
                print(f"\n👤 User {i}: {email}")
                print(f"   Email confirmed: {'✅ Yes' if confirmed else '❌ No'}")
                print(f"   Last sign in: {last_signin or 'Never'}")
                print(f"   Can sign in: {'✅ Yes' if confirmed else '❌ No (needs email confirmation)'}")
                
                if not confirmed:
                    print(f"   💡 To fix: Need to confirm email or disable email confirmation")
                    
            # Test actual sign-in with confirmed user
            confirmed_users = [u for u in users if u.get('email_confirmed_at')]
            if confirmed_users:
                print(f"\n🧪 TESTING SIGN-IN")
                test_user = confirmed_users[0]
                print(f"Testing with confirmed user: {test_user['email']}")
                print(f"⚠️  NOTE: You need to know the password for this user to test sign-in")
                print(f"   If this is your email, try signing in with your password")
            else:
                print(f"\n❌ NO CONFIRMED USERS FOUND")
                print(f"   All users need email confirmation before they can sign in")
                print(f"   Solution: Disable email confirmation in Supabase settings")
                
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
    print(f"\n🔧 SOLUTIONS:")
    print(f"1. Use a confirmed email (like medaminebenaoun@gmail.com)")
    print(f"2. Disable email confirmation in Supabase Dashboard")
    print(f"3. Check email and confirm signup link")
    print(f"4. Make sure password is correct (minimum 6 characters)")

if __name__ == "__main__":
    debug_signin()