-- FRESH START - Complete Database Rebuild
-- This script completely drops and recreates the VisionSeal database

-- ===========================================
-- STEP 1: DROP EVERYTHING
-- ===========================================

-- Drop all views first
DROP VIEW IF EXISTS active_tenders CASCADE;
DROP VIEW IF EXISTS recent_tenders CASCADE;
DROP VIEW IF EXISTS high_relevance_tenders CASCADE;

-- Drop all functions
DROP FUNCTION IF EXISTS update_tenders_search_vector() CASCADE;
DROP FUNCTION IF EXISTS clean_expired_tenders() CASCADE;
DROP FUNCTION IF EXISTS safe_date_convert(TEXT) CASCADE;

-- Drop all tables
DROP TABLE IF EXISTS public.tenders CASCADE;
DROP TABLE IF EXISTS public.tenders_backup CASCADE;
DROP TABLE IF EXISTS public.automation_sessions CASCADE;
DROP TABLE IF EXISTS public.automation_stats CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- ===========================================
-- STEP 2: CREATE FRESH TENDERS TABLE
-- ===========================================

-- Create optimized tenders table for scraped data
CREATE TABLE public.tenders (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core tender information
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    source TEXT NOT NULL CHECK (source IN ('UNGM', 'TUNIPAGES', 'MANUAL')),
    
    -- Location and organization
    country TEXT NOT NULL DEFAULT '',
    organization TEXT NOT NULL DEFAULT '',
    
    -- Dates (using proper DATE types)
    deadline DATE,
    publication_date DATE,
    
    -- URLs and references
    url TEXT UNIQUE NOT NULL,
    reference TEXT DEFAULT '',
    
    -- Status and classification
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'EXPIRED', 'CANCELLED', 'AWARDED')),
    notice_type TEXT DEFAULT 'Request for Proposal',
    
    -- Scoring and relevance
    relevance_score DECIMAL(5,2) DEFAULT 50.0 CHECK (relevance_score >= 0 AND relevance_score <= 100),
    
    -- Financial information
    estimated_budget TEXT DEFAULT '',
    currency TEXT DEFAULT '',
    
    -- Contact information
    contact_email TEXT DEFAULT '',
    
    -- Additional data (JSON for flexibility)
    document_links JSONB DEFAULT '[]',
    additional_data JSONB DEFAULT '{}',
    
    -- Metadata
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Full text search
    search_vector TSVECTOR
);

-- ===========================================
-- STEP 3: CREATE INDEXES
-- ===========================================

CREATE INDEX idx_tenders_source ON public.tenders(source);
CREATE INDEX idx_tenders_country ON public.tenders(country);
CREATE INDEX idx_tenders_organization ON public.tenders(organization);
CREATE INDEX idx_tenders_deadline ON public.tenders(deadline);
CREATE INDEX idx_tenders_status ON public.tenders(status);
CREATE INDEX idx_tenders_relevance_score ON public.tenders(relevance_score DESC);
CREATE INDEX idx_tenders_search_vector ON public.tenders USING GIN(search_vector);
CREATE INDEX idx_tenders_created_at ON public.tenders(created_at DESC);
CREATE INDEX idx_tenders_url ON public.tenders(url);
CREATE INDEX idx_tenders_extracted_at ON public.tenders(extracted_at DESC);

-- ===========================================
-- STEP 4: CREATE FUNCTIONS
-- ===========================================

-- Function to automatically update search_vector and updated_at
CREATE OR REPLACE FUNCTION update_tenders_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.description, '') || ' ' || 
        COALESCE(NEW.organization, '') || ' ' || 
        COALESCE(NEW.country, '')
    );
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old expired tenders
CREATE OR REPLACE FUNCTION clean_expired_tenders()
RETURNS void AS $$
BEGIN
    -- Update status of expired tenders
    UPDATE public.tenders 
    SET status = 'EXPIRED', updated_at = NOW()
    WHERE deadline IS NOT NULL 
    AND deadline < CURRENT_DATE 
    AND status = 'ACTIVE';
    
    -- Optional: Delete very old expired tenders (older than 1 year)
    -- DELETE FROM public.tenders 
    -- WHERE status = 'EXPIRED' 
    -- AND deadline < CURRENT_DATE - INTERVAL '1 year';
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- STEP 5: CREATE TRIGGERS
-- ===========================================

