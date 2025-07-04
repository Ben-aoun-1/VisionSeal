"""
Enhanced UNGM Scraper with Python/Playwright
Improved version of the original Node.js automation with better error handling and database integration
"""
import asyncio
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from core.config.settings import settings
from core.logging.setup import get_logger
from core.database.connection import db_manager
from core.database.repositories import TenderRepository, AutomationSessionRepository
from models.tender import TenderCreate, TenderSource, TenderCategory, TenderStatus

logger = get_logger("ungm_scraper")


class UNGMScraperError(Exception):
    """Custom exception for UNGM scraper errors"""
    pass


class UNGMScraper:
    """Enhanced UNGM scraper with improved reliability and database integration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Authentication credentials
        self.username = self.config.get('username') or settings.automation.ungm_username
        self.password = self.config.get('password') or settings.automation.ungm_password
        
        # Scraping configuration
        self.base_url = self.config.get('base_url', 'https://www.ungm.org')
        self.max_pages = self.config.get('max_pages', settings.automation.max_pages)
        self.headless = self.config.get('headless', settings.automation.headless)
        self.timeout = self.config.get('timeout', settings.automation.timeout)
        self.request_delay = self.config.get('request_delay', 2000)  # 2 seconds
        
        # Search parameters
        self.search_terms = self.config.get('search_terms', [
            'consulting', 'technical assistance', 'advisory services',
            'capacity building', 'business development', 'entrepreneurship',
            'innovation', 'digital transformation', 'sustainability'
        ])
        
        self.target_countries = self.config.get('target_countries', [
            'Tunisia', 'Morocco', 'Algeria', 'Egypt', 'Libya',
            'Nigeria', 'Kenya', 'Ghana', 'Senegal', 'Ethiopia'
        ])
        
        # Browser instances
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
            'authenticated': False
        }
        
        # Improved selectors based on UNGM site structure
        self.selectors = {
            # Authentication
            'login_link': 'a[href*="login"], .login-link, #loginLink',
            'username_input': 'input[name="username"], input[id="username"], #loginName',
            'password_input': 'input[name="password"], input[id="password"], #password',
            'login_button': 'button[type="submit"], input[type="submit"], .login-button',
            'logout_link': 'a[href*="logout"], .logout-link',
            
            # Search and navigation
            'search_input': 'input[name="search"], #search, .search-input',
            'search_button': 'button[type="submit"], .search-button, #searchButton',
            'advanced_search': 'a[href*="advanced"], .advanced-search',
            
            # Opportunity listings
            'opportunity_table': 'table[role="grid"], .opportunities-table, #opportunitiesGrid',
            'opportunity_rows': 'table[role="grid"] tbody tr, .opportunity-row',
            'opportunity_link': 'a[href*="/Public/Notice/"], a[href*="Notice"]',
            'opportunity_title': 'td:nth-child(1) a, .opportunity-title, .title-cell',
            'deadline_cell': 'td:nth-child(2), .deadline-cell',
            'published_cell': 'td:nth-child(3), .published-cell',
            'organization_cell': 'td:nth-child(4), .organization-cell',
            'type_cell': 'td:nth-child(5), .type-cell',
            'reference_cell': 'td:nth-child(6), .reference-cell',
            'country_cell': 'td:nth-child(7), .country-cell',
            
            # Pagination
            'next_page': 'a[aria-label="Next"], .next-page, button:contains("Next")',
            'page_numbers': '.pagination a, .page-number',
            'current_page': '.pagination .active, .current-page',
            
            # Detail page elements
            'detail_container': '.notice-detail, .opportunity-detail, .main-content',
            'description_section': '.description, .summary, .opportunity-description',
            'contact_section': '.contact, .contact-info, .contact-details',
            'deadline_section': '.deadline, .closing-date, .submission-deadline',
            'value_section': '.value, .budget, .contract-value',
            'documents_section': '.attachments, .documents, .files, .related-documents',
            'document_links': 'a[href*="attachment"], a[href*="document"], a[download]',
            
            # Filters and options
            'country_filter': 'select[name*="country"], #countryFilter',
            'type_filter': 'select[name*="type"], #typeFilter',
            'status_filter': 'select[name*="status"], #statusFilter'
        }
        
        logger.info(f"UNGM Scraper initialized - Session: {self.session_id}")
    
    async def initialize_browser(self) -> None:
        """Initialize Playwright browser with optimal settings"""
        try:
            playwright = await async_playwright().start()
            
            # Launch browser with secure settings
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows'
                ]
            )
            
            # Create context with realistic user agent
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                accept_downloads=True
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set timeout
            self.page.set_default_timeout(self.timeout)
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise UNGMScraperError(f"Browser initialization failed: {str(e)}")
    
    async def authenticate(self) -> bool:
        """Authenticate with UNGM platform"""
        try:
            logger.info("Starting UNGM authentication...")
            
            # Navigate to UNGM homepage
            await self.page.goto(self.base_url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Look for login link
            login_selectors = self.selectors['login_link'].split(', ')
            login_element = None
            
            for selector in login_selectors:
                try:
                    login_element = await self.page.wait_for_selector(selector, timeout=5000)
                    if login_element:
                        logger.info(f"Found login link with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_element:
                logger.warning("Login link not found, checking if already logged in")
                # Check if already authenticated
                logout_element = await self.page.query_selector(self.selectors['logout_link'])
                if logout_element:
                    logger.info("Already authenticated")
                    self.session_data['authenticated'] = True
                    return True
                else:
                    raise UNGMScraperError("Login link not found and not authenticated")
            
            # Click login link
            await login_element.click()
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Fill credentials
            username_input = await self.page.wait_for_selector(self.selectors['username_input'])
            password_input = await self.page.wait_for_selector(self.selectors['password_input'])
            login_button = await self.page.wait_for_selector(self.selectors['login_button'])
            
            await username_input.fill(self.username)
            await asyncio.sleep(1)
            await password_input.fill(self.password)
            await asyncio.sleep(1)
            
            # Submit login
            await login_button.click()
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Verify authentication
            current_url = self.page.url
            logout_element = await self.page.query_selector(self.selectors['logout_link'])
            
            if logout_element or 'dashboard' in current_url.lower():
                logger.info("Authentication successful")
                self.session_data['authenticated'] = True
                return True
            else:
                raise UNGMScraperError("Authentication failed - no logout link found")
                
        except Exception as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
    
    async def search_opportunities(self, search_term: str = None) -> None:
        """Navigate to opportunities search with filters"""
        try:
            search_term = search_term or ' OR '.join(self.search_terms)
            
            # Navigate to opportunities/notices page
            opportunities_url = f"{self.base_url}/Public/Notice"
            await self.page.goto(opportunities_url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Apply search if search input exists
            search_input = await self.page.query_selector(self.selectors['search_input'])
            if search_input:
                await search_input.fill(search_term)
                await asyncio.sleep(1)
                
                search_button = await self.page.query_selector(self.selectors['search_button'])
                if search_button:
                    await search_button.click()
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
            
            logger.info(f"Navigated to opportunities page with search: {search_term}")
            
        except Exception as e:
            error_msg = f"Failed to search opportunities: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            raise UNGMScraperError(error_msg)
    
    async def extract_opportunities_from_page(self) -> List[Dict[str, Any]]:
        """Extract opportunity data from current page"""
        opportunities = []
        
        try:
            # Wait for opportunities table
            table = await self.page.wait_for_selector(self.selectors['opportunity_table'], timeout=10000)
            if not table:
                logger.warning("No opportunities table found")
                return opportunities
            
            # Get all opportunity rows
            rows = await self.page.query_selector_all(self.selectors['opportunity_rows'])
            logger.info(f"Found {len(rows)} opportunity rows")
            
            for i, row in enumerate(rows):
                try:
                    opportunity = await self.extract_opportunity_from_row(row, i)
                    if opportunity and self.is_relevant_opportunity(opportunity):
                        opportunities.append(opportunity)
                        self.session_data['tenders_found'] += 1
                        
                        # Add delay between extractions
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"Failed to extract opportunity from row {i}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(opportunities)} relevant opportunities")
            return opportunities
            
        except Exception as e:
            error_msg = f"Failed to extract opportunities from page: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return opportunities
    
    async def extract_opportunity_from_row(self, row, index: int) -> Optional[Dict[str, Any]]:
        """Extract opportunity data from a table row"""
        try:
            # Extract basic information from row cells
            cells = await row.query_selector_all('td')
            if len(cells) < 4:
                return None
            
            # Get opportunity link and title
            title_link = await row.query_selector(self.selectors['opportunity_link'])
            if not title_link:
                return None
                
            title = await title_link.text_content()
            url = await title_link.get_attribute('href')
            
            # Make URL absolute if relative
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}" if url.startswith('/') else f"{self.base_url}/{url}"
            
            # Extract other cell data
            deadline = await self.extract_cell_text(cells, 1) if len(cells) > 1 else None
            published = await self.extract_cell_text(cells, 2) if len(cells) > 2 else None
            organization = await self.extract_cell_text(cells, 3) if len(cells) > 3 else None
            opp_type = await self.extract_cell_text(cells, 4) if len(cells) > 4 else None
            reference = await self.extract_cell_text(cells, 5) if len(cells) > 5 else None
            country = await self.extract_cell_text(cells, 6) if len(cells) > 6 else None
            
            # Parse dates
            published_date = self.parse_date(published)
            deadline_date = self.parse_date(deadline)
            
            # Generate unique ID
            opportunity_id = f"ungm_{uuid.uuid4().hex[:12]}"
            
            opportunity = {
                'id': opportunity_id,
                'title': title.strip() if title else '',
                'url': url,
                'deadline': deadline.strip() if deadline else '',
                'deadline_date': deadline_date,
                'published': published.strip() if published else '',
                'published_date': published_date,
                'organization': organization.strip() if organization else '',
                'type': opp_type.strip() if opp_type else '',
                'reference': reference.strip() if reference else '',
                'country': country.strip() if country else '',
                'source': 'UNGM Enhanced',
                'extracted_at': datetime.now(timezone.utc).isoformat(),
                'relevance_score': self.calculate_relevance_score({
                    'title': title or '',
                    'type': opp_type or '',
                    'country': country or ''
                })
            }
            
            return opportunity
            
        except Exception as e:
            logger.warning(f"Failed to extract opportunity from row {index}: {str(e)}")
            return None
    
    async def extract_cell_text(self, cells, index: int) -> Optional[str]:
        """Extract text content from table cell"""
        try:
            if index < len(cells):
                text = await cells[index].text_content()
                return text.strip() if text else None
            return None
        except:
            return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        if not date_str:
            return None
            
        try:
            # Common UNGM date formats
            date_formats = [
                '%d/%m/%Y %H:%M',
                '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%m/%d/%Y'
            ]
            
            date_str = date_str.strip()
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {str(e)}")
            
        return None
    
    def calculate_relevance_score(self, opportunity: Dict[str, str]) -> float:
        """Calculate relevance score based on title, type, and country"""
        score = 0.0
        
        title = opportunity.get('title', '').lower()
        opp_type = opportunity.get('type', '').lower()
        country = opportunity.get('country', '').lower()
        
        # Score based on search terms in title
        for term in self.search_terms:
            if term.lower() in title:
                score += 15.0
        
        # Score based on target countries
        for target_country in self.target_countries:
            if target_country.lower() in country:
                score += 25.0
                break
        
        # Score based on opportunity type
        relevant_types = ['consulting', 'advisory', 'services', 'technical', 'capacity']
        for rel_type in relevant_types:
            if rel_type in opp_type:
                score += 10.0
        
        # Bonus for business development related terms
        business_terms = ['business', 'development', 'entrepreneurship', 'innovation']
        for term in business_terms:
            if term in title:
                score += 10.0
        
        return min(score, 100.0)  # Cap at 100
    
    def is_relevant_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity meets relevance criteria"""
        relevance_score = opportunity.get('relevance_score', 0)
        
        # Minimum relevance threshold
        if relevance_score < 20.0:
            return False
        
        # Check if deadline is in the future
        deadline_date = opportunity.get('deadline_date')
        if deadline_date and deadline_date < datetime.now(timezone.utc):
            return False
        
        return True
    
    async def has_next_page(self) -> bool:
        """Check if there's a next page available"""
        try:
            next_button = await self.page.query_selector(self.selectors['next_page'])
            if next_button:
                # Check if button is enabled
                disabled = await next_button.get_attribute('disabled')
                aria_disabled = await next_button.get_attribute('aria-disabled')
                class_list = await next_button.get_attribute('class')
                
                if disabled or aria_disabled == 'true' or (class_list and 'disabled' in class_list):
                    return False
                return True
            return False
        except:
            return False
    
    async def go_to_next_page(self) -> bool:
        """Navigate to next page"""
        try:
            next_button = await self.page.query_selector(self.selectors['next_page'])
            if next_button:
                await next_button.click()
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(self.request_delay / 1000)  # Convert to seconds
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to go to next page: {str(e)}")
            return False
    
    async def save_opportunities_to_database(self, opportunities: List[Dict[str, Any]]) -> None:
        """Save extracted opportunities to database"""
        try:
            with db_manager.session_scope() as session:
                tender_repo = TenderRepository(session)
                
                for opp in opportunities:
                    try:
                        # Map opportunity data to tender model
                        tender_data = TenderCreate(
                            id=opp['id'],
                            title=opp['title'],
                            description=f"UNGM Opportunity: {opp.get('type', '')}",
                            source=TenderSource.UNGM,
                            country=opp.get('country'),
                            organization=opp.get('organization'),
                            published_date=opp.get('published_date'),
                            deadline=opp.get('deadline_date'),
                            status=TenderStatus.ACTIVE,
                            category=self.map_to_category(opp.get('type', '')),
                            url=opp.get('url'),
                            relevance_score=opp.get('relevance_score', 0.0),
                            raw_data=opp
                        )
                        
                        # Create tender in database
                        tender_repo.create(tender_data)
                        self.session_data['tenders_processed'] += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to save opportunity {opp['id']}: {str(e)}")
                        continue
                
                logger.info(f"Saved {self.session_data['tenders_processed']} opportunities to database")
                
        except Exception as e:
            error_msg = f"Failed to save opportunities to database: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
    
    def map_to_category(self, opp_type: str) -> Optional[TenderCategory]:
        """Map opportunity type to tender category"""
        if not opp_type:
            return None
            
        opp_type_lower = opp_type.lower()
        
        if any(term in opp_type_lower for term in ['consulting', 'advisory']):
            return TenderCategory.CONSULTING
        elif any(term in opp_type_lower for term in ['technical', 'assistance']):
            return TenderCategory.TECHNICAL_ASSISTANCE
        elif any(term in opp_type_lower for term in ['capacity', 'building']):
            return TenderCategory.CAPACITY_BUILDING
        elif any(term in opp_type_lower for term in ['business', 'development']):
            return TenderCategory.BUSINESS_DEVELOPMENT
        elif 'entrepreneurship' in opp_type_lower:
            return TenderCategory.ENTREPRENEURSHIP
        else:
            return TenderCategory.OTHER
    
    async def update_session_progress(self, page_num: int) -> None:
        """Update automation session progress in database"""
        try:
            with db_manager.session_scope() as session:
                session_repo = AutomationSessionRepository(session)
                session_repo.update_progress(
                    session_id=self.session_id,
                    current_page=page_num,
                    tenders_found=self.session_data['tenders_found'],
                    tenders_processed=self.session_data['tenders_processed']
                )
        except Exception as e:
            logger.warning(f"Failed to update session progress: {str(e)}")
    
    async def cleanup(self) -> None:
        """Cleanup browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser cleanup completed")
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")
    
    async def run_scraping_session(self) -> Dict[str, Any]:
        """Run complete UNGM scraping session"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Initialize session in database
            with db_manager.session_scope() as session:
                session_repo = AutomationSessionRepository(session)
                session_repo.create(
                    session_id=self.session_id,
                    source=TenderSource.UNGM,
                    search_params={
                        'search_terms': self.search_terms,
                        'target_countries': self.target_countries,
                        'max_pages': self.max_pages
                    },
                    max_pages=self.max_pages
                )
            
            logger.info(f"Starting UNGM scraping session: {self.session_id}")
            
            # Initialize browser
            await self.initialize_browser()
            
            # Authenticate
            if not await self.authenticate():
                raise UNGMScraperError("Authentication failed")
            
            # Search for opportunities
            await self.search_opportunities()
            
            # Scrape pages
            page_num = 1
            total_opportunities = []
            
            while page_num <= self.max_pages:
                logger.info(f"Processing page {page_num}...")
                
                # Extract opportunities from current page
                page_opportunities = await self.extract_opportunities_from_page()
                total_opportunities.extend(page_opportunities)
                
                # Save to database
                if page_opportunities:
                    await self.save_opportunities_to_database(page_opportunities)
                
                # Update progress
                self.session_data['pages_processed'] = page_num
                await self.update_session_progress(page_num)
                
                # Check for next page
                if not await self.has_next_page():
                    logger.info("No more pages available")
                    break
                
                # Go to next page
                if not await self.go_to_next_page():
                    logger.warning("Failed to navigate to next page")
                    break
                
                page_num += 1
                
                # Rate limiting
                await asyncio.sleep(self.request_delay / 1000)
            
            # Complete session
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            session_summary = {
                'session_id': self.session_id,
                'status': 'completed',
                'duration_seconds': duration,
                'pages_processed': self.session_data['pages_processed'],
                'tenders_found': self.session_data['tenders_found'],
                'tenders_processed': self.session_data['tenders_processed'],
                'errors': self.session_data['errors'],
                'performance_metrics': {
                    'pages_per_minute': (self.session_data['pages_processed'] / duration) * 60 if duration > 0 else 0,
                    'tenders_per_minute': (self.session_data['tenders_found'] / duration) * 60 if duration > 0 else 0
                }
            }
            
            # Update session in database
            with db_manager.session_scope() as session:
                session_repo = AutomationSessionRepository(session)
                session_repo.complete_session(
                    session_id=self.session_id,
                    status='completed',
                    performance_metrics=session_summary['performance_metrics']
                )
            
            logger.info(f"UNGM scraping session completed successfully: {session_summary}")
            return session_summary
            
        except Exception as e:
            error_msg = f"UNGM scraping session failed: {str(e)}"
            logger.error(error_msg)
            
            # Update session with error
            with db_manager.session_scope() as session:
                session_repo = AutomationSessionRepository(session)
                session_repo.complete_session(
                    session_id=self.session_id,
                    status='failed',
                    error_message=error_msg
                )
            
            raise UNGMScraperError(error_msg)
            
        finally:
            await self.cleanup()


# Async function to run UNGM scraping
async def run_ungm_scraping(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run UNGM scraping session"""
    scraper = UNGMScraper(config)
    return await scraper.run_scraping_session()


# Test function
async def test_ungm_scraper():
    """Test UNGM scraper functionality"""
    config = {
        'max_pages': 2,  # Limit for testing
        'headless': False,  # Show browser for debugging
        'request_delay': 1000  # Faster for testing
    }
    
    try:
        result = await run_ungm_scraping(config)
        print(f"Test completed successfully: {result}")
    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_ungm_scraper())