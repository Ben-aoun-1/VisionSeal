#!/usr/bin/env python3
"""
Test the fixed TuniPages scraper with proper URL extraction
"""
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_fixed_tunipages():
    """Test the fixed TuniPages scraper"""
    print("🧪 TESTING FIXED TUNIPAGES SCRAPER")
    print("=" * 40)
    
    # Import the fixed scraper
    sys.path.insert(0, str(Path(__file__).parent))
    from tunipages_final_scraper import scrape_tunipages_final
    
    # Run the scraper
    opportunities = await scrape_tunipages_final()
    
    print(f"\n📊 RESULTS:")
    print(f"   Total opportunities: {len(opportunities)}")
    
    # Check URLs
    print(f"\n🔗 URL EXTRACTION CHECK:")
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"   {i}. {opp['title'][:50]}...")
        print(f"      Country: {opp['country']}")
        print(f"      URL: {opp['url']}")
        
        # Check if URL is specific (contains tender ID)
        if 'appels-offres/' in opp['url'] and opp['url'] != 'https://www.appeloffres.net/appels-offres':
            print(f"      ✅ Specific tender URL extracted!")
        else:
            print(f"      ❌ Generic URL - extraction failed")
    
    return opportunities

if __name__ == "__main__":
    asyncio.run(test_fixed_tunipages())