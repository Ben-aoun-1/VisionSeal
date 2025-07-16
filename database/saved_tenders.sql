-- Saved Tenders Table
-- This table tracks which tenders users have saved for later reference

CREATE TABLE IF NOT EXISTS saved_tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tender_id TEXT NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT, -- Optional user notes about the tender
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

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_saved_tenders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updating updated_at
CREATE TRIGGER trigger_update_saved_tenders_updated_at
    BEFORE UPDATE ON saved_tenders
    FOR EACH ROW
    EXECUTE FUNCTION update_saved_tenders_updated_at();

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

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON saved_tenders TO authenticated;
GRANT SELECT ON saved_tenders_detailed TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Add some helpful comments
COMMENT ON TABLE saved_tenders IS 'Stores user saved tender references';
COMMENT ON COLUMN saved_tenders.user_id IS 'Reference to the user who saved the tender';
COMMENT ON COLUMN saved_tenders.tender_id IS 'Reference to the saved tender';
COMMENT ON COLUMN saved_tenders.saved_at IS 'When the tender was saved';
COMMENT ON COLUMN saved_tenders.notes IS 'Optional user notes about the tender';
COMMENT ON VIEW saved_tenders_detailed IS 'Saved tenders with full tender details joined';