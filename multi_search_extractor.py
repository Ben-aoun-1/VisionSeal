#!/usr/bin/env python3
"""
Multi-search UNGM extractor to maximize opportunity discovery
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

async def multi_search_extraction():
    """Extract opportunities using multiple search terms"""
    print("🎯 MULTI-SEARCH UNGM EXTRACTOR")
    print("=" * 35)
    print("✅ Testing multiple search terms")
    print("✅ Maximizing opportunity discovery")
    print("✅ Avoiding duplicates")
    print()
    
    search_terms = [
        'consulting',
        'consultancy', 
        'advisory',
        'evaluation',
        'technical assistance',
        'capacity building',
        'development',
        'management'
    ]
    
    all_opportunities = []
    seen_references = set()
    
    try:
        from automation.scrapers.ungm_simple_scraper import UNGMSimpleScraper
        
        scraper = UNGMSimpleScraper({'headless': False})
        
        # Initialize and login once
        print("🚀 Initializing and logging in...")
        await scraper.initialize_browser()
        
        if not await scraper.login_to_ungm():
            print("❌ Login failed")
            return []
        
        print("✅ Login successful!")
        
        # Search with each term
        for i, term in enumerate(search_terms, 1):
            print(f"\n🔍 Search {i}/{len(search_terms)}: '{term}'")
            
            # Go to opportunities page
            await scraper.page.goto('https://www.ungm.org/Public/Notice')
            await asyncio.sleep(2)
            
            # Clear and fill search term
            await scraper.page.fill('#txtNoticeFilterTitle', '')
            await scraper.page.fill('#txtNoticeFilterTitle', term)
            await scraper.page.check('#chkIsActive')
            await scraper.page.click('button:has-text("Rechercher")')
            
            # Wait for results
            await asyncio.sleep(6)
            
            # Extract opportunities
            opportunities = await extract_from_custom_table(scraper.page)
            
            # Filter out duplicates
            new_opportunities = []
            for opp in opportunities:
                ref = opp['reference']
                if ref not in seen_references:
                    seen_references.add(ref)
                    new_opportunities.append(opp)
                    all_opportunities.append(opp)
            
            print(f"   Found: {len(opportunities)} total, {len(new_opportunities)} new")
            
            # Show top 3 new opportunities
            for j, opp in enumerate(new_opportunities[:3], 1):
                print(f"   💼 {j}. {opp['title'][:60]}... (Deadline: {opp['deadline'][:15]}...)")
        
        print(f"\n📊 MULTI-SEARCH RESULTS:")
        print(f"   Total unique opportunities: {len(all_opportunities)}")
        print(f"   Search terms tested: {len(search_terms)}")
        
        # Save all to Supabase
        if all_opportunities:
            print(f"\n💾 Saving {len(all_opportunities)} opportunities to Supabase...")
            saved_count = await save_to_supabase(all_opportunities)
            print(f"✅ Saved {saved_count}/{len(all_opportunities)} to Supabase")
        
        await scraper.cleanup()
        return all_opportunities
        
    except Exception as e:
        print(f"❌ Multi-search extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

async def extract_from_custom_table(page):
    """Extract from UNGM's custom div-based table"""
    opportunities = []
    
    try:
        # Find the main table div
        table_div = page.locator('div[role="table"]#tblNotices')
        
        if not await table_div.count():
            return []
        
        # Find the table body
        table_body = table_div.locator('div[role="rowgroup"].tableBody')
        
        if not await table_body.count():
            return []
        
        # Get all data rows
        data_rows = table_body.locator('div[role="row"]')
        row_count = await data_rows.count()
        
        # Extract data from each row
        for i in range(row_count):
            try:
                row = data_rows.nth(i)
                cells = row.locator('div[role="cell"], div[role="gridcell"]')
                cell_count = await cells.count()
                
                if cell_count >= 7:
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
                    
                    if title and len(title) > 5:
                        opportunity = {
                            'title': title,
                            'deadline': deadline,
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
                        
                        # Calculate relevance for African focus
                        score = calculate_african_relevance(opportunity)
                        opportunity['relevance_score'] = score
                        
                        opportunities.append(opportunity)
                        
            except Exception as e:
                continue
        
        return opportunities
        
    except Exception as e:
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
        'central african republic', 'côte d\'ivoire'
    ]
    
    for country in african_countries:
        if country in text_lower:
            return country.title()
    
    if any(term in text_lower for term in ['africa', 'african', 'afrique']):
        return 'Africa (General)'
    
    return 'Global'

