#!/usr/bin/env python3
"""
Extract authentication token from reset link and create working session
"""
import urllib.parse

def extract_token_info():
    """Extract token info from the reset URL"""
    print("🔗 EXTRACTING AUTHENTICATION TOKEN")
    print("=" * 35)
    
    # The URL you provided
    reset_url = "http://localhost:3000/#access_token=eyJhbGciOiJIUzI1NiIsImtpZCI6IlBVODJhWGlhNzFrSlR5YnEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2Z5Y2F0cnVpYXd5bmJ6dWFmZHN4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI1M2FhMjZjYS0wNDdhLTQ4ZTEtYmRhZS02NTYwYmJjYmMxMTAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUxNjMyNjI2LCJpYXQiOjE3NTE2MjkwMjYsImVtYWlsIjoibWVkYW1pbmViZW5hb3VuQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJtZWRhbWluZWJlbmFvdW5AZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiNTNhYTI2Y2EtMDQ3YS00OGUxLWJkYWUtNjU2MGJiY2JjMTEwIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib3RwIiwidGltZXN0YW1wIjoxNzUxNjI5MDI2fV0sInNlc3Npb25faWQiOiI4ODFhYTdiZC1kZjg3LTQwN2QtODcxMy00ZTJmZmM3ZjNjYzAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.uajeGWhC59M3UeFsBhEhIHvMsIkudxd4-Sb2m9vOvE8&expires_at=1751632626&expires_in=3600&refresh_token=5du4hdih3iw4&token_type=bearer&type=recovery"
    
    # Parse the fragment (everything after #)
    fragment = reset_url.split('#')[1]
    params = urllib.parse.parse_qs(fragment)
    
    access_token = params.get('access_token', [None])[0]
    refresh_token = params.get('refresh_token', [None])[0]
    expires_at = params.get('expires_at', [None])[0]
    token_type = params.get('token_type', [None])[0]
    
    print(f"✅ Token extracted successfully!")
    print(f"   Email: medaminebenaoun@gmail.com")
    print(f"   Token type: {token_type}")
    print(f"   Expires at: {expires_at}")
    print(f"   Access token: {access_token[:50]}...")
    print(f"   Refresh token: {refresh_token}")
    
    # Create the correct redirect URL
    correct_url = f"http://localhost:8081/dashboard.html#access_token={access_token}&expires_at={expires_at}&expires_in=3600&refresh_token={refresh_token}&token_type={token_type}&type=recovery"
    
    print(f"\n🔧 CORRECTED URL:")
    print(f"Copy and paste this URL in your browser:")
    print(f"\n{correct_url}\n")
    
    print(f"🎯 ALTERNATIVE: Manual Sign-In")
    print(f"Since you reset your password, you can now:")
    print(f"1. Go to http://localhost:8081/auth.html")
    print(f"2. Enter email: medaminebenaoun@gmail.com")
    print(f"3. Enter your NEW password (the one you just set)")
    print(f"4. Sign in normally")

if __name__ == "__main__":
    extract_token_info()