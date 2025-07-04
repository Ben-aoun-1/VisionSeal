#!/usr/bin/env python3
"""
Test UNGM table detection without full scraping
"""
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_ungm_table_detection():
    """Test UNGM table detection"""
    print("🧪 TESTING UNGM TABLE DETECTION")
    print("=" * 40)
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        # Create scraper
        scraper = UNGMSimpleScraper({'headless': True})
        
        # Initialize browser
        if not await scraper.initialize_browser():
            print("❌ Browser initialization failed")
            return
        
        # Go to search page
        print("🌐 Navigating to UNGM search page...")
        await scraper.page.goto(f'{scraper.base_url}/Public/Notice', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Fill search form  
        print("🔍 Performing search...")
        await scraper.page.fill('#txtNoticeFilterTitle', 'consulting')
        await scraper.page.check('#chkIsActive')
        await scraper.page.click('button:has-text("Search")')
        await asyncio.sleep(8)
        
        # Test the improved table detection
        print("📊 Testing table detection...")
        tables = await scraper.page.locator('table').all()
        print(f"Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            try:
                rows = await table.locator('tr').all()
                if len(rows) > 2:
                    first_row_cells = await rows[0].locator('td, th').all()
                    if len(first_row_cells) >= 6:
                        cell_texts = []
                        for cell in first_row_cells[:8]:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip().lower())
                        
                        header_text = ' '.join(cell_texts)
                        print(f"\n📋 Table {i+1}:")
                        print(f"   Rows: {len(rows)}")
                        print(f"   Columns: {len(first_row_cells)}")
                        print(f"   Headers: {cell_texts}")
                        
                        # Test UNGM indicators
                        ungm_indicators = [
                            'titre', 'title', 'deadline', 'échéance',
                            'publication', 'organisation', 'organization',
                            'reference', 'référence', 'notice', 'avis',
                            'pays', 'country', 'type'
                        ]
                        
                        indicator_count = sum(1 for indicator in ungm_indicators if indicator in header_text)
                        
                        # Check for calendar indicators
                        calendar_indicators = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
                                             'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        is_calendar = any(indicator in header_text for indicator in calendar_indicators)
                        
                        print(f"   UNGM indicators: {indicator_count}")
                        print(f"   Is calendar: {is_calendar}")
                        
                        if indicator_count >= 3 and not is_calendar:
                            print(f"   ✅ This looks like the UNGM results table!")
                            
                            # Check a few data rows
                            print(f"   📋 Checking first few data rows:")
                            for j in range(1, min(4, len(rows))):
                                data_cells = await rows[j].locator('td').all()
                                if len(data_cells) >= 6:
                                    title_cell = data_cells[1]
                                    title_text = await title_cell.inner_text()
                                    print(f"      Row {j}: {title_text[:50]}...")
                                    
                                    # Check for links
                                    links = await title_cell.locator('a').all()
                                    if links:
                                        for link in links:
                                            href = await link.get_attribute('href')
                                            print(f"         Link: {href}")
                        else:
                            print(f"   ⏭️ Skipping (not UNGM results table)")
                            
            except Exception as e:
                print(f"   ❌ Error checking table {i}: {str(e)}")
        
        # Cleanup
        await scraper.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ungm_table_detection())