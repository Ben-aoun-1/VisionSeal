-- API Support Functions for React Frontend
-- Creates database functions to support statistics and aggregations

-- Function to get sources breakdown
CREATE OR REPLACE FUNCTION get_sources_breakdown()
RETURNS TABLE(source TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.source,
        COUNT(*) as count
    FROM public.tenders t
    GROUP BY t.source
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get countries breakdown
CREATE OR REPLACE FUNCTION get_countries_breakdown()
RETURNS TABLE(country TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.country,
        COUNT(*) as count
    FROM public.tenders t
    WHERE t.country IS NOT NULL 
    AND t.country != ''
    GROUP BY t.country
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get organizations breakdown
CREATE OR REPLACE FUNCTION get_organizations_breakdown()
RETURNS TABLE(organization TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.organization,
        COUNT(*) as count
    FROM public.tenders t
    WHERE t.organization IS NOT NULL 
    AND t.organization != ''
    GROUP BY t.organization
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get average relevance score
CREATE OR REPLACE FUNCTION get_avg_relevance_score()
RETURNS TABLE(avg_score NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT AVG(relevance_score) as avg_score
    FROM public.tenders;
END;
$$ LANGUAGE plpgsql;

-- Function to get tender counts by status
CREATE OR REPLACE FUNCTION get_status_breakdown()
RETURNS TABLE(status TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.status,
        COUNT(*) as count
    FROM public.tenders t
    GROUP BY t.status
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get recent tenders (last N days)
CREATE OR REPLACE FUNCTION get_recent_tenders(days_back INTEGER DEFAULT 7)
RETURNS TABLE(
    id UUID,
    title TEXT,
    organization TEXT,
    country TEXT,
    source TEXT,
    relevance_score DECIMAL,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.organization,
        t.country,
        t.source,
        t.relevance_score,
        t.created_at
    FROM public.tenders t
    WHERE t.created_at >= NOW() - INTERVAL '1 day' * days_back
    ORDER BY t.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get high-relevance tenders
CREATE OR REPLACE FUNCTION get_high_relevance_tenders(min_score DECIMAL DEFAULT 75.0)
RETURNS TABLE(
    id UUID,
    title TEXT,
    organization TEXT,
    country TEXT,
    source TEXT,
    relevance_score DECIMAL,
    deadline DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.organization,
        t.country,
        t.source,
        t.relevance_score,
        t.deadline
    FROM public.tenders t
    WHERE t.relevance_score >= min_score
    AND t.status = 'ACTIVE'
    ORDER BY t.relevance_score DESC, t.deadline ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to search tenders with full-text search
CREATE OR REPLACE FUNCTION search_tenders(
    search_term TEXT,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE(
    id UUID,
    title TEXT,
    description TEXT,
    organization TEXT,
    country TEXT,
    source TEXT,
    relevance_score DECIMAL,
    deadline DATE,
    url TEXT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.description,
        t.organization,
        t.country,
        t.source,
        t.relevance_score,
        t.deadline,
        t.url,
        ts_rank(t.search_vector, plainto_tsquery('english', search_term)) as rank
    FROM public.tenders t
    WHERE t.search_vector @@ plainto_tsquery('english', search_term)
    AND t.status = 'ACTIVE'
    ORDER BY rank DESC, t.relevance_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get tender analytics by date range
CREATE OR REPLACE FUNCTION get_tender_analytics(
    start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    date DATE,
    total_added INTEGER,
    avg_relevance_score DECIMAL,
    sources_count INTEGER,
    countries_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(t.created_at) as date,
        COUNT(*)::INTEGER as total_added,
        AVG(t.relevance_score) as avg_relevance_score,
        COUNT(DISTINCT t.source)::INTEGER as sources_count,
        COUNT(DISTINCT t.country)::INTEGER as countries_count
    FROM public.tenders t
    WHERE DATE(t.created_at) >= start_date
    AND DATE(t.created_at) <= end_date
    GROUP BY DATE(t.created_at)
    ORDER BY date DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions for API functions
GRANT EXECUTE ON FUNCTION get_sources_breakdown() TO anon;
GRANT EXECUTE ON FUNCTION get_countries_breakdown() TO anon;
GRANT EXECUTE ON FUNCTION get_organizations_breakdown() TO anon;
GRANT EXECUTE ON FUNCTION get_avg_relevance_score() TO anon;
GRANT EXECUTE ON FUNCTION get_status_breakdown() TO anon;
GRANT EXECUTE ON FUNCTION get_recent_tenders(INTEGER) TO anon;
GRANT EXECUTE ON FUNCTION get_high_relevance_tenders(DECIMAL) TO anon;
GRANT EXECUTE ON FUNCTION search_tenders(TEXT, INTEGER) TO anon;
GRANT EXECUTE ON FUNCTION get_tender_analytics(DATE, DATE) TO anon;

-- Create additional indexes for API performance
CREATE INDEX IF NOT EXISTS idx_tenders_status_created_at ON public.tenders(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tenders_relevance_status ON public.tenders(relevance_score DESC, status);
CREATE INDEX IF NOT EXISTS idx_tenders_deadline_status ON public.tenders(deadline, status);
CREATE INDEX IF NOT EXISTS idx_tenders_source_created_at ON public.tenders(source, created_at DESC);

-- Test the functions
SELECT 'API Functions Created Successfully' as message;

-- Show sample data from functions
SELECT 'Sources Breakdown:' as info;
SELECT * FROM get_sources_breakdown();

SELECT 'Countries Breakdown (Top 5):' as info;
SELECT * FROM get_countries_breakdown() LIMIT 5;

SELECT 'Average Relevance Score:' as info;
SELECT * FROM get_avg_relevance_score();

SELECT 'Recent Tenders Count:' as info;
SELECT COUNT(*) as recent_count FROM get_recent_tenders(7);