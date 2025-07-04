#!/usr/bin/env python3
"""
Check UNGM search results to see if we get any data
"""
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def check_ungm_results():
    """Check UNGM search results"""
    print("🧪 CHECKING UNGM SEARCH RESULTS")
    print("=" * 40)
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        # Create scraper
        scraper = UNGMSimpleScraper({'headless': False})
        
        # Initialize browser
        if not await scraper.initialize_browser():
            print("❌ Browser initialization failed")
            return
        
        # Login first
        print("🔐 Attempting login...")
        login_success = await scraper.login_to_ungm()
        if login_success:
            print("✅ Login successful")
        else:
            print("⚠️ Login failed, continuing anyway...")
        
        # Go to search page
        print("🌐 Navigating to UNGM search page...")
        await scraper.page.goto(f'{scraper.base_url}/Public/Notice', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Fill search form  
        print("🔍 Performing search...")
        await scraper.page.fill('#txtNoticeFilterTitle', 'consulting')
        await scraper.page.check('#chkIsActive')
        await scraper.page.click('button:has-text("Search")')
        await asyncio.sleep(10)  # Wait longer for results
        
        # Check for results indicators
        print("📊 Checking for results...")
        page_content = await scraper.page.content()
        
        # Look for common results indicators
        if 'result' in page_content.lower():
            print("   ✅ Found 'result' in page content")
        if 'notice' in page_content.lower():
            print("   ✅ Found 'notice' in page content")
        if 'opportunity' in page_content.lower():
            print("   ✅ Found 'opportunity' in page content")
        if 'no results' in page_content.lower() or 'aucun résultat' in page_content.lower():
            print("   ❌ 'No results' found in page content")
        
        # Check for pagination or results count
        try:
            # Look for results count or pagination
            result_count = await scraper.page.locator('text=/\d+ result/i').first.inner_text()
            print(f"   📊 Results count: {result_count}")
        except:
            print("   ❓ No results count found")
        
        # Look for all div elements that might contain results
        print("\n🔍 Looking for results containers...")
        divs = await scraper.page.locator('div').all()
        print(f"Found {len(divs)} div elements")
        
        # Check for specific classes that might indicate results
        results_containers = await scraper.page.locator('div[class*="result"], div[class*="notice"], div[class*="opportunity"]').all()
        print(f"Found {len(results_containers)} potential results containers")
        
        # Check if there are any links that look like tender details
        print("\n🔗 Looking for tender links...")
        links = await scraper.page.locator('a').all()
        tender_links = []
        
        for link in links:
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                if href and ('/Public/Notice/' in href or '/notice/' in href.lower()):
                    tender_links.append((href, text[:50]))
            except:
                continue
        
        print(f"Found {len(tender_links)} potential tender links:")
        for href, text in tender_links[:5]:
            print(f"   {href} - {text}...")
        
        # Take a screenshot for debugging
        print("\n📸 Taking screenshot for debugging...")
        await scraper.page.screenshot(path='/root/VisionSeal-Refactored/ungm_search_results.png')
        print("   Screenshot saved as ungm_search_results.png")
        
        # Wait for manual inspection
        print("\n⏳ Waiting 15 seconds for manual inspection...")
        await asyncio.sleep(15)
        
        # Cleanup
        await scraper.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_ungm_results())