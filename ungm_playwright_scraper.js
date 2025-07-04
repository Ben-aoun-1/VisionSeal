const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

class UNGMAfricanOpportunitiesScraper {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = [];
        this.scrapedCount = 0;
        this.errors = [];
        this.currentSession = new Date().toISOString().replace(/[:.]/g, '-');
        
        // Create output directories
        this.outputDir = path.join(__dirname, 'ungm_african_opportunities', this.currentSession);
        this.screenshotsDir = path.join(this.outputDir, 'screenshots');
        this.documentsDir = path.join(this.outputDir, 'documents');
        this.checkpointsDir = path.join(this.outputDir, 'checkpoints');
        
        this.createDirectories();
        
        // Configuration
        this.config = {
            credentials: {
                username: 'topaza.bd@gmail.com',
                password: 'Topaza2223**'
            },
            baseUrl: 'https://www.ungm.org',
            maxPages: 15,
            delayBetweenRequests: 3000, // 3 seconds
            delayBetweenPages: 5000, // 5 seconds
            requestTimeout: 45000,
            checkpointInterval: 50, // Save every 50 opportunities
            maxRetries: 3
        };
        
        // Search keywords for consulting and business development (TITLE ONLY)
        this.searchKeywords = [
            'consulting',
            'advisory services', 
            'technical assistance',
            'capacity building',
            'business development',
            'training',
            'management',
            'strategy',
            'evaluation'
        ];
        
        // All 54 African countries for filtering
        this.africanCountries = [
            // North Africa
            'Tunisia', 'Morocco', 'Algeria', 'Egypt', 'Libya', 'Sudan',
            // West Africa  
            'Nigeria', 'Ghana', 'Senegal', 'Mali', 'Burkina Faso', 'Niger',
            'Guinea', 'Sierra Leone', 'Liberia', 'Gambia', 'Cape Verde',
            'Mauritania', 'Benin', 'Togo', 'Ivory Coast', 'Guinea-Bissau',
            'Côte d\'Ivoire', 'Cote d\'Ivoire',
            // East Africa
            'Kenya', 'Ethiopia', 'Tanzania', 'Uganda', 'Rwanda', 'Burundi',
            'Somalia', 'Djibouti', 'Eritrea', 'South Sudan', 'Madagascar',
            'Mauritius', 'Seychelles', 'Comoros',
            // Central Africa
            'Democratic Republic of Congo', 'DRC', 'Congo', 'Cameroon',
            'Central African Republic', 'CAR', 'Chad', 'Gabon', 'Equatorial Guinea',
            'São Tomé and Príncipe', 'Sao Tome',
            // Southern Africa
            'South Africa', 'Botswana', 'Namibia', 'Zimbabwe', 'Zambia',
            'Angola', 'Mozambique', 'Malawi', 'Lesotho', 'Swaziland',
            'Eswatini'
        ];
        
