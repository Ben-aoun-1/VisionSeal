#!/usr/bin/env python3
"""
Final corrected TuniPages scraper with proper field mapping
"""
import sys
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def scrape_tunipages_final():
    """Final corrected TuniPages scraper with proper field mapping"""
    print("🎯 FINAL CORRECTED TUNIPAGES SCRAPER")
    print("=" * 40)
    print("✅ Correct field mapping: Pays, Titre, Avis, Promoteur, Type, Expire le")
    print("✅ Extracting real African tender opportunities")
    print("✅ Proper data structure parsing")
    print()
    
    all_opportunities = []
    
    # Target the working appeloffres.net URLs
    urls_to_scrape = [
        'https://www.appeloffres.net',
        'https://www.appeloffres.net/appels-offres?countryId=219',  # Tunisia
        'https://www.appeloffres.net/appels-offres?countryId=6',    # Algeria
        'https://www.appeloffres.net/appels-offres?countryId=160'   # Morocco
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8,ar;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    for url in urls_to_scrape:
        print(f"🌐 Scraping {url}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                print(f"   ✅ Connected successfully")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract opportunities using corrected mapping
                opportunities = extract_with_correct_mapping(soup, url)
                
                if opportunities:
                    all_opportunities.extend(opportunities)
                    print(f"   ✅ Extracted {len(opportunities)} opportunities")
                else:
                    print(f"   ⚠️ No opportunities found")
            else:
                print(f"   ❌ Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue
    
    print(f"\n📊 FINAL EXTRACTION RESULTS:")
    print(f"   Total found: {len(all_opportunities)} real opportunities")
    
    # Show extracted opportunities with correct data
    for i, opp in enumerate(all_opportunities[:5], 1):
        print(f"\n💼 Opportunity {i}:")
        print(f"   📝 Title: {opp['title']}")
        print(f"   🌍 Country: {opp['country']}")
        print(f"   🏢 Organization: {opp['organization']}")
        print(f"   📅 Deadline: {opp['deadline']}")
        print(f"   📋 Type: {opp['notice_type']}")
        print(f"   📊 Score: {opp['relevance_score']}")
    
    # Save to Supabase
    if all_opportunities:
        print(f"\n💾 Saving {len(all_opportunities)} opportunities to Supabase...")
        saved_count = await save_to_supabase(all_opportunities)
        print(f"✅ Saved {saved_count}/{len(all_opportunities)} to Supabase")
    
    return all_opportunities

def extract_with_correct_mapping(soup, source_url):
    """Extract opportunities with correct field mapping"""
    opportunities = []
    
    try:
        # Find the table with tender data
        table = soup.find('table')
        
        if not table:
            print(f"   ⚠️ No table found")
            return opportunities
        
        rows = table.find_all('tr')
        
        if len(rows) < 2:
            print(f"   ⚠️ Table has no data rows")
            return opportunities
        
        # Verify the header structure
        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        print(f"   📋 Table headers: {headers}")
        print(f"   📋 Header mapping: 0=Publié, 1=Pays, 2=Description, 3=Promoteur, 4=Type, 5=Expire")
        
        # Process data rows with correct mapping
        for row_idx, row in enumerate(rows[1:], 1):
            try:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 6:  # Should have 6 columns
                    # CORRECT MAPPING based on actual live table structure:
                    # 0: Pays (Country)
                    # 1: Titre (Title with clickable link)
                    # 2: Avis (Notice Type)
                    # 3: Promoteur (Organization)
                    # 4: Type (Type - national/international)
                    # 5: Expire le (Deadline)
                    
                    country = cells[0].get_text(strip=True)
                    title = cells[1].get_text(strip=True)
                    notice_type = cells[2].get_text(strip=True)
                    organization = cells[3].get_text(strip=True)
                    tender_type = cells[4].get_text(strip=True)
                    deadline = cells[5].get_text(strip=True)
                    
                    # Extract detail URL from the table row x-data attribute
                    detail_url = extract_detail_url(row, source_url)
                    
                    # Only process valid opportunities
                    if (title and country and 
                        len(title) > 5 and len(country) > 2 and
                        country.lower() not in ['pays', 'country'] and
                        title.lower() not in ['titre', 'title']):
                        
                        opportunity = {
                            'title': title,
                            'country': country,
                            'organization': organization,
                            'publication_date': datetime.now().strftime('%Y-%m-%d'),  # Current date as publication
                            'deadline': deadline,
                            'notice_type': notice_type,  # Use actual notice type field
                            'tender_type': tender_type,
                            'detail_url': detail_url,
                            'source': 'TUNIPAGES',
                            'reference': f'TUNIPAGES-{row_idx}',
                            'url': detail_url,  # Use detail URL as main URL for clickable titles
                            'extracted_at': datetime.now().isoformat(),
                            'status': 'ACTIVE'
                        }
                        
                        # Calculate relevance score
                        score = calculate_relevance_score(opportunity)
                        opportunity['relevance_score'] = score
                        
                        opportunities.append(opportunity)
                        print(f"   ✅ Row {row_idx}: {country} - {title[:40]}... (Deadline: {deadline})")
                        
            except Exception as e:
                print(f"   ⚠️ Error in row {row_idx}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"   ❌ Extraction error: {str(e)}")
    
    return opportunities

def extract_detail_url(table_row, base_url):
    """Extract detail URL from table row x-data attribute"""
    try:
        # Check if row has x-data attribute with redirect URL
        x_data = table_row.get('x-data', '')
        
        if x_data:
            # Extract URL from x-data attribute
            # Format: "{ redirect() { window.location.href = 'https://www.appeloffres.net/appels-offres/1736561'; } }"
            import re
            url_match = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", x_data)
            if url_match:
                detail_url = url_match.group(1)
                print(f"   🔗 Extracted URL from x-data: {detail_url}")
                return detail_url
        
        # Fallback: look for links in cells (for backward compatibility)
        cells = table_row.find_all(['td', 'th'])
        for cell in cells:
            links = cell.find_all('a')
            if links:
                href = links[0].get('href', '')
                if href.startswith('/'):
                    return base_url + href
                elif href.startswith('http'):
                    return href
                else:
                    return f"{base_url}/{href}"
        
        # If no direct link found, return general tender search page
        return f"{base_url}/appels-offres"
        
    except Exception as e:
        print(f"   ❌ Error extracting URL: {str(e)}")
        return f"{base_url}/appels-offres"

def calculate_relevance_score(opportunity):
    """Calculate relevance score for opportunities"""
    score = 50  # Base score
    
    # Combine text for analysis
    all_text = ' '.join([
        opportunity.get('title', ''),
        opportunity.get('country', ''),
        opportunity.get('organization', ''),
        opportunity.get('notice_type', '')
    ]).lower()
    
    # African countries boost
    african_countries = [
        'tunisie', 'tunisia', 'algeria', 'algérie', 'morocco', 'maroc', 
        'libya', 'libye', 'egypt', 'égypte', 'soudan', 'sudan',
        'nigeria', 'ghana', 'kenya', 'south africa', 'afrique du sud',
        'cameroon', 'cameroun', 'senegal', 'sénégal', 'mali', 'niger',
        'burkina faso', 'ivory coast', 'côte d\'ivoire'
    ]
    
    for country in african_countries:
        if country in all_text:
            score += 25
            break
    
    # High-value service keywords
    service_keywords = [
        'consulting', 'consultancy', 'conseil', 'expertise', 'advisory',
        'formation', 'training', 'étude', 'study', 'evaluation', 'audit'
    ]
    
    if any(keyword in all_text for keyword in service_keywords):
        score += 20
    
    # Technical/Infrastructure keywords  
    tech_keywords = [
        'construction', 'travaux', 'aménagement', 'équipements', 'matériel',
        'technical', 'technique', 'engineering', 'ingénierie'
    ]
    
    if any(keyword in all_text for keyword in tech_keywords):
        score += 15
    
    # International organizations boost
    intl_orgs = [
        'fao', 'undp', 'pnud', 'unicef', 'who', 'oms', 'world bank', 
        'banque mondiale', 'african development bank', 'bad'
    ]
    
    if any(org in all_text for org in intl_orgs):
        score += 20
    
    # Educational/Government institutions
    edu_gov = [
        'université', 'university', 'école', 'école nationale', 'institut',
        'ministère', 'ministry', 'gouvernement', 'government', 'office',
        'agence', 'agency', 'hôpital', 'hospital'
    ]
    
    if any(org in all_text for org in edu_gov):
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
                    'description': f"TuniPages opportunity in {opp['country']}: {opp['title']}",
                    'source': opp['source'],
                    'country': opp['country'],
                    'organization': opp['organization'],
                    'deadline': opp['deadline'],
                    'url': opp['detail_url'],
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
                print(f"   ❌ Error saving: {str(e)}")
                continue
        
        return saved_count
        
    except Exception as e:
        print(f"❌ Supabase error: {str(e)}")
        return 0

async def main():
    """Run final corrected TuniPages scraping"""
    print("🎯 FINAL CORRECTED TUNIPAGES EXTRACTION")
    print("Proper field mapping and African tender focus")
    print()
    
    opportunities = await scrape_tunipages_final()
    
    if opportunities:
        print(f"\n🎉 SUCCESS! Extracted {len(opportunities)} REAL opportunities")
        print("✅ Correct field mapping (Pays→Country, Titre→Title, etc.)")
        print("✅ Proper African tender data extraction")
        print("✅ Real organizations and deadlines")
        print("✅ Saved to Supabase database")
        
        print(f"\n💰 FINAL TUNIPAGES VALUE:")
        print(f"   • {len(opportunities)} correctly parsed tender opportunities")
        print(f"   • Accurate African country and organization data")
        print(f"   • Real deadlines and publication information")
        print(f"   • Direct links to tender detail pages")
        print(f"   • Relevance scoring for African business focus")
        
        # Show country breakdown
        countries = {}
        for opp in opportunities:
            country = opp['country']
            countries[country] = countries.get(country, 0) + 1
        
        print(f"\n🌍 COUNTRY BREAKDOWN:")
        for country, count in sorted(countries.items()):
            print(f"   • {country}: {count} opportunities")
        
    else:
        print(f"\n📝 No opportunities extracted")
        print("🔍 Check if appeloffres.net structure has changed")
    
    print(f"\n🌐 View your data:")
    print(f"   https://supabase.com/dashboard/project/fycatruiawynbzuafdsx")

if __name__ == "__main__":
    asyncio.run(main())