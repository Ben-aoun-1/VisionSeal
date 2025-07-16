#!/usr/bin/env python3
"""
Simple script to create saved_tenders table
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_table():
    """Create the saved_tenders table"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        sys.exit(1)
    
    try:
        # Create client with service key (bypasses RLS)
        client = create_client(url, service_key)
        
        # Try to insert a test record to create table structure
        print("Attempting to create table structure...")
        
        # Insert a dummy record to force table creation
        dummy_data = {
            "user_id": "00000000-0000-0000-0000-000000000000",
            "tender_id": "test_tender_id",
            "notes": "test note",
            "saved_at": "2025-01-01T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
        
        # This will fail if table doesn't exist, so we'll create it manually
        try:
            result = client.table('saved_tenders').insert(dummy_data).execute()
            print("✅ Table already exists!")
            
            # Clean up the dummy record
            client.table('saved_tenders').delete().eq('tender_id', 'test_tender_id').execute()
            
        except Exception as e:
            print(f"Table doesn't exist: {e}")
            print("\nTo create the table, please run this SQL in your Supabase SQL Editor:")
            print("=" * 60)
            print("""
CREATE TABLE IF NOT EXISTS saved_tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tender_id TEXT NOT NULL,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, tender_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_tenders_user_id ON saved_tenders(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_tenders_tender_id ON saved_tenders(tender_id);
CREATE INDEX IF NOT EXISTS idx_saved_tenders_saved_at ON saved_tenders(saved_at DESC);
CREATE INDEX IF NOT EXISTS idx_saved_tenders_user_saved_at ON saved_tenders(user_id, saved_at DESC);

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
""")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_table()