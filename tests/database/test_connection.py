"""
Tests for database connection pooling and error handling
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.database.connection import DatabaseManager, db_manager
from sqlalchemy.exc import DisconnectionError, TimeoutError, SQLAlchemyError


class TestDatabaseConnection:
    """Test database connection and pooling"""
    
    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization"""
        manager = DatabaseManager()
        assert manager.engine is None
        assert manager.SessionLocal is None
        assert not manager._initialized
    
    @patch('core.database.connection.create_engine')
    @patch('core.database.connection.sessionmaker')
    def test_initialize_sqlite(self, mock_sessionmaker, mock_create_engine):
        """Test SQLite database initialization"""
        manager = DatabaseManager()
        
        # Mock settings for SQLite
        with patch('core.database.connection.settings') as mock_settings:
            mock_settings.database.url = "sqlite:///test.db"
            mock_settings.database.echo_queries = False
            
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            mock_session = Mock()
            mock_sessionmaker.return_value = mock_session
            
            manager.initialize()
            
            # Verify engine creation with SQLite config
            assert mock_create_engine.called
            call_args = mock_create_engine.call_args[1]
            assert 'connect_args' in call_args
            assert call_args['connect_args']['check_same_thread'] is False
            
            assert manager._initialized is True
    
    @patch('core.database.connection.create_engine')
    @patch('core.database.connection.sessionmaker')
    def test_initialize_postgresql(self, mock_sessionmaker, mock_create_engine):
        """Test PostgreSQL database initialization"""
        manager = DatabaseManager()
        
        # Mock settings for PostgreSQL
        with patch('core.database.connection.settings') as mock_settings:
            mock_settings.database.url = "postgresql://user:pass@host:5432/db"
            mock_settings.database.pool_size = 10
            mock_settings.database.max_overflow = 20
            mock_settings.database.echo_queries = False
            
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            mock_session = Mock()
            mock_sessionmaker.return_value = mock_session
            
            manager.initialize()
            
            # Verify engine creation with PostgreSQL pooling config
            assert mock_create_engine.called
            call_args = mock_create_engine.call_args[1]
            assert call_args['pool_size'] == 10
            assert call_args['max_overflow'] == 20
            assert call_args['pool_pre_ping'] is True
            assert call_args['pool_recycle'] == 3600
            assert call_args['pool_timeout'] == 30
            assert call_args['future'] is True
            
            assert manager._initialized is True
    
    def test_session_scope_success(self):
        """Test successful session scope operation"""
        manager = DatabaseManager()
        
        # Mock initialized manager
        mock_session = Mock()
        manager.SessionLocal = Mock(return_value=mock_session)
        manager._initialized = True
        
        with manager.session_scope() as session:
            assert session == mock_session
            session.execute("SELECT 1")
        
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
    
    def test_session_scope_with_exception(self):
        """Test session scope with exception handling"""
        manager = DatabaseManager()
        
        # Mock initialized manager
        mock_session = Mock()
        manager.SessionLocal = Mock(return_value=mock_session)
        manager._initialized = True
        
        with pytest.raises(Exception):
            with manager.session_scope() as session:
                raise Exception("Test error")
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    @patch('time.sleep')
    def test_session_scope_with_retry(self, mock_sleep):
        """Test session scope with retry logic for connection errors"""
        manager = DatabaseManager()
        
        # Mock sessions - first two fail, third succeeds
        mock_session1 = Mock()
        mock_session1.commit.side_effect = DisconnectionError("Connection lost", None, None)
        mock_session2 = Mock()
        mock_session2.commit.side_effect = TimeoutError("Timeout", None, None)
        mock_session3 = Mock()
        
        manager.SessionLocal = Mock(side_effect=[mock_session1, mock_session2, mock_session3])
        manager._initialized = True
        
        with manager.session_scope() as session:
            assert session == mock_session3
        
        # Verify retries and exponential backoff
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.5)  # First retry
        mock_sleep.assert_any_call(1.0)  # Second retry
        
        mock_session3.commit.assert_called_once()
        mock_session3.close.assert_called_once()
    
    def test_execute_query_success(self):
        """Test successful query execution"""
        manager = DatabaseManager()
        
        # Mock session and result
        mock_session = Mock()
        mock_result = Mock()
        mock_result.returns_rows = True
        mock_result.keys.return_value = ['id', 'name']
        mock_result.fetchall.return_value = [(1, 'test')]
        mock_session.execute.return_value = mock_result
        
        manager.SessionLocal = Mock(return_value=mock_session)
        manager._initialized = True
        
        result = manager.execute_query("SELECT * FROM test")
        
        assert result == [{'id': 1, 'name': 'test'}]
        mock_session.execute.assert_called_once()
    
    @patch('time.sleep')
    def test_execute_query_with_retry(self, mock_sleep):
        """Test query execution with retry logic"""
        manager = DatabaseManager()
        
        # Mock sessions - first fails, second succeeds
        mock_session1 = Mock()
        mock_session1.execute.side_effect = DisconnectionError("Connection lost", None, None)
        mock_session2 = Mock()
        mock_result = Mock()
        mock_result.returns_rows = False
        mock_result.rowcount = 1
        mock_session2.execute.return_value = mock_result
        
        manager.SessionLocal = Mock(side_effect=[mock_session1, mock_session2])
        manager._initialized = True
        
        result = manager.execute_query("UPDATE test SET name = 'new'")
        
        assert result == 1
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(0.5)
    
    def test_health_check_success(self):
        """Test successful health check"""
        manager = DatabaseManager()
        
        # Mock session
        mock_session = Mock()
        manager.SessionLocal = Mock(return_value=mock_session)
        manager._initialized = True
        
        with patch('core.database.connection.settings') as mock_settings:
            mock_settings.database.url = "postgresql://user:pass@host:5432/db"
            
            result = manager.health_check()
            
            assert result is True
            mock_session.execute.assert_called()
    
    def test_health_check_failure(self):
        """Test health check failure"""
        manager = DatabaseManager()
        
        # Mock session that fails
        mock_session = Mock()
        mock_session.execute.side_effect = SQLAlchemyError("Connection failed")
        manager.SessionLocal = Mock(return_value=mock_session)
        manager._initialized = True
        
        result = manager.health_check()
        
        assert result is False
    
    def test_get_connection_info(self):
        """Test connection info retrieval"""
        manager = DatabaseManager()
        
        # Mock engine with pool
        mock_pool = Mock()
        mock_pool.size.return_value = 10
        mock_pool.checkedin.return_value = 5
        mock_pool.checkedout.return_value = 3
        mock_pool.overflow.return_value = 2
        mock_pool.invalid.return_value = 0
        
        mock_engine = Mock()
        mock_engine.pool = mock_pool
        mock_engine.url.drivername = "postgresql"
        
        manager.engine = mock_engine
        
        info = manager.get_connection_info()
        
        assert info['status'] == 'connected'
        assert info['pool_size'] == 10
        assert info['checked_in'] == 5
        assert info['checked_out'] == 3
        assert info['overflow'] == 2
        assert info['invalid'] == 0
        assert info['url_scheme'] == 'postgresql'
    
    def test_get_connection_info_not_initialized(self):
        """Test connection info when not initialized"""
        manager = DatabaseManager()
        
        info = manager.get_connection_info()
        
        assert info == {"status": "not_initialized"}
    
    def test_reset_connection(self):
        """Test connection reset"""
        manager = DatabaseManager()
        
        # Mock engine
        mock_engine = Mock()
        manager.engine = mock_engine
        
        manager.reset_connection()
        
        mock_engine.dispose.assert_called_once()
    
    def test_close_connection(self):
        """Test connection closure"""
        manager = DatabaseManager()
        
        # Mock engine
        mock_engine = Mock()
        manager.engine = mock_engine
        
        manager.close()
        
        mock_engine.dispose.assert_called_once()


class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def test_get_db_function(self):
        """Test get_db dependency function"""
        from core.database.connection import get_db
        
        # Mock db_manager
        mock_session = Mock()
        with patch('core.database.connection.db_manager') as mock_manager:
            mock_manager.session_scope.return_value.__enter__.return_value = mock_session
            mock_manager.session_scope.return_value.__exit__.return_value = None
            
            # Test generator behavior
            db_gen = get_db()
            session = next(db_gen)
            
            assert session == mock_session
    
    def test_init_database_function(self):
        """Test init_database function"""
        from core.database.connection import init_database
        
        with patch('core.database.connection.db_manager') as mock_manager:
            init_database()
            mock_manager.initialize.assert_called_once()
    
    def test_close_database_function(self):
        """Test close_database function"""
        from core.database.connection import close_database
        
        with patch('core.database.connection.db_manager') as mock_manager:
            close_database()
            mock_manager.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])