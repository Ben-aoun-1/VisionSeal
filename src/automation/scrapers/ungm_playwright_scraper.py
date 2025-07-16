#!/usr/bin/env python3
"""
UNGM Playwright Scraper - PRODUCTION READY
Complete scraper for United Nations Global Marketplace (UNGM) tender opportunities
With verified selectors and full functionality
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
    
    def save_tender(self, tender_data: Dict[str, Any], source: str = "UNGM") -> Dict[str, Any]:
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
    
    def save_tenders_batch(self, tenders: List[Dict[str, Any]], source: str = "UNGM") -> Dict[str, Any]:
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
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%m/%d/%Y",
                "%d-%b-%Y"
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

# Comprehensive African countries list for maximum tender coverage
AFRICAN_COUNTRIES = [
    "tunisia", "algeria", "morocco", "senegal", "nigeria", "kenya",
    "ghana", "cameroon", "ivory coast", "burkina faso", "mali",
    "madagascar", "rwanda", "uganda", "tanzania", "ethiopia",
    "south africa", "egypt", "libya", "sudan", "chad", "niger",
    "mozambique", "angola", "zambia", "zimbabwe", "botswana",
    "namibia", "mauritius", "mauritania", "somalia", "djibouti",
    "guinea", "sierra leone", "liberia", "gambia", "benin", "togo",
    "central african republic", "democratic republic of congo", "congo",
    "equatorial guinea", "gabon", "sao tome", "cape verde", "seychelles",
    "comoros", "lesotho", "swaziland", "eswatini", "malawi", "burundi",
    "eritrea", "south sudan", "africa", "african", "francophone africa",
    "subsaharan africa", "sub-saharan africa", "west africa", "east africa",
    "north africa", "southern africa", "central africa"
]

# Priority keywords for consulting/training
PRIORITY_KEYWORDS = [
    "consulting", "training", "formation", "capacity building",
    "technical assistance", "advisory", "expertise", "consultancy",
    "consultant", "expert", "coaching", "mentoring", "workshop",
    "assessment", "evaluation", "support services", "institutional strengthening"
]

# Major organizations
MAJOR_ORGS = [
    "world bank", "undp", "unicef", "who", "african development bank",
    "european union", "usaid", "giz", "unesco", "fao", "wfp",
    "unhcr", "iom", "afdb", "african union", "ecowas", "sadc"
]


def calculate_relevance_score(tender_data: Dict[str, Any]) -> float:
    """Calculate relevance score based on country, keywords, deadline, and organization"""
    score = 50.0  # Base score

    # African countries boost (+20 points)
    if any(country in tender_data.get("country", "").lower() for country in AFRICAN_COUNTRIES):
        score += 20

    # Consulting/training keywords (+15 points)
    text = f"{tender_data.get('title', '')} {tender_data.get('description', '')}".lower()
    if any(keyword in text for keyword in PRIORITY_KEYWORDS):
        score += 15

    # Recent deadline boost (+10 points)
    try:
        deadline = datetime.strptime(tender_data.get('deadline', ''), '%Y-%m-%d')
        days_until = (deadline - datetime.now()).days
        if 0 <= days_until <= 30:  # Deadline within 30 days
            score += 10
    except:
        pass

    # Large organizations boost (+5 points)
    if any(org in tender_data.get("organization", "").lower() for org in MAJOR_ORGS):
        score += 5

    return min(score, 100.0)


async def login_ungm(page, credentials: Dict[str, str]) -> bool:
    """
    Handle UNGM login process with verified selectors
    """
    try:
        logger.info("Navigating to UNGM login page...")
        await page.goto("https://www.ungm.org/Login", wait_until="domcontentloaded")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Wait for login form - using verified selectors from provided HTML
        await page.wait_for_selector('#UserName', timeout=10000)
        logger.info("Login form found")
        
        # Fill credentials using the correct input IDs
        await page.fill('#UserName', credentials['username'])
        logger.info("Email field filled")
        
        await page.fill('#Password', credentials['password'])
        logger.info("Password field filled")
        
        # Submit the form - using the provided button structure
        submit_button = await page.query_selector('button[type="submit"]:has-text("Se connecter")')
        if not submit_button:
            # Fallback to any submit button
            submit_button = await page.query_selector('button[type="submit"]')
        
        if submit_button:
            await submit_button.click()
            logger.info("Login button clicked")
        else:
            # Fallback: press Enter on password field
            await page.press('#Password', 'Enter')
        
        # Wait for navigation
        await page.wait_for_load_state('networkidle')
        
        # Check for successful login - look for logout link or user menu
        success_indicators = [
            'a[href*="/Account/Logout"]',
            'text=Dashboard',
            'text=My Account',
            '.user-menu',
            'a[href*="/Private"]'
        ]
        
        for indicator in success_indicators:
            if await page.query_selector(indicator):
                logger.info("Login successful!")
                return True
        
        # Check for error messages
        error_selectors = [
            '.validation-summary-errors',
            '.alert-danger',
            'text=Invalid username or password'
        ]
        
        for error_sel in error_selectors:
            error_elem = await page.query_selector(error_sel)
            if error_elem:
                error_text = await error_elem.inner_text()
                logger.error(f"Login failed with error: {error_text}")
                return False
        
        # If we're still on login page, login failed
        if "login" in page.url.lower():
            logger.error("Login failed - still on login page")
            return False
            
        return True

    except Exception as e:
        logger.error(f"Login failed with exception: {e}")
        return False


async def navigate_to_tenders(page) -> None:
    """Navigate to the public tender notices page"""
    try:
        logger.info("Navigating to tender notices...")
        await page.goto("https://www.ungm.org/Public/Notice", wait_until="networkidle")
        
        # Wait for the tender table to load
        await page.wait_for_selector('#tblNotices', timeout=15000)
        
    except Exception as e:
        logger.warning(f"Error navigating to tenders: {e}")


async def apply_ungm_filters(page, config: Dict[str, Any]) -> None:
    """Apply search filters for African countries and consulting keywords"""
    try:
        logger.info("Applying search filters...")
        
        # Look for search/filter inputs
        search_input = await page.query_selector('input[type="search"], input[placeholder*="Search"], #txtSearch')
        if search_input:
            # Build search query
            search_terms = []
            
            # Add keywords
            search_terms.extend(PRIORITY_KEYWORDS[:3])
            
            # Add African countries
            search_terms.extend(["Africa", "African"])
            
            search_query = " OR ".join(search_terms)
            await search_input.fill(search_query)
            
            # Trigger search
            await page.press('input[type="search"]', 'Enter')
            await page.wait_for_load_state('networkidle')
        
        # Look for advanced filters
        advanced_filters = await page.query_selector('a:has-text("Advanced Search"), button:has-text("Filters")')
        if advanced_filters:
            await advanced_filters.click()
            await asyncio.sleep(1)
            
            # Try to set country filter
            country_select = await page.query_selector('select[name*="Country"], #ddlCountry')
            if country_select:
                # Try to select African countries
                for country in ["Tunisia", "Kenya", "Nigeria", "South Africa"]:
                    try:
                        await country_select.select_option(label=country)
                        break
                    except:
                        continue
            
            # Set date range for recent tenders
            date_from = await page.query_selector('input[name*="DateFrom"], #txtDateFrom')
            if date_from:
                from_date = (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y')
                await date_from.fill(from_date)
            
            # Apply filters
            apply_button = await page.query_selector('button:has-text("Apply"), button:has-text("Search")')
            if apply_button:
                await apply_button.click()
                await page.wait_for_load_state('networkidle')
        
    except Exception as e:
        logger.warning(f"Error applying filters: {e}")


async def extract_tender_from_row(row_element) -> Dict[str, Any]:
    """Extract tender data from a table row using verified selectors from provided HTML"""
    tender_data = {
        "title": "",
        "description": "",
        "country": "",
        "organization": "",
        "deadline": "",
        "reference": "",
        "url": "",
        "type": "Request for Proposal",
        "publication_date": ""
    }
    
    try:
        # Get all cells in the row using the exact structure provided
        cells = await row_element.query_selector_all('.tableCell')
        
        if len(cells) >= 8:
            # Cell 0: Actions (skip)
            # Cell 1: Title - extract from .ungm-title span
            title_cell = cells[1]
            title_span = await title_cell.query_selector('.ungm-title.ungm-title--small')
            if title_span:
                tender_data["title"] = (await title_span.inner_text()).strip()
            
            # Extract URL from the "open in new tab" link
            link_element = await title_cell.query_selector('a[href*="/Public/Notice/"]')
            if link_element:
                href = await link_element.get_attribute('href')
                tender_data["url"] = f"https://www.ungm.org{href}" if href.startswith('/') else href
            
            # Define French month mappings
            french_months = {
                'janv.': 'Jan', 'févr.': 'Feb', 'mars': 'Mar', 'avr.': 'Apr',
                'mai': 'May', 'juin': 'Jun', 'juil.': 'Jul', 'août': 'Aug',
                'sept.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'déc.': 'Dec'
            }
            
            # Cell 2: Deadline - format "09-juil.-2025 10:00 (GMT 00.00)"
            deadline_cell = cells[2]
            deadline_text = await deadline_cell.inner_text()
            # Parse deadline - look for date pattern
            date_match = re.search(r'(\d{1,2}-\w+\.?-\d{4})', deadline_text)
            if date_match:
                date_str = date_match.group(1)
                # Handle French month abbreviations
                for fr, en in french_months.items():
                    date_str = date_str.replace(fr, en)
                
                try:
                    # Try different date formats
                    for fmt in ['%d-%b-%Y', '%d-%b.-%Y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            tender_data["deadline"] = date_obj.strftime('%Y-%m-%d')
                            break
                        except:
                            continue
                except:
                    tender_data["deadline"] = deadline_text.split('\n')[0].strip()
            
            # Cell 3: Publication date - format "27-juin-2025"
            pub_date_cell = cells[3]
            pub_date_text = await pub_date_cell.inner_text()
            date_match = re.search(r'(\d{1,2}-\w+\.?-\d{4})', pub_date_text)
            if date_match:
                date_str = date_match.group(1)
                # Handle French month abbreviations
                for fr, en in french_months.items():
                    date_str = date_str.replace(fr, en)
                
                try:
                    for fmt in ['%d-%b-%Y', '%d-%b.-%Y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            tender_data["publication_date"] = date_obj.strftime('%Y-%m-%d')
                            break
                        except:
                            continue
                except:
                    tender_data["publication_date"] = pub_date_text.strip()
            
            # Cell 4: Organization/Agency - extract from span
            org_cell = cells[4]
            org_span = await org_cell.query_selector('span')
            if org_span:
                tender_data["organization"] = (await org_span.inner_text()).strip()
            
            # Cell 5: Type - extract from label
            type_cell = cells[5]
            type_label = await type_cell.query_selector('label')
            if type_label:
                tender_data["type"] = (await type_label.inner_text()).strip()
            
            # Cell 6: Reference number - extract from span
            ref_cell = cells[6]
            ref_span = await ref_cell.query_selector('span')
            if ref_span:
                tender_data["reference"] = (await ref_span.inner_text()).strip()
            
            # Cell 7: Country - extract from span
            country_cell = cells[7]
            country_span = await country_cell.query_selector('span')
            if country_span:
                tender_data["country"] = (await country_span.inner_text()).strip()
    
    except Exception as e:
        logger.warning(f"Error extracting tender from row: {e}")
    
    return tender_data


async def extract_tender_details(page, tender_url: str) -> Dict[str, Any]:
    """Extract detailed information from a tender page"""
    try:
        await page.goto(tender_url, wait_until="networkidle")
        
        tender_data = {
            "url": tender_url,
            "description": "",
            "estimated_budget": "",
            "contact_email": ""
        }
        
        # Extract description - look for main content area
        desc_selectors = [
            '.notice-description',
            '.tender-description',
            '#divDescription',
            '.content-main',
            'div[class*="description"]'
        ]
        
        for selector in desc_selectors:
            desc_elem = await page.query_selector(selector)
            if desc_elem:
                tender_data["description"] = await desc_elem.inner_text()
                break
        
        # Extract budget if available
        budget_text = await page.inner_text('body')
        budget_match = re.search(r'(budget|amount|value).*?(\$|USD|EUR)?\s*([\d,]+)', budget_text, re.IGNORECASE)
        if budget_match:
            tender_data["estimated_budget"] = budget_match.group(0)
        
        # Extract contact email
        email_links = await page.query_selector_all('a[href^="mailto:"]')
        if email_links:
            first_email = await email_links[0].get_attribute('href')
            tender_data["contact_email"] = first_email.replace('mailto:', '')
        
        return tender_data
        
    except Exception as e:
        logger.error(f"Error extracting tender details from {tender_url}: {e}")
        return {}


async def extract_tenders_from_current_page(page, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract tenders from the current page state"""
    tenders = []
    
    try:
        # Wait for tender table
        await page.wait_for_selector('#tblNotices', timeout=10000)
        
        # Get all tender rows - using exact selector from provided HTML
        tender_rows = await page.query_selector_all('.tableRow.dataRow.notice-table')
        
        logger.info(f"Found {len(tender_rows)} tender rows on current page")
        
        for row in tender_rows:
            try:
                # Extract basic tender data from row
                tender_data = await extract_tender_from_row(row)
                
                # Skip if no title or URL
                if not tender_data["title"] or not tender_data["url"]:
                    continue
                
                # Get detailed information if enabled
                if tender_data["url"] and config.get('fetch_details', True):
                    # Open in new tab
                    new_page = await page.context.new_page()
                    try:
                        detailed_data = await extract_tender_details(new_page, tender_data["url"])
                        tender_data.update(detailed_data)
                    finally:
                        await new_page.close()
                
                # Calculate relevance score
                tender_data["relevance_score"] = calculate_relevance_score(tender_data)
                
                # Only add if meets minimum relevance threshold
                if tender_data["relevance_score"] >= 50:
                    tenders.append(tender_data)
                    logger.info(f"Added tender: {tender_data['title'][:50]}... (Score: {tender_data['relevance_score']})")
                    
            except Exception as e:
                logger.warning(f"Error processing tender row: {e}")
                continue
        
        logger.info(f"Extracted {len(tenders)} relevant tenders from current page")
        
    except Exception as e:
        logger.error(f"Error extracting tenders from current page: {e}")
    
    return tenders


