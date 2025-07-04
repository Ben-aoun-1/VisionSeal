#!/usr/bin/env python3
"""
Manually confirm all users to bypass email confirmation
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def confirm_all_users():
    """Manually confirm all unconfirmed users"""
    print("🔧 MANUALLY CONFIRMING ALL USERS")
    print("=" * 35)
    
    try:
        headers = {
            'Authorization': f'Bearer {os.getenv("SUPABASE_SERVICE_KEY")}',
            'apikey': os.getenv("SUPABASE_SERVICE_KEY"),
            'Content-Type': 'application/json'
        }
        
        # Get all users
        response = requests.get(
            f'{os.getenv("SUPABASE_URL")}/auth/v1/admin/users',
            headers=headers
        )
        
        if response.status_code == 200:
            users = response.json().get('users', [])
            unconfirmed_users = [u for u in users if not u.get('email_confirmed_at')]
            
            print(f"Found {len(unconfirmed_users)} unconfirmed users")
            
            for user in unconfirmed_users:
                user_id = user['id']
                email = user['email']
                
                print(f"\n📧 Confirming user: {email}")
                
                # Manually confirm user
                confirm_response = requests.put(
                    f'{os.getenv("SUPABASE_URL")}/auth/v1/admin/users/{user_id}',
                    headers=headers,
                    json={
                        'email_confirm': True
                    }
                )
                
                if confirm_response.status_code == 200:
                    print(f"   ✅ User {email} confirmed successfully")
                else:
                    print(f"   ❌ Failed to confirm {email}: {confirm_response.status_code}")
                    print(f"   Response: {confirm_response.text}")
            
            print(f"\n🎉 All users should now be able to sign in!")
            print(f"Try signing in with any of these emails:")
            for user in users:
                print(f"   - {user['email']}")
                
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    confirm_all_users()