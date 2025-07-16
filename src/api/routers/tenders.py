#!/usr/bin/env python3
"""
Tenders API Router - RESTful endpoints for React frontend
Provides comprehensive tender data access with filtering, search, and pagination
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize router (prefix will be added by main.py)
router = APIRouter(prefix="/tenders", tags=["tenders"])

# Handle both /tenders and /tenders/ routes

# Use centralized supabase manager
def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    try:
        from core.database.supabase_client import supabase_manager
        return supabase_manager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Database connection failed: {str(e)}"
        )

# Pydantic models for API responses
class TenderBase(BaseModel):
    """Base tender model"""
    id: str
    title: str
    description: Optional[str] = None
    source: str
    country: str
    organization: str
    deadline: Optional[date] = None
    publication_date: Optional[date] = None
    url: str
    reference: Optional[str] = None
    status: str
    notice_type: Optional[str] = None
    relevance_score: float
    estimated_budget: Optional[str] = None
    currency: Optional[str] = None
    contact_email: Optional[str] = None
    extracted_at: datetime
    created_at: datetime
    updated_at: datetime

class TenderListResponse(BaseModel):
    """Response model for tender list"""
    tenders: List[TenderBase]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class TenderFilters(BaseModel):
    """Model for tender filters"""
    sources: List[str] = Field(default_factory=list)
    countries: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    statuses: List[str] = Field(default_factory=list)
    min_relevance_score: Optional[float] = None
    max_relevance_score: Optional[float] = None
    deadline_from: Optional[date] = None
    deadline_to: Optional[date] = None
    search: Optional[str] = None

class TenderStats(BaseModel):
    """Model for tender statistics"""
    total_tenders: int
    active_tenders: int
    expired_tenders: int
    sources_breakdown: Dict[str, int]
    countries_breakdown: Dict[str, int]
    organizations_breakdown: Dict[str, int]
    avg_relevance_score: float
    recent_tenders_count: int  # Last 7 days

class FilterOptions(BaseModel):
    """Model for filter options"""
    sources: List[str]
    countries: List[str]
    organizations: List[str]
    statuses: List[str]
    relevance_score_range: Dict[str, float]
    date_range: Dict[str, Optional[date]]

# API Endpoints

@router.get("/health")
async def tenders_health_check():
    """Health check for tenders API"""
    try:
        # Test database connection
        supabase = get_supabase_client()
        # Simple query to test connection
        response = supabase.table('tenders').select('id').limit(1).execute()
        return {
            "status": "healthy",
            "service": "tenders",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "tenders", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/", response_model=TenderListResponse)
@router.get("", response_model=TenderListResponse)  # Handle both /tenders/ and /tenders
async def get_tenders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title, description, organization"),
    source: Optional[str] = Query(None, description="Filter by source (UNGM, TUNIPAGES, MANUAL)"),
    country: Optional[str] = Query(None, description="Filter by country"),
    organization: Optional[str] = Query(None, description="Filter by organization"),
    status: Optional[str] = Query("ACTIVE", description="Filter by status"),
    min_relevance: Optional[float] = Query(None, ge=0, le=100, description="Minimum relevance score"),
    max_relevance: Optional[float] = Query(None, ge=0, le=100, description="Maximum relevance score"),
    deadline_from: Optional[date] = Query(None, description="Deadline from date (YYYY-MM-DD)"),
    deadline_to: Optional[date] = Query(None, description="Deadline to date (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get paginated list of tenders with filtering and search
    """
    try:
        # Build query step by step to avoid chaining issues
        query = supabase.table('tenders').select('*', count='exact')
        
        # Apply filters
        if status:
            query = query.eq('status', status)
        if source:
            query = query.eq('source', source)
        if country:
            query = query.ilike('country', f'%{country}%')
        if organization:
            query = query.ilike('organization', f'%{organization}%')
        if min_relevance is not None:
            query = query.gte('relevance_score', min_relevance)
        if max_relevance is not None:
            query = query.lte('relevance_score', max_relevance)
        if deadline_from:
            query = query.gte('deadline', deadline_from.isoformat())
        if deadline_to:
            query = query.lte('deadline', deadline_to.isoformat())
        
        # Apply search (simplified approach)
        if search:
            # Use simple ilike search instead of full-text search
            query = query.or_(f'title.ilike.%{search}%,description.ilike.%{search}%,organization.ilike.%{search}%')
        
        # Apply sorting - use simpler approach
        try:
            if sort_order == "desc":
                query = query.order(sort_by, desc=True)
            else:
                query = query.order(sort_by)
        except:
            # Fallback to default sorting
            query = query.order('created_at', desc=True)
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)
        
        # Execute query
        response = query.execute()
        
        # Calculate pagination info
        total = response.count
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return TenderListResponse(
            tenders=response.data,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tenders: {str(e)}")

@router.get("/{tender_id}", response_model=TenderBase)
async def get_tender(
    tender_id: str,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a specific tender by ID
    """
    try:
        response = supabase.table('tenders').select('*').eq('id', tender_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        return response.data[0]
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error fetching tender: {str(e)}")

@router.get("/stats/summary", response_model=TenderStats)
async def get_tender_stats(
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get tender statistics and summary
    """
    try:
        # Get total counts
        total_response = supabase.table('tenders').select('*', count='exact').execute()
        total_tenders = total_response.count
        
        # Get active tenders
        active_response = supabase.table('tenders').select('*', count='exact').eq('status', 'ACTIVE').execute()
        active_tenders = active_response.count
        
        # Get expired tenders
        expired_response = supabase.table('tenders').select('*', count='exact').eq('status', 'EXPIRED').execute()
        expired_tenders = expired_response.count
        
        # Get sources breakdown
        sources_response = supabase.rpc('get_sources_breakdown').execute()
        sources_breakdown = {item['source']: item['count'] for item in sources_response.data}
        
        # Get countries breakdown (top 10)
        countries_response = supabase.rpc('get_countries_breakdown').limit(10).execute()
        countries_breakdown = {item['country']: item['count'] for item in countries_response.data}
        
        # Get organizations breakdown (top 10)
        orgs_response = supabase.rpc('get_organizations_breakdown').limit(10).execute()
        organizations_breakdown = {item['organization']: item['count'] for item in orgs_response.data}
        
        # Get average relevance score
        avg_response = supabase.rpc('get_avg_relevance_score').execute()
        avg_relevance_score = avg_response.data[0]['avg_score'] if avg_response.data else 0
        
        # Get recent tenders count (last 7 days)
        recent_response = supabase.table('tenders').select('*', count='exact').gte('created_at', (datetime.now() - timedelta(days=7)).isoformat()).execute()
        recent_tenders_count = recent_response.count
        
        return TenderStats(
            total_tenders=total_tenders,
            active_tenders=active_tenders,
            expired_tenders=expired_tenders,
            sources_breakdown=sources_breakdown,
            countries_breakdown=countries_breakdown,
            organizations_breakdown=organizations_breakdown,
            avg_relevance_score=avg_relevance_score,
            recent_tenders_count=recent_tenders_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@router.get("/filters/options", response_model=FilterOptions)
async def get_filter_options(
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get available filter options for the frontend
    """
    try:
        # Get unique sources
        sources_response = supabase.table('tenders').select('source').execute()
        sources = list(set(item['source'] for item in sources_response.data))
        
        # Get unique countries (top 20)
        countries_response = supabase.rpc('get_countries_breakdown').limit(20).execute()
        countries = [item['country'] for item in countries_response.data]
        
        # Get unique organizations (top 30)
        orgs_response = supabase.rpc('get_organizations_breakdown').limit(30).execute()
        organizations = [item['organization'] for item in orgs_response.data]
        
        # Get unique statuses
        statuses_response = supabase.table('tenders').select('status').execute()
        statuses = list(set(item['status'] for item in statuses_response.data))
        
        # Get relevance score range (simplified approach)
        try:
            min_score_response = supabase.table('tenders').select('relevance_score').order('relevance_score').limit(1).execute()
            max_score_response = supabase.table('tenders').select('relevance_score').order('relevance_score', desc=True).limit(1).execute()
            min_score = min_score_response.data[0]['relevance_score'] if min_score_response.data else 0
            max_score = max_score_response.data[0]['relevance_score'] if max_score_response.data else 100
        except:
            # Fallback values
            min_score = 0
            max_score = 100
        
        # Get date range (simplified approach)
        try:
            min_date_response = supabase.table('tenders').select('deadline').order('deadline').limit(1).execute()
            max_date_response = supabase.table('tenders').select('deadline').order('deadline', desc=True).limit(1).execute()
            min_date = min_date_response.data[0]['deadline'] if min_date_response.data else None
            max_date = max_date_response.data[0]['deadline'] if max_date_response.data else None
        except:
            # Fallback values
            min_date = None
            max_date = None
        
        return FilterOptions(
            sources=sources,
            countries=countries,
            organizations=organizations,
            statuses=statuses,
            relevance_score_range={"min": min_score, "max": max_score},
            date_range={"min": min_date, "max": max_date}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filter options: {str(e)}")

@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get search suggestions for autocomplete
    """
    try:
        # Search in titles and organizations
        title_response = supabase.table('tenders').select('title').ilike('title', f'%{q}%').limit(limit//2).execute()
        org_response = supabase.table('tenders').select('organization').ilike('organization', f'%{q}%').limit(limit//2).execute()
        
        suggestions = []
        
        # Add title suggestions
        for item in title_response.data:
            suggestions.append({
                "type": "title",
                "value": item['title'],
                "category": "Tender Title"
            })
        
        # Add organization suggestions
        for item in org_response.data:
            suggestions.append({
                "type": "organization", 
                "value": item['organization'],
                "category": "Organization"
            })
        
        # Remove duplicates and limit
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion['value'] not in seen:
                seen.add(suggestion['value'])
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= limit:
                    break
        
        return {"suggestions": unique_suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching suggestions: {str(e)}")

@router.get("/export/csv")
async def export_tenders_csv(
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    status: Optional[str] = Query("ACTIVE"),
    min_relevance: Optional[float] = Query(None),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Export filtered tenders to CSV
    """
    try:
        # Build query (similar to get_tenders but without pagination)
        query = supabase.table('tenders').select('*')
        
        # Apply same filters as get_tenders
        if status:
            query = query.eq('status', status)
        if source:
            query = query.eq('source', source)
        if country:
            query = query.ilike('country', f'%{country}%')
        if min_relevance is not None:
            query = query.gte('relevance_score', min_relevance)
        if search:
            query = query.text_search('search_vector', search)
        
        # Limit to prevent large exports
        query = query.limit(1000)
        
        response = query.execute()
        
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        if response.data:
            headers = ['title', 'organization', 'country', 'source', 'deadline', 'relevance_score', 'status', 'url']
            writer.writerow(headers)
            
            # Write data
            for tender in response.data:
                row = [
                    tender.get('title', ''),
                    tender.get('organization', ''),
                    tender.get('country', ''),
                    tender.get('source', ''),
                    tender.get('deadline', ''),
                    tender.get('relevance_score', ''),
                    tender.get('status', ''),
                    tender.get('url', '')
                ]
                writer.writerow(row)
        
        # Return CSV content
        from fastapi.responses import StreamingResponse
        
        output.seek(0)
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="tenders.csv"'}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")