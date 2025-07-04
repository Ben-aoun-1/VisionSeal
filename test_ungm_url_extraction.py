#!/usr/bin/env python3
"""
Test UNGM URL extraction functionality
"""
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_ungm_url_extraction():
    """Test UNGM scraper with URL extraction"""
    print("🧪 TESTING UNGM URL EXTRACTION")
    print("=" * 35)
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        scraper = UNGMSimpleScraper({'headless': False})
        
        # Initialize and login
        print("🚀 Initializing browser...")
        await scraper.initialize_browser()
        
        print("🔐 Logging in...")
        login_success = await scraper.login_to_ungm()
        
        if login_success:
            print("✅ Login successful!")
            
            # Test a simple search
            print("🔍 Testing search with URL extraction...")
            opportunities = await scraper.search_opportunities('consulting')
            
            print(f"\n📊 Results: {len(opportunities)} opportunities found")
            
            # Check if URLs are being extracted correctly
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"\n💼 Opportunity {i}:")
                print(f"   Title: {opp['title'][:60]}...")
                print(f"   URL: {opp['url']}")
                print(f"   Organization: {opp['organization']}")
                print(f"   Country: {opp['country']}")
                
                # Check if URL is different from page URL
                if '/Public/Notice/' in opp['url']:
                    print(f"   ✅ Detail URL extracted successfully!")
                else:
                    print(f"   ⚠️ Using fallback URL")
                    
        else:
            print("❌ Login failed")
            
        # Cleanup
        await scraper.cleanup()
        print("\n🧹 Cleanup completed")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ungm_url_extraction())