async def scrape_ungm_page(page, page_num: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape a single UNGM page using verified selectors"""
    tenders = []
    
    try:
        logger.info(f"Scraping page {page_num}...")
        
        # Handle pagination if not on page 1
        if page_num > 1:
            # Look for pagination controls
            pagination_selector = f'a[href*="page={page_num}"], .pagination a:has-text("{page_num}")'
            pagination_link = await page.query_selector(pagination_selector)
            
            if pagination_link:
                await pagination_link.click()
                await page.wait_for_load_state('networkidle')
            else:
                # Try next button
                next_button = await page.query_selector('a:has-text("Next"), .pagination .next')
                if next_button and page_num > 1:
                    for _ in range(page_num - 1):
                        await next_button.click()
                        await page.wait_for_load_state('networkidle')
                        await asyncio.sleep(1)
        
        # Wait for tender table
        await page.wait_for_selector('#tblNotices', timeout=10000)
        
        # Get all tender rows - using exact selector from provided HTML
        tender_rows = await page.query_selector_all('.tableRow.dataRow.notice-table')
        
        logger.info(f"Found {len(tender_rows)} tender rows on page {page_num}")
        
        for row in tender_rows:
            try:
                # Extract basic tender data from row
                tender_data = await extract_tender_from_row(row)
                
                # Skip if no title or URL
                if not tender_data["title"] or not tender_data["url"]:
                    continue
                
                # Get detailed information if enabled
                if tender_data["url"] and config.get('fetch_details', True):
                    # Open in new tab
                    new_page = await page.context.new_page()
                    try:
                        detailed_data = await extract_tender_details(new_page, tender_data["url"])
                        tender_data.update(detailed_data)
                    finally:
                        await new_page.close()
                
                # Calculate relevance score
                tender_data["relevance_score"] = calculate_relevance_score(tender_data)
                
                # Only add if meets minimum relevance threshold
                if tender_data["relevance_score"] >= 50:
                    tenders.append(tender_data)
                    logger.info(f"Added tender: {tender_data['title'][:50]}... (Score: {tender_data['relevance_score']})")
                    
            except Exception as e:
                logger.warning(f"Error processing tender row: {e}")
                continue
        
        logger.info(f"Extracted {len(tenders)} relevant tenders from page {page_num}")
        
    except Exception as e:
        logger.error(f"Error scraping page {page_num}: {e}")
    
    return tenders


async def run_ungm_scraping(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main UNGM scraping function with authentication
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
            
            # Create context with proper viewport
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            page.set_default_timeout(config.get('timeout', 30) * 1000)
            
            # Step 1: Authenticate
            credentials = config.get('credentials', {})
            if not credentials.get('username') or not credentials.get('password'):
                raise Exception("Missing credentials in config")
            
            logger.info("Attempting to login to UNGM...")
            authentication_success = await login_ungm(page, credentials)
            
            if not authentication_success:
                raise Exception("Authentication failed - please check credentials")
            
            logger.info("Login successful, proceeding to tender search...")
            
            # Step 2: Navigate to tenders
            await navigate_to_tenders(page)
            
            # Step 3: Apply filters
            await apply_ungm_filters(page, config)
            
            # Step 4: Optimized batch AJAX scraping - Load all pages at once
            max_pages = config.get('max_pages', 5)  # Default to 5 pages for efficiency
            if config.get('test_mode', False):
                max_pages = min(max_pages, 2)
            
            logger.info(f"Starting batch AJAX scraping for {max_pages} pages...")
            
            # Use correct UNGM JSON AJAX pagination 
            for page_num in range(2, max_pages + 1):
                try:
                    logger.info(f"Loading page {page_num} via UNGM AJAX...")
                    
                    # Count current rows before loading
                    current_rows = await page.query_selector_all('.tableRow.dataRow.notice-table')
                    current_count = len(current_rows)
                    logger.info(f"Current tender rows: {current_count}")
                    
                    # Get current date for payload (UNGM requires date filters)
                    from datetime import datetime
                    current_date = datetime.now().strftime("%d-%b-%Y")
                    
                    # Make AJAX call with correct JSON payload
                    await page.evaluate(f"""
                        fetch('/Public/Notice/Search', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            }},
                            body: JSON.stringify({{
                                "PageIndex": {page_num},
                                "PageSize": 15,
                                "Title": "",
                                "Description": "",
                                "Reference": "",
                                "PublishedFrom": "",
                                "PublishedTo": "{current_date}",
                                "DeadlineFrom": "{current_date}",
                                "DeadlineTo": "",
                                "Countries": [],
                                "Agencies": [],
                                "UNSPSCs": [],
                                "NoticeTypes": [],
                                "SortField": "Deadline",
                                "SortAscending": true,
                                "isPicker": false,
                                "IsSustainable": false,
                                "IsActive": true,
                                "NoticeDisplayType": null,
                                "NoticeSearchTotalLabelId": "noticeSearchTotal",
                                "TypeOfCompetitions": []
                            }})
                        }}).then(response => response.text()).then(html => {{
                            // Parse HTML response and append to table
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(html, 'text/html');
                            const newRows = doc.querySelectorAll('.tableRow.dataRow.notice-table');
                            const tbody = document.querySelector('#tblNotices tbody, #tblNotices');
                            
                            if (tbody && newRows.length > 0) {{
                                newRows.forEach(row => tbody.appendChild(row));
                                console.log('Appended', newRows.length, 'new tender rows');
                            }} else {{
                                console.log('No new rows found in response');
                            }}
                        }}).catch(err => console.log('AJAX failed:', err));
                    """)
                    
                    # Wait for content to load
                    await asyncio.sleep(3)
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Count rows after loading attempt
                    new_rows = await page.query_selector_all('.tableRow.dataRow.notice-table')
                    new_count = len(new_rows)
                    logger.info(f"Tender rows after AJAX call: {new_count}")
                    
                    if new_count <= current_count:
                        logger.warning(f"No new tenders loaded on page {page_num}, stopping")
                        break
                    
                    logger.info(f"Successfully loaded {new_count - current_count} new tenders from page {page_num}")
                    
                except Exception as e:
                    logger.warning(f"Error loading page {page_num}: {e}")
                    continue
            
            # Now extract all tenders from the loaded content (all pages at once)
            logger.info("Extracting all tenders from loaded content...")
            await page.wait_for_selector('#tblNotices', timeout=10000)
            all_rows = await page.query_selector_all('.tableRow.dataRow.notice-table')
            
            logger.info(f"Found {len(all_rows)} total tender rows after loading all pages")
            
            # Collect all raw tender data first (without processing)
            all_raw_tenders = []
            for row in all_rows:
                try:
                    raw_data = await extract_tender_from_row(row)
                    if raw_data["title"] and raw_data["url"]:
                        all_raw_tenders.append(raw_data)
                except Exception as e:
                    logger.debug(f"Error extracting raw tender: {e}")
                    continue
            
            # Remove duplicates by URL, reference, and title
            unique_tenders = {}
            for tender in all_raw_tenders:
                # Create a unique identifier using URL, reference, and title
                identifier = (tender.get('url', ''), tender.get('reference', ''), tender.get('title', ''))
                if identifier not in unique_tenders and identifier[0]:  # Ensure URL exists
                    unique_tenders[identifier] = tender
            
            logger.info(f"Found {len(unique_tenders)} unique tenders after deduplication")
            
            # Now process each unique tender (fetch details, score, etc.)
            for idx, (identifier, tender_data) in enumerate(unique_tenders.items(), 1):
                try:
                    logger.info(f"Processing tender {idx}/{len(unique_tenders)}: {tender_data['title'][:50]}...")
                    
                    # Get detailed information if enabled
                    if config.get('fetch_details', True):
                        new_page = await context.new_page()
                        try:
                            detailed_data = await extract_tender_details(new_page, tender_data['url'])
                            tender_data.update(detailed_data)
                        finally:
                            await new_page.close()
                    
                    # Calculate relevance score
                    tender_data["relevance_score"] = calculate_relevance_score(tender_data)
                    
                    # Only add if meets minimum relevance threshold
                    if tender_data["relevance_score"] >= 50:
                        tenders.append(tender_data)
                        logger.info(f"Added tender: {tender_data['title'][:50]}... (Score: {tender_data['relevance_score']})")
                        
                except Exception as e:
                    logger.warning(f"Error processing tender {idx}: {e}")
                    continue
            
            pages_processed = max_pages
            
            await browser.close()
            
            # Sort tenders by relevance score
            tenders.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Save tenders to Supabase
            supabase_result = {"saved_count": 0, "errors": []}
            
            if tenders and config.get('save_to_supabase', True):
                try:
                    logger.info(f"Saving {len(tenders)} tenders to Supabase...")
                    saver = SupabaseTenderSaver()
                    supabase_result = saver.save_tenders_batch(tenders, "UNGM")
                    
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
                    "source": "ungm",
                    "execution_time": time.time() - start_time,
                    "config_used": config,
                    "login_attempt": True,
                    "session_valid": True
                }
            }
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return {
            "success": False,
            "tenders_found": len(tenders),
            "tenders_processed": len(tenders),
            "pages_processed": pages_processed,
            "authentication_success": authentication_success,
            "tenders": tenders,
            "error": str(e),
            "supabase_result": {"saved_count": 0, "errors": [str(e)]},
            "metadata": {
                "source": "ungm",
                "execution_time": time.time() - start_time,
                "config_used": config,
                "login_attempt": True,
                "session_valid": False
            }
        }



# Test function
if __name__ == "__main__":
    # Maximum African tender extraction configuration
    test_config = {
        "max_pages": 100,  # Increased for maximum extraction
        "timeout": 45,
        "headless": True,  # Faster scraping
        "request_delay": 2,  # Reasonable delay for details fetching
        "test_mode": False,  # No page limit
        "max_retries": 3,
        "retry_delay": 3,
        "fetch_details": True,  # Keep fetching details
        "save_to_supabase": True,  # Enable Supabase integration
        "credentials": {
            "username": os.getenv("UNGM_USERNAME"),
            "password": os.getenv("UNGM_PASSWORD")
        }
    }
    
    # Validate credentials
    if not test_config["credentials"]["username"] or not test_config["credentials"]["password"]:
        print("❌ Error: UNGM credentials not found in environment variables")
        print("Please set UNGM_USERNAME and UNGM_PASSWORD")
        exit(1)
    
    # Run the scraper
    result = asyncio.run(run_ungm_scraping(test_config))
    
    # Print results
    print(f"\nScraping completed!")
    print(f"Success: {result['success']}")
    print(f"Authentication: {result['authentication_success']}")
    print(f"Tenders found: {result['tenders_found']}")
    print(f"Pages processed: {result['pages_processed']}")
    print(f"Execution time: {result['metadata']['execution_time']:.2f} seconds")
    
    # Print Supabase results
    if 'supabase_result' in result:
        supabase = result['supabase_result']
        print(f"Supabase: {supabase['saved_count']}/{result['tenders_found']} saved")
        if supabase['errors']:
            print(f"Supabase errors: {len(supabase['errors'])}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    if result['tenders']:
        print(f"\nTop 5 tenders by relevance:")
        for i, tender in enumerate(result['tenders'][:5], 1):
            print(f"\n{i}. {tender['title']}")
            print(f"   Organization: {tender['organization']}")
            print(f"   Country: {tender['country']}")
            print(f"   Deadline: {tender['deadline']}")
            print(f"   Relevance Score: {tender['relevance_score']}")
            print(f"   URL: {tender['url']}")
    
    # Save results to file
    with open('ungm_results.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to ungm_results.json")