        // Major African economies for bonus scoring (40 points base + 10 bonus)
        this.majorAfricanEconomies = [
            'Nigeria', 'South Africa', 'Kenya', 'Ghana', 'Egypt'
        ];
    }
    
    createDirectories() {
        const dirs = [this.outputDir, this.screenshotsDir, this.documentsDir, this.checkpointsDir];
        dirs.forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });
        
        console.log(`📁 Created output directories in: ${this.outputDir}`);
    }
    
    async initialize() {
        console.log('🚀 Initializing UNGM African Opportunities Scraper...');
        
        this.browser = await chromium.launch({
            headless: false, // Set to true for production
            slowMo: 100,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        });
        
        this.page = await this.browser.newPage();
        
        // Set realistic headers to avoid bot detection
        await this.page.setExtraHTTPHeaders({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        });
        
        // Set viewport
        await this.page.setViewportSize({ width: 1366, height: 768 });
        
        console.log('✅ Browser initialized successfully');
        await this.takeScreenshot('01-browser-initialized');
    }
    
    async login() {
        console.log('🔐 Logging in to UNGM...');
        
        try {
            await this.page.goto(`${this.config.baseUrl}/Login`, {
                waitUntil: 'networkidle',
                timeout: this.config.requestTimeout
            });
            
            await this.takeScreenshot('02-login-page');
            
            await this.page.fill('#UserName', this.config.credentials.username);
            await this.page.fill('#Password', this.config.credentials.password);
            
            await this.takeScreenshot('03-credentials-filled');
            
            await this.page.click('button[type=\"submit\"]:has-text(\"Log in\")');
            await this.page.waitForSelector('text=Tableau De Bord', { timeout: 15000 });
            
            console.log('✅ Successfully logged in to UNGM');
            await this.takeScreenshot('04-logged-in-dashboard');
            await this.delay(2000);
            
        } catch (error) {
            console.error('❌ Login failed:', error.message);
            await this.takeScreenshot('error-login-failed');
            throw new Error(`Login failed: ${error.message}`);
        }
    }
    
    async navigateToBusinessOpportunities() {
        console.log('📋 Navigating to Business Opportunities...');
        
        try {
            await this.page.click('a:has-text(\"Opportunités commerciales\")');
            await this.page.waitForSelector('text=Opportunités Commerciales', { timeout: 15000 });
            
            console.log('✅ Successfully navigated to Business Opportunities');
            await this.takeScreenshot('05-business-opportunities-page');
            await this.delay(2000);
            
        } catch (error) {
            console.error('❌ Failed to navigate to Business Opportunities:', error.message);
            await this.takeScreenshot('error-navigation-failed');
            throw error;
        }
    }
    
    async performKeywordSearch(keyword) {
        console.log(`🔍 Searching for active opportunities with keyword: \"${keyword}\"...`);
        
        try {
            // Clear all search fields
            await this.page.evaluate(() => {
                document.getElementById('txtNoticeFilterTitle').value = '';
                document.getElementById('txtNoticeFilterDesc').value = '';
                document.getElementById('txtNoticeFilterRef').value = '';
            });
            
            // Enter keyword ONLY in title field as requested
            await this.page.fill('#txtNoticeFilterTitle', keyword);
            
            // Ensure \"Actuellement actif uniquement\" (Currently active only) is checked
            await this.page.click('#chkIsActive');
            
            await this.takeScreenshot(`06-search-configured-${keyword.replace(/\\s+/g, '-')}`);
            
            // Click search button
            await this.page.click('button:has-text(\"Rechercher\")');
            
            // Wait for results (either table or no results message)
            try {
                await this.page.waitForSelector('table tbody tr, text=\"Aucun avis de marché\"', { timeout: 10000 });
            } catch (e) {
                // Continue even if timeout - may still have results
            }
            
            await this.delay(3000);
            
            console.log(`✅ Search completed for keyword: \"${keyword}\"`);
            await this.takeScreenshot(`07-search-results-${keyword.replace(/\\s+/g, '-')}`);
            
        } catch (error) {
            console.error(`❌ Search failed for keyword \"${keyword}\":`, error.message);
            await this.takeScreenshot(`error-search-failed-${keyword.replace(/\\s+/g, '-')}`);
            throw error;
        }
    }
    
    async extractOpportunityDetails(row, index) {
        console.log(`📋 Extracting details for opportunity ${index}...`);
        
        try {
            const cells = await row.locator('td').all();
            if (cells.length < 6) {
                console.log('⚠️ Insufficient cell data, skipping...');
                return null;
            }
            
            // Extract basic information from table row
            const basicInfo = {
                title: await this.getTextContent(cells[0]),
                deadline: await this.getTextContent(cells[1]),
                publicationDate: await this.getTextContent(cells[2]),
                organization: await this.getTextContent(cells[3]),
                noticeType: await this.getTextContent(cells[4]),
                reference: await this.getTextContent(cells[5]),
                country: cells.length > 6 ? await this.getTextContent(cells[6]) : '', // If country column exists
            };
            
            // Try to extract detailed information by clicking into the opportunity
            let detailedInfo = {};
            let documentLinks = [];
            
            try {
                const titleLink = row.locator('td:first-child a');
                if (await titleLink.isVisible()) {
                    console.log(`🔗 Extracting detailed info for: ${basicInfo.title.substring(0, 50)}...`);
                    
                    await titleLink.click();
                    await this.page.waitForLoadState('networkidle', { timeout: 15000 });
                    
                    // Extract comprehensive details from the detail page
                    detailedInfo = await this.extractDetailedInformation();
                    documentLinks = await this.extractDocumentLinks();
                    
                    await this.takeScreenshot(`opportunity-detail-${index}`);
                    
                    // Go back to results
                    await this.page.goBack();
                    await this.page.waitForLoadState('networkidle', { timeout: 15000 });
                    await this.delay(2000);
                    
                    console.log(`✅ Detailed extraction completed for opportunity ${index}`);
                } else {
                    console.log(`ℹ️ No clickable link found for opportunity ${index}`);
                }
            } catch (detailError) {
                console.warn(`⚠️ Could not extract detailed information for opportunity ${index}:`, detailError.message);
                this.errors.push({
                    type: 'detail_extraction_error',
                    opportunity: basicInfo.title,
                    error: detailError.message,
                    timestamp: new Date().toISOString()
                });
            }
            
            // Create comprehensive opportunity object
            const opportunity = {
                // Basic Information
                title: basicInfo.title || '',
                reference: basicInfo.reference || '',
                organization: basicInfo.organization || '',
                deadline: basicInfo.deadline || '',
                publicationDate: basicInfo.publicationDate || '',
                noticeType: basicInfo.noticeType || '',
                status: 'Active', // Since we filter for active only
                
                // Organization Details
                organizationType: this.determineOrganizationType(basicInfo.organization),
                contactPerson: detailedInfo.contactPerson || '',
                contactEmail: detailedInfo.contactEmail || '',
                contactPhone: detailedInfo.contactPhone || '',
                officeAddress: detailedInfo.address || '',
                
                // Geographic Information
                country: detailedInfo.country || basicInfo.country || this.extractCountryFromText(detailedInfo.description + ' ' + basicInfo.organization),
                specificLocation: detailedInfo.location || '',
                regionalCoverage: detailedInfo.regionalCoverage || '',
                implementationLocation: detailedInfo.implementationLocation || '',
                
                // Project Details
                fullDescription: detailedInfo.description || '',
                technicalRequirements: detailedInfo.technicalRequirements || '',
                qualificationsRequired: detailedInfo.qualifications || '',
                experienceRequirements: detailedInfo.experience || '',
                languageRequirements: detailedInfo.languages || '',
                
                // Financial Information
                estimatedBudget: detailedInfo.budget || '',
                currency: detailedInfo.currency || '',
                paymentTerms: detailedInfo.paymentTerms || '',
                budgetSource: detailedInfo.budgetSource || '',
                
                // Timeline Information
                contractDuration: detailedInfo.duration || '',
                expectedStartDate: detailedInfo.startDate || '',
                keyMilestones: detailedInfo.milestones || '',
                submissionDeadline: basicInfo.deadline,
                
                // Documentation
                tenderDocuments: documentLinks.filter(link => link.type === 'tender'),
                annexesAttachments: documentLinks.filter(link => link.type === 'annex'),
                termsOfReference: documentLinks.filter(link => link.type === 'tor'),
                biddingDocuments: documentLinks.filter(link => link.type === 'bidding'),
                
                // Submission Requirements
                submissionMethod: detailedInfo.submissionMethod || '',
                requiredDocuments: detailedInfo.requiredDocs || '',
                proposalFormat: detailedInfo.proposalFormat || '',
                evaluationCriteria: detailedInfo.evaluationCriteria || '',
                
                // Metadata
                url: detailedInfo.url || this.page.url(),
                extractedAt: new Date().toISOString(),
                isAfricanOpportunity: false, // Will be determined below
                relevanceScore: 0, // Will be calculated below
                priorityLevel: 'Low' // Will be determined below
            };
            
            // Determine if this is an African opportunity
            opportunity.isAfricanOpportunity = this.isAfricanOpportunity(opportunity);
            
            // Calculate relevance score
            opportunity.relevanceScore = this.calculateRelevanceScore(opportunity);
            
            // Determine priority level
            opportunity.priorityLevel = this.determinePriorityLevel(opportunity);
            
            return opportunity;
            
        } catch (error) {
            console.error(`❌ Error extracting opportunity details for row ${index}:`, error.message);
            this.errors.push({
                type: 'extraction_error',
                row: index,
                error: error.message,
                timestamp: new Date().toISOString()
            });
            return null;
        }
    }
    
    async extractDetailedInformation() {
        const details = {};
        
        try {
            await this.page.waitForLoadState('networkidle', { timeout: 10000 });
            
            // Get the full page text for pattern matching
            const pageText = await this.page.textContent('body');
            
            // Extract description/scope of work
            const descriptionSelectors = [
                'text=/Description/i',
                'text=/Scope of Work/i',
                'text=/Project Description/i',
                'text=/Objective/i',
                '[class*=\"description\"]'
            ];
            
            for (const selector of descriptionSelectors) {
                try {
                    const element = await this.page.locator(selector).first();
                    if (await element.isVisible()) {
                        const nextElement = element.locator('..').locator('+ *');
                        const text = await nextElement.textContent();
                        if (text && text.length > 100) {
                            details.description = text.trim();
                            break;
                        }
                    }
                } catch (e) {
                    continue;
                }
            }
            
            // Extract country/location using patterns
            const locationPatterns = [
                /(?:Country|Location|Implementation)\\s*:?\\s*([^\\n\\r]+)/gi,
                /(?:Project Location|Duty Station)\\s*:?\\s*([^\\n\\r]+)/gi
            ];
            
            for (const pattern of locationPatterns) {
                const matches = [...pageText.matchAll(pattern)];
                if (matches.length > 0) {
                    details.country = matches[0][1].trim();
                    break;
                }
            }
            
            // Extract budget information
            const budgetPatterns = [
                /(?:Budget|Contract Value|Amount)\\s*:?\\s*([^\\n\\r]+)/gi,
                /(USD|EUR|\\$)\\s*([\\d,\\.]+)/gi
            ];
            
            for (const pattern of budgetPatterns) {
                const matches = [...pageText.matchAll(pattern)];
                if (matches.length > 0) {
                    details.budget = matches[0][0].trim();
                    if (matches[0][0].includes('USD') || matches[0][0].includes('$')) {
                        details.currency = 'USD';
                    } else if (matches[0][0].includes('EUR')) {
                        details.currency = 'EUR';
                    }
                    break;
                }
            }
            
            // Extract contact information
            const emailPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})/g;
            const phonePattern = /(?:Phone|Tel|Telephone)\\s*:?\\s*([^\\n\\r]+)/gi;
            
            const emails = [...pageText.matchAll(emailPattern)];
            if (emails.length > 0) {
                details.contactEmail = emails[0][0];
            }
            
            const phones = [...pageText.matchAll(phonePattern)];
            if (phones.length > 0) {
                details.contactPhone = phones[0][1].trim();
            }
            
            // Extract duration
            const durationPattern = /(?:Duration|Contract Period|Timeline)\\s*:?\\s*([^\\n\\r]+)/gi;
            const durations = [...pageText.matchAll(durationPattern)];
            if (durations.length > 0) {
                details.duration = durations[0][1].trim();
            }
            
            // Get current URL
            details.url = this.page.url();
            
        } catch (error) {
            console.warn('⚠️ Error extracting detailed information:', error.message);
        }
        
        return details;
    }
    
    async extractDocumentLinks() {
        const documentLinks = [];
        
        try {
            const downloadSelectors = [
                'a[href*=\".pdf\"]',
                'a[href*=\".doc\"]',
                'a[href*=\".docx\"]',
                'a[href*=\"download\"]',
                'a:has-text(\"Download\")',
                'a:has-text(\"Document\")',
                'a:has-text(\"Terms of Reference\")',
                'a:has-text(\"TOR\")'
            ];
            
            for (const selector of downloadSelectors) {
                try {
                    const links = await this.page.locator(selector).all();
                    for (const link of links) {
                        if (await link.isVisible()) {
                            const href = await link.getAttribute('href');
                            const text = await link.textContent();
                            
                            if (href && text) {
                                documentLinks.push({
                                    title: text.trim(),
                                    url: href.startsWith('http') ? href : this.config.baseUrl + href,
                                    type: this.categorizeDocument(text.trim())
                                });
                            }
                        }
                    }
                } catch (e) {
                    continue;
                }
            }
        } catch (error) {
            console.warn('⚠️ Error extracting document links:', error.message);
        }
        
        return documentLinks;
    }
    
    categorizeDocument(title) {
        const lowerTitle = title.toLowerCase();
        if (lowerTitle.includes('terms of reference') || lowerTitle.includes('tor')) {
            return 'tor';
        } else if (lowerTitle.includes('tender') || lowerTitle.includes('rfp')) {
            return 'tender';
        } else if (lowerTitle.includes('annex') || lowerTitle.includes('attachment')) {
            return 'annex';
        } else if (lowerTitle.includes('bidding') || lowerTitle.includes('bid')) {
            return 'bidding';
        }
        return 'other';
    }
    
    isAfricanOpportunity(opportunity) {
        const textToCheck = `${opportunity.country} ${opportunity.organization} ${opportunity.fullDescription} ${opportunity.implementationLocation}`.toLowerCase();
        
        return this.africanCountries.some(country => 
            textToCheck.includes(country.toLowerCase())
        );
    }
    
    extractCountryFromText(text) {
        if (!text) return '';
        
        const lowerText = text.toLowerCase();
        for (const country of this.africanCountries) {
            if (lowerText.includes(country.toLowerCase())) {
                return country;
            }
        }
        return '';
    }
    
    determineOrganizationType(organization) {
        if (!organization) return 'Unknown';
        
        const lowerOrg = organization.toLowerCase();
        
        if (lowerOrg.includes('un ') || lowerOrg.includes('united nations')) {
            return 'UN Agency';
        } else if (lowerOrg.includes('world bank') || lowerOrg.includes('wb')) {
            return 'World Bank';
        } else if (lowerOrg.includes('government') || lowerOrg.includes('ministry')) {
            return 'Government';
        } else if (lowerOrg.includes('ngo') || lowerOrg.includes('foundation')) {
            return 'NGO';
        } else if (lowerOrg.includes('private') || lowerOrg.includes('company')) {
            return 'Private Sector';
        }
        
        return 'International Organization';
    }
    
    calculateRelevanceScore(opportunity) {
        let score = 0;
        
        // African country relevance (40 points base)
        if (opportunity.isAfricanOpportunity) {
            score += 40;
            
            // Bonus for major African economies (+10 points)
            const country = opportunity.country.toLowerCase();
            if (this.majorAfricanEconomies.some(majorCountry => 
                country.includes(majorCountry.toLowerCase()))) {
                score += 10;
            }
        } else {
            // Penalty for non-African focus (-20 points)
            score -= 20;
        }
        
        // Management consulting keywords (+15 points)
        const text = `${opportunity.title} ${opportunity.fullDescription}`.toLowerCase();
        const managementKeywords = ['management consulting', 'business consulting', 'strategic consulting'];
        if (managementKeywords.some(keyword => text.includes(keyword))) {
            score += 15;
        }
        
        // Capacity building/training (+10 points)
        const capacityKeywords = ['capacity building', 'training', 'institutional strengthening'];
        if (capacityKeywords.some(keyword => text.includes(keyword))) {
            score += 10;
        }
        
        // General consulting relevance (+5 points per keyword)
        const consultingKeywords = ['consulting', 'advisory', 'technical assistance'];
        consultingKeywords.forEach(keyword => {
            if (text.includes(keyword)) {
                score += 5;
            }
        });
        
        return Math.max(0, score); // Ensure score is not negative
    }
    
    determinePriorityLevel(opportunity) {
        if (opportunity.relevanceScore >= 70) {
            return 'High';
        } else if (opportunity.relevanceScore >= 50) {
            return 'Medium';
        } else if (opportunity.relevanceScore >= 30) {
            return 'Low';
        }
        return 'Very Low';
    }
    
    async scrapeCurrentPage() {
        console.log('📄 Scraping current page for opportunities...');
        
        try {
            // Check if there are results
            const noResultsMessage = await this.page.locator('text=\"Aucun avis de marché\"').first();
            if (await noResultsMessage.isVisible()) {
                console.log('ℹ️ No opportunities found for current search');
                return 0;
            }
            
            // Wait for results table
            await this.page.waitForSelector('table tbody tr', { timeout: 10000 });
            
            const rows = await this.page.locator('table tbody tr').all();
            console.log(`Found ${rows.length} opportunities on current page`);
            
            let processedCount = 0;
            
            for (let i = 0; i < rows.length; i++) {
                try {
                    console.log(`\\n📋 Processing opportunity ${i + 1}/${rows.length}...`);
                    
                    const opportunity = await this.extractOpportunityDetails(rows[i], i + 1);
                    
                    if (opportunity) {
                        // Only save opportunities with relevance score > 0
                        if (opportunity.relevanceScore > 0) {
                            this.results.push(opportunity);
                            this.scrapedCount++;
                            processedCount++;
                            
                            console.log(`✅ Added opportunity: ${opportunity.title.substring(0, 50)}... (Score: ${opportunity.relevanceScore}, Priority: ${opportunity.priorityLevel})`);
                            
                            // Create checkpoint save every N opportunities
                            if (this.scrapedCount % this.config.checkpointInterval === 0) {
                                await this.createCheckpoint();
                            }
                        } else {
                            console.log(`⏭️ Skipped low-relevance opportunity: ${opportunity.title.substring(0, 50)}...`);
                        }
                    }
                    
                    // Delay between opportunity extractions
                    await this.delay(1000);
                    
                } catch (error) {
                    console.error(`❌ Error processing opportunity ${i + 1}:`, error.message);
                    continue;
                }
            }
            
            console.log(`✅ Completed page scraping. Added ${processedCount} relevant opportunities.`);
            return processedCount;
            
        } catch (error) {
            console.error('❌ Error scraping current page:', error.message);
            throw error;
        }
    }
    
    async handlePagination() {
        let currentPage = 1;
        let hasNextPage = true;
        let totalProcessed = 0;
        
        while (hasNextPage && currentPage <= this.config.maxPages) {
            console.log(`\\n📄 Processing page ${currentPage}...`);
            
            const pageProcessed = await this.scrapeCurrentPage();
            totalProcessed += pageProcessed;
            
            // Check for next page
            try {
                // Look for pagination controls
                const nextButtonSelectors = [
                    'a:has-text(\"Suivant\")',
                    'a:has-text(\"Next\")',
                    'a[aria-label=\"Next\"]',
                    '.pagination a:has-text(\">\")'
                ];
                
                let nextClicked = false;
                
                for (const selector of nextButtonSelectors) {
                    try {
                        const nextButton = this.page.locator(selector);
                        if (await nextButton.isVisible() && await nextButton.isEnabled()) {
                            console.log(`⏭️ Moving to page ${currentPage + 1}...`);
                            await nextButton.click();
                            await this.page.waitForLoadState('networkidle', { timeout: 15000 });
                            await this.delay(this.config.delayBetweenPages);
                            currentPage++;
                            nextClicked = true;
                            break;
                        }
                    } catch (e) {
                        continue;
                    }
                }
                
                if (!nextClicked) {
                    console.log('📄 No more pages available or pagination not found');
                    hasNextPage = false;
                }
                
            } catch (error) {
                console.log('📄 Pagination ended:', error.message);
                hasNextPage = false;
            }
        }
        
        console.log(`\\n✅ Pagination completed. Processed ${currentPage - 1} pages, added ${totalProcessed} opportunities.`);
        return totalProcessed;
    }
    
    async scrapeAllKeywords() {
        console.log('🔍 Starting comprehensive search across all keywords...');
        let totalOpportunities = 0;
        
        for (let i = 0; i < this.searchKeywords.length; i++) {
            const keyword = this.searchKeywords[i];
            console.log(`\\n🔎 Searching for keyword ${i + 1}/${this.searchKeywords.length}: "${keyword}"`);
            
            try {
                await this.performKeywordSearch(keyword);
                const keywordResults = await this.handlePagination();
                totalOpportunities += keywordResults;
                
                console.log(`✅ Completed search for "${keyword}". Found ${keywordResults} relevant opportunities.`);
                
                // Delay between different keyword searches
                if (i < this.searchKeywords.length - 1) {
                    await this.delay(this.config.delayBetweenRequests);
                }
                
            } catch (error) {
                console.error(`❌ Error searching for keyword "${keyword}":`, error.message);
                this.errors.push({
                    type: 'keyword_search_error',
                    keyword: keyword,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                continue;
            }
        }
        
        console.log(`\\n🎯 Total opportunities found across all keywords: ${totalOpportunities}`);
        return totalOpportunities;
    }
    
    async createCheckpoint() {
        const checkpointFile = path.join(this.checkpointsDir, `checkpoint-${this.scrapedCount}-${Date.now()}.json`);
        
        const checkpointData = {
            timestamp: new Date().toISOString(),
            totalResults: this.scrapedCount,
            results: this.results,
            errors: this.errors
        };
        
        fs.writeFileSync(checkpointFile, JSON.stringify(checkpointData, null, 2));
        console.log(`💾 Checkpoint saved: ${this.scrapedCount} opportunities`);
    }
    
    generateSummaryReport() {
        console.log('\\n📊 Generating comprehensive summary report...');
        
        const africanOpportunities = this.results.filter(opp => opp.isAfricanOpportunity);
        const highPriorityOpportunities = this.results.filter(opp => opp.priorityLevel === 'High');
        const mediumPriorityOpportunities = this.results.filter(opp => opp.priorityLevel === 'Medium');
        
        // Count by country
        const countryCounts = {};
        africanOpportunities.forEach(opp => {
            if (opp.country) {
                countryCounts[opp.country] = (countryCounts[opp.country] || 0) + 1;
            }
        });
        
        // Count by organization type
        const organizationCounts = {};
        this.results.forEach(opp => {
            if (opp.organizationType) {
                organizationCounts[opp.organizationType] = (organizationCounts[opp.organizationType] || 0) + 1;
            }
        });
        
        // Analyze budget ranges
        const budgetAnalysis = this.analyzeBudgets();
        
        // Upcoming deadlines (next 30 days)
        const upcomingDeadlines = this.getUpcomingDeadlines(30);
        
        const summary = {
            generatedAt: new Date().toISOString(),
            searchSession: this.currentSession,
            
            // Overall Statistics
            totalOpportunitiesScraped: this.results.length,
            africanOpportunities: africanOpportunities.length,
            nonAfricanOpportunities: this.results.length - africanOpportunities.length,
            
            // Priority Breakdown
            highPriorityOpportunities: highPriorityOpportunities.length,
            mediumPriorityOpportunities: mediumPriorityOpportunities.length,
            lowPriorityOpportunities: this.results.filter(opp => opp.priorityLevel === 'Low').length,
            
            // Geographic Distribution
            countriesRepresented: Object.keys(countryCounts).length,
            topCountries: Object.entries(countryCounts)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 10)
                .map(([country, count]) => ({ country, count })),
            
            // Organization Analysis
            organizationTypes: Object.entries(organizationCounts)
                .sort(([,a], [,b]) => b - a)
                .map(([type, count]) => ({ type, count })),
            
            // Budget Analysis
            budgetAnalysis: budgetAnalysis,
            
            // Timeline Analysis
            upcomingDeadlines: upcomingDeadlines.length,
            urgentOpportunities: upcomingDeadlines.filter(opp => opp.daysUntilDeadline <= 7).length,
            
            // Quality Metrics
            opportunitiesWithBudget: this.results.filter(opp => opp.estimatedBudget).length,
            opportunitiesWithContacts: this.results.filter(opp => opp.contactEmail).length,
            opportunitiesWithDocuments: this.results.filter(opp => opp.tenderDocuments.length > 0).length,
            
            // Error Summary
            totalErrors: this.errors.length,
            errorTypes: this.summarizeErrors(),
            
            // Recommendations for Topaza.net
            topRecommendations: this.generateRecommendations()
        };
        
        return summary;
    }
    
    analyzeBudgets() {
        const budgets = this.results
            .filter(opp => opp.estimatedBudget)
            .map(opp => this.extractBudgetValue(opp.estimatedBudget))
            .filter(budget => budget > 0);
        
        if (budgets.length === 0) {
            return { message: 'No budget information available' };
        }
        
        budgets.sort((a, b) => a - b);
        
        return {
            totalWithBudget: budgets.length,
            averageBudget: Math.round(budgets.reduce((sum, budget) => sum + budget, 0) / budgets.length),
            medianBudget: budgets[Math.floor(budgets.length / 2)],
            minBudget: budgets[0],
            maxBudget: budgets[budgets.length - 1],
            budgetRanges: {
                under50k: budgets.filter(b => b < 50000).length,
                '50k-200k': budgets.filter(b => b >= 50000 && b < 200000).length,
                '200k-500k': budgets.filter(b => b >= 200000 && b < 500000).length,
                over500k: budgets.filter(b => b >= 500000).length
            }
        };
    }
    
    extractBudgetValue(budgetString) {
        if (!budgetString) return 0;
        
        // Extract numeric value from budget string
        const matches = budgetString.match(/([\\d,\\.]+)/);
        if (matches) {
            return parseFloat(matches[1].replace(/,/g, ''));
        }
        return 0;
    }
    
    getUpcomingDeadlines(days = 30) {
        const now = new Date();
        const futureDate = new Date();
        futureDate.setDate(now.getDate() + days);
        
        return this.results
            .filter(opp => opp.deadline)
            .map(opp => {
                const deadline = this.parseDate(opp.deadline);
                if (deadline && deadline >= now && deadline <= futureDate) {
                    const daysUntilDeadline = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
                    return {
                        ...opp,
                        parsedDeadline: deadline,
                        daysUntilDeadline: daysUntilDeadline
                    };
                }
                return null;
            })
            .filter(opp => opp !== null)
            .sort((a, b) => a.parsedDeadline - b.parsedDeadline);
    }
    
    parseDate(dateString) {
        if (!dateString) return null;
        
        // Handle various date formats common in UNGM
        const formats = [
            /(\d{1,2})-(\w+)-(\d{4})/, // DD-MMM-YYYY
            /(\d{1,2})\/(\d{1,2})\/(\d{4})/, // DD/MM/YYYY
            /(\d{4})-(\d{1,2})-(\d{1,2})/ // YYYY-MM-DD
        ];
        
        for (const format of formats) {
            const match = dateString.match(format);
            if (match) {
                try {
                    return new Date(dateString);
                } catch (e) {
                    continue;
                }
            }
        }
        
        return null;
    }
    
    summarizeErrors() {
        const errorTypes = {};
        this.errors.forEach(error => {
            errorTypes[error.type] = (errorTypes[error.type] || 0) + 1;
        });
        return errorTypes;
    }
    
    generateRecommendations() {
        const recommendations = [];
        
        // Analyze high-priority opportunities
        const highPriority = this.results.filter(opp => opp.priorityLevel === 'High');
        if (highPriority.length > 0) {
            recommendations.push({
                priority: 'High',
                type: 'Immediate Action',
                recommendation: `Focus on ${highPriority.length} high-priority opportunities with strong African focus and consulting relevance.`,
                opportunities: highPriority.slice(0, 5).map(opp => ({
                    title: opp.title,
                    country: opp.country,
                    deadline: opp.deadline,
                    score: opp.relevanceScore
                }))
            });
        }
        
        // Identify major economy opportunities
        const majorEconomyOpps = this.results.filter(opp => 
            this.majorAfricanEconomies.some(country => 
                opp.country.toLowerCase().includes(country.toLowerCase())
            )
        );
        
        if (majorEconomyOpps.length > 0) {
            recommendations.push({
                priority: 'Medium',
                type: 'Strategic Focus',
                recommendation: `Target opportunities in major African economies: ${majorEconomyOpps.length} opportunities found.`,
                countries: [...new Set(majorEconomyOpps.map(opp => opp.country))]
            });
        }
        
        // Urgent deadlines
        const urgent = this.getUpcomingDeadlines(7);
        if (urgent.length > 0) {
            recommendations.push({
                priority: 'Urgent',
                type: 'Time-Sensitive',
                recommendation: `${urgent.length} opportunities have deadlines within 7 days - immediate action required.`,
                opportunities: urgent.map(opp => ({
                    title: opp.title,
                    deadline: opp.deadline,
                    daysLeft: opp.daysUntilDeadline
                }))
            });
        }
        
        return recommendations;
    }
    
    async saveResults() {
        console.log('💾 Saving comprehensive results...');
        
        try {
            // Generate summary report
            const summary = this.generateSummaryReport();
            
            // Save JSON results
            const jsonFile = path.join(this.outputDir, 'african_opportunities.json');
            fs.writeFileSync(jsonFile, JSON.stringify({
                summary: summary,
                opportunities: this.results,
                errors: this.errors
            }, null, 2));
            
            // Create Excel export
            await this.createExcelExport();
            
            // Save summary report
            const summaryFile = path.join(this.outputDir, 'summary_report.json');
            fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));
            
            // Create CSV for easy analysis
            await this.createCSVExport();
            
            console.log(`✅ Results saved to: ${this.outputDir}`);
            console.log(`📊 Summary: ${this.results.length} opportunities, ${this.results.filter(opp => opp.isAfricanOpportunity).length} African-focused`);
            
        } catch (error) {
            console.error('❌ Error saving results:', error.message);
            throw error;
        }
    }
    
    async createExcelExport() {
        const workbook = XLSX.utils.book_new();
        
        // Main opportunities sheet
        const opportunitiesData = this.results.map(opp => ({
            'Title': opp.title,
            'Reference': opp.reference,
            'Organization': opp.organization,
            'Organization Type': opp.organizationType,
            'Country': opp.country,
            'Deadline': opp.deadline,
            'Publication Date': opp.publicationDate,
            'Notice Type': opp.noticeType,
            'Priority Level': opp.priorityLevel,
            'Relevance Score': opp.relevanceScore,
            'Is African': opp.isAfricanOpportunity ? 'Yes' : 'No',
            'Estimated Budget': opp.estimatedBudget,
            'Currency': opp.currency,
            'Contract Duration': opp.contractDuration,
            'Contact Email': opp.contactEmail,
            'Contact Phone': opp.contactPhone,
            'Full Description': opp.fullDescription,
            'Technical Requirements': opp.technicalRequirements,
            'Qualifications Required': opp.qualificationsRequired,
            'URL': opp.url,
            'Extracted At': opp.extractedAt
        }));
        
        const opportunitiesSheet = XLSX.utils.json_to_sheet(opportunitiesData);
        XLSX.utils.book_append_sheet(workbook, opportunitiesSheet, 'Opportunities');
        
        // High priority opportunities sheet
        const highPriorityData = this.results
            .filter(opp => opp.priorityLevel === 'High')
            .map(opp => ({
                'Title': opp.title,
                'Country': opp.country,
                'Organization': opp.organization,
                'Deadline': opp.deadline,
                'Score': opp.relevanceScore,
                'Budget': opp.estimatedBudget,
                'Contact': opp.contactEmail,
                'URL': opp.url
            }));
        
        if (highPriorityData.length > 0) {
            const highPrioritySheet = XLSX.utils.json_to_sheet(highPriorityData);
            XLSX.utils.book_append_sheet(workbook, highPrioritySheet, 'High Priority');
        }
        
        // African opportunities sheet
        const africanData = this.results
            .filter(opp => opp.isAfricanOpportunity)
            .map(opp => ({
                'Title': opp.title,
                'Country': opp.country,
                'Organization': opp.organization,
                'Deadline': opp.deadline,
                'Priority': opp.priorityLevel,
                'Budget': opp.estimatedBudget,
                'Contact': opp.contactEmail,
                'URL': opp.url
            }));
        
        if (africanData.length > 0) {
            const africanSheet = XLSX.utils.json_to_sheet(africanData);
            XLSX.utils.book_append_sheet(workbook, africanSheet, 'African Opportunities');
        }
        
        // Summary statistics sheet
        const summary = this.generateSummaryReport();
        const summaryData = [
            { 'Metric': 'Total Opportunities', 'Value': summary.totalOpportunitiesScraped },
            { 'Metric': 'African Opportunities', 'Value': summary.africanOpportunities },
            { 'Metric': 'High Priority', 'Value': summary.highPriorityOpportunities },
            { 'Metric': 'Medium Priority', 'Value': summary.mediumPriorityOpportunities },
            { 'Metric': 'Countries Represented', 'Value': summary.countriesRepresented },
            { 'Metric': 'Upcoming Deadlines (30 days)', 'Value': summary.upcomingDeadlines },
            { 'Metric': 'Urgent (7 days)', 'Value': summary.urgentOpportunities },
            { 'Metric': 'With Budget Info', 'Value': summary.opportunitiesWithBudget },
            { 'Metric': 'With Contact Info', 'Value': summary.opportunitiesWithContacts }
        ];
        
        const summarySheet = XLSX.utils.json_to_sheet(summaryData);
        XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary Statistics');
        
        // Save Excel file
        const excelFile = path.join(this.outputDir, 'african_opportunities.xlsx');
        XLSX.writeFile(workbook, excelFile);
        
        console.log('📊 Excel export created successfully');
    }
    
    async createCSVExport() {
        const csvData = this.results.map(opp => ({
            Title: opp.title,
            Reference: opp.reference,
            Organization: opp.organization,
            Country: opp.country,
            Deadline: opp.deadline,
            Priority: opp.priorityLevel,
            Score: opp.relevanceScore,
            African: opp.isAfricanOpportunity ? 'Yes' : 'No',
            Budget: opp.estimatedBudget,
            Contact: opp.contactEmail,
            URL: opp.url
        }));
        
        if (csvData.length > 0) {
            const csv = this.convertToCSV(csvData);
            const csvFile = path.join(this.outputDir, 'african_opportunities.csv');
            fs.writeFileSync(csvFile, csv);
            console.log('📄 CSV export created successfully');
        }
    }
    
    convertToCSV(data) {
        if (data.length === 0) return '';
        
        const headers = Object.keys(data[0]);
        const csvRows = [headers.join(',')];
        
        for (const row of data) {
            const values = headers.map(header => {
                const value = row[header] || '';
                return `"${value.toString().replace(/"/g, '""')}"`;
            });
            csvRows.push(values.join(','));
        }
        
        return csvRows.join('\\n');
    }
    
    async takeScreenshot(name) {
        try {
            const screenshotPath = path.join(this.screenshotsDir, `${name}.png`);
            await this.page.screenshot({ 
                path: screenshotPath, 
                fullPage: true 
            });
        } catch (error) {
            console.warn(`⚠️ Failed to take screenshot ${name}:`, error.message);
        }
    }
    
    async getTextContent(element) {
        try {
            return await element.textContent() || '';
        } catch (error) {
            return '';
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    async run() {
        console.log('🎯 Starting UNGM African Business Opportunities Scraper for Topaza.net');
        
        try {
            // Initialize browser
            await this.initialize();
            
            // Login to UNGM
            await this.login();
            
            // Navigate to business opportunities
            await this.navigateToBusinessOpportunities();
            
            // Scrape all keywords
            const totalFound = await this.scrapeAllKeywords();
            
            // Save all results
            await this.saveResults();
            
            // Generate final report
            const summary = this.generateSummaryReport();
            
            console.log('\\n🎉 SCRAPING COMPLETED SUCCESSFULLY!');
            console.log('=' * 50);
            console.log(`📊 FINAL SUMMARY:`);
            console.log(`   • Total Opportunities Scraped: ${summary.totalOpportunitiesScraped}`);
            console.log(`   • African-Focused Opportunities: ${summary.africanOpportunities}`);
            console.log(`   • High Priority for Topaza.net: ${summary.highPriorityOpportunities}`);
            console.log(`   • Countries Represented: ${summary.countriesRepresented}`);
            console.log(`   • Urgent Deadlines (7 days): ${summary.urgentOpportunities}`);
            console.log(`   • Opportunities with Budget Info: ${summary.opportunitiesWithBudget}`);
            console.log(`   • Results saved to: ${this.outputDir}`);
            
            if (summary.topRecommendations.length > 0) {
                console.log('\\n🎯 TOP RECOMMENDATIONS FOR TOPAZA.NET:');
                summary.topRecommendations.forEach((rec, i) => {
                    console.log(`   ${i + 1}. [${rec.priority}] ${rec.recommendation}`);
                });
            }
            
        } catch (error) {
            console.error('❌ Scraping failed:', error.message);
            await this.takeScreenshot('error-final-failure');
            throw error;
        } finally {
            if (this.browser) {
                await this.browser.close();
                console.log('🔒 Browser closed');
            }
        }
    }
}

// Export for use
module.exports = UNGMAfricanOpportunitiesScraper;

// If running directly
if (require.main === module) {
    const scraper = new UNGMAfricanOpportunitiesScraper();
    scraper.run().catch(console.error);
}