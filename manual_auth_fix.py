#!/usr/bin/env python3
"""
Manual fix for VisionSeal Authentication System
Uses direct SQL execution to fix authentication issues
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get direct PostgreSQL connection to Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found")
        return None
    
    # Extract connection details from Supabase URL
    # Format: https://project-id.supabase.co
    if 'supabase.co' in supabase_url:
        project_id = supabase_url.split('//')[1].split('.')[0]
        
        # Supabase PostgreSQL connection details
        host = f"db.{project_id}.supabase.co"
        port = 5432
        database = "postgres"
        user = "postgres"
        
        # The service key contains the password for direct connection
        # For direct connection, you'd typically need the database password
        print(f"📊 Connection details:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Database: {database}")
        print(f"   User: {user}")
        print("   ❌ Direct PostgreSQL connection requires database password")
        print("   💡 Use Supabase SQL Editor or API instead")
        
        return None
    
    return None

def apply_fixes_via_supabase_api():
    """Apply fixes using Supabase API"""
    print("🔧 APPLYING FIXES VIA SUPABASE API")
    print("=" * 40)
    
    from supabase import create_client, Client
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase environment variables")
        return False
    
    # Create Supabase client with service key
    supabase: Client = create_client(supabase_url, supabase_service_key)
    
    print("🔗 Connected to Supabase with service key")
    
    # Step 1: Create the trigger function
    print("\n📝 Creating trigger function...")
    trigger_function = """
    CREATE OR REPLACE FUNCTION public.handle_new_user()
    RETURNS TRIGGER AS $$
    BEGIN
        INSERT INTO public.users (id, email, full_name, subscription_tier)
        VALUES (
            NEW.id,
            NEW.email,
            COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
            'FREE'
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    
    try:
        # Using the SQL editor endpoint (this may not work directly)
        # We'll need to use the dashboard or a different approach
        print("   ⚠️  Cannot execute complex SQL via API")
        print("   💡 Manual steps required in Supabase Dashboard")
        
        # Alternative: Test if we can at least read the users table
        users = supabase.table('users').select('*').limit(1).execute()
        print(f"   ✅ Can access users table: {len(users.data)} users")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_current_auth_flow():
    """Test the current authentication flow to understand the issue"""
    print("\n🧪 TESTING CURRENT AUTHENTICATION FLOW")
    print("=" * 45)
    
    from supabase import create_client, Client
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_anon_key)
    
    # Test 1: Check existing users
    print("1. Checking existing users...")
    try:
        users = supabase.table('users').select('*').execute()
        print(f"   ✅ Found {len(users.data)} users in public.users table")
        
        if users.data:
            print("   📊 Sample user data:")
            for user in users.data[:2]:
                print(f"      - ID: {user.get('id')}")
                print(f"        Email: {user.get('email')}")
                print(f"        Tier: {user.get('subscription_tier')}")
                print(f"        Created: {user.get('created_at')}")
                print()
    except Exception as e:
        print(f"   ❌ Error reading users: {e}")
    
    # Test 2: Try to create a user manually
    print("2. Testing manual user creation...")
    try:
        # First, let's check if we can get an auth user
        session = supabase.auth.get_session()
        print(f"   Current session: {session}")
        
        # Try to create a test user in public.users
        test_user = {
            'email': 'manualtest@example.com',
            'full_name': 'Manual Test User',
            'subscription_tier': 'FREE'
        }
        
        create_response = supabase.table('users').insert(test_user).execute()
        if create_response.data:
            print(f"   ✅ Manual user creation works: {create_response.data[0]}")
        else:
            print("   ❌ Manual user creation failed")
            
    except Exception as e:
        print(f"   ❌ Manual user creation error: {e}")
    
    # Test 3: Check RLS policies
    print("\n3. Testing RLS policies...")
    try:
        # Try to read with different contexts
        supabase_service = create_client(supabase_url, os.getenv('SUPABASE_SERVICE_KEY'))
        
        service_users = supabase_service.table('users').select('*').execute()
        print(f"   ✅ Service role can read: {len(service_users.data)} users")
        
        anon_users = supabase.table('users').select('*').execute()
        print(f"   ✅ Anonymous role can read: {len(anon_users.data)} users")
        
    except Exception as e:
        print(f"   ❌ RLS policy test error: {e}")
    
    return True

