-- VisionSeal Supabase Database Setup
-- This script creates the necessary tables and security policies for VisionSeal authentication

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    phone TEXT,
    country TEXT,
    role TEXT DEFAULT 'user',
    status TEXT DEFAULT 'pending_verification',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Users can read their own profile
CREATE POLICY "Users can read own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- Service role can insert profiles (for registration)
CREATE POLICY "Service role can insert profiles" ON user_profiles
    FOR INSERT WITH CHECK (true);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_status ON user_profiles(status);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- Create function to handle user registration
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (
        id, 
        email, 
        first_name, 
        last_name, 
        company, 
        phone, 
        country, 
        role, 
        status, 
        preferences
    ) VALUES (
        NEW.id, 
        NEW.email, 
        COALESCE(NEW.raw_user_meta_data->>'first_name', ''), 
        COALESCE(NEW.raw_user_meta_data->>'last_name', ''), 
        NEW.raw_user_meta_data->>'company', 
        NEW.raw_user_meta_data->>'phone', 
        NEW.raw_user_meta_data->>'country', 
        COALESCE(NEW.raw_user_meta_data->>'role', 'user'), 
        'pending_verification', 
        COALESCE(NEW.raw_user_meta_data->'preferences', '{}'::jsonb)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for automatic profile creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON user_profiles TO anon, authenticated;
GRANT SELECT ON user_profiles TO service_role;
GRANT INSERT, UPDATE, DELETE ON user_profiles TO service_role;

-- ============================================
-- SAVED TENDERS SCHEMA
-- ============================================

-- Create saved_tenders table
CREATE TABLE IF NOT EXISTS saved_tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tender_id TEXT NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure a user can only save a tender once
    UNIQUE(user_id, tender_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_saved_tenders_user_id ON saved_tenders(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_tenders_tender_id ON saved_tenders(tender_id);
CREATE INDEX IF NOT EXISTS idx_saved_tenders_saved_at ON saved_tenders(saved_at DESC);
CREATE INDEX IF NOT EXISTS idx_saved_tenders_user_saved_at ON saved_tenders(user_id, saved_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE saved_tenders ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see their own saved tenders
CREATE POLICY "Users can view their own saved tenders" ON saved_tenders
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own saved tenders
CREATE POLICY "Users can save tenders for themselves" ON saved_tenders
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own saved tenders
CREATE POLICY "Users can update their own saved tenders" ON saved_tenders
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own saved tenders
CREATE POLICY "Users can delete their own saved tenders" ON saved_tenders
    FOR DELETE USING (auth.uid() = user_id);

-- Create trigger for updating updated_at
CREATE TRIGGER trigger_update_saved_tenders_updated_at
    BEFORE UPDATE ON saved_tenders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for saved tenders with tender details
CREATE OR REPLACE VIEW saved_tenders_detailed AS
SELECT 
    st.id as saved_tender_id,
    st.user_id,
    st.tender_id,
    st.saved_at,
    st.notes,
    st.created_at,
    st.updated_at,
    t.title,
    t.description,
    t.source,
    t.country,
    t.organization,
    t.deadline,
    t.publication_date,
    t.url,
    t.reference,
    t.status,
    t.notice_type,
    t.relevance_score,
    t.estimated_budget,
    t.currency,
    t.contact_email,
    t.extracted_at as tender_extracted_at,
    t.created_at as tender_created_at,
    t.updated_at as tender_updated_at
FROM saved_tenders st
JOIN tenders t ON st.tender_id = t.id;

-- Grant necessary permissions for saved_tenders
GRANT SELECT, INSERT, UPDATE, DELETE ON saved_tenders TO authenticated;
GRANT SELECT ON saved_tenders_detailed TO authenticated;

-- Add comments
COMMENT ON TABLE saved_tenders IS 'Stores user saved tender references';
COMMENT ON COLUMN saved_tenders.user_id IS 'Reference to the user who saved the tender';
COMMENT ON COLUMN saved_tenders.tender_id IS 'Reference to the saved tender';
COMMENT ON COLUMN saved_tenders.saved_at IS 'When the tender was saved';
COMMENT ON COLUMN saved_tenders.notes IS 'Optional user notes about the tender';
COMMENT ON VIEW saved_tenders_detailed IS 'Saved tenders with full tender details joined';