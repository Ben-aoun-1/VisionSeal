#!/usr/bin/env python3
"""
Test the fixed UNGM scraper with improved table detection and URL extraction
"""
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_fixed_ungm():
    """Test the fixed UNGM scraper"""
    print("🧪 TESTING FIXED UNGM SCRAPER")
    print("=" * 40)
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        # Create scraper with visible browser for debugging
        scraper = UNGMSimpleScraper({'headless': False})
        
        # Initialize and login
        print("🚀 Initializing browser...")
        if not await scraper.initialize_browser():
            print("❌ Browser initialization failed")
            return
        
        print("🔐 Logging in...")
        login_success = await scraper.login_to_ungm()
        
        if login_success:
            print("✅ Login successful!")
        else:
            print("⚠️ Login failed, continuing with limited access...")
        
        # Test search with improved table detection
        print("🔍 Testing search with improved table detection...")
        opportunities = await scraper.search_opportunities('consulting')
        
        print(f"\n📊 RESULTS:")
        print(f"   Total opportunities: {len(opportunities)}")
        
        # Check URLs
        print(f"\n🔗 URL EXTRACTION CHECK:")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"   {i}. {opp['title'][:50]}...")
            print(f"      Country: {opp['country']}")
            print(f"      Organization: {opp['organization']}")
            print(f"      Reference: {opp['reference']}")
            print(f"      URL: {opp['url']}")
            
            # Check if URL is specific (not just the search page)
            if opp['url'] != scraper.page.url and '/Public/Notice' in opp['url']:
                print(f"      ✅ Specific tender URL extracted!")
            else:
                print(f"      ❌ Generic URL - using search page")
        
        # Cleanup
        await scraper.cleanup()
        print("\n🧹 Cleanup completed")
        
        return opportunities
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(test_fixed_ungm())