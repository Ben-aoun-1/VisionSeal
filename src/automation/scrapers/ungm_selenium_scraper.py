"""
Enhanced UNGM Scraper with Selenium
Improved version based on live website analysis with functional authentication and navigation
"""
import time
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from core.config.settings import settings
from core.logging.setup import get_logger
from core.database.connection import db_manager
from core.database.repositories import TenderRepository, AutomationSessionRepository
from models.tender import TenderCreate, TenderSource, TenderCategory, TenderStatus

logger = get_logger("ungm_selenium_scraper")


class UNGMSeleniumScraperError(Exception):
    """Custom exception for UNGM Selenium scraper errors"""
    pass


class UNGMSeleniumScraper:
    """Enhanced UNGM scraper using Selenium with real website insights"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Authentication credentials from .env
        self.username = self.config.get('username') or settings.automation.ungm_username
        self.password = self.config.get('password') or settings.automation.ungm_password
        
        # Scraping configuration
        self.base_url = self.config.get('base_url', 'https://www.ungm.org')
        self.max_pages = self.config.get('max_pages', settings.automation.max_pages)
        self.headless = self.config.get('headless', settings.automation.headless)
        self.timeout = self.config.get('timeout', 30)  # 30 seconds timeout
        self.request_delay = self.config.get('request_delay', 2)  # 2 seconds between requests
        
        # Search parameters specifically for Topaza.net business focus
        self.search_terms = self.config.get('search_terms', [
            'consulting', 'conseil', 'advisory services', 'services consultatifs',
            'technical assistance', 'assistance technique', 'capacity building',
            'business development', 'développement des affaires', 'entrepreneurship',
            'formation', 'training', 'étude', 'study', 'expertise',
            'management', 'gestion', 'strategy', 'stratégie', 'evaluation'
        ])
        
        # Priority focus on Africa for Topaza.net
        self.target_countries = self.config.get('target_countries', [
            # North Africa
            'Tunisia', 'Tunisie', 'Morocco', 'Maroc', 'Algeria', 'Algérie', 
            'Egypt', 'Égypte', 'Libya', 'Libye', 'Sudan', 'Soudan',
            
            # West Africa
            'Nigeria', 'Ghana', 'Senegal', 'Sénégal', 'Mali', 'Burkina Faso',
            'Niger', 'Guinea', 'Guinée', 'Sierra Leone', 'Liberia', 'Gambia',
            'Cape Verde', 'Mauritania', 'Mauritanie', 'Benin', 'Bénin', 'Togo',
            'Ivory Coast', "Côte d'Ivoire", 'Guinea-Bissau',
            
            # East Africa
            'Kenya', 'Ethiopia', 'Éthiopie', 'Tanzania', 'Tanzanie', 'Uganda', 'Ouganda',
            'Rwanda', 'Burundi', 'Somalia', 'Somalie', 'Djibouti', 'Eritrea', 'Érythrée',
            'South Sudan', 'Soudan du Sud', 'Madagascar', 'Mauritius', 'Maurice',
            'Seychelles', 'Comoros', 'Comores',
            
            # Central Africa
            'Democratic Republic of Congo', 'DRC', 'RDC', 'Congo', 'Cameroon', 'Cameroun',
            'Central African Republic', 'CAR', 'RCA', 'Chad', 'Tchad', 'Gabon',
            'Equatorial Guinea', 'Guinée équatoriale', 'São Tomé and Príncipe',
            
            # Southern Africa
            'South Africa', 'Afrique du Sud', 'Botswana', 'Namibia', 'Namibie',
            'Zimbabwe', 'Zambia', 'Zambie', 'Angola', 'Mozambique', 'Malawi',
            'Lesotho', 'Swaziland', 'eSwatini'
        ])
        
        # Selenium driver
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
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
        
        # Updated selectors based on live site analysis
        self.selectors = {
            # Authentication (tested and working)
            'login_button': "//a[contains(text(), 'Log in')] | //*[contains(text(), 'Log in')]",
            'email_input': "input[type='text'], input[type='email']",
            'password_input': "input[type='password']",
            'submit_button': "button[type='submit'], .btn, button",
            'logout_indicator': "//*[contains(text(), 'topaza.bd@gmail.com')] | //*[contains(@class, 'user')]",
            
            # Navigation (confirmed working)
            'business_opportunities': "//a[contains(text(), 'Opportunités commerciales')]",
            'market_notices': "//a[contains(text(), 'Mes avis de marché')]",
            
            # Search interface (tested)
            'title_input': "input[type='text']",  # First text input is usually title
            'search_button': "//button[contains(text(), 'Recherch')] | //button[contains(text(), 'Search')] | //input[@type='submit']",
            'clear_button': "//button[contains(text(), 'Tout effacer')]",
            
            # Filters and checkboxes
            'checkbox_consultants': "//input[@type='checkbox' and following-sibling::text()[contains(., 'consultants')]]",
            'checkbox_services': "//input[@type='checkbox' and following-sibling::text()[contains(., 'services')]]",
            'checkbox_development': "//input[@type='checkbox' and following-sibling::text()[contains(., 'développement')]]",
            
            # Results table (to be confirmed)
            'results_table': "table, .table, .results",
            'result_rows': "tr, .row, .result-item",
            'opportunity_links': "a[href*='/Public/Notice/'], a[href*='Notice']",
            'title_cells': "td:nth-child(1), .title",
            'deadline_cells': "td:nth-child(2), .deadline",
            'organization_cells': "td:nth-child(3), .organization",
            'country_cells': "td:nth-child(4), .country",
            
            # Pagination
            'next_page': "//a[contains(text(), 'Suivant')] | //a[contains(text(), 'Next')] | .next",
            'page_numbers': ".pagination a, .page-link",
            'current_page': ".pagination .active, .current"
        }
        
        logger.info(f"UNGM Selenium Scraper initialized - Session: {self.session_id}")
    
    def initialize_driver(self) -> None:
        """Initialize Selenium Chrome driver with optimal settings"""
        try:
            chrome_options = Options()
            
            # Basic options
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Stealth and reliability options
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            
            # User agent for stealth
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Performance options
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-gpu-logging')
            chrome_options.add_argument('--silent')
            
            # Use chromium instead of chrome
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Initialize driver without service (let selenium handle it)
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            # Add stealth measures after driver initialization
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            })
            
            logger.info("Selenium Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {str(e)}")
            raise UNGMSeleniumScraperError(f"Driver initialization failed: {str(e)}")
    
    def authenticate(self) -> bool:
        """Authenticate with UNGM using tested credentials and navigation"""
        try:
            logger.info("Starting UNGM authentication process...")
            
            # Navigate to UNGM homepage
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Click login button
            login_element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, self.selectors['login_button']))
            )
            login_element.click()
            time.sleep(2)
            
            # Fill email
            email_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['email_input']))
            )
            email_input.clear()
            email_input.send_keys(self.username)
            time.sleep(1)
            
            # Fill password
            password_input = self.driver.find_element(By.CSS_SELECTOR, self.selectors['password_input'])
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)
            
            # Submit login
            submit_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['submit_button'])
            submit_button.click()
            time.sleep(5)  # Wait for login processing
            
            # Verify authentication by checking for user indicator
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, self.selectors['logout_indicator']))
                )
                logger.info("Authentication successful - user logged in")
                self.session_data['authenticated'] = True
                return True
            except TimeoutException:
                logger.error("Authentication failed - no user indicator found")
                return False
                
        except Exception as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
    
    def navigate_to_opportunities(self) -> bool:
        """Navigate to business opportunities section"""
        try:
            logger.info("Navigating to business opportunities...")
            
            # Click on business opportunities
            opportunities_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, self.selectors['business_opportunities']))
            )
            opportunities_link.click()
            time.sleep(3)
            
            logger.info("Successfully navigated to opportunities section")
            return True
            
        except Exception as e:
            error_msg = f"Failed to navigate to opportunities: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
    
    def setup_search_filters(self, search_term: str = None) -> bool:
        """Setup search filters and criteria"""
        try:
            logger.info("Setting up search filters...")
            
            # Use default search term if none provided
            if not search_term:
                search_term = ' OR '.join(self.search_terms[:3])  # Use first 3 terms
            
            # Clear any existing search
            try:
                clear_button = self.driver.find_element(By.XPATH, self.selectors['clear_button'])
                clear_button.click()
                time.sleep(1)
            except NoSuchElementException:
                pass  # Clear button might not exist
            
            # Enter search term in title field
            try:
                title_input = self.driver.find_element(By.CSS_SELECTOR, self.selectors['title_input'])
                title_input.clear()
                title_input.send_keys(search_term)
                time.sleep(1)
                logger.info(f"Entered search term: {search_term}")
            except NoSuchElementException:
                logger.warning("Title input field not found")
            
            # Try to select relevant checkboxes (consulting, services)
            checkbox_selectors = [
                self.selectors['checkbox_consultants'],
                self.selectors['checkbox_services'],
                self.selectors['checkbox_development']
            ]
            
            for checkbox_selector in checkbox_selectors:
                try:
                    checkboxes = self.driver.find_elements(By.XPATH, checkbox_selector)
                    for checkbox in checkboxes[:2]:  # Select first 2 matching checkboxes
                        if not checkbox.is_selected():
                            checkbox.click()
                            time.sleep(0.5)
                except:
                    continue  # Skip if checkbox not found
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to setup search filters: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
    
    def execute_search(self) -> bool:
        """Execute the search with current filters"""
        try:
            # Click search button
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, self.selectors['search_button']))
            )
            search_button.click()
            time.sleep(5)  # Wait for results to load
            
            logger.info("Search executed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to execute search: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
    
    def extract_opportunities_from_page(self) -> List[Dict[str, Any]]:
        """Extract opportunity data from current results page"""
        opportunities = []
        
        try:
            # Look for results table or container
            results_selectors = self.selectors['results_table'].split(', ')
            results_container = None
            
            for selector in results_selectors:
                try:
                    results_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not results_container:
                logger.warning("No results container found on page")
                return opportunities
            
            # Extract opportunity rows
            row_selectors = self.selectors['result_rows'].split(', ')
            rows = []
            
            for selector in row_selectors:
                try:
                    rows = results_container.find_elements(By.CSS_SELECTOR, selector)
                    if rows:
                        break
                except:
                    continue
            
            logger.info(f"Found {len(rows)} potential opportunity rows")
            
            for i, row in enumerate(rows):
                try:
                    opportunity = self.extract_opportunity_from_row(row, i)
                    if opportunity and self.is_relevant_opportunity(opportunity):
                        opportunities.append(opportunity)
                        self.session_data['tenders_found'] += 1
                        
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
    
    def extract_opportunity_from_row(self, row, index: int) -> Optional[Dict[str, Any]]:
        """Extract comprehensive opportunity data for Topaza.net requirements"""
        try:
            # Try to find link to opportunity details
            link_element = None
            try:
                link_element = row.find_element(By.CSS_SELECTOR, self.selectors['opportunity_links'])
            except NoSuchElementException:
                # Try alternative link selectors
                try:
                    link_element = row.find_element(By.TAG_NAME, 'a')
                except NoSuchElementException:
                    return None
            
            if not link_element:
                return None
            
            # Extract basic information
            title = link_element.text.strip() if link_element.text else 'N/A'
            detail_url = link_element.get_attribute('href')
            
            # Make URL absolute if relative
            if detail_url and not detail_url.startswith('http'):
                detail_url = f"{self.base_url}{detail_url}" if detail_url.startswith('/') else f"{self.base_url}/{detail_url}"
            
            # Extract comprehensive cell data for Topaza.net requirements
            cells = row.find_elements(By.TAG_NAME, 'td')
            
            # Enhanced extraction for key Topaza.net data points
            title_full = self.extract_cell_content(cells, 0, 'title') if cells else title
            deadline = self.extract_cell_content(cells, 1, 'deadline')
            published = self.extract_cell_content(cells, 2, 'published')
            organization = self.extract_cell_content(cells, 3, 'organization')
            tender_type = self.extract_cell_content(cells, 4, 'type')
            reference = self.extract_cell_content(cells, 5, 'reference')
            country = self.extract_cell_content(cells, 6, 'country')
            
            # Parse and validate dates
            published_date = self.parse_date(published)
            deadline_date = self.parse_date(deadline)
            
            # Extract additional business-relevant information
            tender_value = self.extract_tender_value(row)
            sector = self.identify_sector(title_full, tender_type)
            
            # Generate unique ID with Topaza prefix
            opportunity_id = f"topaza_ungm_{uuid.uuid4().hex[:12]}"
            
            # Comprehensive opportunity data for Topaza.net
            opportunity = {
                # Core identification
                'id': opportunity_id,
                'title': title_full or title,
                'reference': reference,
                'source': 'UNGM Enhanced for Topaza',
                
                # Critical Topaza.net requirements
                'deadline': deadline,
                'deadline_date': deadline_date,
                'country': country,
                'organization': organization,
                'detail_url': detail_url,  # Link for more info
                
                # Additional business context
                'published': published,
                'published_date': published_date,
                'tender_type': tender_type,
                'sector': sector,
                'estimated_value': tender_value,
                
                # Metadata
                'extracted_at': datetime.now(timezone.utc).isoformat(),
                'days_until_deadline': self.calculate_days_until_deadline(deadline_date),
                'is_urgent': self.is_urgent_deadline(deadline_date),
                'topaza_relevance_score': self.calculate_topaza_relevance_score({
                    'title': title_full or title,
                    'organization': organization,
                    'country': country,
                    'type': tender_type,
                    'sector': sector
                }),
                
                # Raw data for reference
                'raw_cells': [cell.text.strip() for cell in cells if cell.text.strip()]
            }
            
            return opportunity
            
        except Exception as e:
            logger.warning(f"Failed to extract opportunity from row {index}: {str(e)}")
            return None
    
    def extract_cell_content(self, cells: List, index: int, content_type: str) -> str:
        """Extract content from table cell based on index and type"""
        try:
            if index < len(cells):
                text = cells[index].text.strip()
                return text if text else 'N/A'
            return 'N/A'
        except:
            return 'N/A'
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object with French format support"""
        if not date_str or date_str == 'N/A':
            return None
            
        try:
            # Common French/UNGM date formats
            date_formats = [
                '%d/%m/%Y %H:%M',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d %B %Y',  # e.g., "27 juin 2025"
                '%d %b %Y'   # e.g., "27 juin 2025"
            ]
            
            # Clean up date string
            date_str = date_str.strip()
            
            # Handle French month names
            french_months = {
                'janvier': 'January', 'février': 'February', 'mars': 'March',
                'avril': 'April', 'mai': 'May', 'juin': 'June',
                'juillet': 'July', 'août': 'August', 'septembre': 'September',
                'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
            }
            
            for fr_month, en_month in french_months.items():
                if fr_month in date_str.lower():
                    date_str = date_str.lower().replace(fr_month, en_month)
                    break
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {str(e)}")
            
        return None
    
    def extract_tender_value(self, row) -> Optional[str]:
        """Extract estimated tender value if available"""
        try:
            # Look for value indicators in row text
            row_text = row.text.lower()
            value_patterns = [
                r'(\$|€|£)\s*(\d+[,.]?\d*)\s*(million|k|thousand)',
                r'(\d+[,.]?\d*)\s*(usd|eur|euros?|dollars?)',
                r'budget[:\s]*(\d+[,.]?\d*)',
                r'value[:\s]*(\d+[,.]?\d*)'
            ]
            
            for pattern in value_patterns:
                match = re.search(pattern, row_text)
                if match:
                    return match.group(0)
            
            return None
        except:
            return None
    
    def identify_sector(self, title: str, tender_type: str) -> str:
        """Identify business sector for Topaza.net categorization"""
        combined_text = f"{title} {tender_type}".lower()
        
        sectors = {
            'Management Consulting': ['management', 'gestion', 'strategy', 'stratégie', 'organizational'],
            'Technical Assistance': ['technical', 'technique', 'assistance', 'implementation'],
            'Training & Development': ['training', 'formation', 'capacity building', 'education'],
            'Business Development': ['business', 'développement', 'entrepreneurship', 'innovation'],
            'Financial Services': ['financial', 'finance', 'banking', 'investment'],
            'IT & Digital': ['digital', 'technology', 'it', 'software', 'system'],
            'Healthcare': ['health', 'santé', 'medical', 'hospital'],
            'Agriculture': ['agriculture', 'farming', 'rural', 'food'],
            'Infrastructure': ['infrastructure', 'construction', 'roads', 'water'],
            'Other': []
        }
        
        for sector, keywords in sectors.items():
            if any(keyword in combined_text for keyword in keywords):
                return sector
        
        return 'Other'
    
    def calculate_days_until_deadline(self, deadline_date: Optional[datetime]) -> Optional[int]:
        """Calculate days remaining until deadline"""
        if not deadline_date:
            return None
        
        try:
            now = datetime.now(timezone.utc)
            delta = deadline_date - now
            return max(0, delta.days)
        except:
            return None
    
    def is_urgent_deadline(self, deadline_date: Optional[datetime]) -> bool:
        """Check if deadline is urgent (within 7 days)"""
        days_left = self.calculate_days_until_deadline(deadline_date)
        return days_left is not None and days_left <= 7
    
    def calculate_topaza_relevance_score(self, opportunity: Dict[str, str]) -> float:
        """Calculate relevance score specifically for Topaza.net business focus"""
        score = 0.0
        
        title = opportunity.get('title', '').lower()
        organization = opportunity.get('organization', '').lower()
        country = opportunity.get('country', '').lower()
        tender_type = opportunity.get('type', '').lower()
        sector = opportunity.get('sector', '').lower()
        
        # High priority for Topaza's core services
        topaza_core_terms = [
            'consulting', 'conseil', 'advisory', 'consulting services',
            'management', 'gestion', 'strategy', 'stratégie',
            'business development', 'développement des affaires',
            'training', 'formation', 'capacity building'
        ]
        for term in topaza_core_terms:
            if term in title:
                score += 25.0
        
        # Geographic priority - All African countries
        # Check if country is in Africa using comprehensive African country list
        is_african = False
        for african_country in self.target_countries:
            if african_country.lower() in country:
                is_african = True
                break
        
        if is_african:
            score += 40.0  # High priority for any African country
            
            # Extra points for major African economies
            major_economies = ['nigeria', 'south africa', 'afrique du sud', 'egypt', 'égypte', 
                             'kenya', 'ghana', 'morocco', 'maroc', 'ethiopia', 'éthiopie']
            if any(economy in country for economy in major_economies):
                score += 10.0
        
        # General African continent indicators
        african_indicators = ['africa', 'afrique', 'african', 'africain', 'africaine']
        if any(indicator in country for indicator in african_indicators):
            score += 25.0
        
        # UN and international organizations (Topaza's specialty)
        priority_orgs = ['undp', 'unicef', 'unhcr', 'world bank', 'banque mondiale', 
                        'african development', 'unesco', 'who', 'oms', 'unops']
        for org in priority_orgs:
            if org in organization:
                score += 25.0
                break
        
        # Sector-specific bonuses
        if 'management consulting' in sector.lower():
            score += 20.0
        elif 'business development' in sector.lower():
            score += 18.0
        elif 'training' in sector.lower():
            score += 15.0
        
        # Tender type preferences
        preferred_types = ['consulting', 'services', 'advisory', 'étude', 'study']
        if any(pref_type in tender_type for pref_type in preferred_types):
            score += 15.0
        
        # Language bonus (French/Arabic markets)
        if any(term in title for term in ['francophone', 'français', 'arabe', 'arabic']):
            score += 10.0
        
        return min(score, 100.0)  # Cap at 100
    
    def is_relevant_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity meets Topaza.net relevance criteria"""
        topaza_score = opportunity.get('topaza_relevance_score', 0)
        
        # Higher threshold for Topaza.net - must be genuinely relevant
        if topaza_score < 25.0:
            return False
        
        # Check if deadline is in the future (with buffer)
        deadline_date = opportunity.get('deadline_date')
        if deadline_date:
            now = datetime.now(timezone.utc)
            # Reject if deadline has already passed
            if deadline_date < now:
                return False
            
            # Reject if deadline is too far in the future (over 6 months)
            six_months = now + timedelta(days=180)
            if deadline_date > six_months:
                return False
        
        # Must have organization and country information
        if not opportunity.get('organization') or opportunity.get('organization') == 'N/A':
            return False
            
        if not opportunity.get('country') or opportunity.get('country') == 'N/A':
            return False
        
        # Must have a valid detail URL for more information
        if not opportunity.get('detail_url') or opportunity.get('detail_url') == 'N/A':
            return False
        
        return True
    
    def save_opportunities_to_database(self, opportunities: List[Dict[str, Any]]) -> None:
        """Save extracted opportunities to database"""
        try:
            with db_manager.session_scope() as session:
                tender_repo = TenderRepository(session)
                
                for opp in opportunities:
                    try:
                        # Map opportunity data to tender model with Topaza-specific fields
                        description = f"Topaza Opportunity: {opp.get('sector', 'Unknown Sector')} in {opp.get('country', 'Unknown')} - {opp.get('organization', 'Unknown Org')}"
                        if opp.get('days_until_deadline'):
                            description += f" (Deadline in {opp.get('days_until_deadline')} days)"
                        
                        tender_data = TenderCreate(
                            id=opp['id'],
                            title=opp['title'],
                            description=description,
                            source=TenderSource.UNGM,
                            country=opp.get('country'),
                            organization=opp.get('organization'),
                            published_date=opp.get('published_date'),
                            deadline=opp.get('deadline_date'),
                            status=TenderStatus.ACTIVE,
                            category=self.map_to_category(opp.get('title', '')),
                            url=opp.get('detail_url'),  # Use detail_url for more info
                            relevance_score=opp.get('topaza_relevance_score', 0.0),
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
    
    def map_to_category(self, title: str) -> Optional[TenderCategory]:
        """Map opportunity title to tender category"""
        if not title:
            return None
            
        title_lower = title.lower()
        
        if any(term in title_lower for term in ['consulting', 'advisory', 'conseil']):
            return TenderCategory.CONSULTING
        elif any(term in title_lower for term in ['technical', 'technique', 'assistance']):
            return TenderCategory.TECHNICAL_ASSISTANCE
        elif any(term in title_lower for term in ['capacity', 'capacité', 'building', 'renforcement']):
            return TenderCategory.CAPACITY_BUILDING
        elif any(term in title_lower for term in ['business', 'développement', 'development']):
            return TenderCategory.BUSINESS_DEVELOPMENT
        elif any(term in title_lower for term in ['entrepreneurship', 'entrepreneuriat']):
            return TenderCategory.ENTREPRENEURSHIP
        else:
            return TenderCategory.OTHER
    
    def has_next_page(self) -> bool:
        """Check if there's a next page available"""
        try:
            next_elements = self.driver.find_elements(By.XPATH, self.selectors['next_page'])
            for element in next_elements:
                if element.is_enabled() and element.is_displayed():
                    return True
            return False
        except:
            return False
    
    def go_to_next_page(self) -> bool:
        """Navigate to next page"""
        try:
            next_button = self.driver.find_element(By.XPATH, self.selectors['next_page'])
            if next_button.is_enabled():
                next_button.click()
                time.sleep(self.request_delay)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to go to next page: {str(e)}")
            return False
    
    def update_session_progress(self, page_num: int) -> None:
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
    
    def cleanup(self) -> None:
        """Cleanup Selenium driver"""
        try:
            if self.driver:
                self.driver.quit()
            logger.info("Selenium driver cleanup completed")
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")
    
    def run_scraping_session(self) -> Dict[str, Any]:
        """Run complete UNGM scraping session with Selenium"""
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
                        'max_pages': self.max_pages,
                        'scraper_type': 'selenium_enhanced'
                    },
                    max_pages=self.max_pages
                )
            
            logger.info(f"Starting UNGM Selenium scraping session: {self.session_id}")
            
            # Initialize Selenium driver
            self.initialize_driver()
            
            # Authenticate
            if not self.authenticate():
                raise UNGMSeleniumScraperError("Authentication failed")
            
            # Navigate to opportunities
            if not self.navigate_to_opportunities():
                raise UNGMSeleniumScraperError("Failed to navigate to opportunities")
            
            # Setup search filters
            if not self.setup_search_filters():
                raise UNGMSeleniumScraperError("Failed to setup search filters")
            
            # Execute search
            if not self.execute_search():
                raise UNGMSeleniumScraperError("Failed to execute search")
            
            # Scrape pages
            page_num = 1
            total_opportunities = []
            
            while page_num <= self.max_pages:
                logger.info(f"Processing page {page_num}...")
                
                # Extract opportunities from current page
                page_opportunities = self.extract_opportunities_from_page()
                total_opportunities.extend(page_opportunities)
                
                # Save to database
                if page_opportunities:
                    self.save_opportunities_to_database(page_opportunities)
                
                # Update progress
                self.session_data['pages_processed'] = page_num
                self.update_session_progress(page_num)
                
                # Check for next page
                if not self.has_next_page():
                    logger.info("No more pages available")
                    break
                
                # Go to next page
                if not self.go_to_next_page():
                    logger.warning("Failed to navigate to next page")
                    break
                
                page_num += 1
                time.sleep(self.request_delay)
            
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
                    'tenders_per_minute': (self.session_data['tenders_found'] / duration) * 60 if duration > 0 else 0,
                    'authentication_successful': self.session_data['authenticated']
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
            
            logger.info(f"UNGM Selenium scraping session completed successfully: {session_summary}")
            return session_summary
            
        except Exception as e:
            error_msg = f"UNGM Selenium scraping session failed: {str(e)}"
            logger.error(error_msg)
            
            # Update session with error
            with db_manager.session_scope() as session:
                session_repo = AutomationSessionRepository(session)
                session_repo.complete_session(
                    session_id=self.session_id,
                    status='failed',
                    error_message=error_msg
                )
            
            raise UNGMSeleniumScraperError(error_msg)
            
        finally:
            self.cleanup()


# Function to run UNGM scraping
def run_ungm_selenium_scraping(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run UNGM Selenium scraping session"""
    scraper = UNGMSeleniumScraper(config)
    return scraper.run_scraping_session()


# Test function
def test_ungm_selenium_scraper():
    """Test UNGM Selenium scraper functionality"""
    config = {
        'max_pages': 2,  # Limit for testing
        'headless': False,  # Show browser for debugging
        'request_delay': 1  # Faster for testing
    }
    
    try:
        result = run_ungm_selenium_scraping(config)
        print(f"Test completed successfully: {result}")
    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    # Run test
    test_ungm_selenium_scraper()