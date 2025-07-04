#!/usr/bin/env python3
"""
Test what URLs are actually in the database and displayed in dashboard
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(os.path.dirname(__file__) + '/src'))

from core.database.supabase_client import supabase_manager

def test_dashboard_urls():
    """Test URLs in database"""
    print("🔍 TESTING DASHBOARD URLS")
    print("=" * 30)
    
    try:
        # Get recent opportunities
        response = supabase_manager.client.table('tender_opportunities').select('*').order('extracted_at', desc=True).limit(10).execute()
        
        if response.data:
            print(f"✅ Found {len(response.data)} recent opportunities")
            
            for i, opp in enumerate(response.data[:5], 1):
                title = opp.get('title', 'No title')[:50]
                url = opp.get('url', 'No URL')
                source = opp.get('source', 'Unknown')
                
                print(f"\n💼 {i}. {source}: {title}...")
                print(f"   🔗 URL: {url}")
                
                # Check if URL is specific or generic
                if url and url != 'N/A':
                    if 'appeloffres.net/appels-offres/' in url and url.split('/')[-1].isdigit():
                        print(f"   ✅ SPECIFIC TuniPages URL (has tender ID)")
                    elif 'ungm.org' in url and ('AdvertisementDetails' in url or 'tenders' in url):
                        print(f"   ✅ SPECIFIC UNGM URL (has tender details)")
                    elif 'ungm.org' in url:
                        print(f"   ⚠️ GENERIC UNGM URL (general page)")
                    elif 'appeloffres.net' in url:
                        print(f"   ⚠️ GENERIC TuniPages URL (general page)")
                    else:
                        print(f"   ❓ OTHER URL")
                else:
                    print(f"   ❌ NO URL or N/A")
                    
            # Test dashboard display
            print(f"\n🌐 DASHBOARD URL TEST:")
            print(f"Visit: http://localhost:8082/dashboard.html")
            print(f"Check if tender titles are clickable and open specific pages")
            
        else:
            print(f"❌ No opportunities found in database")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_dashboard_urls()