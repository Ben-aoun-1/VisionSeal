"""
Database connection and session management
"""
import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

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
                # PostgreSQL or other databases
                self.engine = create_engine(
                    settings.database.url,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=settings.database.echo_queries
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
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


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