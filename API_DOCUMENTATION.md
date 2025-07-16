# VisionSeal API Documentation

## 🚀 **Overview**

RESTful API for VisionSeal tender management system, designed specifically for React frontend integration.

## 📡 **Base URL**

```
http://localhost:8080
```

## 🔧 **Quick Start**

### **Start the API Server**
```bash
python3 main.py
```

### **API Documentation**
- **Interactive Docs**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **Health Check**: http://localhost:8080/health

## 📋 **Endpoints**

### **1. Health & Info**

#### `GET /health`
Health check endpoint
```json
{
  "status": "healthy",
  "service": "VisionSeal API",
  "version": "1.0.0"
}
```

#### `GET /`
Root endpoint with API information
```json
{
  "message": "VisionSeal API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "tenders": "/api/v1/tenders",
    "automation": "/api/v1/automation",
    "auth": "/api/v1/auth"
  }
}
```

### **2. Tenders API**

#### `GET /api/v1/tenders`
Get paginated list of tenders with filtering and search

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `search` (string): Search in title, description, organization
- `source` (string): Filter by source (UNGM, TUNIPAGES, MANUAL)
- `country` (string): Filter by country
- `organization` (string): Filter by organization
- `status` (string): Filter by status (default: ACTIVE)
- `min_relevance` (float): Minimum relevance score (0-100)
- `max_relevance` (float): Maximum relevance score (0-100)
- `deadline_from` (date): Deadline from date (YYYY-MM-DD)
- `deadline_to` (date): Deadline to date (YYYY-MM-DD)
- `sort_by` (string): Sort by field (default: created_at)
- `sort_order` (string): Sort order (asc/desc, default: desc)

**Response:**
```json
{
  "tenders": [
    {
      "id": "uuid",
      "title": "Tender Title",
      "description": "Tender description",
      "source": "UNGM",
      "country": "Kenya",
      "organization": "UNDP",
      "deadline": "2024-12-31",
      "publication_date": "2024-01-01",
      "url": "https://example.com/tender",
      "reference": "REF-001",
      "status": "ACTIVE",
      "notice_type": "Request for Proposal",
      "relevance_score": 85.5,
      "estimated_budget": "$100,000",
      "currency": "USD",
      "contact_email": "contact@example.com",
      "extracted_at": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1500,
  "page": 1,
  "per_page": 20,
  "total_pages": 75,
  "has_next": true,
  "has_prev": false
}
```

#### `GET /api/v1/tenders/{tender_id}`
Get a specific tender by ID

**Response:**
```json
{
  "id": "uuid",
  "title": "Tender Title",
  "description": "Detailed tender description",
  "source": "UNGM",
  "country": "Kenya",
  "organization": "UNDP",
  "deadline": "2024-12-31",
  "publication_date": "2024-01-01",
  "url": "https://example.com/tender",
  "reference": "REF-001",
  "status": "ACTIVE",
  "notice_type": "Request for Proposal",
  "relevance_score": 85.5,
  "estimated_budget": "$100,000",
  "currency": "USD",
  "contact_email": "contact@example.com",
  "extracted_at": "2024-01-01T10:00:00Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

#### `GET /api/v1/tenders/stats/summary`
Get tender statistics and summary

**Response:**
```json
{
  "total_tenders": 1500,
  "active_tenders": 1200,
  "expired_tenders": 300,
  "sources_breakdown": {
    "UNGM": 800,
    "TUNIPAGES": 600,
    "MANUAL": 100
  },
  "countries_breakdown": {
    "Kenya": 200,
    "Nigeria": 180,
    "South Africa": 150
  },
  "organizations_breakdown": {
    "UNDP": 150,
    "World Bank": 120,
    "UNICEF": 100
  },
  "avg_relevance_score": 67.5,
  "recent_tenders_count": 45
}
```

#### `GET /api/v1/tenders/filters/options`
Get available filter options for the frontend

**Response:**
```json
{
  "sources": ["UNGM", "TUNIPAGES", "MANUAL"],
  "countries": ["Kenya", "Nigeria", "South Africa", "Tunisia"],
  "organizations": ["UNDP", "World Bank", "UNICEF"],
  "statuses": ["ACTIVE", "EXPIRED", "CANCELLED", "AWARDED"],
  "relevance_score_range": {
    "min": 0,
    "max": 100
  },
  "date_range": {
    "min": "2024-01-01",
    "max": "2024-12-31"
  }
}
```

#### `GET /api/v1/tenders/search/suggestions`
Get search suggestions for autocomplete

**Query Parameters:**
- `q` (string): Search query (min 2 characters)
- `limit` (int): Maximum suggestions (default: 10, max: 50)

**Response:**
```json
{
  "suggestions": [
    {
      "type": "title",
      "value": "Technical Assistance for Healthcare",
      "category": "Tender Title"
    },
    {
      "type": "organization",
      "value": "UNDP Kenya",
      "category": "Organization"
    }
  ]
}
```

#### `GET /api/v1/tenders/export/csv`
Export filtered tenders to CSV

**Query Parameters:** (Same as GET /api/v1/tenders)

**Response:** CSV file download

## 🔧 **React Frontend Integration**

### **Installation**
```bash
npm install axios
```

### **API Client Setup**
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8080',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export default api;
```

