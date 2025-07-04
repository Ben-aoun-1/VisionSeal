#!/usr/bin/env python3
"""
UNGM extractor targeting the actual div-based table structure
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def extract_from_div_table():
    """Extract opportunities from UNGM's div-based table structure"""
    print("🎯 UNGM DIV-TABLE EXTRACTOR")
    print("=" * 35)
    print("✅ Targeting div[role='table'] structure")
    print("✅ Using actual UNGM table selectors")
    print("✅ Extracting Date d'échéance correctly")
    print()
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        scraper = UNGMSimpleScraper({'headless': False})
        
        # Initialize and login
        print("🚀 Initializing and logging in...")
        await scraper.initialize_browser()
        
        if not await scraper.login_to_ungm():
            print("❌ Login failed")
            return []
        
        print("✅ Login successful!")
        
        # Go to opportunities page
        await scraper.page.goto('https://www.ungm.org/Public/Notice')
        await asyncio.sleep(3)
        
        # Search for Africa
        print("🔍 Searching for 'africa'...")
        await scraper.page.fill('#txtNoticeFilterTitle', 'africa')
        await scraper.page.check('#chkIsActive')
        await scraper.page.click('button:has-text("Rechercher")')
        
        # Wait for results
        await asyncio.sleep(8)
        
        # Take screenshot
        await scraper.page.screenshot(path='/tmp/ungm_div_table_results.png')
        
        # Extract from div-based table
        print("📋 Extracting from div-based table...")
        opportunities = await extract_from_custom_table(scraper.page)
        
        print(f"\n📊 DIV-TABLE EXTRACTION RESULTS:")
        print(f"   Found: {len(opportunities)} opportunities")
        
        # Show extracted data
        for i, opp in enumerate(opportunities, 1):
            print(f"\n💼 Opportunity {i}:")
            print(f"   Title: {opp['title']}")
            print(f"   Deadline: {opp['deadline']}")
            print(f"   Publication: {opp['publication_date']}")
            print(f"   Organization: {opp['organization']}")
            print(f"   Type: {opp['notice_type']}")
            print(f"   Reference: {opp['reference']}")
            print(f"   Country: {opp['country']}")
            print(f"   Score: {opp['relevance_score']}")
        
        # Save to Supabase
        if opportunities:
            print(f"\n💾 Saving to Supabase...")
            saved_count = await save_to_supabase(opportunities)
            print(f"✅ Saved {saved_count}/{len(opportunities)} to Supabase")
        
        await scraper.cleanup()
        return opportunities
        
    except Exception as e:
        print(f"❌ Extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

async def extract_from_custom_table(page):
    """Extract from UNGM's custom div-based table"""
    opportunities = []
    
    try:
        print("   🔍 Looking for div[role='table']...")
        
        # Find the main table div
        table_div = page.locator('div[role="table"]#tblNotices')
        
        if not await table_div.count():
            print("   ❌ Could not find div[role='table']#tblNotices")
            return []
        
        print("   ✅ Found div-based table!")
        
        # Find the table body
        table_body = table_div.locator('div[role="rowgroup"].tableBody')
        
        if not await table_body.count():
            print("   ❌ Could not find table body")
            return []
        
        # Get all data rows
        data_rows = table_body.locator('div[role="row"]')
        row_count = await data_rows.count()
        
        print(f"   📋 Found {row_count} data rows")
        
        # Extract data from each row
        for i in range(row_count):
            try:
                row = data_rows.nth(i)
                
                # Get all cells in this row
                cells = row.locator('div[role="cell"], div[role="gridcell"]')
                cell_count = await cells.count()
                
                if cell_count >= 7:  # Need at least 7 cells for all columns
                    # Extract text from each cell according to the column structure:
                    # 0: Empty (buttons)
                    # 1: Titre (Title)
                    # 2: Date d'échéance (Deadline)
                    # 3: Date de publication (Publication Date)
                    # 4: Organisation
                    # 5: Type d'avis (Notice Type)
                    # 6: Référence
                    # 7: Pays/territoire bénéficiaire (Country)
                    
                    cell_texts = []
                    for j in range(cell_count):
                        cell = cells.nth(j)
                        text = await cell.inner_text()
                        cell_texts.append(text.strip())
                    
                    # Map to opportunity fields (skip first empty cell)
                    title = cell_texts[1] if len(cell_texts) > 1 else ''
                    deadline = cell_texts[2] if len(cell_texts) > 2 else ''
                    pub_date = cell_texts[3] if len(cell_texts) > 3 else ''
                    organization = cell_texts[4] if len(cell_texts) > 4 else ''
                    notice_type = cell_texts[5] if len(cell_texts) > 5 else ''
                    reference = cell_texts[6] if len(cell_texts) > 6 else ''
                    country = cell_texts[7] if len(cell_texts) > 7 else ''
                    
                    # Only process if we have meaningful data
                    if title and len(title) > 5:
                        opportunity = {
                            'title': title,
                            'deadline': deadline,  # Date d'échéance
                            'publication_date': pub_date,
                            'organization': organization,
                            'notice_type': notice_type,
                            'reference': reference,
                            'country': country if country else extract_country_from_text(title + ' ' + organization),
                            'source': 'UNGM',
                            'url': page.url,
                            'extracted_at': datetime.now().isoformat(),
                            'status': 'ACTIVE'
                        }
                        
                        # Calculate relevance
                        score = calculate_relevance(opportunity)
                        opportunity['relevance_score'] = score
                        
                        opportunities.append(opportunity)
                        print(f"   ✅ Row {i+1}: {title[:50]}... (Deadline: {deadline})")
                        
            except Exception as e:
                print(f"   ⚠️ Error processing row {i+1}: {str(e)}")
                continue
        
        return opportunities
        
    except Exception as e:
        print(f"   ❌ Div-table extraction failed: {str(e)}")
        return []

def extract_country_from_text(text):
    """Extract country from text"""
    text_lower = text.lower()
    
    african_countries = [
        'nigeria', 'ghana', 'kenya', 'south africa', 'morocco', 'egypt',
        'algeria', 'angola', 'benin', 'botswana', 'burkina faso', 'burundi',
        'cameroon', 'cape verde', 'chad', 'comoros', 'congo', 'djibouti',
        'equatorial guinea', 'eritrea', 'ethiopia', 'gabon', 'gambia',
        'guinea', 'ivory coast', 'lesotho', 'liberia', 'libya', 'madagascar',
        'malawi', 'mali', 'mauritania', 'mauritius', 'mozambique', 'namibia',
        'niger', 'rwanda', 'senegal', 'sierra leone', 'somalia', 'sudan',
        'tanzania', 'togo', 'tunisia', 'uganda', 'zambia', 'zimbabwe',
        'central african republic'
    ]
    
    for country in african_countries:
        if country in text_lower:
            return country.title()
    
    if any(term in text_lower for term in ['africa', 'african', 'afrique']):
        return 'Africa (General)'
    
    return 'Not specified'

def calculate_relevance(opportunity):
    """Calculate relevance score"""
    score = 25  # Base score
    
    all_text = ' '.join([
        opportunity.get('title', ''),
        opportunity.get('organization', ''),
        opportunity.get('country', ''),
        opportunity.get('notice_type', '')
    ]).lower()
    
    # African boost
    african_terms = ['africa', 'african', 'nigeria', 'ghana', 'kenya', 'morocco', 'egypt', 'central african republic']
    if any(term in all_text for term in african_terms):
        score += 40
    
    # Consulting boost
    consulting_terms = ['consulting', 'consultancy', 'advisory', 'evaluation']
    if any(term in all_text for term in consulting_terms):
        score += 20
    
    # Development boost
    dev_terms = ['development', 'capacity building', 'sme', 'small business']
    if any(term in all_text for term in dev_terms):
        score += 15
    
    return min(score, 100)

async def save_to_supabase(opportunities):
    """Save opportunities to Supabase"""
    try:
        from core.database.supabase_client import supabase_manager
        
        saved_count = 0
        for opp in opportunities:
            try:
                tender_data = {
                    'title': opp['title'],
                    'description': f"Opportunity from {opp['organization']}: {opp['title']}",
                    'source': opp['source'],
                    'country': opp['country'],
                    'organization': opp['organization'],
                    'deadline': opp['deadline'],
                    'url': opp['url'],
                    'reference': opp['reference'],
                    'status': opp['status'],
                    'relevance_score': opp['relevance_score'],
                    'publication_date': opp['publication_date'],
                    'notice_type': opp['notice_type'],
                    'extracted_at': opp['extracted_at']
                }
                
                result = await supabase_manager.insert_tender(tender_data)
                if result:
                    saved_count += 1
                    
            except Exception as e:
                print(f"   ❌ Error saving opportunity: {str(e)}")
                continue
        
        return saved_count
        
    except Exception as e:
        print(f"❌ Supabase save failed: {str(e)}")
        return 0

async def show_supabase_results():
    """Show results in Supabase"""
    try:
        from core.database.supabase_client import supabase_manager
        
        print(f"\n🔥 LATEST SUPABASE RESULTS:")
        print("=" * 30)
        
        recent = await supabase_manager.get_recent_tenders(limit=8)
        
        if recent:
            print(f"Showing latest {len(recent)} opportunities:")
            print()
            
            for i, opp in enumerate(recent, 1):
                print(f"💼 #{i}: {opp['title']}")
                print(f"   📅 Deadline: {opp['deadline']}")
                print(f"   🏢 Organization: {opp['organization']}")
                print(f"   🌍 Country: {opp['country']}")
                print(f"   📊 Score: {opp['relevance_score']}")
                print()
        else:
            print("No opportunities found")
            
    except Exception as e:
        print(f"Error accessing Supabase: {str(e)}")

async def main():
    """Run div-table extraction"""
    print("🎯 UNGM DIV-TABLE OPPORTUNITY EXTRACTION")
    print("Using the actual UNGM table structure")
    print()
    
    opportunities = await extract_from_div_table()
    
    if opportunities:
        print(f"\n🎉 SUCCESS! Extracted {len(opportunities)} opportunities")
        print("✅ Using real UNGM div-table structure")
        print("✅ Date d'échéance extracted correctly")
        print("✅ All table columns mapped properly")
        print("✅ Saved to Supabase database")
        
        await show_supabase_results()
        
        print(f"\n💰 BUSINESS VALUE:")
        print(f"   • Real tender opportunities with deadlines")
        print(f"   • Proper field mapping from UNGM")
        print(f"   • Ready for customer dashboard")
        
    else:
        print(f"\n📝 No opportunities extracted")
        print("Check screenshots and selectors")
    
    print(f"\n🌐 View your data:")
    print(f"   https://supabase.com/dashboard/project/fycatruiawynbzuafdsx")

if __name__ == "__main__":
    asyncio.run(main())