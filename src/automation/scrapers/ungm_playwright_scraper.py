"""
UNGM Playwright Scraper for VisionSeal
Replaces the broken Selenium scraper with working Playwright automation
"""
import asyncio
import time
import uuid
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from core.config.settings import settings
from core.logging.setup import get_logger
from core.database.connection import db_manager
from core.database.repositories import TenderRepository
from models.tender import TenderCreate, TenderSource, TenderStatus

logger = get_logger("ungm_playwright_scraper")


class UNGMPlaywrightScraperError(Exception):
    """Custom exception for UNGM Playwright scraper errors"""
    pass


class UNGMPlaywrightScraper:
    """UNGM scraper using Playwright - African opportunities focus for Topaza.net"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Authentication credentials from .env
        self.username = self.config.get('username') or settings.automation.ungm_username
        self.password = self.config.get('password') or settings.automation.ungm_password
        
        # Scraping configuration
        self.base_url = self.config.get('base_url', 'https://www.ungm.org')
        self.max_pages = self.config.get('max_pages', 5)  # Start small
        self.headless = self.config.get('headless', True)
        self.timeout = self.config.get('timeout', 30000)  # 30 seconds
        self.request_delay = self.config.get('request_delay', 3000)  # 3 seconds
        
        # Search keywords for African consulting opportunities
        self.search_keywords = [
            'consulting', 'advisory services', 'technical assistance',
            'capacity building', 'business development', 'training',
            'management', 'strategy', 'evaluation'
        ]
        
        # All 54 African countries for relevance scoring
        self.african_countries = [
            # North Africa
            'Tunisia', 'Morocco', 'Algeria', 'Egypt', 'Libya', 'Sudan',
            # West Africa  
            'Nigeria', 'Ghana', 'Senegal', 'Mali', 'Burkina Faso', 'Niger',
            'Guinea', 'Sierra Leone', 'Liberia', 'Gambia', 'Cape Verde',
            'Mauritania', 'Benin', 'Togo', 'Ivory Coast', 'Guinea-Bissau',
            'Côte d\'Ivoire', 'Cote d\'Ivoire',
            # East Africa
            'Kenya', 'Ethiopia', 'Tanzania', 'Uganda', 'Rwanda', 'Burundi',
            'Somalia', 'Djibouti', 'Eritrea', 'South Sudan', 'Madagascar',
            'Mauritius', 'Seychelles', 'Comoros',
            # Central Africa
            'Democratic Republic of Congo', 'DRC', 'Congo', 'Cameroon',
            'Central African Republic', 'CAR', 'Chad', 'Gabon', 'Equatorial Guinea',
            'São Tomé and Príncipe', 'Sao Tome',
            # Southern Africa
            'South Africa', 'Botswana', 'Namibia', 'Zimbabwe', 'Zambia',
            'Angola', 'Mozambique', 'Malawi', 'Lesotho', 'Swaziland', 'Eswatini'
        ]
        
        # Major African economies for bonus scoring
        self.major_african_economies = [
            'Nigeria', 'South Africa', 'Kenya', 'Ghana', 'Egypt'
        ]
        
        # Playwright objects
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Session tracking
        self.session_id = str(uuid.uuid4())
        self.session_data = {
            'start_time': datetime.now(timezone.utc),
            'tenders_found': 0,
            'tenders_processed': 0,
            'pages_processed': 0,
            'errors': [],
            'status': 'initializing'
        }
        
        # Initialize database - repository will be created when needed
        db_manager.initialize()
        
        logger.info(f"UNGM Playwright Scraper initialized - Session: {self.session_id}")
    
    async def initialize_browser(self) -> None:
        """Initialize Playwright browser with optimal settings"""
        try:
            logger.info("Initializing Playwright browser...")
            
            self.playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--allow-running-insecure-content',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-gpu'
                ]
            )
            
            # Create context with realistic headers
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.timeout)
            
            # Add stealth measures
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            logger.info("Playwright browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {str(e)}")
            raise UNGMPlaywrightScraperError(f"Browser initialization failed: {str(e)}")
    
    async def login_to_ungm(self) -> bool:
        """Login to UNGM using CONFIRMED working selectors"""
        try:
            logger.info("🔐 Logging in to UNGM using confirmed selectors...")
            
            # Navigate directly to login page (confirmed working)
            await self.page.goto(f'{self.base_url}/Login', 
                                wait_until='networkidle', 
                                timeout=self.timeout)
            
            logger.info("📍 Loaded UNGM login page")
            await self.page.screenshot(path='/tmp/ungm_01_login_page.png')
            
            # Fill username field using CONFIRMED selector
            await self.page.fill('#UserName', self.username)
            logger.info(f"✅ Filled username: {self.username}")
            
            # Fill password field using CONFIRMED selector  
            await self.page.fill('#Password', self.password)
            logger.info("✅ Filled password")
            
            await self.page.screenshot(path='/tmp/ungm_02_credentials_filled.png')
            
            # Click submit button using CONFIRMED selector
            await self.page.click('button[type="submit"]:has-text("Log in")')
            logger.info("🚀 Clicked login button")
            
            # Wait for login to process and redirect - try multiple indicators
            try:
                await self.page.wait_for_selector('text=Tableau De Bord', timeout=15000)
            except:
                # Try alternative dashboard indicators
                try:
                    await self.page.wait_for_selector('text=Dashboard', timeout=5000)
                except:
                    try:
                        await self.page.wait_for_selector('text=Home', timeout=5000)
                    except:
                        # Check if we're logged in by looking for logout link
                        await self.page.wait_for_selector('a:has-text("Logout"), a:has-text("Sign Out"), a:has-text("Déconnexion")', timeout=5000)
            
            logger.info("✅ Successfully logged in to UNGM - Dashboard loaded")
            await self.page.screenshot(path='/tmp/ungm_03_logged_in.png')
            
            # Add small delay as in working JS
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            await self.page.screenshot(path='/tmp/ungm_error_login.png')
            return False
    
    async def navigate_to_opportunities(self) -> bool:
        """Navigate to business opportunities using CONFIRMED selector"""
        try:
            logger.info("📋 Navigating to Business Opportunities...")
            
            # Use CONFIRMED working selector from JS script
            await self.page.click('a:has-text("Opportunités commerciales")')
            
            # Wait for opportunities page to load (confirmed indicator)
            await self.page.wait_for_selector('text=Opportunités Commerciales', timeout=15000)
            
            logger.info("✅ Successfully navigated to Business Opportunities")
            await self.page.screenshot(path='/tmp/ungm_04_opportunities_page.png')
            
            # Add delay as in working JS
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate to Business Opportunities: {str(e)}")
            await self.page.screenshot(path='/tmp/ungm_error_navigation.png')
            return False
    
    async def perform_keyword_search(self, keyword: str) -> bool:
        """Search for opportunities using CONFIRMED selectors from JS"""
        try:
            logger.info(f"🔍 Searching for active opportunities with keyword: '{keyword}'...")
            
            # Clear all search fields using CONFIRMED method from JS
            await self.page.evaluate("""() => {
                document.getElementById('txtNoticeFilterTitle').value = '';
                document.getElementById('txtNoticeFilterDesc').value = '';
                document.getElementById('txtNoticeFilterRef').value = '';
            }""")
            
            # Enter keyword ONLY in title field (CONFIRMED working)
            await self.page.fill('#txtNoticeFilterTitle', keyword)
            logger.info(f"✅ Filled title search with: '{keyword}'")
            
            # Ensure "Actuellement actif uniquement" is checked (CONFIRMED selector)
            await self.page.click('#chkIsActive')
            logger.info("✅ Checked 'Currently active only' filter")
            
            await self.page.screenshot(path=f'/tmp/ungm_05_search_{keyword.replace(" ", "_")}.png')
            
            # Click search button (CONFIRMED selector)
            await self.page.click('button:has-text("Rechercher")')
            logger.info("🚀 Clicked search button")
            
            # Wait for results using CONFIRMED logic from JS
            try:
                await self.page.wait_for_selector('table tbody tr, text="Aucun avis de marché"', timeout=10000)
            except:
                # Continue even if timeout - may still have results
                pass
            
            # Add delay as in working JS
            await asyncio.sleep(3)
            
            logger.info(f"✅ Search completed for keyword: '{keyword}'")
            await self.page.screenshot(path=f'/tmp/ungm_06_results_{keyword.replace(" ", "_")}.png')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Search failed for keyword '{keyword}': {str(e)}")
            await self.page.screenshot(path=f'/tmp/ungm_error_search_{keyword.replace(" ", "_")}.png')
            return False
    
    async def extract_opportunities_from_page(self) -> List[Dict[str, Any]]:
        """Extract opportunities using CONFIRMED table structure"""
        try:
            logger.info("📄 Extracting opportunities from current page...")
            opportunities = []
            
            # Check if there are results using CONFIRMED selector
            try:
                no_results = await self.page.locator('text="Aucun avis de marché"').first()
                if await no_results.is_visible():
                    logger.info("ℹ️ No opportunities found for current search")
                    return []
            except:
                pass
            
            # Wait for results table using CONFIRMED structure
            await self.page.wait_for_selector('table tbody tr', timeout=10000)
            
            # Get all table rows (CONFIRMED working structure)
            rows = await self.page.locator('table tbody tr').all()
            logger.info(f"Found {len(rows)} opportunities on current page")
            
            for i, row in enumerate(rows):
                try:
                    logger.info(f"📋 Processing opportunity {i + 1}/{len(rows)}...")
                    
                    opportunity = await self.extract_opportunity_from_row(row, i + 1)
                    
                    if opportunity and opportunity.get('relevance_score', 0) > 30:
                        opportunities.append(opportunity)
                        logger.info(f"✅ Added opportunity: {opportunity['title'][:50]}... (Score: {opportunity['relevance_score']})")
                    elif opportunity:
                        logger.info(f"⏭️ Skipped low-relevance opportunity: {opportunity['title'][:50]}... (Score: {opportunity['relevance_score']})")
                    
                    # Small delay between extractions
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"❌ Error processing opportunity {i + 1}: {str(e)}")
                    continue
            
            logger.info(f"✅ Extracted {len(opportunities)} relevant opportunities from page")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Failed to extract opportunities from page: {str(e)}")
            return []
    
    async def extract_opportunity_from_row(self, row, index: int) -> Optional[Dict[str, Any]]:
        """Extract opportunity from table row using CONFIRMED structure from JS"""
        try:
            # Get all table cells (confirmed structure from JS)
            cells = await row.locator('td').all()
            if len(cells) < 6:
                logger.warning('⚠️ Insufficient cell data, skipping...')
                return None
            
            # Extract basic information from table cells (CONFIRMED structure)
            basic_info = {
                'title': await self.get_text_content(cells[0]),
                'deadline': await self.get_text_content(cells[1]),
                'publication_date': await self.get_text_content(cells[2]),
                'organization': await self.get_text_content(cells[3]),
                'notice_type': await self.get_text_content(cells[4]),
                'reference': await self.get_text_content(cells[5]),
                'country': await self.get_text_content(cells[6]) if len(cells) > 6 else ''
            }
            
            # Validate we have minimum required data
            if not basic_info['title'] or len(basic_info['title']) < 10:
                return None
            
            # Try to extract detailed information (UNTESTED - handle carefully)
            detailed_info = {}
            document_links = []
            
            try:
                title_link = row.locator('td:first-child a')
                if await title_link.is_visible():
                    logger.info(f"🔗 Extracting detailed info for: {basic_info['title'][:50]}...")
                    
                    # Click into opportunity detail page
                    await title_link.click()
                    await self.page.wait_for_load_state('networkidle', timeout=15000)
                    
                    # Extract detailed information (UNTESTED part)
                    detailed_info = await self.extract_detailed_information()
                    document_links = await self.extract_document_links()
                    
                    await self.page.screenshot(path=f'/tmp/ungm_detail_{index}.png')
                    
                    # Go back to results
                    await self.page.go_back()
                    await self.page.wait_for_load_state('networkidle', timeout=15000)
                    await asyncio.sleep(2)
                    
                    logger.info(f"✅ Detailed extraction completed for opportunity {index}")
                
            except Exception as detail_error:
                logger.warning(f"⚠️ Could not extract detailed information: {detail_error}")
                # Continue with basic info only
            
            # Create comprehensive opportunity object
            opportunity = {
                'id': f"ungm_{self.session_id}_{index}_{int(time.time())}",
                'title': basic_info['title'],
                'description': detailed_info.get('description', basic_info['title']),
                'source': TenderSource.UNGM,
                'country': detailed_info.get('country', basic_info['country']) or self.extract_country_from_text(basic_info['title'] + ' ' + basic_info['organization']),
                'organization': basic_info['organization'],
                'deadline': basic_info['deadline'],
                'url': detailed_info.get('url', self.page.url),
                'reference': basic_info['reference'],
                'status': TenderStatus.ACTIVE,
                'extracted_at': datetime.now(timezone.utc).isoformat(),
                'publication_date': basic_info['publication_date'],
                'notice_type': basic_info['notice_type'],
                'contact_email': detailed_info.get('contactEmail', ''),
                'estimated_budget': detailed_info.get('budget', ''),
                'currency': detailed_info.get('currency', ''),
                'document_links': document_links
            }
            
            # Calculate African relevance score
            opportunity['relevance_score'] = self.calculate_relevance_score_for_opportunity(opportunity)
            
            return opportunity
            
        except Exception as e:
            logger.warning(f"❌ Error extracting opportunity from row {index}: {str(e)}")
            return None
    
    def extract_title_from_text(self, text: str) -> str:
        """Extract title from text content"""
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20 and len(line) < 200:
                return line
        return text[:100] if text else ""
    
    def extract_country_from_text(self, text: str) -> str:
        """Extract African country from text"""
        text_lower = text.lower()
        for country in self.african_countries:
            if country.lower() in text_lower:
                return country
        return ""
    
    def extract_organization_from_text(self, text: str) -> str:
        """Extract organization name from text"""
        # Look for common organization patterns
        org_patterns = [
            r'(UN\w+|United Nations \w+)',
            r'(World Bank|WB)',
            r'(UNDP|UNICEF|WHO|UNESCO)',
            r'(\w+ Ministry|\w+ Government)'
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    def extract_deadline_from_text(self, text: str) -> str:
        """Extract deadline from text"""
        # Look for date patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}\s+\w+\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return ""
    
    def extract_reference_from_text(self, text: str) -> str:
        """Extract reference number from text"""
        ref_patterns = [
            r'REF[:\s]*([A-Z0-9/-]+)',
            r'Reference[:\s]*([A-Z0-9/-]+)',
            r'([A-Z]{2,}\d{2,})',
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def calculate_relevance_score(self, text: str) -> float:
        """Calculate relevance score for African consulting opportunities"""
        score = 0.0
        text_lower = text.lower()
        
        # African country relevance (40 points base)
        african_found = False
        for country in self.african_countries:
            if country.lower() in text_lower:
                score += 40
                african_found = True
                
                # Bonus for major African economies
                if country in self.major_african_economies:
                    score += 10
                break
        
        if not african_found:
            return 0  # Skip non-African opportunities
        
        # Consulting keywords (15 points each)
        consulting_keywords = ['consulting', 'advisory', 'technical assistance']
        for keyword in consulting_keywords:
            if keyword in text_lower:
                score += 15
        
        # Capacity building keywords (10 points each)
        capacity_keywords = ['capacity building', 'training', 'development']
        for keyword in capacity_keywords:
            if keyword in text_lower:
                score += 10
        
        # Management keywords (10 points each)
        management_keywords = ['management', 'strategy', 'business']
        for keyword in management_keywords:
            if keyword in text_lower:
                score += 10
        
        return min(score, 100)  # Cap at 100
    
    def calculate_relevance_score_for_opportunity(self, opportunity: Dict[str, Any]) -> float:
        """Calculate relevance score for extracted opportunity"""
        # Combine all text fields for scoring
        combined_text = ' '.join([
            opportunity.get('title', ''),
            opportunity.get('description', ''),
            opportunity.get('organization', ''),
            opportunity.get('country', '')
        ])
        return self.calculate_relevance_score(combined_text)
    
    async def get_text_content(self, locator) -> str:
        """Safely get text content from a locator"""
        try:
            if locator and await locator.is_visible():
                text = await locator.inner_text()
                return text.strip() if text else ''
            return ''
        except Exception:
            return ''
    
    async def extract_detailed_information(self) -> Dict[str, Any]:
        """Extract detailed information from opportunity detail page (UNTESTED)"""
        detailed_info = {}
        
        try:
            # Extract description (UNTESTED - be careful)
            description_selectors = [
                '[data-field="description"]',
                '.description',
                '#description', 
                'div:has-text("Description")',
                'div:has-text("Summary")',
                'div:has-text("Objective")'
            ]
            
            for selector in description_selectors:
                try:
                    element = self.page.locator(selector).first()
                    if await element.is_visible():
                        detailed_info['description'] = await element.inner_text()
                        break
                except:
                    continue
            
            # Extract contact information (UNTESTED)
            contact_selectors = [
                '[data-field="contact"]',
                'a[href^="mailto:"]',
                'div:has-text("Contact")',
                'div:has-text("Email")'
            ]
            
            for selector in contact_selectors:
                try:
                    element = self.page.locator(selector).first()
                    if await element.is_visible():
                        text = await element.inner_text()
                        if '@' in text:
                            detailed_info['contactEmail'] = text
                            break
                except:
                    continue
            
            # Extract budget information (UNTESTED)
            budget_selectors = [
                '[data-field="budget"]',
                'div:has-text("Budget")',
                'div:has-text("Value")',
                'div:has-text("Amount")'
            ]
            
            for selector in budget_selectors:
                try:
                    element = self.page.locator(selector).first()
                    if await element.is_visible():
                        detailed_info['budget'] = await element.inner_text()
                        break
                except:
                    continue
            
            # Current page URL
            detailed_info['url'] = self.page.url
            
        except Exception as e:
            logger.warning(f"Error extracting detailed information: {str(e)}")
        
        return detailed_info
    
    async def extract_document_links(self) -> List[str]:
        """Extract document download links (UNTESTED)"""
        document_links = []
        
        try:
            # Look for common document link patterns (UNTESTED)
            link_selectors = [
                'a[href*=".pdf"]',
                'a[href*=".doc"]',
                'a[href*=".docx"]',
                'a:has-text("Download")',
                'a:has-text("Document")',
                'a:has-text("Attachment")'
            ]
            
            for selector in link_selectors:
                try:
                    links = await self.page.locator(selector).all()
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and href not in document_links:
                            document_links.append(href)
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting document links: {str(e)}")
        
        return document_links
    
    async def save_opportunities(self, opportunities: List[Dict[str, Any]]) -> int:
        """Save opportunities to database"""
        saved_count = 0
        
        # Create database session and repository
        with db_manager.get_session() as session:
            tender_repo = TenderRepository(session)
            
            for opp_data in opportunities:
                try:
                    # Create TenderCreate object
                    tender = TenderCreate(**opp_data)
                    
                    # Save to database
                    saved_tender = tender_repo.create(tender)
                    if saved_tender:
                        saved_count += 1
                        logger.info(f"Saved opportunity: {tender.title[:50]}... (Score: {tender.relevance_score})")
                    
                except Exception as e:
                    logger.error(f"Failed to save opportunity: {str(e)}")
                    continue
        
        return saved_count
    
    async def search_opportunities(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for opportunities with a specific keyword"""
        try:
            # Perform search
            search_success = await self.perform_keyword_search(keyword)
            if not search_success:
                logger.warning(f"Search failed for keyword: {keyword}")
                return []
            
            # Extract opportunities from results
            opportunities = await self.extract_opportunities_from_page()
            
            logger.info(f"Found {len(opportunities)} opportunities for keyword '{keyword}'")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error searching for keyword '{keyword}': {str(e)}")
            return []
    
    async def run_scraping_session(self) -> Dict[str, Any]:
        """Run complete scraping session"""
        try:
            logger.info("Starting UNGM scraping session...")
            self.session_data['status'] = 'running'
            
            # Initialize browser
            await self.initialize_browser()
            
            # Login to UNGM
            login_success = await self.login_to_ungm()
            if not login_success:
                logger.warning("Login failed, continuing with public access...")
            
            # Navigate to opportunities
            nav_success = await self.navigate_to_opportunities()
            if not nav_success:
                logger.warning("Could not navigate to opportunities, trying direct search...")
            
            # Search for opportunities with each keyword
            all_opportunities = []
            
            for keyword in self.search_keywords[:3]:  # Limit to first 3 keywords for testing
                try:
                    opportunities = await self.search_opportunities(keyword)
                    all_opportunities.extend(opportunities)
                    
                    # Delay between searches
                    await asyncio.sleep(self.request_delay / 1000)
                    
                except Exception as e:
                    logger.error(f"Search failed for keyword {keyword}: {str(e)}")
                    continue
            
            # Remove duplicates
            unique_opportunities = []
            seen_titles = set()
            
            for opp in all_opportunities:
                if opp['title'] not in seen_titles:
                    unique_opportunities.append(opp)
                    seen_titles.add(opp['title'])
            
            # Save to database
            saved_count = await self.save_opportunities(unique_opportunities)
            
            # Update session data
            self.session_data.update({
                'status': 'completed',
                'tenders_found': len(unique_opportunities),
                'tenders_processed': saved_count,
                'pages_processed': 1,
                'end_time': datetime.now(timezone.utc)
            })
            
            logger.info(f"Scraping session completed: {saved_count} opportunities saved")
            return self.session_data
            
        except Exception as e:
            logger.error(f"Scraping session failed: {str(e)}")
            self.session_data.update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now(timezone.utc)
            })
            return self.session_data
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            logger.info("Browser cleanup completed")
            
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        return self.session_data.copy()


# Async wrapper for integration with existing system
async def run_ungm_playwright_scraper(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run UNGM Playwright scraper"""
    scraper = UNGMPlaywrightScraper(config)
    return await scraper.run_scraping_session()


# Sync wrapper for backward compatibility
def run_ungm_scraping_session(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sync wrapper for UNGM Playwright scraper"""
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_running_loop()
        # If we are, create a new thread to run the async function
        import concurrent.futures
        import threading
        
        def run_in_thread():
            return asyncio.run(run_ungm_playwright_scraper(config))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(run_ungm_playwright_scraper(config))


if __name__ == "__main__":
    # Test the scraper
    result = run_ungm_scraping_session({
        'max_pages': 2,
        'headless': False  # Set to True for production
    })
    print(f"Scraping result: {result}")