### **Example Usage**

#### **Get Tenders with Filters**
```javascript
const fetchTenders = async (filters = {}) => {
  try {
    const response = await api.get('/api/v1/tenders', {
      params: {
        page: filters.page || 1,
        per_page: filters.perPage || 20,
        search: filters.search,
        source: filters.source,
        country: filters.country,
        min_relevance: filters.minRelevance,
        status: filters.status || 'ACTIVE'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching tenders:', error);
    throw error;
  }
};
```

#### **Get Tender Statistics**
```javascript
const fetchStats = async () => {
  try {
    const response = await api.get('/api/v1/tenders/stats/summary');
    return response.data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw error;
  }
};
```

#### **Search Suggestions**
```javascript
const fetchSuggestions = async (query) => {
  try {
    const response = await api.get('/api/v1/tenders/search/suggestions', {
      params: { q: query, limit: 10 }
    });
    return response.data.suggestions;
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    return [];
  }
};
```

## 🛡️ **Security & CORS**

The API is configured with CORS support for React development:

**Allowed Origins:**
- `http://localhost:3000` (React dev server)
- `http://localhost:3001` (Alternative React port)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

**Allowed Methods:**
- `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

**Allowed Headers:**
- All headers (`*`)

## 📊 **Response Format**

All API responses follow consistent format:

**Success Response:**
```json
{
  "data": { ... },
  "status": "success"
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## 🔍 **Search Capabilities**

The API supports powerful search features:

1. **Full-text search** across title, description, organization, and country
2. **Filtering** by source, country, organization, status, relevance score, and dates
3. **Sorting** by any field with ascending/descending order
4. **Pagination** with configurable page size
5. **Search suggestions** for autocomplete functionality

## 📈 **Performance**

- **Database optimization**: Indexes on all searchable fields
- **Pagination**: Efficient offset-based pagination
- **Compression**: GZip compression for large responses
- **Caching**: Optimized database queries with proper indexing

## 🎯 **Frontend Features Supported**

The API is designed to support these React frontend features:

- ✅ **Tender listing** with infinite scroll/pagination
- ✅ **Advanced filtering** with multiple criteria
- ✅ **Real-time search** with suggestions
- ✅ **Tender details** modal/page
- ✅ **Statistics dashboard** with charts
- ✅ **Export functionality** (CSV)
- ✅ **Responsive design** support
- ✅ **Performance optimization** with efficient queries

## 🚀 **Getting Started**

1. **Start the API server**:
   ```bash
   python3 main.py
   ```

2. **Test the API**:
   ```bash
   python3 test_api.py
   ```

3. **Build your React frontend** using the endpoints above

Your backend is now ready for React frontend integration! 🎉