#!/usr/bin/env python3
"""
Debug UNGM search form to find correct button text
"""
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def debug_ungm_search():
    """Debug UNGM search form"""
    print("🧪 DEBUGGING UNGM SEARCH FORM")
    print("=" * 40)
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        # Create scraper
        scraper = UNGMSimpleScraper({'headless': False})
        
        # Initialize browser
        if not await scraper.initialize_browser():
            print("❌ Browser initialization failed")
            return
        
        # Go to search page
        print("🌐 Navigating to UNGM search page...")
        await scraper.page.goto(f'{scraper.base_url}/Public/Notice', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Check what buttons are available
        print("🔍 Looking for buttons on the page...")
        buttons = await scraper.page.locator('button').all()
        print(f"Found {len(buttons)} buttons:")
        
        for i, button in enumerate(buttons):
            try:
                text = await button.inner_text()
                type_attr = await button.get_attribute('type')
                onclick = await button.get_attribute('onclick')
                print(f"   Button {i+1}: '{text}' (type: {type_attr}, onclick: {onclick})")
            except:
                print(f"   Button {i+1}: Could not get text")
        
        # Also check for input type=submit
        print("\n🔍 Looking for submit inputs...")
        submits = await scraper.page.locator('input[type="submit"]').all()
        print(f"Found {len(submits)} submit inputs:")
        
        for i, submit in enumerate(submits):
            try:
                value = await submit.get_attribute('value')
                onclick = await submit.get_attribute('onclick')
                print(f"   Submit {i+1}: value='{value}' (onclick: {onclick})")
            except:
                print(f"   Submit {i+1}: Could not get value")
        
        # Check the page content for any other search triggers
        print("\n🔍 Checking page content for search-related elements...")
        page_content = await scraper.page.content()
        
        # Look for French search terms
        if 'recherche' in page_content.lower():
            print("   ✅ Found 'recherche' in page content")
        if 'search' in page_content.lower():
            print("   ✅ Found 'search' in page content")
        if 'filter' in page_content.lower():
            print("   ✅ Found 'filter' in page content")
        
        # Wait a bit for manual inspection
        print("\n⏳ Waiting 10 seconds for manual inspection...")
        await asyncio.sleep(10)
        
        # Cleanup
        await scraper.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ungm_search())