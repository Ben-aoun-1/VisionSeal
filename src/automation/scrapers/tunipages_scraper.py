#!/usr/bin/env python3
"""
TuniPages Fixed Scraper - With Correct Selectors from Real HTML
Based on actual HTML structure from appeloffres.net
"""

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
import time
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import uuid
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseTenderSaver:
    """Handles saving tender data to Supabase database"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        # Use SERVICE_KEY for scrapers (bypasses RLS)
        self.key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        
        self.client = create_client(self.url, self.key)
    
    def save_tender(self, tender_data: Dict[str, Any], source: str = "TUNIPAGES") -> Dict[str, Any]:
        """Save a single tender to Supabase"""
        try:
            # Prepare data for Supabase
            supabase_data = {
                "id": str(uuid.uuid4()),
                "title": tender_data.get("title", "")[:500],  # Truncate to avoid issues
                "description": tender_data.get("description", ""),
                "source": source,
                "country": tender_data.get("country", "")[:100],
                "organization": tender_data.get("organization", "")[:200],
                "deadline": self._parse_date(tender_data.get("deadline")),
                "publication_date": self._parse_date(tender_data.get("publication_date")),
                "url": tender_data.get("url", ""),
                "reference": tender_data.get("reference", "")[:100],
                "status": "ACTIVE",
                "notice_type": tender_data.get("type", "Request for Proposal")[:100],
                "relevance_score": float(tender_data.get("relevance_score", 50.0)),
                "estimated_budget": tender_data.get("estimated_budget", "")[:200] if tender_data.get("estimated_budget") else None,
                "currency": tender_data.get("currency", "")[:10] if tender_data.get("currency") else None,
                "contact_email": tender_data.get("contact_email", "")[:100] if tender_data.get("contact_email") else None,
                "document_links": tender_data.get("document_links", []),
                "additional_data": {
                    "original_data": tender_data,
                    "extracted_fields": list(tender_data.keys())
                },
                "extracted_at": datetime.now().isoformat()
            }
            
            # Insert into Supabase (upsert to handle duplicates)
            response = self.client.table('tenders').upsert(supabase_data, on_conflict="url").execute()
            
            return {
                "success": True,
                "id": supabase_data["id"],
                "message": "Tender saved successfully",
                "upserted": len(response.data) > 0
            }
            
        except Exception as e:
            logger.error(f"Error saving tender to Supabase: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_tenders_batch(self, tenders: List[Dict[str, Any]], source: str = "TUNIPAGES") -> Dict[str, Any]:
        """Save multiple tenders to Supabase"""
        try:
            saved_count = 0
            errors = []
            
            for i, tender in enumerate(tenders):
                try:
                    result = self.save_tender(tender, source)
                    if result["success"]:
                        saved_count += 1
                        if i % 10 == 0:  # Log every 10 saves
                            logger.info(f"Saved {saved_count}/{len(tenders)} tenders to Supabase")
                    else:
                        errors.append(f"Tender {i}: {result['error']}")
                except Exception as e:
                    errors.append(f"Tender {i}: {str(e)}")
                    
            return {
                "success": True,
                "saved_count": saved_count,
                "total_count": len(tenders),
                "errors": errors[:10]  # Limit error list
            }
            
        except Exception as e:
            logger.error(f"Error in batch save: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string to ISO format"""
        if not date_str or date_str == "Unknown":
            return None
        
        try:
            # Try different date formats
            formats = [
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%m/%d/%Y"
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.date().isoformat()
                except ValueError:
                    continue
            
            # If no format works, return None
            return None
            
        except Exception:
            return None

def calculate_relevance_score(tender_data: Dict[str, Any]) -> float:
    """Calculate relevance score based on country, keywords, deadline, and organization"""
    score = 50.0  # Base score
    
    # ALL African countries boost (+20 points) for maximum coverage
    african_countries = [
        "tunisie", "tunisia", "algérie", "algeria", "maroc", "morocco",
        "sénégal", "senegal", "côte d'ivoire", "ivory coast", "burkina faso",
        "mali", "niger", "tchad", "chad", "cameroun", "cameroon",
        "gabon", "congo", "madagascar", "mauritanie", "mauritania",
        "djibouti", "comores", "comoros", "egypt", "égypte", "libya", "libye",
        "sudan", "soudan", "ethiopia", "éthiopie", "kenya", "uganda", "ouganda",
        "tanzania", "tanzanie", "rwanda", "burundi", "south africa", "afrique du sud",
        "nigeria", "ghana", "sierra leone", "liberia", "guinea", "guinée",
        "zambia", "zambie", "zimbabwe", "botswana", "namibia", "namibie",
        "angola", "mozambique", "malawi", "lesotho", "swaziland", "eswatini",
        "central african republic", "république centrafricaine", "democratic republic of congo",
        "république démocratique du congo", "equatorial guinea", "guinée équatoriale",
        "sao tome", "cape verde", "cap-vert", "seychelles", "mauritius", "maurice",
        "gambia", "gambie", "benin", "bénin", "togo", "eritrea", "érythrée",
        "somalia", "somalie", "south sudan", "soudan du sud", "africa", "afrique",
        "african", "africain", "africaine", "autres pays d'afrique"
    ]
    
    country_text = tender_data.get("country", "").lower()
    if any(country in country_text for country in african_countries):
        score += 20
    
    # French consulting/training keywords (+15 points)
    priority_keywords = [
        "formation", "emploi", "entrepreneuriat", "consulting", "assistance technique",
        "conseil", "expertise", "consultant", "expert", "coaching", "mentorat",
        "renforcement des capacités", "appui", "accompagnement", "évaluation",
        "étude", "audit", "diagnostic", "stratégie", "développement"
    ]
    
    text = f"{tender_data.get('title', '')} {tender_data.get('description', '')}".lower()
    matching_keywords = sum(1 for keyword in priority_keywords if keyword in text)
    score += min(matching_keywords * 5, 15)  # Max 15 points for keywords
    
    # Recent deadline boost (+10 points)
    try:
        deadline_str = tender_data.get('deadline', '')
        if deadline_str and deadline_str != "Unknown":
            # Try to parse French date format (DD/MM/YYYY)
            date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', deadline_str)
            if date_match:
                day, month, year = date_match.groups()
                deadline = datetime(int(year), int(month), int(day))
                days_until = (deadline - datetime.now()).days
                if 0 <= days_until <= 30:  # Deadline within 30 days
                    score += 10
    except:
        pass
    
    # Major organizations boost (+5 points)
    major_orgs = [
        "banque mondiale", "world bank", "pnud", "undp", "unicef", "oms", "who",
        "banque africaine de développement", "bad", "afdb", "union européenne",
        "ue", "eu", "afd", "agence française de développement", "giz", "usaid"
    ]
    
    org_text = tender_data.get("organization", "").lower()
    if any(org in org_text for org in major_orgs):
        score += 5
    
    return min(score, 100.0)

async def login_tunipages(page, credentials: Dict[str, str]) -> bool:
    """Handle TuniPages authentication"""
    try:
        logger.info("Attempting to login to TuniPages...")
        logger.info("Navigating to TuniPages login page...")
        
        # Navigate to login page
        await page.goto("https://www.appeloffres.net/connexion", wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(3)
        
        # Handle cookies if present
        try:
            cookie_button = await page.query_selector('button:has-text("Accepter"), button:has-text("Accept")')
            if cookie_button:
                await cookie_button.click()
                await asyncio.sleep(1)
        except:
            pass
        
        # Fill login form
        await page.fill('input[type="email"], input[name="email"]', credentials['username'])
        logger.info("Email field filled")
        
        await page.fill('input[type="password"], input[name="password"]', credentials['password'])
        logger.info("Password field filled")
        
        # Submit form
        await page.click('button[type="submit"], input[type="submit"]')
        logger.info("Login form submitted")
        
        # Wait for navigation and check if login successful
        await page.wait_for_load_state('networkidle', timeout=15000)
        await asyncio.sleep(2)
        
        # Check for successful login (look for user menu, dashboard, or absence of login form)
        success_indicators = [
            'a:has-text("Mon compte")',
            '.user-menu',
            'a:has-text("Déconnexion")',
            'a:has-text("Logout")'
        ]
        
        for indicator in success_indicators:
            element = await page.query_selector(indicator)
            if element:
                logger.info("Login successful!")
                return True
        
        # Also check if we're redirected away from login page
        current_url = page.url
        if 'connexion' not in current_url and 'login' not in current_url:
            logger.info("Login successful!")
            return True
        
        logger.error("Login failed - no success indicators found")
        return False
        
    except Exception as e:
        logger.error(f"Login failed with exception: {e}")
        return False

async def scrape_tunipages_page(page, page_num: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape a single TuniPages page with correct selectors"""
    tenders = []
    
    try:
        logger.info(f"Scraping page {page_num}...")
        
        # Navigate to the specific page using correct URL structure
        if page_num > 1:
            try:
                page_url = f"https://www.appeloffres.net/appels-offres?status=active&page={page_num}"
                await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)  # Wait for content to load
                logger.info(f"Navigated to page {page_num} via URL")
            except Exception as e:
                logger.warning(f"Could not navigate to page {page_num}: {e}")
                return []
        
        await asyncio.sleep(2)  # Wait for content to load
        
        # NEW VERSION SELECTORS - Based on actual HTML structure from debugging
        # Find tender links - they have a very specific class
        tender_elements = await page.query_selector_all('a.p-8.group.space-y-6.bg-white')
        
        logger.info(f"Processing {len(tender_elements)} tender elements")
        
        # Extract data from each tender element
        for element in tender_elements:
            try:
                tender_data = {}
                
                # Extract URL directly from the link
                href = await element.get_attribute('href')
                if href:
                    tender_data["url"] = href
                
                # Extract title - it's in a div with specific classes: .text-base.md:text-lg.font-semibold.text-primary
                title_element = await element.query_selector('.text-base.font-semibold.text-primary, .text-lg.font-semibold.text-primary')
                if title_element:
                    title_text = await title_element.inner_text()
                    tender_data["title"] = title_text.strip() if title_text else "Unknown Title"
                else:
                    tender_data["title"] = "Unknown Title"
                
                # Extract description - it's in a gray text div below title: .text-gray-500.text-xs.md:text-sm
                desc_elements = await element.query_selector_all('.text-gray-500.text-xs, .text-gray-500.text-sm')
                description = ""
                for desc_elem in desc_elements:
                    desc_text = await desc_elem.inner_text()
                    # Look for actual description text (not dates, not promoter info)
                    if desc_text and len(desc_text) > 10 and "Promoteur:" not in desc_text and "Publié le:" not in desc_text:
                        description = desc_text.strip()
                        break
                tender_data["description"] = description
                
                # Extract country - it's in uppercase font-bold text: .text-xs.md:text-sm.font-bold.text-gray-600.uppercase
                country_element = await element.query_selector('.font-bold.text-gray-600.uppercase')
                if country_element:
                    country_text = await country_element.inner_text()
                    tender_data["country"] = country_text.strip() if country_text else "Unknown"
                else:
                    tender_data["country"] = "Unknown"
                
                # Extract organization/promoter - look for text after "Promoteur:"
                org_text = await element.inner_text()
                org_match = re.search(r'Promoteur:\s*(.+?)(?:\n|Expire le:|$)', org_text, re.IGNORECASE | re.DOTALL)
                if org_match:
                    tender_data["organization"] = org_match.group(1).strip()
                else:
                    tender_data["organization"] = "Unknown"
                
                # Extract deadline - look for text after "Expire le:"
                deadline_match = re.search(r'Expire le:\s*(.+?)(?:\n|$)', org_text, re.IGNORECASE)
                if deadline_match:
                    deadline_text = deadline_match.group(1).strip()
                    tender_data["deadline"] = deadline_text
                else:
                    tender_data["deadline"] = "Unknown"
                
                # Extract type - it's in the gray text above title: .text-gray-500.text-sm.font-bold
                type_element = await element.query_selector('.text-gray-500.text-sm.font-bold')
                if type_element:
                    type_text = await type_element.inner_text()
                    tender_data["type"] = type_text.strip() if type_text else "Unknown"
                else:
                    tender_data["type"] = "Unknown"
                
                # Set additional defaults
                tender_data.setdefault("reference", "")
                tender_data.setdefault("publication_date", "")
                tender_data.setdefault("estimated_budget", "")
                tender_data.setdefault("contact_email", "")
                
                # Calculate relevance score
                tender_data["relevance_score"] = calculate_relevance_score(tender_data)
                
                # Only include if we have meaningful data
                if tender_data["title"] != "Unknown Title" and tender_data["url"]:
                    tenders.append(tender_data)
                
            except Exception as e:
                logger.warning(f"Error extracting tender data: {e}")
                continue
        
        logger.info(f"Extracted {len(tenders)} relevant tenders from page {page_num}")
        return tenders
        
    except Exception as e:
        logger.error(f"Error scraping page {page_num}: {e}")
        return []

async def run_tunipages_scraping(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main TuniPages scraping function with correct selectors
    """
    start_time = time.time()
    tenders = []
    pages_processed = 0
    authentication_success = False
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=config.get('headless', True),
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # Create context with French locale
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='fr-FR'
            )
            
            page = await context.new_page()
            page.set_default_timeout(config.get('timeout', 30) * 1000)
            
            # Step 1: Authenticate
            credentials = config.get('credentials', {})
            if not credentials.get('username') or not credentials.get('password'):
                raise Exception("Missing credentials in config")
            
            authentication_success = await login_tunipages(page, credentials)
            
            if not authentication_success:
                raise Exception("Authentication failed - please check credentials")
            
            logger.info("Login successful, proceeding to tender search...")
            
            # Step 2: Navigate to active tender listing
            logger.info("Navigating to active tender listing...")
            try:
                await page.goto("https://www.appeloffres.net/appels-offres?status=active", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)  # Wait for content to load
                logger.info("Successfully navigated to active tenders page")
            except Exception as e:
                logger.warning(f"Error navigating to tender listing: {e}")
                return {
                    "success": False,
                    "tenders_found": 0,
                    "tenders_processed": 0,
                    "pages_processed": 0,
                    "authentication_success": authentication_success,
                    "tenders": [],
                    "error": f"Navigation failed: {e}",
                    "metadata": {
                        "source": "tunipages",
                        "execution_time": time.time() - start_time,
                        "config_used": config,
                        "login_attempt": True,
                        "session_valid": False
                    }
                }
            
            # Step 3: Scrape pages
            max_pages = config.get('max_pages', 10)
            if config.get('test_mode', False):
                max_pages = min(max_pages, 2)
            
            for page_num in range(1, max_pages + 1):
                try:
                    page_tenders = await scrape_tunipages_page(page, page_num, config)
                    tenders.extend(page_tenders)
                    pages_processed += 1
                    
                    # Delay between pages
                    if page_num < max_pages:
                        await asyncio.sleep(config.get('request_delay', 2))
                    
                except Exception as e:
                    logger.error(f"Error on page {page_num}: {e}")
                    continue
            
            await browser.close()
            
            # Save tenders to Supabase
            supabase_result = {"saved_count": 0, "errors": []}
            
            if tenders and config.get('save_to_supabase', True):
                try:
                    logger.info(f"Saving {len(tenders)} tenders to Supabase...")
                    saver = SupabaseTenderSaver()
                    supabase_result = saver.save_tenders_batch(tenders, "TUNIPAGES")
                    
                    if supabase_result["success"]:
                        logger.info(f"✅ Successfully saved {supabase_result['saved_count']}/{len(tenders)} tenders to Supabase")
                        if supabase_result["errors"]:
                            logger.warning(f"Encountered {len(supabase_result['errors'])} errors during save")
                    else:
                        logger.error(f"❌ Supabase save failed: {supabase_result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ Error initializing Supabase saver: {e}")
                    supabase_result = {"saved_count": 0, "errors": [str(e)]}
            
            return {
                "success": True,
                "tenders_found": len(tenders),
                "tenders_processed": len(tenders),
                "pages_processed": pages_processed,
                "authentication_success": authentication_success,
                "tenders": tenders,
                "error": None,
                "supabase_result": supabase_result,
                "metadata": {
                    "source": "tunipages",
                    "execution_time": time.time() - start_time,
                    "config_used": config,
                    "login_attempt": True,
                    "session_valid": True
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "tenders_found": 0,
            "tenders_processed": 0,
            "pages_processed": pages_processed,
            "authentication_success": authentication_success,
            "tenders": [],
            "error": str(e),
            "metadata": {
                "source": "tunipages",
                "execution_time": time.time() - start_time,
                "config_used": config,
                "login_attempt": True,
                "session_valid": False
            }
        }




# Test the scraper
if __name__ == "__main__":
    async def test_scraper():
        config = {
            "max_pages": 50,  # Increased for maximum extraction
            "headless": True,  # Faster scraping
            "test_mode": False,
            "request_delay": 1,  # Faster between pages
            "credentials": {
                "username": os.getenv("TUNIPAGES_USERNAME"),
                "password": os.getenv("TUNIPAGES_PASSWORD")
            }
        }
        
        # Validate credentials
        if not config["credentials"]["username"] or not config["credentials"]["password"]:
            print("❌ Error: TuniPages credentials not found in environment variables")
            print("Please set TUNIPAGES_USERNAME and TUNIPAGES_PASSWORD")
            return
        
        result = await run_tunipages_scraping(config)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test_scraper())