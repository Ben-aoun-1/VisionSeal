# VisionSeal Usage Guide for Topaza.net

## 🎯 Overview
VisionSeal automates tender discovery across Africa for Topaza.net's consulting business. It scrapes UNGM and TuniPages for relevant opportunities and manages them through a sophisticated task system.

## 🛠️ Setup & Configuration

### Step 1: Environment Setup
```bash
# Create environment file
cat > .env << 'EOF'
# Database
DATABASE_URL=sqlite:///./data/topaza_tenders.db

# Scraper Credentials (REQUIRED for live scraping)
UNGM_USERNAME=your_ungm_username
UNGM_PASSWORD=your_ungm_password
TUNIPAGES_USERNAME=your_tunipages_username
TUNIPAGES_PASSWORD=your_tunipages_password

# Browser Settings
BROWSER_HEADLESS=true
AUTOMATION_MAX_PAGES=20
AUTOMATION_REQUEST_DELAY=3

# Security
SECRET_KEY=your-secure-secret-key-here

# Optional: OpenAI for AI processing
OPENAI_API_KEY=your_openai_key_here
EOF
```

### Step 2: Install Dependencies
```bash
# Install required packages
pip install selenium webdriver-manager
# or
pip install -r requirements.txt  # if you have a requirements file
```

### Step 3: Configure for African Markets
```bash
# View current profiles
./config-cli profiles list

# Use the African-focused profile
./config-cli profiles show topaza_africa
```

## 🎮 Basic Operations

### Starting Automation Sessions

#### Option 1: Command Line Interface
```bash
# Start UNGM scraping with African focus
./automation-cli start ungm --max-pages 15 --headless

# Start TuniPages scraping
./automation-cli start tunipages --max-pages 10 --headless

# Start both scrapers simultaneously
./automation-cli start all --max-pages 20
```

#### Option 2: Monitor Progress
```bash
# List all running sessions
./automation-cli list

# Monitor a specific session
./automation-cli monitor task_abc123def456

# Check system metrics
./automation-cli metrics
```

#### Option 3: Python API
```python
from automation.task_manager import automation_manager

# Start scraping with African profile
task_id = automation_manager.schedule_scraping_session(
    source='ungm',
    profile='topaza_africa',
    config={'max_pages': 20}
)

# Check status
status = automation_manager.get_session_status(task_id)
print(f"Status: {status['status']}")
```

## 🌍 African Market Configuration

### View African Coverage
```bash
# See all African countries in scope
./config-cli merged ungm --profile topaza_africa | grep -A 50 target_countries

# Check priority countries
./config-cli profiles show topaza_africa
```

### Customize for Specific African Markets
```bash
# Create custom profile for West Africa focus
cat > west_africa_settings.json << 'EOF'
{
  "max_pages": 25,
  "priority_countries": [
    "Nigeria", "Ghana", "Senegal", "Mali", "Burkina Faso",
    "Niger", "Guinea", "Sierra Leone", "Liberia", "Ivory Coast"
  ],
  "priority_sectors": [
    "management consulting", "business development",
    "digital transformation", "capacity building"
  ],
  "min_relevance_score": 35.0,
  "geographic_focus": "West Africa"
}
EOF

# Create the profile
./config-cli profiles create "west_africa_focus" "Specialized West African markets" --settings-file west_africa_settings.json
```

## 📊 Monitoring & Results

### Real-time Monitoring
```bash
# Dashboard view of all sessions
./automation-cli list

# Example output:
# Task ID          Source    Status     Tenders  Pages  Created
# task_abc123      ungm      running    15/12    8      2025-06-28
# task_def456      tunipages completed  23/23    10     2025-06-28
```

### Database Access
```python
from core.database.connection import db_manager
from core.database.repositories import TenderRepository

# Access discovered tenders
with db_manager.session_scope() as session:
    tender_repo = TenderRepository(session)
    
    # Get recent African opportunities
    african_tenders = tender_repo.get_all(
        country="Nigeria",  # or any African country
        limit=20
    )
    
    # Search for consulting opportunities
    consulting_tenders = tender_repo.search(
        search_term="consulting",
        limit=50
    )
    
    for tender in consulting_tenders:
        print(f"{tender.title} - {tender.country} - Score: {tender.relevance_score}")
```

