"""
Database connection and session management
"""
import os
import time
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError

from core.config.settings import settings
from core.logging.setup import get_logger
from models.tender import Base

logger = get_logger("database")


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
        
        try:
            # Create engine based on database URL
            if settings.database.url.startswith("sqlite"):
                # SQLite configuration
                self.engine = create_engine(
                    settings.database.url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=settings.database.echo_queries
                )
                
                # Enable foreign key constraints for SQLite
                @event.listens_for(Engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
                    
            else:
                # PostgreSQL or other databases with enhanced connection pooling
                self.engine = create_engine(
                    settings.database.url,
                    pool_size=settings.database.pool_size,
                    max_overflow=settings.database.max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    pool_timeout=30,
                    echo=settings.database.echo_queries,
                    echo_pool=False,  # Set to True for pool debugging
                    future=True  # Enable SQLAlchemy 2.0 style
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            self.create_tables()
            
            self._initialized = True
            logger.info(
                "Database initialized successfully",
                extra={
                    "database_url": settings.database.url.split("://")[0] + "://***",
                    "echo_queries": settings.database.echo_queries
                }
            )
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self._initialized:
            self.initialize()
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self, max_retries: int = 3) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations with retry logic"""
        session = None
        for attempt in range(max_retries):
            try:
                session = self.get_session()
                yield session
                session.commit()
                break
            except (DisconnectionError, TimeoutError) as e:
                if session:
                    session.rollback()
                    session.close()
                    session = None
                
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database connection error on attempt {attempt + 1}, retrying...",
                        extra={"error": str(e), "attempt": attempt + 1}
                    )
                    # Exponential backoff: 0.5, 1, 2 seconds
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
                    raise
            except SQLAlchemyError as e:
                if session:
                    session.rollback()
                logger.error(f"Database operation failed: {str(e)}")
                raise
            except Exception as e:
                if session:
                    session.rollback()
                logger.error(f"Unexpected database error: {str(e)}")
                raise
            finally:
                if session:
                    session.close()
    
    def execute_query(self, query: str, params: dict = None, max_retries: int = 3):
        """Execute a raw SQL query and return results with retry logic"""
        for attempt in range(max_retries):
            try:
                with self.session_scope(max_retries=1) as session:
                    result = session.execute(text(query), params or {})
                    # Convert result to list of dicts
                    if result.returns_rows:
                        columns = result.keys()
                        return [dict(zip(columns, row)) for row in result.fetchall()]
                    return result.rowcount
                    
            except (DisconnectionError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Query execution connection error on attempt {attempt + 1}, retrying...",
                        extra={"query": query[:100], "error": str(e), "attempt": attempt + 1}
                    )
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Query execution failed after {max_retries} attempts: {str(e)}")
                    return []
            except SQLAlchemyError as e:
                logger.error(f"Query execution failed: {str(e)}", extra={"query": query[:100]})
                return []
            except Exception as e:
                logger.error(f"Unexpected query execution error: {str(e)}", extra={"query": query[:100]})
                return []
    
    def health_check(self) -> bool:
        """Check database connectivity with comprehensive checks"""
        try:
            with self.session_scope(max_retries=1) as session:
                # Basic connectivity check
                session.execute(text("SELECT 1"))
                
                # Check if we can access tables
                if not settings.database.url.startswith("sqlite"):
                    session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tenders'"))
                
            logger.info("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information for monitoring"""
        if not self.engine:
            return {"status": "not_initialized"}
        
        try:
            pool = self.engine.pool
            return {
                "status": "connected",
                "pool_size": getattr(pool, 'size', lambda: 'N/A')(),
                "checked_in": getattr(pool, 'checkedin', lambda: 'N/A')(),
                "checked_out": getattr(pool, 'checkedout', lambda: 'N/A')(),
                "overflow": getattr(pool, 'overflow', lambda: 'N/A')(),
                "invalid": getattr(pool, 'invalid', lambda: 'N/A')(),
                "url_scheme": self.engine.url.drivername
            }
        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def reset_connection(self):
        """Reset database connection pool"""
        if self.engine:
            try:
                self.engine.dispose()
                logger.info("Database connection pool reset")
            except Exception as e:
                logger.error(f"Failed to reset connection pool: {str(e)}")
    
    def close(self):
        """Close database connections"""
        if self.engine:
            try:
                self.engine.dispose()
                logger.info("Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database connections: {str(e)}")


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session for FastAPI"""
    with db_manager.session_scope() as session:
        yield session


def init_database():
    """Initialize database (called at startup)"""
    db_manager.initialize()


def close_database():
    """Close database (called at shutdown)"""
    db_manager.close()