"""
Database repositories for data access layer
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from models.tender import (
    Tender, TenderDocument, AutomationSession, AIProcessingJob,
    TenderCreate, TenderUpdate, TenderSource, TenderStatus
)
from core.logging.setup import get_logger

logger = get_logger("repositories")


class TenderRepository:
    """Repository for tender data operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, tender_data: TenderCreate) -> Tender:
        """Create a new tender"""
        tender = Tender(
            id=tender_data.id,
            title=tender_data.title,
            description=tender_data.description,
            source=tender_data.source.value,
            country=tender_data.country,
            organization=tender_data.organization,
            promoter=tender_data.promoter,
            published_date=tender_data.published_date,
            deadline=tender_data.deadline,
            status=tender_data.status.value,
            category=tender_data.category.value if tender_data.category else None,
            tender_type=tender_data.tender_type,
            url=tender_data.url,
            relevance_score=tender_data.relevance_score,
            raw_data=tender_data.raw_data
        )
        
        self.db.add(tender)
        self.db.commit()
        self.db.refresh(tender)
        
        logger.info(f"Created tender: {tender.id}")
        return tender
    
    def get_by_id(self, tender_id: str) -> Optional[Tender]:
        """Get tender by ID"""
        return self.db.query(Tender).filter(Tender.id == tender_id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        source: Optional[TenderSource] = None,
        status: Optional[TenderStatus] = None,
        country: Optional[str] = None
    ) -> List[Tender]:
        """Get all tenders with optional filtering"""
        query = self.db.query(Tender)
        
        if source:
            query = query.filter(Tender.source == source.value)
        if status:
            query = query.filter(Tender.status == status.value)
        if country:
            query = query.filter(Tender.country == country)
        
        return query.order_by(desc(Tender.created_at)).offset(skip).limit(limit).all()
    
    def search(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        source: Optional[TenderSource] = None
    ) -> List[Tender]:
        """Search tenders by title or description"""
        query = self.db.query(Tender).filter(
            or_(
                Tender.title.contains(search_term),
                Tender.description.contains(search_term),
                Tender.organization.contains(search_term)
            )
        )
        
        if source:
            query = query.filter(Tender.source == source.value)
        
        return query.order_by(desc(Tender.relevance_score)).offset(skip).limit(limit).all()
    
    def update(self, tender_id: str, tender_data: TenderUpdate) -> Optional[Tender]:
        """Update tender"""
        tender = self.get_by_id(tender_id)
        if not tender:
            return None
        
        update_data = tender_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(tender, field):
                if field in ['status', 'category'] and value:
                    setattr(tender, field, value.value)
                else:
                    setattr(tender, field, value)
        
        tender.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(tender)
        
        logger.info(f"Updated tender: {tender_id}")
        return tender
    
    def delete(self, tender_id: str) -> bool:
        """Delete tender"""
        tender = self.get_by_id(tender_id)
        if not tender:
            return False
        
        self.db.delete(tender)
        self.db.commit()
        
        logger.info(f"Deleted tender: {tender_id}")
        return True
    
    def get_by_source_and_date(
        self,
        source: TenderSource,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> List[Tender]:
        """Get tenders by source and date range"""
        query = self.db.query(Tender).filter(
            and_(
                Tender.source == source.value,
                Tender.created_at >= start_date
            )
        )
        
        if end_date:
            query = query.filter(Tender.created_at <= end_date)
        
        return query.order_by(desc(Tender.created_at)).all()
    
    def get_active_tenders(self, limit: int = 50) -> List[Tender]:
        """Get active tenders with upcoming deadlines"""
        now = datetime.now(timezone.utc)
        return self.db.query(Tender).filter(
            and_(
                Tender.status == TenderStatus.ACTIVE.value,
                Tender.deadline > now
            )
        ).order_by(asc(Tender.deadline)).limit(limit).all()
    
    def count(
        self,
        source: Optional[TenderSource] = None,
        status: Optional[TenderStatus] = None
    ) -> int:
        """Count tenders with optional filtering"""
        query = self.db.query(Tender)
        
        if source:
            query = query.filter(Tender.source == source.value)
        if status:
            query = query.filter(Tender.status == status.value)
        
        return query.count()


class AutomationSessionRepository:
    """Repository for automation session operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, session_id: str, source: TenderSource, **kwargs) -> AutomationSession:
        """Create automation session"""
        session = AutomationSession(
            id=session_id,
            source=source.value,
            **kwargs
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Created automation session: {session_id}")
        return session
    
    def get_by_id(self, session_id: str) -> Optional[AutomationSession]:
        """Get session by ID"""
        return self.db.query(AutomationSession).filter(
            AutomationSession.id == session_id
        ).first()
    
    def update_progress(
        self,
        session_id: str,
        current_page: int,
        tenders_found: int = None,
        tenders_processed: int = None
    ) -> Optional[AutomationSession]:
        """Update session progress"""
        session = self.get_by_id(session_id)
        if not session:
            return None
        
        session.current_page = current_page
        if tenders_found is not None:
            session.tenders_found = tenders_found
        if tenders_processed is not None:
            session.tenders_processed = tenders_processed
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def complete_session(
        self,
        session_id: str,
        status: str,
        output_file: Optional[str] = None,
        error_message: Optional[str] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> Optional[AutomationSession]:
        """Complete automation session"""
        session = self.get_by_id(session_id)
        if not session:
            return None
        
        session.status = status
        session.completed_at = datetime.now(timezone.utc)
        session.output_file = output_file
        session.error_message = error_message
        session.performance_metrics = performance_metrics
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Completed automation session: {session_id} with status: {status}")
        return session
    
    def get_recent_sessions(
        self,
        source: Optional[TenderSource] = None,
        limit: int = 10
    ) -> List[AutomationSession]:
        """Get recent automation sessions"""
        query = self.db.query(AutomationSession)
        
        if source:
            query = query.filter(AutomationSession.source == source.value)
        
        return query.order_by(desc(AutomationSession.started_at)).limit(limit).all()


class AIProcessingJobRepository:
    """Repository for AI processing job operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, job_id: str, job_type: str, input_data: Dict[str, Any], **kwargs) -> AIProcessingJob:
        """Create AI processing job"""
        job = AIProcessingJob(
            id=job_id,
            job_type=job_type,
            input_data=input_data,
            **kwargs
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(f"Created AI processing job: {job_id}")
        return job
    
    def get_by_id(self, job_id: str) -> Optional[AIProcessingJob]:
        """Get job by ID"""
        return self.db.query(AIProcessingJob).filter(
            AIProcessingJob.id == job_id
        ).first()
    
    def update_status(self, job_id: str, status: str) -> Optional[AIProcessingJob]:
        """Update job status"""
        job = self.get_by_id(job_id)
        if not job:
            return None
        
        job.status = status
        if status == "running":
            job.started_at = datetime.now(timezone.utc)
        elif status in ["completed", "failed"]:
            job.completed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def complete_job(
        self,
        job_id: str,
        status: str,
        result_data: Optional[Dict[str, Any]] = None,
        output_files: Optional[List[str]] = None,
        processing_time: Optional[float] = None,
        model_used: Optional[str] = None,
        token_usage: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[AIProcessingJob]:
        """Complete AI processing job"""
        job = self.get_by_id(job_id)
        if not job:
            return None
        
        job.status = status
        job.completed_at = datetime.now(timezone.utc)
        job.result_data = result_data
        job.output_files = output_files
        job.processing_time = processing_time
        job.model_used = model_used
        job.token_usage = token_usage
        job.error_message = error_message
        
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(f"Completed AI processing job: {job_id} with status: {status}")
        return job