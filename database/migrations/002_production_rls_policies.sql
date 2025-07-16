-- Production-Ready RLS Policies for VisionSeal
-- This creates secure policies while allowing legitimate scraper access

-- Drop any existing policies
DROP POLICY IF EXISTS "Allow public insert for scrapers" ON public.tenders;
DROP POLICY IF EXISTS "Allow public update for scrapers" ON public.tenders;
DROP POLICY IF EXISTS "Allow public read access" ON public.tenders;
DROP POLICY IF EXISTS "Allow authenticated full access" ON public.tenders;

-- ===========================================
-- PRODUCTION RLS POLICIES
-- ===========================================

-- 1. Public READ access to active tenders only
CREATE POLICY "Public read active tenders" ON public.tenders
    FOR SELECT USING (status = 'ACTIVE');

-- 2. Authenticated users can read all tenders
CREATE POLICY "Authenticated read all tenders" ON public.tenders
    FOR SELECT USING (auth.role() = 'authenticated');

-- 3. Authenticated users can insert tenders
CREATE POLICY "Authenticated insert tenders" ON public.tenders
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- 4. Authenticated users can update tenders
CREATE POLICY "Authenticated update tenders" ON public.tenders
    FOR UPDATE USING (auth.role() = 'authenticated');

-- 5. Only authenticated users can delete (admin function)
CREATE POLICY "Authenticated delete tenders" ON public.tenders
    FOR DELETE USING (auth.role() = 'authenticated');

-- ===========================================
-- SCRAPER ACCESS STRATEGY
-- ===========================================

-- NOTE: Scrapers should use SUPABASE_SERVICE_KEY which bypasses RLS
-- This provides secure access for automated systems while maintaining
-- proper access controls for public/authenticated users

-- ===========================================
-- ADDITIONAL SECURITY MEASURES
-- ===========================================

-- Create a function to validate tender data quality
CREATE OR REPLACE FUNCTION validate_tender_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate required fields
    IF NEW.title IS NULL OR LENGTH(NEW.title) < 3 THEN
        RAISE EXCEPTION 'Title must be at least 3 characters long';
    END IF;
    
    IF NEW.url IS NULL OR LENGTH(NEW.url) < 10 THEN
        RAISE EXCEPTION 'URL must be at least 10 characters long';
    END IF;
    
    IF NEW.source NOT IN ('UNGM', 'TUNIPAGES', 'MANUAL') THEN
        RAISE EXCEPTION 'Source must be UNGM, TUNIPAGES, or MANUAL';
    END IF;
    
    IF NEW.relevance_score < 0 OR NEW.relevance_score > 100 THEN
        RAISE EXCEPTION 'Relevance score must be between 0 and 100';
    END IF;
    
    -- Prevent suspicious URLs
    IF NEW.url ~ '(javascript:|data:|vbscript:)' THEN
        RAISE EXCEPTION 'Suspicious URL format detected';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for data validation
DROP TRIGGER IF EXISTS validate_tender_data_trigger ON public.tenders;
CREATE TRIGGER validate_tender_data_trigger
    BEFORE INSERT OR UPDATE ON public.tenders
    FOR EACH ROW
    EXECUTE FUNCTION validate_tender_data();

-- ===========================================
-- RATE LIMITING (Optional Enhancement)
-- ===========================================

-- Create table to track API usage
CREATE TABLE IF NOT EXISTS public.api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action TEXT,
    table_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create function to check rate limits
CREATE OR REPLACE FUNCTION check_rate_limit()
RETURNS TRIGGER AS $$
DECLARE
    recent_inserts INTEGER;
BEGIN
    -- Count recent inserts from this user (last 1 minute)
    SELECT COUNT(*) INTO recent_inserts
    FROM public.api_usage
    WHERE user_id = auth.uid()
    AND action = 'INSERT'
    AND table_name = 'tenders'
    AND created_at > NOW() - INTERVAL '1 minute';
    
    -- Allow up to 100 inserts per minute for authenticated users
    IF recent_inserts >= 100 THEN
        RAISE EXCEPTION 'Rate limit exceeded: too many inserts per minute';
    END IF;
    
    -- Log the action
    INSERT INTO public.api_usage (user_id, action, table_name)
    VALUES (auth.uid(), TG_OP, TG_TABLE_NAME);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create rate limiting trigger (optional - uncomment if needed)
-- CREATE TRIGGER rate_limit_trigger
--     BEFORE INSERT OR UPDATE ON public.tenders
--     FOR EACH ROW
--     EXECUTE FUNCTION check_rate_limit();

-- ===========================================
-- GRANTS AND PERMISSIONS
-- ===========================================

-- Grant appropriate permissions
GRANT SELECT ON public.tenders TO anon;
GRANT SELECT ON public.active_tenders TO anon;
GRANT SELECT ON public.recent_tenders TO anon;
GRANT SELECT ON public.high_relevance_tenders TO anon;

GRANT ALL ON public.tenders TO authenticated;
GRANT ALL ON public.active_tenders TO authenticated;
GRANT ALL ON public.recent_tenders TO authenticated;
GRANT ALL ON public.high_relevance_tenders TO authenticated;

-- Grant usage tracking permissions
GRANT SELECT, INSERT ON public.api_usage TO authenticated;

-- ===========================================
-- VERIFICATION
-- ===========================================

-- Show current policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies 
WHERE tablename = 'tenders';

-- Test insert with validation
INSERT INTO public.tenders (
    title,
    description,
    source,
    country,
    organization,
    url,
    relevance_score
) VALUES (
    'Production Security Test',
    'This tender tests the production security setup',
    'MANUAL',
    'Test Country',
    'Test Organization',
    'https://secure.example.com/tender/production-test',
    85.0
);

-- Display security summary
SELECT 
    'Production Security Setup Complete' as status,
    COUNT(*) as total_records,
    COUNT(CASE WHEN title LIKE '%Production Security%' THEN 1 END) as security_test_records
FROM public.tenders;

-- Success message
SELECT '🔐 Production-ready RLS policies and security measures activated!' as message;