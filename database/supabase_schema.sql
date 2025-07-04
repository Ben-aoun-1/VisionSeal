-- VisionSeal Supabase Database Schema
-- Optimized for African tender opportunity SaaS

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Tender sources enum
CREATE TYPE tender_source AS ENUM ('UNGM', 'TUNIPAGES', 'OTHER');

-- Tender status enum  
CREATE TYPE tender_status AS ENUM ('ACTIVE', 'EXPIRED', 'AWARDED', 'CANCELLED');

-- User subscription tiers
CREATE TYPE subscription_tier AS ENUM ('FREE', 'BASIC', 'PREMIUM', 'ENTERPRISE');

-- ====================================
-- CORE TABLES
-- ====================================

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    country TEXT,
    subscription_tier subscription_tier DEFAULT 'FREE',
    subscription_expires_at TIMESTAMPTZ,
    api_key UUID DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tender opportunities table
CREATE TABLE public.tenders (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    source tender_source NOT NULL,
    country TEXT,
    organization TEXT,
    deadline TEXT, -- Keep as text since formats vary
    url TEXT,
    reference TEXT,
    status tender_status DEFAULT 'ACTIVE',
    relevance_score DECIMAL(5,2) DEFAULT 0,
    publication_date TEXT,
    notice_type TEXT,
    estimated_budget TEXT,
    currency TEXT,
    contact_email TEXT,
    document_links JSONB DEFAULT '[]',
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', 
            COALESCE(title, '') || ' ' || 
            COALESCE(description, '') || ' ' ||
            COALESCE(organization, '') || ' ' ||
            COALESCE(country, '')
        )
    ) STORED
);

-- Automation sessions table
CREATE TABLE public.automation_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    source tender_source NOT NULL,
    status TEXT NOT NULL,
    tenders_found INTEGER DEFAULT 0,
    tenders_processed INTEGER DEFAULT 0,
    pages_processed INTEGER DEFAULT 0,
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User activity tracking
CREATE TABLE public.user_activity (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Saved searches
CREATE TABLE public.saved_searches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id),
    name TEXT NOT NULL,
    keywords TEXT[],
    countries TEXT[],
    sources tender_source[],
    min_relevance_score DECIMAL(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User favorites
CREATE TABLE public.user_favorites (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id),
    tender_id UUID REFERENCES public.tenders(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, tender_id)
);

-- ====================================
-- INDEXES FOR PERFORMANCE
-- ====================================

-- Tenders search and filtering indexes
CREATE INDEX idx_tenders_source ON public.tenders(source);
CREATE INDEX idx_tenders_country ON public.tenders(country);
CREATE INDEX idx_tenders_status ON public.tenders(status);
CREATE INDEX idx_tenders_relevance_score ON public.tenders(relevance_score DESC);
CREATE INDEX idx_tenders_created_at ON public.tenders(created_at DESC);
CREATE INDEX idx_tenders_search_vector ON public.tenders USING gin(search_vector);
CREATE INDEX idx_tenders_organization ON public.tenders(organization);

-- Composite indexes for common queries
CREATE INDEX idx_tenders_active_african ON public.tenders(status, country, relevance_score DESC) 
    WHERE status = 'ACTIVE' AND relevance_score > 0;

-- User activity indexes
CREATE INDEX idx_user_activity_user_id ON public.user_activity(user_id, created_at DESC);
CREATE INDEX idx_automation_sessions_created_at ON public.automation_sessions(created_at DESC);

-- ====================================
-- ROW LEVEL SECURITY (RLS)
-- ====================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_favorites ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Tenders are publicly readable but only automation can insert
CREATE POLICY "Tenders are publicly readable" ON public.tenders
    FOR SELECT USING (true);

-- Only service role can insert tenders (for automation)
CREATE POLICY "Service role can insert tenders" ON public.tenders
    FOR INSERT WITH CHECK (
        auth.jwt() ->> 'role' = 'service_role' OR
        auth.jwt() ->> 'email' = 'automation@visionseal.com'
    );

-- Users can manage their own saved searches and favorites
CREATE POLICY "Users can manage own searches" ON public.saved_searches
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own favorites" ON public.user_favorites  
    FOR ALL USING (auth.uid() = user_id);

-- User activity is private to each user
CREATE POLICY "Users can view own activity" ON public.user_activity
    FOR SELECT USING (auth.uid() = user_id);

-- ====================================
-- FUNCTIONS
-- ====================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenders_updated_at 
    BEFORE UPDATE ON public.tenders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_searches_updated_at 
    BEFORE UPDATE ON public.saved_searches 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to search tenders with full-text search
CREATE OR REPLACE FUNCTION search_tenders(
    search_query TEXT DEFAULT '',
    filter_countries TEXT[] DEFAULT NULL,
    filter_sources tender_source[] DEFAULT NULL,
    min_score DECIMAL DEFAULT 0,
    limit_count INTEGER DEFAULT 50,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    description TEXT,
    source tender_source,
    country TEXT,
    organization TEXT,
    deadline TEXT,
    url TEXT,
    relevance_score DECIMAL,
    created_at TIMESTAMPTZ,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.description,
        t.source,
        t.country,
        t.organization,
        t.deadline,
        t.url,
        t.relevance_score,
        t.created_at,
        CASE 
            WHEN search_query = '' THEN 1.0
            ELSE ts_rank(t.search_vector, plainto_tsquery('english', search_query))
        END as rank
    FROM public.tenders t
    WHERE 
        t.status = 'ACTIVE'
        AND t.relevance_score >= min_score
        AND (filter_countries IS NULL OR t.country = ANY(filter_countries))
        AND (filter_sources IS NULL OR t.source = ANY(filter_sources))
        AND (
            search_query = '' OR 
            t.search_vector @@ plainto_tsquery('english', search_query)
        )
    ORDER BY 
        CASE WHEN search_query = '' THEN t.created_at ELSE NULL END DESC,
        CASE WHEN search_query != '' THEN rank ELSE NULL END DESC,
        t.relevance_score DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- ====================================
-- VIEWS FOR COMMON QUERIES
-- ====================================

-- Recent opportunities view
CREATE VIEW recent_opportunities AS
SELECT 
    id,
    title,
    source,
    country,
    organization,
    deadline,
    relevance_score,
    created_at
FROM public.tenders 
WHERE status = 'ACTIVE' 
ORDER BY created_at DESC;

-- High priority African opportunities
CREATE VIEW high_priority_opportunities AS
SELECT 
    id,
    title,
    source,
    country,
    organization,
    deadline,
    relevance_score,
    created_at
FROM public.tenders 
WHERE 
    status = 'ACTIVE' 
    AND relevance_score >= 70
ORDER BY relevance_score DESC, created_at DESC;

-- Automation statistics view
CREATE VIEW automation_stats AS
SELECT 
    source,
    DATE(created_at) as date,
    COUNT(*) as sessions_count,
    SUM(tenders_found) as total_found,
    SUM(tenders_processed) as total_processed,
    AVG(tenders_found) as avg_found_per_session
FROM public.automation_sessions 
GROUP BY source, DATE(created_at)
ORDER BY date DESC;

-- ====================================
-- SAMPLE DATA (for testing)
-- ====================================

-- Insert sample user (will be created via Supabase Auth)
-- This is just for reference - actual users created through auth flow

-- Insert sample automation session
INSERT INTO public.automation_sessions (
    session_id,
    source,
    status,
    tenders_found,
    tenders_processed,
    pages_processed
) VALUES (
    'ungm_sample_' || extract(epoch from now()),
    'UNGM',
    'completed',
    5,
    5,
    1
);

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- Grant permissions to service role (for automation)
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;