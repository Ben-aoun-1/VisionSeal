# VisionSeal Authentication Fix Instructions


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