CREATE TRIGGER update_tenders_search_vector_trigger
    BEFORE INSERT OR UPDATE ON public.tenders
    FOR EACH ROW
    EXECUTE FUNCTION update_tenders_search_vector();

-- ===========================================
-- STEP 6: CREATE VIEWS
-- ===========================================

-- Active tenders view
CREATE VIEW active_tenders AS
SELECT * FROM public.tenders 
WHERE status = 'ACTIVE' 
AND (deadline IS NULL OR deadline >= CURRENT_DATE)
ORDER BY relevance_score DESC, deadline ASC;

-- Recent tenders view (last 7 days)
CREATE VIEW recent_tenders AS
SELECT * FROM public.tenders 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY created_at DESC;

-- High relevance tenders view
CREATE VIEW high_relevance_tenders AS
SELECT * FROM public.tenders 
WHERE relevance_score >= 70
AND status = 'ACTIVE'
ORDER BY relevance_score DESC, deadline ASC;

-- ===========================================
-- STEP 7: SET UP PERMISSIONS
-- ===========================================

-- Enable Row Level Security
ALTER TABLE public.tenders ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY "Public read access to active tenders" ON public.tenders
    FOR SELECT USING (status = 'ACTIVE');

CREATE POLICY "Authenticated users can insert tenders" ON public.tenders
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can update tenders" ON public.tenders
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Grant permissions
GRANT SELECT ON public.tenders TO anon;
GRANT SELECT ON public.active_tenders TO anon;
GRANT SELECT ON public.recent_tenders TO anon;
GRANT SELECT ON public.high_relevance_tenders TO anon;

GRANT ALL ON public.tenders TO authenticated;
GRANT ALL ON public.active_tenders TO authenticated;
GRANT ALL ON public.recent_tenders TO authenticated;
GRANT ALL ON public.high_relevance_tenders TO authenticated;

-- ===========================================
-- STEP 8: ADD COMMENTS
-- ===========================================

COMMENT ON TABLE public.tenders IS 'Tender opportunities scraped from UNGM, TuniPages, and other sources';
COMMENT ON COLUMN public.tenders.relevance_score IS 'Calculated relevance score (0-100) based on keywords, country, and organization';
COMMENT ON COLUMN public.tenders.search_vector IS 'Full-text search vector for efficient searching';
COMMENT ON COLUMN public.tenders.additional_data IS 'Flexible JSON field for source-specific data';
COMMENT ON COLUMN public.tenders.document_links IS 'JSON array of document download links';

-- ===========================================
-- STEP 9: VERIFICATION
-- ===========================================

-- Insert a test record to verify everything works
INSERT INTO public.tenders (
    title,
    description,
    source,
    country,
    organization,
    url,
    relevance_score
) VALUES (
    'Test Tender - Database Setup Complete',
    'This is a test tender to verify the database setup is working correctly',
    'MANUAL',
    'Test Country',
    'Test Organization',
    'https://test.example.com/tender/1',
    75.0
);

-- Display setup summary
SELECT 
    'Fresh Database Setup Complete' as status,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_records,
    AVG(relevance_score) as avg_relevance_score,
    NOW() as setup_time
FROM public.tenders;

-- Show table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'tenders' 
ORDER BY ordinal_position;

-- Show indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'tenders';

-- Show triggers
SELECT 
    trigger_name,
    event_manipulation,
    action_statement
FROM information_schema.triggers 
WHERE event_object_table = 'tenders';

-- Show views
SELECT 
    table_name,
    view_definition
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name LIKE '%tenders%';

-- Final message
SELECT '🎉 Fresh database setup complete! Ready for scraper integration!' as message;