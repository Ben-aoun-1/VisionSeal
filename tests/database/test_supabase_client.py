"""
Tests for Supabase client with enhanced connection pooling and error handling
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.database.supabase_client import SupabaseManager
from postgrest.exceptions import APIError


class TestSupabaseManager:
    """Test Supabase manager functionality"""
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    def test_initialization_with_service_key(self, mock_create_client):
        """Test SupabaseManager initialization with service key"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        manager = SupabaseManager()
        
        assert manager.url == 'https://test.supabase.co'
        assert manager.key == 'test_anon_key'
        assert manager.service_key == 'test_service_key'
        assert manager.client == mock_client
        assert manager.service_client == mock_service_client
        assert mock_create_client.call_count == 2
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key'
    })
    @patch('core.database.supabase_client.create_client')
    def test_initialization_without_service_key(self, mock_create_client):
        """Test SupabaseManager initialization without service key"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = SupabaseManager()
        
        assert manager.url == 'https://test.supabase.co'
        assert manager.key == 'test_anon_key'
        assert manager.service_key is None
        assert manager.client == mock_client
        assert manager.service_client == mock_client  # Falls back to regular client
        assert mock_create_client.call_count == 1
    
    def test_initialization_missing_credentials(self):
        """Test SupabaseManager initialization with missing credentials"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_ANON_KEY must be set"):
                SupabaseManager()
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    def test_get_client(self, mock_create_client):
        """Test get_client method"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        manager = SupabaseManager()
        
        # Test getting regular client
        assert manager.get_client(use_service_key=False) == mock_client
        
        # Test getting service client
        assert manager.get_client(use_service_key=True) == mock_service_client
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_insert_tender_success(self, mock_create_client):
        """Test successful tender insertion"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock successful response
        mock_response = Mock()
        mock_response.data = [{'id': 1, 'title': 'Test Tender'}]
        mock_service_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        manager = SupabaseManager()
        
        tender_data = {
            'title': 'Test Tender',
            'description': 'Test Description',
            'source': 'TEST',
            'country': 'US'
        }
        
        result = await manager.insert_tender(tender_data)
        
        assert result == {'id': 1, 'title': 'Test Tender'}
        mock_service_client.table.assert_called_with('tenders')
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_insert_tender_with_retry(self, mock_create_client):
        """Test tender insertion with retry logic"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock first failure, then success
        mock_response_fail = Mock()
        mock_response_fail.data = None
        mock_response_success = Mock()
        mock_response_success.data = [{'id': 1, 'title': 'Test Tender'}]
        
        mock_service_client.table.return_value.insert.return_value.execute.side_effect = [
            APIError("Rate limit exceeded"),
            mock_response_success
        ]
        
        manager = SupabaseManager()
        
        tender_data = {'title': 'Test Tender'}
        
        with patch('asyncio.sleep') as mock_sleep:
            result = await manager.insert_tender(tender_data)
        
        assert result == {'id': 1, 'title': 'Test Tender'}
        mock_sleep.assert_called_once_with(1)  # First retry delay
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_bulk_insert_tenders(self, mock_create_client):
        """Test bulk tender insertion"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock successful response
        mock_response = Mock()
        mock_response.data = [{'id': 1}, {'id': 2}]
        mock_service_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        manager = SupabaseManager()
        
        tenders = [
            {'title': 'Tender 1', 'description': 'Description 1'},
            {'title': 'Tender 2', 'description': 'Description 2'}
        ]
        
        result = await manager.bulk_insert_tenders(tenders)
        
        assert result == 2
        mock_service_client.table.assert_called_with('tenders')
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_bulk_insert_with_batching(self, mock_create_client):
        """Test bulk insertion with batching"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock successful responses for each batch
        mock_response = Mock()
        mock_response.data = [{'id': 1}] * 50  # 50 items per batch
        mock_service_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        manager = SupabaseManager()
        
        # Create 150 tenders (should be split into 3 batches of 50)
        tenders = [{'title': f'Tender {i}'} for i in range(150)]
        
        result = await manager.bulk_insert_tenders(tenders, batch_size=50)
        
        assert result == 150  # 3 batches * 50 items
        assert mock_service_client.table.return_value.insert.return_value.execute.call_count == 3
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_create_client):
        """Test successful health check"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock successful response
        mock_response = Mock()
        mock_response.data = [{'id': 1}]
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
        mock_service_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
        
        manager = SupabaseManager()
        
        result = await manager.health_check()
        
        assert result['status'] == 'healthy'
        assert result['anon_key_working'] is True
        assert result['service_key_working'] is True
        assert 'response_time_ms' in result
        assert 'timestamp' in result
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_create_client):
        """Test health check failure"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock failed response
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = APIError("Connection failed")
        
        manager = SupabaseManager()
        
        result = await manager.health_check()
        
        assert result['status'] == 'unhealthy'
        assert result['anon_key_working'] is False
        assert result['service_key_working'] is False
        assert 'error' in result
        assert 'timestamp' in result
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    def test_get_connection_stats(self, mock_create_client):
        """Test connection statistics"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        manager = SupabaseManager()
        
        stats = manager.get_connection_stats()
        
        assert stats['supabase_url'] == 'https://test.supabase.co'
        assert stats['has_service_key'] is True
        assert stats['anon_key_configured'] is True
        assert stats['clients_initialized'] is True
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    def test_reset_clients(self, mock_create_client):
        """Test client reset functionality"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client, mock_client, mock_service_client]
        
        manager = SupabaseManager()
        
        # Reset clients
        manager.reset_clients()
        
        # Should have called create_client 4 times total (2 for init, 2 for reset)
        assert mock_create_client.call_count == 4
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_get_recent_tenders(self, mock_create_client):
        """Test getting recent tenders"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock successful response
        mock_response = Mock()
        mock_response.data = [{'id': 1, 'title': 'Recent Tender'}]
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_response
        
        manager = SupabaseManager()
        
        result = await manager.get_recent_tenders(limit=10)
        
        assert result == [{'id': 1, 'title': 'Recent Tender'}]
        mock_client.table.assert_called_with('tenders')
    
    @patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key',
        'SUPABASE_SERVICE_KEY': 'test_service_key'
    })
    @patch('core.database.supabase_client.create_client')
    @pytest.mark.asyncio
    async def test_search_tenders(self, mock_create_client):
        """Test tender search functionality"""
        mock_client = Mock()
        mock_service_client = Mock()
        mock_create_client.side_effect = [mock_client, mock_service_client]
        
        # Mock successful response
        mock_response = Mock()
        mock_response.data = [{'id': 1, 'title': 'Search Result'}]
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        manager = SupabaseManager()
        
        result = await manager.search_tenders(
            query='software',
            countries=['US', 'UK'],
            sources=['TEST'],
            min_score=0.5,
            limit=25
        )
        
        assert result == [{'id': 1, 'title': 'Search Result'}]
        mock_client.rpc.assert_called_with('search_tenders', {
            'search_query': 'software',
            'filter_countries': ['US', 'UK'],
            'filter_sources': ['TEST'],
            'min_score': 0.5,
            'limit_count': 25,
            'offset_count': 0
        })


if __name__ == "__main__":
    pytest.main([__file__, "-v"])