## 🎯 Optimizing for Topaza.net Business

### 1. Focus on High-Value Opportunities
```python
# Get high-relevance African opportunities
high_value = tender_repo.get_by_relevance_above(70.0)

# Filter by Topaza's core services
consulting_keywords = ["management consulting", "business development", "strategy", "training"]
```

### 2. Geographic Prioritization
```bash
# Priority order for Topaza.net:
# 1. Major economies: Nigeria, South Africa, Kenya, Ghana, Egypt
# 2. Francophone Africa: Morocco, Tunisia, Algeria, Senegal, Mali
# 3. East Africa: Ethiopia, Tanzania, Uganda, Rwanda
# 4. Other African markets
```

### 3. Deadline Management
```python
# Get urgent opportunities (deadline < 15 days)
urgent_tenders = [t for t in tenders if t.days_until_deadline and t.days_until_deadline <= 15]

# Sort by relevance and deadline
urgent_tenders.sort(key=lambda x: (x.relevance_score, -x.days_until_deadline), reverse=True)
```

## 🔧 Advanced Configuration

### Custom Relevance Scoring
```json
// In automation.json, customize scoring weights
{
  "relevance_weights": {
    "african_country_bonus": 40,
    "major_economy_bonus": 10,
    "topaza_services_bonus": 30,
    "government_client_bonus": 25,
    "deadline_urgency_bonus": 15
  }
}
```

### Performance Tuning
```bash
# For high-volume operations
./config-cli automation update ungm production_settings.json

# production_settings.json:
{
  "max_pages": 50,
  "request_delay": 2,
  "max_workers": 6,
  "timeout": 45,
  "batch_size": 100
}
```

## 📈 Business Intelligence

### Daily Operations Workflow
```bash
# 1. Morning: Start daily scraping
./automation-cli start all --max-pages 20

# 2. Check progress throughout day
./automation-cli list

# 3. End of day: Review results
./automation-cli metrics
python3 generate_daily_report.py  # Custom script you can create
```

### Weekly Analysis
```python
# Custom analysis script
from datetime import datetime, timedelta
from collections import Counter

# Analyze trends by country
country_trends = Counter([t.country for t in recent_tenders])
print("Top African markets this week:")
for country, count in country_trends.most_common(10):
    print(f"  {country}: {count} opportunities")

# Analyze by sector
sector_trends = Counter([t.category for t in recent_tenders])
print("Top sectors this week:")
for sector, count in sector_trends.most_common(5):
    print(f"  {sector}: {count} opportunities")
```

## 🚨 Troubleshooting

### Common Issues
```bash
# 1. Selenium not found
pip install selenium webdriver-manager

# 2. Credentials not working
# Check .env file and verify UNGM/TuniPages credentials

# 3. Database issues
# Reset database:
rm data/topaza_tenders.db
python3 -c "from core.database.connection import db_manager; db_manager.create_tables()"

# 4. Check logs
tail -f logs/automation.log
```

### Health Checks
```bash
# System health
./automation-cli metrics

# Configuration validation
python3 test_african_focus.py

# Full system test
python3 run_all_tests.py
```

## 🎯 Success Metrics for Topaza.net

### Daily KPIs
- **New African opportunities discovered:** Target 50+ per day
- **High-relevance opportunities:** Target 20+ with score >70
- **Geographic coverage:** Opportunities from 10+ African countries
- **Response time:** Average processing time <2 hours

### Weekly Goals
- **Pipeline growth:** 200+ new qualified opportunities
- **Market coverage:** Active opportunities in top 15 African economies
- **Conversion tracking:** Monitor which opportunities become proposals

## 🚀 Next Steps

1. **Set up credentials** in `.env` file
2. **Run initial test** with limited pages
3. **Monitor first session** to validate setup
4. **Scale up** to full production volumes
5. **Integrate** with Topaza.net's business processes

---

**Ready to discover African business opportunities for Topaza.net!** 🌍✨