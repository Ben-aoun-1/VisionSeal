#!/usr/bin/env python3
"""
Test live TuniPages URL extraction to see the actual HTML structure
"""
import requests
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_live_tunipages_urls():
    """Test live TuniPages URL extraction"""
    print("🧪 TESTING LIVE TUNIPAGES URL EXTRACTION")
    print("=" * 50)
    
    # Test the working appeloffres.net URLs
    urls_to_test = [
        'https://www.appeloffres.net',
        'https://www.appeloffres.net/appels-offres?countryId=219',  # Tunisia
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8,ar;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    for url in urls_to_test:
        print(f"\n🌐 Testing {url}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                print(f"   ✅ Connected successfully")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the table with tender data
                table = soup.find('table')
                
                if table:
                    print(f"   📊 Found table")
                    rows = table.find_all('tr')
                    print(f"   📋 Table has {len(rows)} rows")
                    
                    # Check header row
                    if rows:
                        header_row = rows[0]
                        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                        print(f"   🏷️ Headers: {headers}")
                    
                    # Check first few data rows for links
                    for i, row in enumerate(rows[1:4], 1):
                        cells = row.find_all(['td', 'th'])
                        print(f"\n   🔍 Row {i}: {len(cells)} cells")
                        
                        if len(cells) >= 2:
                            # Check title cell (should be cell 1 based on headers)
                            title_cell = cells[1]  # Index 1 for "Titre"
                            title_text = title_cell.get_text(strip=True)
                            print(f"      📝 Title: {title_text[:60]}...")
                            
                            # Check for links in title cell
                            links = title_cell.find_all('a')
                            if links:
                                print(f"      🔗 Found {len(links)} links in title cell:")
                                for j, link in enumerate(links):
                                    href = link.get('href')
                                    link_text = link.get_text(strip=True)
                                    print(f"         Link {j+1}: {href}")
                                    print(f"         Text: {link_text[:50]}...")
                                    
                                    # Check if it's a specific tender URL
                                    if href and 'appels-offres/' in href:
                                        print(f"         ✅ Tender detail URL found!")
                                    else:
                                        print(f"         ❌ Not a tender detail URL")
                            else:
                                print(f"      ❌ No links found in title cell")
                                print(f"      📄 Cell HTML: {str(title_cell)[:200]}...")
                        
                        # Also check other cells for links
                        for j, cell in enumerate(cells):
                            if j == 1:  # Skip title cell, we already checked it
                                continue
                            links = cell.find_all('a')
                            if links:
                                print(f"      🔗 Cell {j+1} has {len(links)} links")
                                for k, link in enumerate(links):
                                    href = link.get('href')
                                    if href:
                                        print(f"         Link {k+1}: {href}")
                
                else:
                    print(f"   ❌ No table found")
                    # Let's see what content we got
                    print(f"   📄 Page content preview:")
                    print(f"   {response.text[:500]}...")
                    
            else:
                print(f"   ❌ Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue

if __name__ == "__main__":
    test_live_tunipages_urls()