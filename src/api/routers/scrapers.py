"""
Direct Scraper Endpoints
Simple, direct access to individual scrapers without automation manager complexity
"""
import os
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from core.auth.supabase_auth import get_current_user_optional
from core.logging.setup import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("scrapers")
router = APIRouter(prefix="/scrapers", tags=["scrapers"])

# Store running scraper tasks
running_scrapers: Dict[str, Dict[str, Any]] = {}

class ScraperStartRequest(BaseModel):
    max_pages: int = 10  # Increased from 5 to 10 pages (150 tenders)
    headless: bool = True
    save_to_supabase: bool = True

class ScraperResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    status: str

@router.post("/ungm/start", response_model=ScraperResponse)
async def start_ungm_scraper(
    request: ScraperStartRequest,
    background_tasks: BackgroundTasks
):
    """Start UNGM scraper directly"""
    try:
        import uuid
        session_id = f"ungm_{uuid.uuid4().hex[:12]}"
        
        # Get credentials from environment
        ungm_username = os.getenv("UNGM_USERNAME")
        ungm_password = os.getenv("UNGM_PASSWORD")
        
        if not ungm_username or not ungm_password:
            raise HTTPException(
                status_code=400, 
                detail="UNGM credentials not configured. Please set UNGM_USERNAME and UNGM_PASSWORD environment variables."
            )
        
        # Config for UNGM scraper
        config = {
            "max_pages": request.max_pages,
            "headless": request.headless,
            "timeout": 30,
            "save_to_supabase": request.save_to_supabase,
            "fetch_details": True,
            "credentials": {
                "username": ungm_username,
                "password": ungm_password
            }
        }
        
        # Store session info
        running_scrapers[session_id] = {
            "source": "ungm",
            "status": "starting",
            "config": config,
            "start_time": "now"
        }
        
        # Start scraper in background
        background_tasks.add_task(run_ungm_scraper_task, session_id, config)
        
        logger.info(f"Started UNGM scraper session: {session_id}")
        
        return ScraperResponse(
            success=True,
            message="UNGM scraper started successfully",
            session_id=session_id,
            status="running"
        )
        
    except Exception as e:
        logger.error(f"Failed to start UNGM scraper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tunipages/start", response_model=ScraperResponse)
async def start_tunipages_scraper(
    request: ScraperStartRequest,
    background_tasks: BackgroundTasks
):
    """Start TuniPages scraper directly"""
    try:
        import uuid
        session_id = f"tunipages_{uuid.uuid4().hex[:12]}"
        
        # Get credentials from environment
        tunipages_username = os.getenv("TUNIPAGES_USERNAME")
        tunipages_password = os.getenv("TUNIPAGES_PASSWORD")
        
        if not tunipages_username or not tunipages_password:
            raise HTTPException(
                status_code=400, 
                detail="TuniPages credentials not configured. Please set TUNIPAGES_USERNAME and TUNIPAGES_PASSWORD environment variables."
            )
        
        # Config for TuniPages scraper
        config = {
            "max_pages": request.max_pages,
            "headless": request.headless,
            "timeout": 30,
            "save_to_supabase": request.save_to_supabase,
            "fetch_details": True,
            "credentials": {
                "username": tunipages_username,
                "password": tunipages_password
            }
        }
        
        # Store session info
        running_scrapers[session_id] = {
            "source": "tunipages",
            "status": "starting",
            "config": config,
            "start_time": "now"
        }
        
        # Start scraper in background
        background_tasks.add_task(run_tunipages_scraper_task, session_id, config)
        
        logger.info(f"Started TuniPages scraper session: {session_id}")
        
        return ScraperResponse(
            success=True,
            message="TuniPages scraper started successfully",
            session_id=session_id,
            status="running"
        )
        
    except Exception as e:
        logger.error(f"Failed to start TuniPages scraper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}")
async def get_scraper_status(session_id: str):
    """Get status of a running scraper"""
    if session_id not in running_scrapers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return running_scrapers[session_id]

@router.get("/status")
async def get_all_scrapers_status():
    """Get status of all running scrapers"""
    return {"running_scrapers": running_scrapers}

@router.get("/credentials-check")
async def check_credentials():
    """Debug endpoint to check if credentials are loaded"""
    return {
        "ungm_username_set": bool(os.getenv("UNGM_USERNAME")),
        "ungm_password_set": bool(os.getenv("UNGM_PASSWORD")),
        "tunipages_username_set": bool(os.getenv("TUNIPAGES_USERNAME")),
        "tunipages_password_set": bool(os.getenv("TUNIPAGES_PASSWORD")),
        "ungm_username_preview": os.getenv("UNGM_USERNAME", "")[:3] + "***" if os.getenv("UNGM_USERNAME") else "NOT_SET"
    }

async def run_ungm_scraper_task(session_id: str, config: Dict[str, Any]):
    """Run UNGM scraper as background task"""
    try:
        running_scrapers[session_id]["status"] = "running"
        logger.info(f"Running UNGM scraper for session {session_id}")
        
        # Import and run the original async scraper
        from automation.scrapers.ungm_playwright_scraper import run_ungm_scraping
        
        result = await run_ungm_scraping(config)
        
        # Update session with results
        running_scrapers[session_id].update({
            "status": "completed",
            "result": result,
            "tenders_found": result.get("tenders_found", 0),
            "success": result.get("success", False)
        })
        
        logger.info(f"UNGM scraper completed for session {session_id}: {result.get('success', False)}")
        
    except Exception as e:
        logger.error(f"UNGM scraper failed for session {session_id}: {e}")
        running_scrapers[session_id].update({
            "status": "failed",
            "error": str(e),
            "success": False
        })

async def run_tunipages_scraper_task(session_id: str, config: Dict[str, Any]):
    """Run TuniPages scraper as background task"""
    try:
        running_scrapers[session_id]["status"] = "running"
        logger.info(f"Running TuniPages scraper for session {session_id}")
        
        # Import and run the original async scraper
        from automation.scrapers.tunipages_scraper import run_tunipages_scraping
        
        result = await run_tunipages_scraping(config)
        
        # Update session with results
        running_scrapers[session_id].update({
            "status": "completed",
            "result": result,
            "tenders_found": result.get("tenders_found", 0),
            "success": result.get("success", False)
        })
        
        logger.info(f"TuniPages scraper completed for session {session_id}: {result.get('success', False)}")
        
    except Exception as e:
        logger.error(f"TuniPages scraper failed for session {session_id}: {e}")
        running_scrapers[session_id].update({
            "status": "failed",
            "error": str(e),
            "success": False
        })