#!/usr/bin/env python3
"""
Fix TuniPages URL extraction - the current site structure is different
"""
import requests
from bs4 import BeautifulSoup
import urllib3
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def analyze_tunipages_structure():
    """Analyze the actual TuniPages structure to understand clickable elements"""
    print("🔍 ANALYZING TUNIPAGES STRUCTURE")
    print("=" * 40)
    
    url = 'https://www.appeloffres.net'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8,ar;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            print(f"✅ Connected successfully")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for JavaScript or data attributes that might contain URLs
            print("\n🔍 Checking for clickable elements...")
            
            # Find table rows
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                print(f"📊 Found {len(rows)} rows")
                
                # Check each row for clickable attributes
                for i, row in enumerate(rows[1:4], 1):  # Skip header, check first 3 data rows
                    print(f"\n🔍 Row {i}:")
                    
                    # Check row attributes
                    row_attrs = row.attrs
                    print(f"   Row attributes: {row_attrs}")
                    
                    # Check for data attributes that might contain URLs
                    for attr_name, attr_value in row_attrs.items():
                        if 'data-' in attr_name or 'href' in attr_name or 'onclick' in attr_name:
                            print(f"   📍 Found potential URL attribute: {attr_name} = {attr_value}")
                    
                    # Check if row has class that suggests clickability
                    row_classes = row.get('class', [])
                    if any('hover' in cls or 'click' in cls or 'cursor' in cls for cls in row_classes):
                        print(f"   🖱️ Row appears to be clickable (classes: {row_classes})")
                    
                    # Check individual cells for hidden data
                    cells = row.find_all(['td', 'th'])
                    for j, cell in enumerate(cells):
                        cell_attrs = cell.attrs
                        
                        # Look for data attributes
                        for attr_name, attr_value in cell_attrs.items():
                            if 'data-' in attr_name and ('id' in attr_name or 'url' in attr_name):
                                print(f"   📍 Cell {j+1} has data attribute: {attr_name} = {attr_value}")
            
            # Look for JavaScript that might handle row clicks
            print("\n🔍 Checking for JavaScript click handlers...")
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_content = script.string.lower()
                    if 'onclick' in script_content or 'click' in script_content and 'row' in script_content:
                        print(f"   📜 Found potential click handler script")
                        print(f"   Script preview: {script.string[:200]}...")
            
            # Look for any patterns that might indicate tender IDs
            print("\n🔍 Looking for tender ID patterns...")
            page_content = response.text
            
            # Look for tender ID patterns
            tender_patterns = [
                r'appels-offres/(\d+)',
                r'tender[_-]?id["\']?\s*[:=]\s*["\']?(\d+)',
                r'data-id["\']?\s*[:=]\s*["\']?(\d+)'
            ]
            
            for pattern in tender_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    print(f"   🎯 Found tender ID pattern: {pattern}")
                    print(f"   Sample IDs: {matches[:5]}")
            
            # Try to find if there's a pattern we can use to construct URLs
            print("\n🔍 Attempting to construct URLs from available data...")
            
            # If we can extract tender information, we can construct URLs
            # Format: https://www.appeloffres.net/appels-offres/{tender_id}
            if table:
                rows = table.find_all('tr')
                for i, row in enumerate(rows[1:3], 1):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        title = cells[1].get_text(strip=True)
                        print(f"   📝 Row {i} title: {title[:50]}...")
                        
                        # Try to construct URL using a pattern
                        # Since we don't have direct links, we'll need to use the main listing page
                        # or find another way to get specific tender URLs
                        constructed_url = f"https://www.appeloffres.net/appels-offres"
                        print(f"   🔗 Fallback URL: {constructed_url}")
                        
        else:
            print(f"❌ Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    analyze_tunipages_structure()