#!/usr/bin/env python3
"""
Saved Tenders API Router - RESTful endpoints for managing user saved tenders
Allows users to save, unsave, and retrieve their saved tender opportunities
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from supabase import create_client, Client
from core.auth.supabase_auth import get_current_user

# Initialize router
router = APIRouter(prefix="/saved-tenders", tags=["saved-tenders"])

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

# Pydantic models for API
class SavedTenderBase(BaseModel):
    """Base saved tender model"""
    id: str
    user_id: str
    tender_id: str
    saved_at: datetime
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SavedTenderWithDetails(BaseModel):
    """Saved tender with full tender details"""
    saved_tender_id: str
    user_id: str
    tender_id: str
    saved_at: datetime
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Tender details
    title: str
    description: Optional[str] = None
    source: str
    country: str
    organization: str
    deadline: Optional[str] = None
    publication_date: Optional[str] = None
    url: str
    reference: Optional[str] = None
    status: str
    notice_type: Optional[str] = None
    relevance_score: float
    estimated_budget: Optional[str] = None
    currency: Optional[str] = None
    contact_email: Optional[str] = None
    tender_extracted_at: datetime
    tender_created_at: datetime
    tender_updated_at: datetime

class SavedTenderCreate(BaseModel):
    """Model for creating a saved tender"""
    tender_id: str = Field(..., description="ID of the tender to save")
    notes: Optional[str] = Field(None, description="Optional user notes about the tender")

class SavedTenderUpdate(BaseModel):
    """Model for updating a saved tender"""
    notes: Optional[str] = Field(None, description="User notes about the tender")

class SavedTenderResponse(BaseModel):
    """Response model for saved tender operations"""
    saved_tenders: List[SavedTenderWithDetails]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class SavedTenderStats(BaseModel):
    """Statistics about user's saved tenders"""
    total_saved: int
    saved_by_status: dict
    saved_by_source: dict
    recent_saves_count: int  # Last 7 days
    avg_relevance_score: float

# API Endpoints

