#!/usr/bin/env python3
"""
Test TuniPages URL extraction functionality
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_tunipages_url_extraction():
    """Test TuniPages URL extraction with sample HTML"""
    print("🧪 TESTING TUNIPAGES URL EXTRACTION")
    print("=" * 40)
    
    # Sample HTML from your example
    sample_html = '''
    <table class="table table-condensed table-bordered table-striped">
        <tbody>
            <tr>
                <th class="bg-primary">Publié le</th>
                <th class="bg-primary">Pays</th>
                <th class="bg-primary">Description</th>
                <th class="bg-primary hidden-xs">Promoteur</th>
                <th class="bg-primary">Type</th>
                <th class="bg-primary">Expire le</th>
            </tr>
            <tr>
                <td>04 juillet 2025 à 11h36</td>
                <td>Tunisie</td>
                <td>
                    <a href="https://www.appeloffres.net/appels-offres/1736121?ve=0">
                        Désignation d'avocats ou d'une société professionnelle d'avocats pour représenter la Société de Transport du Sahel devant les tribunaux
                    </a>
                </td>
                <td class="hidden-xs">
                    Société de Transport de Sahel - STS
                </td>
                <td>Nat</td>
                <td style="white-space: nowrap;">
                    14 juillet 2025 à 08h00
                </td>
            </tr>
            <tr>
                <td>04 juillet 2025 à 11h35</td>
                <td>Tunisie</td>
                <td>
                    <a href="https://www.appeloffres.net/appels-offres/1736120?ve=0">
                        Fourniture, montage et mise en service des skids de filtration et des systèmes de comptage du gaz naturel.
                    </a>
                </td>
                <td class="hidden-xs">
                    Société Tunisienne de l'Electricité et du Gaz STEG
                </td>
                <td>Inter</td>
                <td style="white-space: nowrap;">
                    02 septembre 2025 à 08h00
                </td>
            </tr>
        </tbody>
    </table>
    '''
    
    # Parse the HTML
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    # Import the extraction function
    sys.path.insert(0, str(Path(__file__).parent))
    from tunipages_final_scraper import extract_detail_url
    
    # Find the table and extract data
    table = soup.find('table')
    rows = table.find_all('tr')
    
    print(f"✅ Found table with {len(rows)} rows")
    
    # Process data rows (skip header)
    for row_idx, row in enumerate(rows[1:], 1):
        cells = row.find_all(['td', 'th'])
        
        if len(cells) >= 6:
            pub_date = cells[0].get_text(strip=True)
            country = cells[1].get_text(strip=True)
            title = cells[2].get_text(strip=True)
            organization = cells[3].get_text(strip=True)
            tender_type = cells[4].get_text(strip=True)
            deadline = cells[5].get_text(strip=True)
            
            # Extract detail URL
            detail_url = extract_detail_url(cells[2], "https://www.appeloffres.net")
            
            print(f"\n💼 Opportunity {row_idx}:")
            print(f"   📅 Published: {pub_date}")
            print(f"   🌍 Country: {country}")
            print(f"   📝 Title: {title[:60]}...")
            print(f"   🏢 Organization: {organization}")
            print(f"   📋 Type: {tender_type}")
            print(f"   ⏰ Deadline: {deadline}")
            print(f"   🔗 Detail URL: {detail_url}")
            
            # Verify URL extraction
            if detail_url and 'appeloffres.net/appels-offres/' in detail_url:
                print(f"   ✅ URL extracted successfully!")
            else:
                print(f"   ❌ URL extraction failed")

if __name__ == "__main__":
    test_tunipages_url_extraction()