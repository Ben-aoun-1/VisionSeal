-- Fix VisionSeal Authentication Issues
-- This script addresses the user signup problems

-- ====================================
-- 1. UPDATE RLS POLICIES
-- ====================================

-- Drop existing problematic policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;

-- Create better policies that allow user creation
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- CRITICAL: Allow users to INSERT their own profile
CREATE POLICY "Users can create own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- ====================================
-- 2. CREATE TRIGGER FUNCTION
-- ====================================

-- Function to automatically create user profile when user signs up
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

-- ====================================
-- 3. CREATE TRIGGER
-- ====================================

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create trigger to automatically create user profile
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ====================================
-- 4. UPDATE EXISTING POLICIES FOR COMPATIBILITY
-- ====================================

-- Make sure automation sessions can still be created
DROP POLICY IF EXISTS "Service role can insert tenders" ON public.tenders;
CREATE POLICY "Service role can insert tenders" ON public.tenders
    FOR INSERT WITH CHECK (
        auth.jwt() ->> 'role' = 'service_role' OR
        auth.jwt() ->> 'email' = 'automation@visionseal.com' OR
        auth.role() = 'service_role'
    );

-- ====================================
-- 5. GRANT NECESSARY PERMISSIONS
-- ====================================

-- Grant execute permission on the trigger function
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;

-- Ensure the trigger can access auth.users
GRANT SELECT ON auth.users TO authenticated;
GRANT SELECT ON auth.users TO service_role;

-- ====================================
-- 6. TEST THE SETUP
-- ====================================

-- Test query to verify policies are working
-- This should show the current user policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'users' AND schemaname = 'public'
ORDER BY policyname;

-- Show current triggers
SELECT trigger_name, event_manipulation, event_object_schema, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';

-- Test RLS policies
SELECT current_setting('row_security');

COMMIT;