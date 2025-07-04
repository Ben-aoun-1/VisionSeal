# 🚀 VisionSeal Supabase Setup Guide

Complete guide to set up Supabase backend for your African tender opportunity SaaS.

## 📋 **Step 1: Create Supabase Project**

1. **Go to [supabase.com](https://supabase.com) and sign up/login**
2. **Click "New Project"**
3. **Fill in project details:**
   - **Organization**: Create new or use existing
   - **Name**: `visionseal-african-tenders`
   - **Database Password**: Generate strong password (save it!)
   - **Region**: Choose closest to your users (e.g., EU West, US East)
   - **Pricing Plan**: Start with Free tier (500MB database, perfect for MVP)

4. **Wait 2-3 minutes for project to initialize**

## 📊 **Step 2: Set Up Database Schema**

1. **Go to your project dashboard**
2. **Navigate to "SQL Editor" in the sidebar**
3. **Copy the entire contents of `database/supabase_schema.sql`**
4. **Paste into SQL Editor and click "Run"**

This will create:
- ✅ All necessary tables (tenders, users, automation_sessions, etc.)
- ✅ Indexes for fast searching
- ✅ Row Level Security (RLS) policies
- ✅ Custom functions for search and analytics
- ✅ Sample data for testing

## 🔑 **Step 3: Get API Keys**

1. **Go to "Settings" → "API" in your Supabase dashboard**
2. **Copy these values:**
   - **Project URL**: `https://your-project-id.supabase.co`
   - **Anon Key**: `eyJhbGc...` (public key for client apps)
   - **Service Role Key**: `eyJhbGc...` (private key for server operations)

## ⚙️ **Step 4: Update Environment Variables**

Update your `.env` file with the Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📦 **Step 5: Install Python Dependencies**

```bash
pip install -r requirements_supabase.txt
```

## 🧪 **Step 6: Test the Connection**

Create and run this test script:

```python
# test_supabase_connection.py
import asyncio
import os
from src.core.database.supabase_client import supabase_manager

async def test_connection():
    print("🧪 Testing Supabase connection...")
    
    # Test basic connection
    health = await supabase_manager.health_check()
    print(f"✅ Connection: {'Working' if health else 'Failed'}")
    
    # Test inserting a sample tender
    sample_tender = {
        'title': 'Test Consulting Opportunity - Nigeria',
        'description': 'Sample tender for testing Supabase integration',
        'source': 'UNGM',
        'country': 'Nigeria',
        'organization': 'World Bank',
        'deadline': '2024-03-15',
        'url': 'https://example.com/tender/123',
        'reference': 'TEST-001',
        'status': 'ACTIVE',
        'relevance_score': 85.5,
        'publication_date': '2024-02-15',
        'notice_type': 'Request for Proposal'
    }
    
    result = await supabase_manager.insert_tender(sample_tender, use_service_key=True)
    if result:
        print(f"✅ Sample tender inserted: {result.get('id')}")
    else:
        print("❌ Failed to insert sample tender")
    
    # Test fetching recent tenders
    recent = await supabase_manager.get_recent_tenders(limit=5)
    print(f"✅ Recent tenders: {len(recent)} found")
    
    for tender in recent[:2]:
        print(f"   - {tender['title'][:50]}...")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run the test:
```bash
python test_supabase_connection.py
```

## 🎯 **Step 7: Configure Row Level Security (RLS)**

Your schema already includes RLS policies, but here's what they do:

### **Public Access (No Login Required):**
- ✅ Anyone can view tender opportunities
- ✅ Perfect for MVP - no login wall

### **User Access (When Logged In):**
- ✅ Users can save searches and favorites
- ✅ Users can view their own activity
- ✅ Ready for premium features

### **Automation Access:**
- ✅ Service key can insert new tenders
- ✅ Scraper automation works seamlessly

## 📱 **Step 8: Set Up Authentication (Optional)**

If you want user accounts:

1. **Go to "Authentication" → "Settings"**
2. **Configure providers:**
   - Email/Password (enabled by default)
   - Google, GitHub, etc. (optional)
3. **Set up email templates**
4. **Configure redirect URLs for your app**

## 🌐 **Step 9: API Endpoints Ready**

Supabase automatically creates REST API endpoints:

```bash
# Get all tenders
GET https://your-project-id.supabase.co/rest/v1/tenders

# Search tenders
POST https://your-project-id.supabase.co/rest/v1/rpc/search_tenders

# Get recent opportunities
GET https://your-project-id.supabase.co/rest/v1/recent_opportunities

# Headers needed:
apikey: your-anon-key
Authorization: Bearer your-anon-key
```

## 💰 **Step 10: Understand Pricing**

### **Free Tier (Perfect for MVP):**
- ✅ 500MB database storage
- ✅ 50MB file storage  
- ✅ 50,000 monthly active users
- ✅ 2GB bandwidth
- ✅ Community support

### **When to Upgrade:**
- **Pro ($25/month)**: 8GB database, 100GB bandwidth
- **Scale**: Custom pricing for enterprise

## 🚀 **Step 11: Next Steps**

1. **Run your scraper** - it will now save to Supabase
2. **Build a simple web dashboard** using the API
3. **Add real-time subscriptions** for live updates
4. **Implement user authentication** for premium features

## 🔧 **Troubleshooting**

### **Connection Issues:**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Test with curl
curl -H "apikey: your-anon-key" \
     "https://your-project-id.supabase.co/rest/v1/tenders?limit=1"
```

### **Permission Issues:**
- Ensure service key is set for automation
- Check RLS policies in Supabase dashboard
- Verify API keys are correct

### **Schema Issues:**
- Re-run the schema SQL if tables are missing
- Check "Database" → "Tables" in Supabase dashboard

## 🎉 **You're Done!**

Your VisionSeal project now has:
- ✅ **Professional database** (Supabase)
- ✅ **Real-time capabilities** 
- ✅ **Auto-generated APIs**
- ✅ **Scalable infrastructure**
- ✅ **User authentication ready**

**Next**: Build your web dashboard and start collecting subscribers!