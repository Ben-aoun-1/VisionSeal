"""
Enhanced TuniPages Scraper with Selenium for Topaza.net
Focused on Maghreb region tenders with comprehensive data extraction for Topaza's business needs
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

logger = get_logger("tunipages_selenium_scraper")


class TuniPagesSeleniumScraperError(Exception):
    """Custom exception for TuniPages Selenium scraper errors"""
    pass


class TuniPagesSeleniumScraper:
    """Enhanced TuniPages scraper using Selenium optimized for Topaza.net requirements"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Authentication credentials from .env
        self.username = self.config.get('username') or settings.automation.tunipages_username
        self.password = self.config.get('password') or settings.automation.tunipages_password
        
        # Scraping configuration
        self.base_url = self.config.get('base_url', 'https://www.appeloffres.net')
        self.max_pages = self.config.get('max_pages', settings.automation.max_pages)
        self.headless = self.config.get('headless', settings.automation.headless)
        self.timeout = self.config.get('timeout', 30)  # 30 seconds timeout
        self.request_delay = self.config.get('request_delay', 2)  # 2 seconds between requests
        
        # Topaza.net specific search parameters for Maghreb region
        self.search_terms = self.config.get('search_terms', [
            'consulting', 'conseil', 'étude', 'study', 'expertise',
            'formation', 'training', 'assistance technique', 'management',
            'développement', 'stratégie', 'business', 'entreprise',
            'innovation', 'digital', 'transformation', 'audit'
        ])
        
        # Primary focus on African countries for Topaza.net
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
        
        # Relevant sectors for Topaza.net business
        self.relevant_sectors = [
            'services', 'consulting', 'formation', 'étude', 'audit',
            'management', 'stratégie', 'développement', 'technique',
            'innovation', 'digital', 'transformation', 'expertise'
        ]
        
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
        
        # TuniPages selectors based on site analysis
        self.selectors = {
            # Cookie and initial setup
            'cookie_accept': "//button[contains(text(), 'Accepter')] | //button[contains(text(), 'Accept')]",
            
            # Authentication (if needed)
            'login_link': "//a[contains(@href, 'login')] | //a[contains(text(), 'Connexion')]",
            'email_input': "input[type='email'], input[name='email']",
            'password_input': "input[type='password'], input[name='password']",
            'login_submit': "button[type='submit'], .btn-login",
            
            # Navigation
            'tenders_section': "//a[contains(@href, 'appels-offres')] | //a[contains(text(), 'Appels d\\'offres')]",
            'menu_toggle': ".menu-toggle, .hamburger, button",
            
            # Tender listings (6-column table structure)
            'tenders_table': "table, .tenders-table, .results-table",
            'tender_rows': "tbody tr, .tender-row, .result-row",
            'tender_headers': "thead th, .table-header",
            
            # Table cells (based on 6-column structure: date, country, description, promoter, type, expiry)
            'publish_date_cell': "td:nth-child(1), .publish-date",
            'country_cell': "td:nth-child(2), .country", 
            'description_cell': "td:nth-child(3), .description",
            'promoter_cell': "td:nth-child(4), .promoter, .organization",
            'type_cell': "td:nth-child(5), .type",
            'expiry_cell': "td:nth-child(6), .expiry, .deadline",
            
            # Links to tender details
            'tender_links': "a[href*='appel'], a[href*='tender'], a[href*='offre']",
            'detail_link': "a, .detail-link, .more-info",
            
            # Pagination
            'next_page': "//a[contains(text(), 'Suivant')] | //a[contains(text(), 'Next')] | .next, .pagination-next",
            'page_numbers': ".pagination a, .page-link",
            'current_page': ".pagination .active, .current"
        }
        
        logger.info(f"TuniPages Selenium Scraper initialized for Topaza.net - Session: {self.session_id}")
    
    def initialize_driver(self) -> None:
        """Initialize Selenium Chrome driver with optimal settings for TuniPages"""
        try:
            chrome_options = Options()
            
            # Basic options
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Stealth and reliability options for TuniPages
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            
            # French locale for better compatibility
            chrome_options.add_argument('--lang=fr-FR')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Performance options
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            logger.info("TuniPages Selenium Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {str(e)}")
            raise TuniPagesSeleniumScraperError(f"Driver initialization failed: {str(e)}")
    
    def handle_initial_setup(self) -> bool:
        """Handle initial setup including cookies and navigation"""
        try:
            logger.info("Starting TuniPages initial setup...")
            
            # Navigate to TuniPages homepage
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Accept cookies if popup appears
            try:
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.selectors['cookie_accept']))
                )
                cookie_button.click()
                time.sleep(2)
                logger.info("Accepted cookies")
            except TimeoutException:
                logger.info("No cookie popup found or already accepted")
            
            # Navigate to tenders section
            try:
                # Try direct URL first
                tenders_url = f"{self.base_url}/appels-offres"
                self.driver.get(tenders_url)
                time.sleep(3)
                logger.info("Navigated directly to tenders section")
                return True
            except:
                # Try navigation through menu
                try:
                    tenders_link = self.driver.find_element(By.XPATH, self.selectors['tenders_section'])
                    tenders_link.click()
                    time.sleep(3)
                    logger.info("Navigated to tenders via menu")
                    return True
                except:
                    logger.warning("Could not find tenders section, proceeding with current page")
                    return True
            
        except Exception as e:
            error_msg = f"Initial setup failed: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
    
    def extract_tenders_from_page(self) -> List[Dict[str, Any]]:
        """Extract tender data from current page using 6-column table structure"""
        tenders = []
        
        try:
            # Look for tenders table
            table_selectors = self.selectors['tenders_table'].split(', ')
            table = None
            
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not table:
                # Try to find any table on the page
                tables = self.driver.find_elements(By.TAG_NAME, 'table')
                if tables:
                    table = tables[0]  # Use first table found
                else:
                    logger.warning("No table found on page")
                    return tenders
            
            # Extract tender rows
            rows = table.find_elements(By.CSS_SELECTOR, self.selectors['tender_rows'])
            if not rows:
                # Try alternative row selectors
                rows = table.find_elements(By.TAG_NAME, 'tr')[1:]  # Skip header row
            
            logger.info(f"Found {len(rows)} potential tender rows")
            
            for i, row in enumerate(rows):
                try:
                    tender = self.extract_tender_from_row(row, i)
                    if tender and self.is_relevant_for_topaza(tender):
                        tenders.append(tender)
                        self.session_data['tenders_found'] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to extract tender from row {i}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(tenders)} relevant tenders for Topaza")
            return tenders
            
        except Exception as e:
            error_msg = f"Failed to extract tenders from page: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return tenders
    
    def extract_tender_from_row(self, row, index: int) -> Optional[Dict[str, Any]]:
        """Extract tender data from table row using 6-column structure for Topaza.net"""
        try:
            # Get all cells in the row
            cells = row.find_elements(By.TAG_NAME, 'td')
            
            if len(cells) < 6:
                # Skip rows with insufficient columns
                return None
            
            # Extract data according to 6-column structure:
            # 1. Publish Date, 2. Country, 3. Description, 4. Promoter, 5. Type, 6. Expiry
            publish_date = self.extract_cell_text(cells[0])
            country = self.extract_cell_text(cells[1])
            description = self.extract_cell_text(cells[2])
            promoter = self.extract_cell_text(cells[3])
            tender_type = self.extract_cell_text(cells[4])
            expiry_date = self.extract_cell_text(cells[5])
            
            # Try to find detail link
            detail_link = None
            for cell in cells:
                try:
                    link = cell.find_element(By.TAG_NAME, 'a')
                    if link:
                        detail_link = link.get_attribute('href')
                        break
                except NoSuchElementException:
                    continue
            
            # Make URL absolute if relative
            if detail_link and not detail_link.startswith('http'):
                detail_link = f"{self.base_url}{detail_link}" if detail_link.startswith('/') else f"{self.base_url}/{detail_link}"
            
            # Parse dates
            published_date = self.parse_french_date(publish_date)
            deadline_date = self.parse_french_date(expiry_date)
            
            # Extract additional business context
            sector = self.identify_topaza_sector(description, tender_type)
            estimated_value = self.extract_tender_value_text(description)
            
            # Generate unique ID for Topaza
            tender_id = f"topaza_tunipages_{uuid.uuid4().hex[:12]}"
            
            # Comprehensive tender data for Topaza.net
            tender = {
                # Core identification
                'id': tender_id,
                'title': description,  # Description serves as title in TuniPages
                'description': f"{tender_type} - {description}",
                'reference': f"TP_{index}_{datetime.now().strftime('%Y%m%d')}",
                'source': 'TuniPages Enhanced for Topaza',
                
                # Critical Topaza.net requirements
                'deadline': expiry_date,
                'deadline_date': deadline_date,
                'country': country,
                'organization': promoter,  # Promoter is the organization
                'detail_url': detail_link,  # Link for more info
                
                # Business context
                'published': publish_date,
                'published_date': published_date,
                'tender_type': tender_type,
                'sector': sector,
                'estimated_value': estimated_value,
                'promoter': promoter,  # Keep separate for clarity
                
                # Topaza-specific analysis
                'extracted_at': datetime.now(timezone.utc).isoformat(),
                'days_until_deadline': self.calculate_days_until_deadline(deadline_date),
                'is_urgent': self.is_urgent_deadline(deadline_date),
                'topaza_relevance_score': self.calculate_topaza_relevance_score({
                    'description': description,
                    'country': country,
                    'promoter': promoter,
                    'type': tender_type,
                    'sector': sector
                }),
                'is_african': self.is_african_country(country),
                
                # Raw data for reference
                'raw_cells': [publish_date, country, description, promoter, tender_type, expiry_date]
            }
            
            return tender
            
        except Exception as e:
            logger.warning(f"Failed to extract tender from row {index}: {str(e)}")
            return None
    
    def extract_cell_text(self, cell) -> str:
        """Extract and clean text from table cell"""
        try:
            text = cell.text.strip()
            return text if text else 'N/A'
        except:
            return 'N/A'
    
    def parse_french_date(self, date_str: str) -> Optional[datetime]:
        """Parse French date string into datetime object"""
        if not date_str or date_str == 'N/A':
            return None
            
        try:
            # Common French date formats used in TuniPages
            date_formats = [
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%d.%m.%Y',
                '%d %m %Y',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M',
                '%d-%m-%Y %H:%M'
            ]
            
            # Clean up date string
            date_str = date_str.strip()
            
            # Handle French month names
            french_months = {
                'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
                'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
                'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12',
                'jan': '01', 'fév': '02', 'mar': '03', 'avr': '04',
                'mai': '05', 'jun': '06', 'jul': '07', 'aoû': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'déc': '12'
            }
            
            for fr_month, num_month in french_months.items():
                if fr_month in date_str.lower():
                    date_str = re.sub(fr_month, num_month, date_str, flags=re.IGNORECASE)
                    break
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {str(e)}")
            
        return None
    
    def identify_topaza_sector(self, description: str, tender_type: str) -> str:
        """Identify business sector relevant to Topaza.net services"""
        combined_text = f"{description} {tender_type}".lower()
        
        topaza_sectors = {
            'Management Consulting': ['management', 'gestion', 'strategy', 'stratégie', 'consulting', 'conseil'],
            'Training & Development': ['formation', 'training', 'éducation', 'capacity building', 'développement capacités'],
            'Technical Studies': ['étude', 'study', 'expertise', 'audit', 'evaluation', 'évaluation'],
            'Business Development': ['développement', 'business', 'entreprise', 'entrepreneurship', 'innovation'],
            'Digital Transformation': ['digital', 'numérique', 'transformation', 'technologie', 'it', 'système'],
            'Financial Services': ['finance', 'financier', 'budget', 'comptabilité', 'accounting'],
            'Public Administration': ['administration', 'gouvernement', 'public', 'municipal', 'gouvernance'],
            'Infrastructure': ['infrastructure', 'construction', 'travaux', 'bâtiment'],
            'Healthcare': ['santé', 'health', 'médical', 'hospital', 'hôpital'],
            'Agriculture': ['agriculture', 'agricole', 'rural', 'farming'],
            'Other Services': []
        }
        
        for sector, keywords in topaza_sectors.items():
            if any(keyword in combined_text for keyword in keywords):
                return sector
        
        return 'Other Services'
    
    def extract_tender_value_text(self, description: str) -> Optional[str]:
        """Extract tender value information from description"""
        try:
            # Look for value indicators in French
            value_patterns = [
                r'(\d+[,.]?\d*)\s*(dinars?|dt|tnd|euros?|€|dollars?|\$)',
                r'budget[:\s]*(\d+[,.]?\d*)',
                r'montant[:\s]*(\d+[,.]?\d*)',
                r'valeur[:\s]*(\d+[,.]?\d*)',
                r'prix[:\s]*(\d+[,.]?\d*)'
            ]
            
            description_lower = description.lower()
            for pattern in value_patterns:
                match = re.search(pattern, description_lower)
                if match:
                    return match.group(0)
            
            return None
        except:
            return None
    
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
        """Check if deadline is urgent (within 10 days for TuniPages)"""
        days_left = self.calculate_days_until_deadline(deadline_date)
        return days_left is not None and days_left <= 10
    
    def is_african_country(self, country: str) -> bool:
        """Check if country is in Africa (Topaza's primary focus)"""
        if not country:
            return False
        
        country_lower = country.lower()
        # Check against comprehensive African country list
        for target_country in self.target_countries:
            if target_country.lower() in country_lower:
                return True
        
        # Additional African indicators
        african_indicators = ['africa', 'afrique', 'african', 'africain', 'africaine']
        return any(indicator in country_lower for indicator in african_indicators)
    
    def calculate_topaza_relevance_score(self, tender: Dict[str, str]) -> float:
        """Calculate relevance score specifically for Topaza.net business in Africa"""
        score = 0.0
        
        description = tender.get('description', '').lower()
        country = tender.get('country', '').lower()
        promoter = tender.get('promoter', '').lower()
        tender_type = tender.get('type', '').lower()
        sector = tender.get('sector', '').lower()
        
        # Maximum priority for Topaza's core services
        topaza_services = [
            'consulting', 'conseil', 'management', 'gestion',
            'strategy', 'stratégie', 'étude', 'study',
            'formation', 'training', 'expertise', 'audit'
        ]
        for service in topaza_services:
            if service in description:
                score += 30.0
        
        # Geographic priority - All African countries
        if self.is_african_country(country):
            score += 40.0  # Very high priority for Africa
            
            # Extra points for major African economies and hubs
            major_economies = ['nigeria', 'south africa', 'afrique du sud', 'egypt', 'égypte', 
                             'kenya', 'ghana', 'morocco', 'maroc', 'ethiopia', 'éthiopie',
                             'tunisia', 'tunisie', 'algeria', 'algérie', 'cameroon', 'cameroun']
            if any(economy in country for economy in major_economies):
                score += 10.0
        
        # Government and institutional clients (Topaza's specialty)
        government_indicators = [
            'ministère', 'ministry', 'gouvernement', 'government',
            'municipal', 'commune', 'région', 'public',
            'état', 'state', 'national', 'office'
        ]
        for indicator in government_indicators:
            if indicator in promoter:
                score += 25.0
                break
        
        # Sector preferences
        if 'management consulting' in sector.lower():
            score += 25.0
        elif 'training' in sector.lower():
            score += 20.0
        elif 'technical studies' in sector.lower():
            score += 20.0
        elif 'business development' in sector.lower():
            score += 18.0
        
        # Service type preferences
        preferred_types = ['services', 'consulting', 'formation', 'étude', 'expertise']
        if any(pref_type in tender_type for pref_type in preferred_types):
            score += 15.0
        
        # French language market bonus
        if any(term in description for term in ['francophone', 'français', 'french']):
            score += 10.0
        
        return min(score, 100.0)  # Cap at 100
    
    def is_relevant_for_topaza(self, tender: Dict[str, Any]) -> bool:
        """Check if tender meets Topaza.net relevance criteria"""
        topaza_score = tender.get('topaza_relevance_score', 0)
        
        # Higher threshold for quality control
        if topaza_score < 30.0:
            return False
        
        # Must be in Africa (Topaza's primary market)
        if not self.is_african_country(tender.get('country', '')):
            return False
        
        # Check deadline validity
        deadline_date = tender.get('deadline_date')
        if deadline_date:
            now = datetime.now(timezone.utc)
            # Reject if deadline has passed
            if deadline_date < now:
                return False
            
            # Reject if deadline is too far (over 1 year)
            one_year = now + timedelta(days=365)
            if deadline_date > one_year:
                return False
        
        # Must have organization/promoter info
        if not tender.get('organization') or tender.get('organization') == 'N/A':
            return False
        
        # Must have country info
        if not tender.get('country') or tender.get('country') == 'N/A':
            return False
        
        return True
    
    def save_tenders_to_database(self, tenders: List[Dict[str, Any]]) -> None:
        """Save extracted tenders to database with Topaza-specific formatting"""
        try:
            with db_manager.session_scope() as session:
                tender_repo = TenderRepository(session)
                
                for tender in tenders:
                    try:
                        # Create description with Topaza context
                        description = f"African Opportunity: {tender.get('sector', 'Unknown')} in {tender.get('country', 'Unknown')}"
                        if tender.get('promoter') != 'N/A':
                            description += f" - {tender.get('promoter')}"
                        if tender.get('days_until_deadline'):
                            description += f" (Deadline in {tender.get('days_until_deadline')} days)"
                        
                        tender_data = TenderCreate(
                            id=tender['id'],
                            title=tender['title'],
                            description=description,
                            source=TenderSource.TUNIPAGES,
                            country=tender.get('country'),
                            organization=tender.get('organization'),
                            promoter=tender.get('promoter'),  # TuniPages specific field
                            published_date=tender.get('published_date'),
                            deadline=tender.get('deadline_date'),
                            status=TenderStatus.ACTIVE,
                            category=self.map_to_category(tender.get('sector', '')),
                            tender_type=tender.get('tender_type'),  # TuniPages specific field
                            url=tender.get('detail_url'),
                            relevance_score=tender.get('topaza_relevance_score', 0.0),
                            raw_data=tender
                        )
                        
                        # Create tender in database
                        tender_repo.create(tender_data)
                        self.session_data['tenders_processed'] += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to save tender {tender['id']}: {str(e)}")
                        continue
                
                logger.info(f"Saved {self.session_data['tenders_processed']} tenders to database")
                
        except Exception as e:
            error_msg = f"Failed to save tenders to database: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
    
    def map_to_category(self, sector: str) -> Optional[TenderCategory]:
        """Map sector to tender category"""
        if not sector:
            return None
            
        sector_lower = sector.lower()
        
        if 'consulting' in sector_lower:
            return TenderCategory.CONSULTING
        elif 'training' in sector_lower or 'development' in sector_lower:
            return TenderCategory.CAPACITY_BUILDING
        elif 'technical' in sector_lower:
            return TenderCategory.TECHNICAL_ASSISTANCE
        elif 'business' in sector_lower:
            return TenderCategory.BUSINESS_DEVELOPMENT
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
            logger.info("TuniPages Selenium driver cleanup completed")
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")
    
    def run_scraping_session(self) -> Dict[str, Any]:
        """Run complete TuniPages scraping session optimized for Topaza.net"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Initialize session in database
            with db_manager.session_scope() as session:
                session_repo = AutomationSessionRepository(session)
                session_repo.create(
                    session_id=self.session_id,
                    source=TenderSource.TUNIPAGES,
                    search_params={
                        'search_terms': self.search_terms,
                        'target_countries': self.target_countries,
                        'max_pages': self.max_pages,
                        'scraper_type': 'selenium_enhanced_topaza',
                        'focus': 'maghreb_region'
                    },
                    max_pages=self.max_pages
                )
            
            logger.info(f"Starting TuniPages scraping session for Topaza.net (African focus): {self.session_id}")
            
            # Initialize Selenium driver
            self.initialize_driver()
            
            # Handle initial setup
            if not self.handle_initial_setup():
                raise TuniPagesSeleniumScraperError("Initial setup failed")
            
            # Scrape pages
            page_num = 1
            total_tenders = []
            
            while page_num <= self.max_pages:
                logger.info(f"Processing TuniPages page {page_num}...")
                
                # Extract tenders from current page
                page_tenders = self.extract_tenders_from_page()
                total_tenders.extend(page_tenders)
                
                # Save to database
                if page_tenders:
                    self.save_tenders_to_database(page_tenders)
                
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
                    'maghreb_focus': True,
                    'topaza_optimized': True
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
            
            logger.info(f"TuniPages scraping session completed successfully: {session_summary}")
            return session_summary
            
        except Exception as e:
            error_msg = f"TuniPages scraping session failed: {str(e)}"
            logger.error(error_msg)
            
            # Update session with error
            with db_manager.session_scope() as session:
                session_repo = AutomationSessionRepository(session)
                session_repo.complete_session(
                    session_id=self.session_id,
                    status='failed',
                    error_message=error_msg
                )
            
            raise TuniPagesSeleniumScraperError(error_msg)
            
        finally:
            self.cleanup()


# Function to run TuniPages scraping
def run_tunipages_selenium_scraping(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run TuniPages Selenium scraping session for Topaza.net"""
    scraper = TuniPagesSeleniumScraper(config)
    return scraper.run_scraping_session()


# Test function
def test_tunipages_selenium_scraper():
    """Test TuniPages Selenium scraper functionality"""
    config = {
        'max_pages': 2,  # Limit for testing
        'headless': False,  # Show browser for debugging
        'request_delay': 1  # Faster for testing
    }
    
    try:
        result = run_tunipages_selenium_scraping(config)
        print(f"TuniPages test completed successfully: {result}")
    except Exception as e:
        print(f"TuniPages test failed: {str(e)}")


if __name__ == "__main__":
    # Run test
    test_tunipages_selenium_scraper()