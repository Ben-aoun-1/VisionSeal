"""
Supabase client configuration for VisionSeal
Handles connection and operations with Supabase backend
"""
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
from postgrest.exceptions import APIError
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

from core.config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages Supabase database operations"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")
        
        # Create clients
        self.client: Client = create_client(self.url, self.key)
        
        # Service client for automation (bypasses RLS)
        if self.service_key:
            self.service_client: Client = create_client(self.url, self.service_key)
        else:
            logger.warning("SUPABASE_SERVICE_KEY not set - automation may have limited access")
            self.service_client = self.client
    
    def get_client(self, use_service_key: bool = False) -> Client:
        """Get appropriate Supabase client"""
        return self.service_client if use_service_key else self.client
    
    async def insert_tender(self, tender_data: Dict[str, Any], use_service_key: bool = True, max_retries: int = 3) -> Dict[str, Any]:
        """Insert a new tender opportunity with retry logic"""
        for attempt in range(max_retries):
            try:
                client = self.get_client(use_service_key)
                
                # Prepare data for insertion
                insert_data = {
                    'title': tender_data.get('title'),
                    'description': tender_data.get('description'),
                    'source': tender_data.get('source'),
                    'country': tender_data.get('country'),
                    'organization': tender_data.get('organization'),
                    'deadline': tender_data.get('deadline'),
                    'url': tender_data.get('url'),
                    'reference': tender_data.get('reference'),
                    'status': tender_data.get('status', 'ACTIVE'),
                    'relevance_score': tender_data.get('relevance_score', 0),
                    'publication_date': tender_data.get('publication_date'),
                    'notice_type': tender_data.get('notice_type'),
                    'estimated_budget': tender_data.get('estimated_budget'),
                    'currency': tender_data.get('currency'),
                    'contact_email': tender_data.get('contact_email'),
                    'document_links': tender_data.get('document_links', []),
                    'extracted_at': tender_data.get('extracted_at', datetime.utcnow().isoformat())
                }
                
                # Remove None values
                insert_data = {k: v for k, v in insert_data.items() if v is not None}
                
                response = client.table('tenders').insert(insert_data).execute()
                
                if response.data:
                    logger.info(f"✅ Inserted tender: {tender_data.get('title', 'Unknown')[:50]}...")
                    return response.data[0]
                else:
                    logger.error(f"❌ Failed to insert tender: {response}")
                    return {}
                    
            except APIError as e:
                if attempt < max_retries - 1 and "rate limit" in str(e).lower():
                    logger.warning(f"Rate limit hit, retrying in {2 ** attempt} seconds...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.error(f"❌ Supabase API error inserting tender: {str(e)}")
                return {}
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Unexpected error on attempt {attempt + 1}, retrying: {str(e)}")
                    await asyncio.sleep(1)
                    continue
                logger.error(f"❌ Unexpected error inserting tender: {str(e)}")
                return {}
    
    async def bulk_insert_tenders(self, tenders: List[Dict[str, Any]], use_service_key: bool = True, batch_size: int = 100, max_retries: int = 3) -> int:
        """Bulk insert multiple tenders with batching and retry logic"""
        if not tenders:
            return 0
        
        total_inserted = 0
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(tenders), batch_size):
            batch = tenders[i:i + batch_size]
            
            for attempt in range(max_retries):
                try:
                    client = self.get_client(use_service_key)
                    
                    # Prepare batch data for insertion
                    insert_data = []
                    for tender in batch:
                        data = {
                            'title': tender.get('title'),
                            'description': tender.get('description'),
                            'source': tender.get('source'),
                            'country': tender.get('country'),
                            'organization': tender.get('organization'),
                            'deadline': tender.get('deadline'),
                            'url': tender.get('url'),
                            'reference': tender.get('reference'),
                            'status': tender.get('status', 'ACTIVE'),
                            'relevance_score': tender.get('relevance_score', 0),
                            'publication_date': tender.get('publication_date'),
                            'notice_type': tender.get('notice_type'),
                            'estimated_budget': tender.get('estimated_budget'),
                            'currency': tender.get('currency'),
                            'contact_email': tender.get('contact_email'),
                            'document_links': tender.get('document_links', []),
                            'extracted_at': tender.get('extracted_at', datetime.utcnow().isoformat())
                        }
                        
                        # Remove None values
                        data = {k: v for k, v in data.items() if v is not None}
                        insert_data.append(data)
                    
                    response = client.table('tenders').insert(insert_data).execute()
                    
                    batch_count = len(response.data) if response.data else 0
                    total_inserted += batch_count
                    logger.info(f"✅ Batch {i//batch_size + 1} inserted {batch_count} tenders")
                    break
                    
                except APIError as e:
                    if attempt < max_retries - 1 and "rate limit" in str(e).lower():
                        logger.warning(f"Rate limit hit on batch {i//batch_size + 1}, retrying in {2 ** attempt} seconds...")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    logger.error(f"❌ Supabase API error in batch {i//batch_size + 1}: {str(e)}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Unexpected error on batch {i//batch_size + 1}, attempt {attempt + 1}: {str(e)}")
                        await asyncio.sleep(1)
                        continue
                    logger.error(f"❌ Unexpected error in batch {i//batch_size + 1}: {str(e)}")
                    break
        
        logger.info(f"✅ Bulk insert completed: {total_inserted} total tenders inserted")
        return total_inserted
    
    async def get_recent_tenders(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent tender opportunities"""
        try:
            client = self.get_client()
            
            response = client.table('tenders')\
                .select('*')\
                .eq('status', 'ACTIVE')\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return response.data if response.data else []
            
        except APIError as e:
            logger.error(f"❌ Error fetching recent tenders: {str(e)}")
            return []
    
    async def search_tenders(self, 
                           query: str = '', 
                           countries: List[str] = None,
                           sources: List[str] = None,
                           min_score: float = 0,
                           limit: int = 50,
                           offset: int = 0) -> List[Dict[str, Any]]:
        """Search tenders with filters"""
        try:
            client = self.get_client()
            
            # Use the custom search function
            response = client.rpc('search_tenders', {
                'search_query': query,
                'filter_countries': countries,
                'filter_sources': sources,
                'min_score': min_score,
                'limit_count': limit,
                'offset_count': offset
            }).execute()
            
            return response.data if response.data else []
            
        except APIError as e:
            logger.error(f"❌ Error searching tenders: {str(e)}")
            return []
    
    async def insert_automation_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert automation session record"""
        try:
            client = self.get_client(use_service_key=True)
            
            insert_data = {
                'session_id': session_data.get('session_id'),
                'source': session_data.get('source'),
                'status': session_data.get('status'),
                'tenders_found': session_data.get('tenders_found', 0),
                'tenders_processed': session_data.get('tenders_processed', 0),
                'pages_processed': session_data.get('pages_processed', 0),
                'start_time': session_data.get('start_time'),
                'end_time': session_data.get('end_time'),
                'error_message': session_data.get('error'),
                'metadata': session_data.get('metadata', {})
            }
            
            # Remove None values
            insert_data = {k: v for k, v in insert_data.items() if v is not None}
            
            response = client.table('automation_sessions').insert(insert_data).execute()
            
            if response.data:
                logger.info(f"✅ Logged automation session: {session_data.get('session_id')}")
                return response.data[0]
            else:
                logger.error(f"❌ Failed to log session: {response}")
                return {}
                
        except APIError as e:
            logger.error(f"❌ Error logging automation session: {str(e)}")
            return {}
    
    async def get_automation_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get automation statistics"""
        try:
            client = self.get_client()
            
            # Get recent automation sessions
            response = client.table('automation_sessions')\
                .select('*')\
                .gte('created_at', datetime.utcnow().date() - timedelta(days=days))\
                .order('created_at', desc=True)\
                .execute()
            
            sessions = response.data if response.data else []
            
            # Calculate stats
            stats = {
                'total_sessions': len(sessions),
                'successful_sessions': len([s for s in sessions if s['status'] == 'completed']),
                'total_tenders_found': sum(s.get('tenders_found', 0) for s in sessions),
                'total_tenders_processed': sum(s.get('tenders_processed', 0) for s in sessions),
                'sources': {}
            }
            
            # Group by source
            for session in sessions:
                source = session['source']
                if source not in stats['sources']:
                    stats['sources'][source] = {
                        'sessions': 0,
                        'tenders_found': 0,
                        'tenders_processed': 0
                    }
                
                stats['sources'][source]['sessions'] += 1
                stats['sources'][source]['tenders_found'] += session.get('tenders_found', 0)
                stats['sources'][source]['tenders_processed'] += session.get('tenders_processed', 0)
            
            return stats
            
        except APIError as e:
            logger.error(f"❌ Error getting automation stats: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Supabase connection is healthy with detailed status"""
        try:
            client = self.get_client()
            
            # Basic connectivity check
            start_time = time.time()
            response = client.table('tenders').select('id').limit(1).execute()
            response_time = time.time() - start_time
            
            # Check service key if available
            service_key_status = False
            if self.service_key:
                try:
                    service_client = self.get_client(use_service_key=True)
                    service_response = service_client.table('tenders').select('id').limit(1).execute()
                    service_key_status = True
                except Exception:
                    service_key_status = False
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "anon_key_working": True,
                "service_key_working": service_key_status,
                "url": self.url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Supabase health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "anon_key_working": False,
                "service_key_working": False,
                "url": self.url,
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics and configuration info"""
        return {
            "supabase_url": self.url,
            "has_service_key": bool(self.service_key),
            "anon_key_configured": bool(self.key),
            "clients_initialized": hasattr(self, 'client') and hasattr(self, 'service_client')
        }
    
    def reset_clients(self):
        """Reset Supabase clients (useful for connection issues)"""
        try:
            self.client = create_client(self.url, self.key)
            if self.service_key:
                self.service_client = create_client(self.url, self.service_key)
            else:
                self.service_client = self.client
            logger.info("Supabase clients reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset Supabase clients: {str(e)}")
            raise

# Global instance
supabase_manager = SupabaseManager()