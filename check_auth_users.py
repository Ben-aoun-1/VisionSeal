#!/usr/bin/env python3
"""
Check existing users in Supabase Auth
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_users():
    """Check users in Supabase Auth"""
    print("🔍 CHECKING SUPABASE AUTH USERS")
    print("=" * 35)
    
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
            data = response.json()
            users = data.get('users', [])
            print(f"✅ Total users found: {len(users)}")
            
            for i, user in enumerate(users, 1):
                print(f"\n👤 User {i}:")
                print(f"   Email: {user.get('email')}")
                print(f"   ID: {user.get('id')}")
                print(f"   Created: {user.get('created_at')}")
                print(f"   Email confirmed: {user.get('email_confirmed_at')}")
                print(f"   Last sign in: {user.get('last_sign_in_at')}")
                
            if len(users) == 0:
                print("📝 No users found in auth system")
                print("💡 This means signup attempts may not be reaching the database")
                
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_users()