@router.get("/health")
async def saved_tenders_health_check():
    """Health check for saved tenders API"""
    try:
        supabase = get_supabase_client()
        # Simple query to test connection
        response = supabase.table('saved_tenders').select('id').limit(1).execute()
        return {
            "status": "healthy",
            "service": "saved-tenders",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "saved-tenders", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/", response_model=SavedTenderResponse)
async def get_saved_tenders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in saved tender titles, descriptions, organizations"),
    source: Optional[str] = Query(None, description="Filter by source"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: Optional[str] = Query("saved_at", description="Sort by field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get user's saved tenders with filtering and pagination
    """
    try:
        user_id = current_user["user_id"]
        
        # Build query for saved tenders with details
        query = supabase.table('saved_tenders_detailed').select('*', count='exact').eq('user_id', user_id)
        
        # Apply filters
        if search:
            query = query.or_(f'title.ilike.%{search}%,description.ilike.%{search}%,organization.ilike.%{search}%')
        
        if source:
            query = query.eq('source', source)
            
        if status:
            query = query.eq('status', status)
        
        # Apply sorting
        try:
            if sort_order == "desc":
                query = query.order(sort_by, desc=True)
            else:
                query = query.order(sort_by)
        except:
            # Fallback to default sorting
            query = query.order('saved_at', desc=True)
        
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
        
        return SavedTenderResponse(
            saved_tenders=response.data,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching saved tenders: {str(e)}")

@router.post("/", response_model=SavedTenderBase)
async def save_tender(
    saved_tender: SavedTenderCreate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Save a tender for the current user
    """
    try:
        user_id = current_user["user_id"]
        
        # Check if tender exists
        tender_response = supabase.table('tenders').select('id').eq('id', saved_tender.tender_id).execute()
        if not tender_response.data:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        # Check if already saved
        existing_response = supabase.table('saved_tenders').select('id').eq('user_id', user_id).eq('tender_id', saved_tender.tender_id).execute()
        if existing_response.data:
            raise HTTPException(status_code=409, detail="Tender already saved")
        
        # Insert saved tender
        insert_data = {
            'user_id': user_id,
            'tender_id': saved_tender.tender_id,
            'notes': saved_tender.notes,
            'saved_at': datetime.now().isoformat(),
        }
        
        response = supabase.table('saved_tenders').insert(insert_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to save tender")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving tender: {str(e)}")

@router.delete("/{tender_id}")
async def unsave_tender(
    tender_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Remove a saved tender for the current user
    """
    try:
        user_id = current_user["user_id"]
        
        # Check if saved tender exists
        response = supabase.table('saved_tenders').select('id').eq('user_id', user_id).eq('tender_id', tender_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Saved tender not found")
        
        # Delete saved tender
        delete_response = supabase.table('saved_tenders').delete().eq('user_id', user_id).eq('tender_id', tender_id).execute()
        
        return {"message": "Tender unsaved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unsaving tender: {str(e)}")

@router.put("/{tender_id}", response_model=SavedTenderBase)
async def update_saved_tender(
    tender_id: str,
    update_data: SavedTenderUpdate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update notes for a saved tender
    """
    try:
        user_id = current_user["user_id"]
        
        # Check if saved tender exists
        response = supabase.table('saved_tenders').select('*').eq('user_id', user_id).eq('tender_id', tender_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Saved tender not found")
        
        # Update saved tender
        update_response = supabase.table('saved_tenders').update({
            'notes': update_data.notes
        }).eq('user_id', user_id).eq('tender_id', tender_id).execute()
        
        return update_response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating saved tender: {str(e)}")

@router.get("/check/{tender_id}")
async def check_tender_saved(
    tender_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Check if a tender is saved by the current user
    """
    try:
        user_id = current_user["user_id"]
        
        response = supabase.table('saved_tenders').select('id,saved_at,notes').eq('user_id', user_id).eq('tender_id', tender_id).execute()
        
        return {
            "is_saved": len(response.data) > 0,
            "saved_data": response.data[0] if response.data else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking saved tender: {str(e)}")

@router.get("/stats", response_model=SavedTenderStats)
async def get_saved_tender_stats(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get statistics about user's saved tenders
    """
    try:
        user_id = current_user["user_id"]
        
        # Get total saved count
        total_response = supabase.table('saved_tenders').select('*', count='exact').eq('user_id', user_id).execute()
        total_saved = total_response.count
        
        # Get saved tenders with details for analysis
        details_response = supabase.table('saved_tenders_detailed').select('*').eq('user_id', user_id).execute()
        saved_tenders = details_response.data
        
        # Calculate statistics
        saved_by_status = {}
        saved_by_source = {}
        total_relevance = 0
        recent_saves_count = 0
        
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        for tender in saved_tenders:
            # Status breakdown
            status = tender.get('status', 'UNKNOWN')
            saved_by_status[status] = saved_by_status.get(status, 0) + 1
            
            # Source breakdown
            source = tender.get('source', 'UNKNOWN')
            saved_by_source[source] = saved_by_source.get(source, 0) + 1
            
            # Relevance score
            relevance = tender.get('relevance_score', 0)
            total_relevance += relevance
            
            # Recent saves
            saved_at = datetime.fromisoformat(tender.get('saved_at', '').replace('Z', '+00:00'))
            if saved_at >= seven_days_ago:
                recent_saves_count += 1
        
        avg_relevance_score = total_relevance / len(saved_tenders) if saved_tenders else 0
        
        return SavedTenderStats(
            total_saved=total_saved,
            saved_by_status=saved_by_status,
            saved_by_source=saved_by_source,
            recent_saves_count=recent_saves_count,
            avg_relevance_score=avg_relevance_score
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching saved tender stats: {str(e)}")

@router.get("/export/csv")
async def export_saved_tenders_csv(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Export user's saved tenders to CSV
    """
    try:
        user_id = current_user["user_id"]
        
        # Get all saved tenders with details
        response = supabase.table('saved_tenders_detailed').select('*').eq('user_id', user_id).execute()
        
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        if response.data:
            headers = ['title', 'organization', 'country', 'source', 'deadline', 'relevance_score', 'status', 'url', 'saved_at', 'notes']
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
                    tender.get('url', ''),
                    tender.get('saved_at', ''),
                    tender.get('notes', '')
                ]
                writer.writerow(row)
        
        # Return CSV content
        from fastapi.responses import StreamingResponse
        
        output.seek(0)
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="saved_tenders.csv"'}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting saved tenders: {str(e)}")