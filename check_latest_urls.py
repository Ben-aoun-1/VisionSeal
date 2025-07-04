#!/usr/bin/env python3
"""
Check the latest URLs extracted from both UNGM and TuniPages
"""
import sys, os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, 'src')
from core.database.supabase_client import supabase_manager

def check_latest_urls():
    print("🔍 CHECKING LATEST URL EXTRACTION RESULTS")
    print("=" * 50)
    
    # Get most recent UNGM records
    response = supabase_manager.client.table('tenders').select('*').eq('source', 'UNGM').gte('extracted_at', '2025-07-04T21:50:00').order('extracted_at', desc=True).limit(5).execute()
    
    if response.data:
        print('\n✅ LATEST UNGM RECORDS:')
        for i, t in enumerate(response.data[:5], 1):
            title = t.get('title', 'No title')[:40]
            url = t.get('url', 'No URL')
            
            print(f'{i}. {title}...')
            print(f'   URL: {url}')
            
            generic_url = 'https://www.ungm.org/Public/Notice'
            if url and url != generic_url:
                if 'AdvertisementDetails' in url or 'Keywords=' in url:
                    print(f'   ✅ IMPROVED URL (specific or search)')
                else:
                    print(f'   ⚠️ Different URL but unknown type')
            else:
                print(f'   ❌ Still generic URL')
            print()
    else:
        print('\n❌ No latest UNGM records found')
    
    # Get latest TuniPages records
    response2 = supabase_manager.client.table('tenders').select('*').eq('source', 'TUNIPAGES').gte('extracted_at', '2025-07-04').order('extracted_at', desc=True).limit(5).execute()
    
    if response2.data:
        print('\n✅ LATEST TUNIPAGES RECORDS:')
        for i, t in enumerate(response2.data[:5], 1):
            title = t.get('title', 'No title')[:40]
            url = t.get('url', 'No URL')
            
            print(f'{i}. {title}...')
            print(f'   URL: {url}')
            
            if 'appeloffres.net/appels-offres/' in url and url.split('/')[-1].isdigit():
                print(f'   ✅ SPECIFIC URL with tender ID: {url.split("/")[-1]}')
            else:
                print(f'   ❌ Generic URL')
            print()
    else:
        print('\n❌ No latest TuniPages records found')
    
    print("\n🌐 DASHBOARD TEST:")
    print("Visit: http://localhost:8082/dashboard.html")
    print("✅ TuniPages titles should link to specific tender pages")
    print("⚠️ UNGM titles may still link to search pages (better than generic)")

if __name__ == "__main__":
    check_latest_urls()