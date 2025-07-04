#!/usr/bin/env python3
"""
Simplified UNGM scraper - MVP approach
Fast, reliable table extraction without complex navigation
"""
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser
from core.config.settings import settings

logger = logging.getLogger(__name__)

class UNGMSimpleScraper:
    """Simplified UNGM scraper for MVP - fast and reliable"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_url = "https://www.ungm.org"
        self.username = settings.automation.ungm_username
        self.password = settings.automation.ungm_password
        
        # African countries for relevance scoring
        self.african_countries = [
            'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi',
            'Cameroon', 'Cape Verde', 'Chad', 'Comoros', 'Congo', 'Djibouti',
            'Egypt', 'Equatorial Guinea', 'Eritrea', 'Ethiopia', 'Gabon', 'Gambia',
            'Ghana', 'Guinea', 'Guinea-Bissau', 'Ivory Coast', 'Kenya', 'Lesotho',
            'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania',
            'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria',
            'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone',
            'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo',
            'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe'
        ]
        
        # Keywords for African consulting opportunities
        self.search_keywords = [
            'consulting', 'advisory services', 'technical assistance',
            'capacity building', 'business development', 'training',
            'management', 'strategy', 'evaluation', 'assessment'
        ]
        
        self.browser = None
        self.page = None
        self.session_id = f"ungm_{int(time.time())}"
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                args=['--disable-dev-shm-usage']
            )
            
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            self.page = await context.new_page()
            
            # Simple stealth measures
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            """)
            
            logger.info("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser initialization failed: {str(e)}")
            return False
    
    async def login_to_ungm(self) -> bool:
        """Login to UNGM with real credentials"""
        try:
            logger.info("🔐 Logging into UNGM...")
            
            # Navigate to login page
            await self.page.goto(f'{self.base_url}/Login', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Fill login form
            await self.page.fill('#UserName', self.username)
            await self.page.fill('#Password', self.password)
            await self.page.click('button[type="submit"]:has-text("Log in")')
            
            # Wait for login to complete
            await asyncio.sleep(5)
            
            # Check if logged in (look for user email in page)
            if self.username.lower() in (await self.page.content()).lower():
                logger.info("✅ Successfully logged into UNGM")
                return True
            else:
                logger.warning("⚠️ Login may have failed, continuing anyway...")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            return False
    
    async def search_opportunities(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for opportunities with simplified extraction"""
        try:
            logger.info(f"🔍 Searching for: {keyword}")
            
            # Go to search page
            await self.page.goto(f'{self.base_url}/Public/Notice', wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Fill search form
            await self.page.fill('#txtNoticeFilterTitle', keyword)
            await self.page.check('#chkIsActive')  # Active opportunities only
            
            # Submit search - try multiple selectors
            try:
                await self.page.click('button[type="submit"]:has-text("Search")')
            except:
                try:
                    await self.page.click('button:has-text("Search")')
                except:
                    # Fallback: try any submit button
                    await self.page.click('button[type="submit"]')
            await asyncio.sleep(8)  # Wait for results
            
            # Extract opportunities using simple approach
            opportunities = await self.extract_table_data()
            
            logger.info(f"✅ Found {len(opportunities)} opportunities for '{keyword}'")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Search failed for '{keyword}': {str(e)}")
            return []
    
    async def extract_table_data(self) -> List[Dict[str, Any]]:
        """Extract data from results table - simplified approach"""
        opportunities = []
        
        try:
            # Wait for search results and look for the specific results table
            await asyncio.sleep(3)  # Give search time to complete
            
            # Look for results indicator first
            try:
                await self.page.wait_for_selector('text=Résultats', timeout=10000)
                logger.info("✅ Found results section")
            except:
                logger.warning("⚠️ No results text found, but continuing...")
            
            # Get all tables and find the right one
            tables = await self.page.locator('table').all()
            logger.info(f"Found {len(tables)} tables on page")
            
            results_table = None
            
            # Find the table with opportunity data - look for specific UNGM results table
            for i, table in enumerate(tables):
                try:
                    # Check if table has multiple rows (data table)
                    rows = await table.locator('tr').all()
                    if len(rows) > 2:  # Header + at least 2 data rows
                        # Check first few cells for content that looks like opportunities
                        first_row_cells = await rows[0].locator('td, th').all()
                        if len(first_row_cells) >= 6:  # UNGM results table should have at least 6 columns
                            # Get text from first few cells
                            cell_texts = []
                            for cell in first_row_cells[:8]:  # Check up to 8 columns
                                text = await cell.inner_text()
                                cell_texts.append(text.strip().lower())
                            
                            # Look for UNGM-specific headers or patterns
                            header_text = ' '.join(cell_texts)
                            logger.debug(f"Table {i+1} headers: {cell_texts}")
                            
                            # UNGM results table indicators (French and English)
                            ungm_indicators = [
                                'titre', 'title', 'deadline', 'échéance',
                                'publication', 'organisation', 'organization',
                                'reference', 'référence', 'notice', 'avis',
                                'pays', 'country', 'type'
                            ]
                            
                            # Count how many UNGM indicators we find
                            indicator_count = sum(1 for indicator in ungm_indicators if indicator in header_text)
                            
                            # Skip calendar tables (they have day names)
                            calendar_indicators = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
                                                 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                            is_calendar = any(indicator in header_text for indicator in calendar_indicators)
                            
                            if indicator_count >= 3 and not is_calendar:
                                logger.info(f"✅ Found UNGM results table {i+1} with {len(rows)} rows (indicators: {indicator_count})")
                                results_table = table
                                break
                            elif is_calendar:
                                logger.debug(f"Skipping calendar table {i+1}")
                                
                except Exception as e:
                    logger.debug(f"Error checking table {i}: {str(e)}")
                    continue
            
            if not results_table:
                logger.warning("❌ Could not find results table")
                return []
            
            # Get all rows from the results table
            rows = await results_table.locator('tr').all()
            logger.info(f"Processing {len(rows)} rows from results table")
            
            # Find the header row to understand table structure
            header_found = False
            data_start_index = 0
            
            for i, row in enumerate(rows):
                cells = await row.locator('td, th').all()
                if cells:
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip().lower())
                    
                    # Look for French headers indicating this is the results table
                    if any('titre' in text for text in cell_texts):
                        header_found = True
                        data_start_index = i + 1
                        logger.info(f"✅ Found results table header at row {i}")
                        break
            
            if not header_found:
                logger.warning("⚠️ Could not find results table header")
                return []
            
            # Extract data rows
            for i in range(data_start_index, min(data_start_index + 20, len(rows))):  # Limit to 20 results
                if i >= len(rows):
                    break
                    
                row = rows[i]
                cells = await row.locator('td').all()
                
                if len(cells) >= 4:  # Need minimum columns
                    try:
                        # Extract basic data - UNGM table structure based on your HTML:
                        # 0: Action buttons, 1: Title (resultTitle), 2: Deadline, 3: Pub Date, 4: Organization, 5: Notice Type, 6: Reference, 7: Country
                        action_buttons = await cells[0].inner_text() if len(cells) > 0 else ''
                        title = await cells[1].inner_text() if len(cells) > 1 else ''
                        deadline = await cells[2].inner_text() if len(cells) > 2 else ''
                        pub_date = await cells[3].inner_text() if len(cells) > 3 else ''
                        organization = await cells[4].inner_text() if len(cells) > 4 else ''
                        notice_type = await cells[5].inner_text() if len(cells) > 5 else ''
                        reference = await cells[6].inner_text() if len(cells) > 6 else ''
                        country = await cells[7].inner_text() if len(cells) > 7 else ''
                        
                        # Extract detail URL from title cell link
                        detail_url = None
                        try:
                            # Look for link in title cell - try multiple approaches
                            title_cell = cells[1] if len(cells) > 1 else None
                            if title_cell:
                                # Try to find any link in the title cell
                                link_elements = await title_cell.locator('a').all()
                                if link_elements:
                                    for link_element in link_elements:
                                        link = await link_element.get_attribute('href')
                                        if link and link != '#':  # Skip empty and placeholder links
                                            if link.startswith('/'):
                                                detail_url = f"{self.base_url}{link}"
                                            elif link.startswith('http'):
                                                detail_url = link
                                            else:
                                                detail_url = f"{self.base_url}/{link}"
                                            logger.debug(f"Extracted detail URL: {detail_url}")
                                            break
                                
                                # If no link found, try to construct from row click action
                                if not detail_url:
                                    # Check if the row has an onclick or data attribute that contains URL
                                    row_onclick = await row.get_attribute('onclick')
                                    if row_onclick and 'Notice' in row_onclick:
                                        import re
                                        url_match = re.search(r"Notice/(\d+)", row_onclick)
                                        if url_match:
                                            notice_id = url_match.group(1)
                                            detail_url = f"{self.base_url}/Public/Notice/AdvertisementDetails/{notice_id}"
                                            logger.debug(f"Constructed URL from onclick: {detail_url}")
                                
                                # If still no link, try to construct from reference
                                if not detail_url:
                                    reference_cell = cells[6] if len(cells) > 6 else None
                                    if reference_cell:
                                        ref_text = await reference_cell.inner_text()
                                        if ref_text.strip() and any(char.isdigit() for char in ref_text):
                                            # Extract numeric part from reference
                                            import re
                                            numbers = re.findall(r'\d+', ref_text)
                                            if numbers:
                                                detail_url = f"{self.base_url}/Public/Notice/AdvertisementDetails/{numbers[-1]}"
                                                logger.debug(f"Constructed URL from reference: {detail_url}")
                                            
                        except Exception as e:
                            logger.debug(f"Could not extract detail URL: {str(e)}")
                        
                        # Final fallback: create search URL with title keywords
                        if not detail_url:
                            title_words = title.split()[:3]  # First 3 words for search
                            search_term = '+'.join(title_words)
                            detail_url = f"{self.base_url}/Public/Notice?Keywords={search_term}"
                            logger.debug(f"Using search URL fallback: {detail_url}")
                        
                        # Clean and validate
                        title = title.strip()
                        if title and len(title) > 10:  # Valid opportunity
                            opportunity = {
                                'id': f"ungm_{self.session_id}_{i}_{int(time.time())}",
                                'title': title,
                                'deadline': deadline.strip(),
                                'publication_date': pub_date.strip(),
                                'organization': organization.strip(),
                                'notice_type': notice_type.strip(),
                                'reference': reference.strip(),
                                'country': country.strip(),
                                'source': 'UNGM',
                                'url': detail_url,  # Use the extracted detail URL
                                'extracted_at': datetime.now(timezone.utc).isoformat(),
                                'status': 'ACTIVE'
                            }
                            
                            # Calculate African relevance
                            relevance_score = self.calculate_african_relevance(opportunity)
                            opportunity['relevance_score'] = relevance_score
                            
                            # Only include African opportunities
                            if relevance_score > 0:
                                opportunities.append(opportunity)
                                logger.info(f"   ✅ Added: {title[:50]}... (Score: {relevance_score})")
                            else:
                                logger.info(f"   ⏭️ Skipped non-African: {title[:50]}...")
                                
                    except Exception as e:
                        logger.warning(f"   ⚠️ Error processing row {i}: {str(e)}")
                        continue
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Table extraction failed: {str(e)}")
            return []
    
    def calculate_african_relevance(self, opportunity: Dict[str, Any]) -> float:
        """Calculate relevance score for African opportunities"""
        score = 0.0
        
        # Combine all text for analysis
        all_text = ' '.join([
            opportunity.get('title', ''),
            opportunity.get('organization', ''),
            opportunity.get('country', ''),
            opportunity.get('notice_type', '')
        ]).lower()
        
        # African indicators
        african_indicators = [
            'africa', 'african', 'afrique', 'africain'
        ] + [country.lower() for country in self.african_countries]
        
        # Check for African relevance
        african_found = False
        for indicator in african_indicators:
            if indicator in all_text:
                score += 50  # High base score for African relevance
                african_found = True
                break
        
        if not african_found:
            return 0  # Skip non-African
        
        # Consulting keywords bonus
        consulting_keywords = ['consulting', 'consultancy', 'advisory', 'technical assistance']
        for keyword in consulting_keywords:
            if keyword in all_text:
                score += 15
        
        # Development keywords bonus
        dev_keywords = ['capacity building', 'training', 'development', 'institutional']
        for keyword in dev_keywords:
            if keyword in all_text:
                score += 10
        
        return min(score, 100)
    
    async def run_full_extraction(self) -> Dict[str, Any]:
        """Run complete extraction session"""
        session_data = {
            'session_id': self.session_id,
            'start_time': datetime.now(timezone.utc),
            'status': 'running',
            'tenders_found': 0,
            'tenders_processed': 0
        }
        
        try:
            logger.info("🚀 Starting UNGM extraction session...")
            
            # Initialize browser
            if not await self.initialize_browser():
                raise Exception("Browser initialization failed")
            
            # Login
            login_success = await self.login_to_ungm()
            if not login_success:
                logger.warning("Login failed, continuing with limited access...")
            
            # Search with multiple keywords
            all_opportunities = []
            
            for keyword in self.search_keywords[:3]:  # Limit to first 3 for MVP
                opportunities = await self.search_opportunities(keyword)
                all_opportunities.extend(opportunities)
                
                # Delay between searches
                await asyncio.sleep(3)
            
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
            session_data.update({
                'status': 'completed',
                'tenders_found': len(unique_opportunities),
                'tenders_processed': saved_count,
                'end_time': datetime.now(timezone.utc)
            })
            
            logger.info(f"✅ Session completed: {saved_count} opportunities saved")
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Session failed: {str(e)}")
            session_data.update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now(timezone.utc)
            })
            return session_data
        
        finally:
            await self.cleanup()
    
    async def save_opportunities(self, opportunities: List[Dict[str, Any]]) -> int:
        """Save opportunities to Supabase database"""
        if not opportunities:
            return 0
        
        try:
            from core.database.supabase_client import supabase_manager
            
            # Prepare opportunities for Supabase
            supabase_opportunities = []
            for opp in opportunities:
                supabase_opp = {
                    'title': opp['title'],
                    'description': opp.get('description') or opp['title'],  # Use title as description fallback
                    'source': opp['source'],
                    'country': opp['country'] or 'Not specified',
                    'organization': opp['organization'],
                    'deadline': opp['deadline'],
                    'url': opp['url'],
                    'reference': opp['reference'],
                    'status': opp['status'],
                    'relevance_score': float(opp['relevance_score']),
                    'publication_date': opp.get('publication_date'),
                    'notice_type': opp.get('notice_type'),
                    'extracted_at': opp['extracted_at']
                }
                supabase_opportunities.append(supabase_opp)
            
            # Bulk insert to Supabase
            saved_count = await supabase_manager.bulk_insert_tenders(supabase_opportunities, use_service_key=True)
            logger.info(f"✅ Saved {saved_count} opportunities to Supabase")
            return saved_count
                
        except Exception as e:
            logger.error(f"Supabase save failed: {str(e)}")
            # Fallback to SQLite for development
            try:
                from core.database.connection import db_manager
                from models.tender import Tender
                
                saved_count = 0
                with db_manager.get_session() as session:
                    for opp in opportunities:
                        try:
                            tender = Tender(
                                title=opp['title'],
                                description=opp['title'],
                                source=opp['source'],
                                country=opp['country'] or 'Not specified',
                                organization=opp['organization'],
                                deadline=opp['deadline'],
                                url=opp['url'],
                                reference=opp['reference'],
                                status=opp['status'],
                                relevance_score=opp['relevance_score'],
                                extracted_at=datetime.now(timezone.utc)
                            )
                            session.add(tender)
                            saved_count += 1
                        except Exception as e:
                            logger.warning(f"Error saving to SQLite: {str(e)}")
                    
                    session.commit()
                    logger.info(f"✅ Fallback: Saved {saved_count} opportunities to SQLite")
                    return saved_count
                    
            except Exception as fallback_error:
                logger.error(f"Both Supabase and SQLite save failed: {str(fallback_error)}")
                return 0
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except:
            pass

# Main function for running the scraper
async def run_ungm_simple_scraping():
    """Run simplified UNGM scraping session"""
    scraper = UNGMSimpleScraper()
    return await scraper.run_full_extraction()

if __name__ == "__main__":
    # Test the simplified scraper
    asyncio.run(run_ungm_simple_scraping())