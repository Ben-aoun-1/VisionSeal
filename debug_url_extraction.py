#!/usr/bin/env python3
"""
Debug URL extraction from both UNGM and TuniPages scrapers
"""
import sys
import asyncio
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def debug_ungm_urls():
    """Debug UNGM URL extraction"""
    print("🔍 DEBUGGING UNGM URL EXTRACTION")
    print("=" * 40)
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        # Create scraper instance
        scraper = UNGMSimpleScraper({'headless': True})
        
        # Initialize browser
        if not await scraper.initialize_browser():
            print("❌ Browser initialization failed")
            return
        
        # Login
        login_success = await scraper.login_to_ungm()
        if not login_success:
            print("⚠️ Login failed, continuing with limited access...")
        
        # Navigate to search page
        await scraper.page.goto(f'{scraper.base_url}/Public/Notice', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Fill search form  
        await scraper.page.fill('#txtNoticeFilterTitle', 'consulting')
        await scraper.page.check('#chkIsActive')
        
        # Submit search
        await scraper.page.click('button:has-text("Rechercher")')
        await asyncio.sleep(8)
        
        # Check page content for URL structure
        page_content = await scraper.page.content()
        print(f"📄 Page loaded, checking for table structure...")
        
        # Find tables
        tables = await scraper.page.locator('table').all()
        print(f"📊 Found {len(tables)} tables")
        
        # Check first table structure
        if tables:
            table = tables[0]
            rows = await table.locator('tr').all()
            print(f"📋 First table has {len(rows)} rows")
            
            # Check first few rows for URL structure
            for i, row in enumerate(rows[:3]):
                cells = await row.locator('td, th').all()
                print(f"\n🔍 Row {i+1}: {len(cells)} cells")
                
                for j, cell in enumerate(cells):
                    cell_text = await cell.inner_text()
                    print(f"   Cell {j+1}: {cell_text[:50]}...")
                    
                    # Check for links
                    links = await cell.locator('a').all()
                    if links:
                        print(f"   Links found: {len(links)}")
                        for k, link in enumerate(links):
                            href = await link.get_attribute('href')
                            target = await link.get_attribute('target')
                            print(f"      Link {k+1}: {href} (target: {target})")
        
        # Cleanup
        await scraper.cleanup()
        
    except Exception as e:
        print(f"❌ UNGM debug failed: {str(e)}")
        import traceback
        traceback.print_exc()

def debug_tunipages_urls():
    """Debug TuniPages URL extraction"""
    print("\n🔍 DEBUGGING TUNIPAGES URL EXTRACTION")
    print("=" * 40)
    
    try:
        # Test live TuniPages structure
        url = 'https://www.appeloffres.net'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        print(f"🌐 Fetching {url}...")
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            print(f"✅ Connected successfully")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table with tender data
            table = soup.find('table')
            if table:
                print(f"📊 Found table")
                rows = table.find_all('tr')
                print(f"📋 Table has {len(rows)} rows")
                
                # Check header
                if rows:
                    header_row = rows[0]
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                    print(f"🏷️ Headers: {headers}")
                
                # Check first few data rows
                for i, row in enumerate(rows[1:6], 1):
                    cells = row.find_all(['td', 'th'])
                    print(f"\n🔍 Row {i}: {len(cells)} cells")
                    
                    for j, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        print(f"   Cell {j+1}: {cell_text[:50]}...")
                        
                        # Check for links
                        links = cell.find_all('a')
                        if links:
                            print(f"   Links found: {len(links)}")
                            for k, link in enumerate(links):
                                href = link.get('href')
                                print(f"      Link {k+1}: {href}")
                                
                                # Check if it's a specific tender URL
                                if href and 'appels-offres/' in href:
                                    print(f"      ✅ Tender detail URL found!")
                                else:
                                    print(f"      ❌ Not a tender detail URL")
            else:
                print(f"❌ No table found")
        else:
            print(f"❌ Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ TuniPages debug failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all URL extraction debugging"""
    print("🧪 URL EXTRACTION DEBUGGING")
    print("=" * 50)
    
    # Debug UNGM
    await debug_ungm_urls()
    
    # Debug TuniPages
    debug_tunipages_urls()
    
    print("\n📋 SUMMARY")
    print("=" * 20)
    print("✅ TuniPages: URLs should be extracted from cell 2 (Description) <a> tags")
    print("❓ UNGM: Need to verify table structure and link extraction")
    print("🔧 Fix required: Ensure extracted URLs are saved to database correctly")

if __name__ == "__main__":
    asyncio.run(main())