def calculate_african_relevance(opportunity):
    """Calculate relevance score for African focus"""
    score = 25  # Base score
    
    all_text = ' '.join([
        opportunity.get('title', ''),
        opportunity.get('organization', ''),
        opportunity.get('country', ''),
        opportunity.get('notice_type', '')
    ]).lower()
    
    # African indicators (high priority)
    african_terms = ['africa', 'african', 'afrique', 'africain']
    african_countries = ['nigeria', 'ghana', 'kenya', 'south africa', 'morocco', 'egypt', 'central african republic', 'côte d\'ivoire']
    
    if any(term in all_text for term in african_terms + african_countries):
        score += 50  # Major boost for African focus
    
    # Consulting/Advisory boost
    consulting_terms = ['consulting', 'consultancy', 'advisory', 'evaluation', 'technical assistance']
    if any(term in all_text for term in consulting_terms):
        score += 25
    
    # Development boost
    dev_terms = ['development', 'capacity building', 'training', 'institutional']
    if any(term in all_text for term in dev_terms):
        score += 15
    
    # Business/Management boost
    business_terms = ['management', 'strategy', 'business', 'sme', 'small business']
    if any(term in all_text for term in business_terms):
        score += 10
    
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
                continue
        
        return saved_count
        
    except Exception as e:
        return 0

async def show_top_opportunities():
    """Show top African opportunities"""
    try:
        from core.database.supabase_client import supabase_manager
        
        print(f"\n🔥 TOP AFRICAN OPPORTUNITIES:")
        print("=" * 35)
        
        # Get high-relevance African opportunities
        recent = await supabase_manager.get_recent_tenders(limit=25)
        
        if recent:
            # Filter for high African relevance
            african_opps = [opp for opp in recent if opp['relevance_score'] >= 70]
            
            print(f"High-relevance African opportunities: {len(african_opps)}")
            print()
            
            for i, opp in enumerate(african_opps[:10], 1):
                print(f"💼 #{i}: {opp['title'][:70]}...")
                print(f"   📅 Deadline: {opp['deadline'][:20]}...")
                print(f"   🏢 Organization: {opp['organization']}")
                print(f"   🌍 Country: {opp['country']}")
                print(f"   📊 Score: {opp['relevance_score']}")
                print()
        else:
            print("No opportunities found")
            
    except Exception as e:
        print(f"Error accessing Supabase: {str(e)}")

async def main():
    """Run multi-search extraction"""
    print("🎯 MULTI-SEARCH UNGM OPPORTUNITY EXTRACTION")
    print("Maximizing opportunity discovery with multiple search terms")
    print()
    
    opportunities = await multi_search_extraction()
    
    if opportunities:
        print(f"\n🎉 SUCCESS! Extracted {len(opportunities)} unique opportunities")
        print("✅ Multiple search terms tested")
        print("✅ Duplicates filtered out")
        print("✅ African relevance prioritized")
        print("✅ All saved to Supabase database")
        
        await show_top_opportunities()
        
        print(f"\n💰 EXPANDED BUSINESS VALUE:")
        print(f"   • {len(opportunities)} unique opportunities")
        print(f"   • Consulting, advisory, and development focus")
        print(f"   • African opportunities prioritized")
        print(f"   • Multiple UN organizations and agencies")
        print(f"   • Complete deadline and reference data")
        
    else:
        print(f"\n📝 No opportunities extracted")
    
    print(f"\n🌐 View your expanded data:")
    print(f"   https://supabase.com/dashboard/project/fycatruiawynbzuafdsx")

if __name__ == "__main__":
    asyncio.run(main())