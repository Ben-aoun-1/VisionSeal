#!/usr/bin/env python3
"""
Debug TuniPages table structure to understand the actual format
"""
import requests
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_tunipages_table():
    """Debug the actual TuniPages table structure"""
    print("🔍 DEBUGGING TUNIPAGES TABLE STRUCTURE")
    print("=" * 45)
    
    url = 'https://www.appeloffres.net'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all tables
            tables = soup.find_all('table')
            print(f"✅ Found {len(tables)} tables on page")
            
            for i, table in enumerate(tables, 1):
                print(f"\n📋 Table {i}:")
                
                # Get table classes
                table_classes = table.get('class', [])
                print(f"   Classes: {' '.join(table_classes)}")
                
                # Get header row
                rows = table.find_all('tr')
                if rows:
                    header_row = rows[0]
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                    print(f"   Headers: {headers}")
                    print(f"   Rows: {len(rows)}")
                    
                    # Show first data row if exists
                    if len(rows) > 1:
                        first_data_row = rows[1]
                        cells = [td.get_text(strip=True)[:50] for td in first_data_row.find_all(['td', 'th'])]
                        print(f"   First row sample: {cells}")
                        
                        # Check for links in cells
                        for j, cell in enumerate(first_data_row.find_all(['td', 'th'])):
                            links = cell.find_all('a')
                            if links:
                                href = links[0].get('href', '')
                                print(f"   Cell {j} has link: {href}")
                
                print(f"   " + "-" * 50)
                
        else:
            print(f"❌ Failed to get page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_tunipages_table()