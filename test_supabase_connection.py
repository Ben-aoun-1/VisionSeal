#!/usr/bin/env python3
"""
Test Supabase connection and basic operations
"""
import sys
import asyncio
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_supabase_connection():
    """Test basic Supabase functionality"""
    print("🧪 TESTING SUPABASE CONNECTION")
    print("=" * 40)
    
    try:
        from core.database.supabase_client import supabase_manager
        
        # Test 1: Basic connection
        print("🔗 Testing basic connection...")
        health = await supabase_manager.health_check()
        print(f"   Connection: {'✅ Working' if health else '❌ Failed'}")
        
        if not health:
            print("❌ Connection failed - check your credentials")
            return False
        
        # Test 2: Insert a sample tender
        print("\n📝 Testing tender insertion...")
        sample_tender = {
            'title': 'Test Consulting Opportunity - Nigeria',
            'description': 'Sample tender for testing Supabase integration with VisionSeal',
            'source': 'UNGM',
            'country': 'Nigeria',
            'organization': 'World Bank Group',
            'deadline': '2024-03-15',
            'url': 'https://example.com/tender/test-123',
            'reference': 'TEST-SUPABASE-001',
            'status': 'ACTIVE',
            'relevance_score': 85.5,
            'publication_date': '2024-02-15',
            'notice_type': 'Request for Proposal',
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        result = await supabase_manager.insert_tender(sample_tender, use_service_key=True)
        if result:
            print(f"   ✅ Sample tender inserted with ID: {result.get('id')}")
        else:
            print("   ❌ Failed to insert sample tender")
            return False
        
        # Test 3: Fetch recent tenders
        print("\n📊 Testing data retrieval...")
        recent = await supabase_manager.get_recent_tenders(limit=5)
        print(f"   ✅ Found {len(recent)} recent tenders")
        
        for i, tender in enumerate(recent[:3], 1):
            print(f"   {i}. {tender['title'][:60]}...")
            print(f"      Country: {tender['country']} | Score: {tender['relevance_score']}")
        
        # Test 4: Search functionality
        print("\n🔍 Testing search functionality...")
        search_results = await supabase_manager.search_tenders(
            query="consulting Nigeria",
            min_score=50,
            limit=3
        )
        print(f"   ✅ Search found {len(search_results)} matching tenders")
        
        for i, tender in enumerate(search_results, 1):
            print(f"   {i}. {tender['title'][:50]}... (Score: {tender['relevance_score']})")
        
        # Test 5: Automation session logging
        print("\n📋 Testing automation session logging...")
        session_data = {
            'session_id': f'test_session_{int(datetime.utcnow().timestamp())}',
            'source': 'UNGM',
            'status': 'completed',
            'tenders_found': 3,
            'tenders_processed': 3,
            'pages_processed': 1,
            'start_time': datetime.utcnow().isoformat(),
            'end_time': datetime.utcnow().isoformat()
        }
        
        session_result = await supabase_manager.insert_automation_session(session_data)
        if session_result:
            print(f"   ✅ Automation session logged with ID: {session_result.get('id')}")
        else:
            print("   ❌ Failed to log automation session")
        
        # Test 6: Get automation stats
        print("\n📈 Testing automation statistics...")
        stats = await supabase_manager.get_automation_stats(days=7)
        print(f"   ✅ Automation stats retrieved:")
        print(f"      Total sessions: {stats.get('total_sessions', 0)}")
        print(f"      Successful sessions: {stats.get('successful_sessions', 0)}")
        print(f"      Total tenders found: {stats.get('total_tenders_found', 0)}")
        print(f"      Total tenders processed: {stats.get('total_tenders_processed', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_bulk_insert():
    """Test bulk insertion capabilities"""
    print("\n🚀 TESTING BULK INSERT")
    print("=" * 30)
    
    try:
        from core.database.supabase_client import supabase_manager
        
        # Create multiple sample tenders
        sample_tenders = []
        african_countries = ['Nigeria', 'Ghana', 'Kenya', 'South Africa', 'Morocco']
        
        for i, country in enumerate(african_countries, 1):
            tender = {
                'title': f'Bulk Test Consulting Project {i} - {country}',
                'description': f'Sample bulk insert tender for {country} market analysis',
                'source': 'UNGM',
                'country': country,
                'organization': f'{country} Development Bank',
                'deadline': '2024-04-30',
                'url': f'https://example.com/bulk-test-{i}',
                'reference': f'BULK-TEST-{i:03d}',
                'status': 'ACTIVE',
                'relevance_score': 70.0 + (i * 5),  # Varying scores
                'publication_date': '2024-02-20',
                'notice_type': 'Expression of Interest',
                'extracted_at': datetime.utcnow().isoformat()
            }
            sample_tenders.append(tender)
        
        # Bulk insert
        print(f"📦 Bulk inserting {len(sample_tenders)} tenders...")
        saved_count = await supabase_manager.bulk_insert_tenders(sample_tenders, use_service_key=True)
        print(f"   ✅ Successfully saved {saved_count}/{len(sample_tenders)} tenders")
        
        return saved_count > 0
        
    except Exception as e:
        print(f"❌ Bulk insert test failed: {str(e)}")
        return False

async def main():
    """Run all Supabase tests"""
    print("🧪 SUPABASE INTEGRATION TEST SUITE")
    print("Testing VisionSeal with real Supabase backend")
    print()
    
    # Check environment variables
    print("🔧 Checking configuration...")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon = os.getenv('SUPABASE_ANON_KEY')
    supabase_service = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url:
        print("❌ SUPABASE_URL not set")
        return
    if not supabase_anon:
        print("❌ SUPABASE_ANON_KEY not set")
        return
    if not supabase_service:
        print("❌ SUPABASE_SERVICE_KEY not set")
        return
    
    print(f"   ✅ URL: {supabase_url}")
    print(f"   ✅ Anon Key: {supabase_anon[:20]}...")
    print(f"   ✅ Service Key: {supabase_service[:20]}...")
    print()
    
    # Run tests
    test1_passed = await test_supabase_connection()
    test2_passed = await test_bulk_insert()
    
    print("\n" + "=" * 50)
    print("🎯 SUPABASE TEST RESULTS")
    print("=" * 50)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Supabase integration is working perfectly")
        print("✅ Ready for production scraping")
        print("✅ Database operations confirmed")
        print("✅ Bulk insert capabilities verified")
        
        print("\n🚀 NEXT STEPS:")
        print("   1. Run the scraper with Supabase backend")
        print("   2. Build a simple web dashboard")
        print("   3. Set up user authentication")
        print("   4. Launch your African tender SaaS!")
        
    else:
        print("⚠️ Some tests failed")
        print("   Check your Supabase configuration")
        print("   Ensure the database schema is properly set up")
    
    print(f"\n💡 Your Supabase project: {supabase_url}")
    print("   Dashboard: https://supabase.com/dashboard")

if __name__ == "__main__":
    asyncio.run(main())