def create_manual_instructions():
    """Create manual instructions for fixing the authentication system"""
    print("\n📋 MANUAL FIX INSTRUCTIONS")
    print("=" * 30)
    
    instructions = """
    Since we cannot execute complex SQL directly via the API, 
    please follow these manual steps in the Supabase Dashboard:
    
    1. Go to https://supabase.com/dashboard
    2. Select your project
    3. Go to "SQL Editor"
    4. Create a new query and paste the following SQL:
    
    -- Step 1: Create the trigger function
    CREATE OR REPLACE FUNCTION public.handle_new_user()
    RETURNS TRIGGER AS $$
    BEGIN
        INSERT INTO public.users (id, email, full_name, subscription_tier)
        VALUES (
            NEW.id,
            NEW.email,
            COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
            'FREE'
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    
    -- Step 2: Create the trigger
    DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
    CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
    
    -- Step 3: Update RLS policies
    DROP POLICY IF EXISTS "Users can create own profile" ON public.users;
    CREATE POLICY "Users can create own profile" ON public.users
        FOR INSERT WITH CHECK (auth.uid() = id);
    
    -- Step 4: Grant permissions
    GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated;
    GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;
    
    5. Run the query
    6. Test user signup from the web interface
    """
    
    print(instructions)
    
    # Save instructions to file
    instructions_file = Path(__file__).parent / "MANUAL_AUTH_FIX_INSTRUCTIONS.md"
    instructions_file.write_text(f"""# VisionSeal Authentication Fix Instructions

{instructions}

## Testing Steps

1. Go to http://localhost:8080/auth.html
2. Click "Sign Up" tab
3. Enter a test email and password
4. Submit the form
5. Check the Supabase dashboard > Authentication > Users
6. Verify the user appears in both auth.users and public.users tables

## Troubleshooting

If the fix doesn't work:
1. Check the PostgreSQL logs in Supabase Dashboard
2. Verify the trigger was created: `SELECT * FROM information_schema.triggers WHERE trigger_name = 'on_auth_user_created';`
3. Test the trigger function manually
4. Check RLS policies: `SELECT * FROM pg_policies WHERE tablename = 'users';`

## Additional Settings

In Supabase Dashboard > Authentication > Settings:
- Confirm new users: DISABLED (for testing)
- Enable email confirmations: DISABLED (for testing)
- Auto-confirm users: ENABLED (for testing)
""")
    
    print(f"\n💾 Instructions saved to: {instructions_file}")
    
    return True

def main():
    """Main function"""
    print("🔐 VISIONSEAL AUTHENTICATION MANUAL FIXER")
    print("This script provides manual instructions to fix authentication")
    print()
    
    # Test current state
    test_current_auth_flow()
    
    # Try API approach (limited)
    apply_fixes_via_supabase_api()
    
    # Provide manual instructions
    create_manual_instructions()
    
    print("\n🎯 SUMMARY")
    print("=" * 20)
    print("✅ Current authentication state analyzed")
    print("✅ Manual fix instructions provided")
    print("✅ Instructions saved to MANUAL_AUTH_FIX_INSTRUCTIONS.md")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Follow the manual instructions in Supabase Dashboard")
    print("2. Test user signup at http://localhost:8080/auth.html")
    print("3. Verify users appear in both auth.users and public.users")
    print("4. Check that the dashboard shows user data correctly")
    
    print(f"\n🔗 Supabase Dashboard: https://supabase.com/dashboard")

if __name__ == "__main__":
    main()