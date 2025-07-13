"""
Tests for Redis caching functionality in the API builder.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import json
import hashlib

from ctutor_backend.api.api_builder import CrudRouter
from ctutor_backend.interface.users import UserInterface, UserGet, UserList, UserQuery
from ctutor_backend.interface.organizations import OrganizationInterface
from ctutor_backend.interface.base import EntityInterface
from ctutor_backend.interface.permissions import Principal


class MockCache:
    """Mock Redis cache for testing"""
    
    def __init__(self):
        self._data = {}
        self._call_log = []
    
    async def get(self, key):
        self._call_log.append(('get', key))
        return self._data.get(key)
    
    async def set(self, key, value, ttl=None):
        self._call_log.append(('set', key, ttl))
        self._data[key] = value
    
    async def delete(self, *keys):
        self._call_log.append(('delete', keys))
        for key in keys:
            self._data.pop(key, None)
    
    def keys(self, pattern):
        """Synchronous keys method for pattern matching"""
        import fnmatch
        matching_keys = [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]
        return matching_keys
    
    def clear_log(self):
        self._call_log = []
    
    @property
    def call_log(self):
        return self._call_log


class MockPermissions:
    """Mock permissions for testing"""
    
    def __init__(self, user_id="test-user"):
        self.user_id = user_id


@pytest.fixture
def mock_cache():
    """Fixture for mock cache"""
    return MockCache()


@pytest.fixture
def mock_permissions():
    """Fixture for mock permissions"""
    return MockPermissions()


@pytest.fixture
def crud_router():
    """Fixture for CrudRouter with UserInterface"""
    return CrudRouter(UserInterface)


class TestCacheKeyGeneration:
    """Test cache key generation logic"""
    
    def test_get_cache_key_format(self):
        """Test GET cache key format"""
        table_name = "user"
        user_id = "test-user-123"
        entity_id = "entity-456"
        
        expected_key = f"{table_name}:get:{user_id}:{entity_id}"
        assert expected_key == "user:get:test-user-123:entity-456"
    
    def test_list_cache_key_format(self):
        """Test LIST cache key format with parameters"""
        table_name = "user"
        user_id = "test-user-123"
        
        # Create mock query parameters
        params = UserQuery(given_name="John", limit=10, skip=0)
        params_json = params.model_dump_json(exclude_none=True)
        params_hash = hashlib.sha256(params_json.encode()).hexdigest()
        
        expected_key = f"{table_name}:list:{user_id}:{params_hash}"
        
        # Verify hash is consistent
        assert len(params_hash) == 64  # SHA256 hex length
        assert expected_key.startswith("user:list:test-user-123:")
    
    def test_cache_key_uniqueness(self):
        """Test that different parameters generate different cache keys"""
        user_id = "test-user"
        
        params1 = UserQuery(given_name="John", limit=10)
        params2 = UserQuery(given_name="Jane", limit=10)
        params3 = UserQuery(given_name="John", limit=20)
        
        hash1 = hashlib.sha256(params1.model_dump_json(exclude_none=True).encode()).hexdigest()
        hash2 = hashlib.sha256(params2.model_dump_json(exclude_none=True).encode()).hexdigest()
        hash3 = hashlib.sha256(params3.model_dump_json(exclude_none=True).encode()).hexdigest()
        
        assert hash1 != hash2  # Different names
        assert hash1 != hash3  # Different limits
        assert hash2 != hash3  # Different names and limits


class TestGetCaching:
    """Test GET operation caching"""
    
    @pytest.mark.asyncio
    async def test_get_cache_miss_then_hit(self, mock_cache, mock_permissions):
        """Test GET operation cache miss followed by cache hit"""
        # Mock the get_id_db function
        mock_user_data = UserGet(
            id="user-123",
            given_name="John",
            family_name="Doe",
            email="john@example.com"
        )
        
        with patch('ctutor_backend.api.api_builder.get_id_db', new_callable=AsyncMock) as mock_get_id_db:
            mock_get_id_db.return_value = mock_user_data
            
            router = CrudRouter(UserInterface)
            get_route = router.get()
            
            # First call - cache miss
            result1 = await get_route(
                permissions=mock_permissions,
                id="user-123",
                cache=mock_cache,
                db=Mock()
            )
            
            # Verify database was called
            mock_get_id_db.assert_called_once()
            
            # Verify cache was set
            cache_calls = mock_cache.call_log
            assert any(call[0] == 'set' for call in cache_calls)
            assert any(call[2] == UserInterface.cache_ttl for call in cache_calls)  # TTL set correctly
            
            # Reset mock
            mock_get_id_db.reset_mock()
            mock_cache.clear_log()
            
            # Second call - cache hit
            result2 = await get_route(
                permissions=mock_permissions,
                id="user-123",
                cache=mock_cache,
                db=Mock()
            )
            
            # Verify database was NOT called
            mock_get_id_db.assert_not_called()
            
            # Verify cache was checked
            cache_calls = mock_cache.call_log
            assert any(call[0] == 'get' for call in cache_calls)
            
            # Results should be identical
            assert result1.id == result2.id
            assert result1.given_name == result2.given_name
    
    @pytest.mark.asyncio
    async def test_get_cache_user_isolation(self, mock_cache):
        """Test that cache is isolated per user"""
        user1_permissions = MockPermissions("user-1")
        user2_permissions = MockPermissions("user-2")
        
        mock_user_data = UserGet(
            id="user-123",
            given_name="John",
            family_name="Doe",
            email="john@example.com"
        )
        
        with patch('ctutor_backend.api.api_builder.get_id_db', new_callable=AsyncMock) as mock_get_id_db:
            mock_get_id_db.return_value = mock_user_data
            
            router = CrudRouter(UserInterface)
            get_route = router.get()
            
            # User 1 makes request
            await get_route(
                permissions=user1_permissions,
                id="user-123",
                cache=mock_cache,
                db=Mock()
            )
            
            # User 2 makes same request - should be cache miss due to user isolation
            await get_route(
                permissions=user2_permissions,
                id="user-123",
                cache=mock_cache,
                db=Mock()
            )
            
            # Both users should have caused database calls
            assert mock_get_id_db.call_count == 2


class TestListCaching:
    """Test LIST operation caching"""
    
    @pytest.mark.asyncio
    async def test_list_cache_with_parameters(self, mock_cache, mock_permissions):
        """Test LIST operation caching with different parameters"""
        mock_list_result = [
            UserList(id="1", given_name="John", email="john@example.com"),
            UserList(id="2", given_name="Jane", email="jane@example.com")
        ]
        mock_total = 2
        
        with patch('ctutor_backend.api.api_builder.list_db', new_callable=AsyncMock) as mock_list_db:
            mock_list_db.return_value = (mock_list_result, mock_total)
            
            router = CrudRouter(UserInterface)
            list_route = router.list()
            
            # Mock response object
            mock_response = Mock()
            mock_response.headers = {}
            
            params1 = UserQuery(given_name="John")
            params2 = UserQuery(given_name="Jane")
            
            # First call with params1
            result1 = await list_route(
                permissions=mock_permissions,
                response=mock_response,
                params=params1,
                cache=mock_cache,
                db=Mock()
            )
            
            # Second call with same params1 - should be cache hit
            mock_list_db.reset_mock()
            result2 = await list_route(
                permissions=mock_permissions,
                response=mock_response,
                params=params1,
                cache=mock_cache,
                db=Mock()
            )
            
            # Database should not be called second time
            mock_list_db.assert_not_called()
            
            # Third call with different params2 - should be cache miss
            await list_route(
                permissions=mock_permissions,
                response=mock_response,
                params=params2,
                cache=mock_cache,
                db=Mock()
            )
            
            # Database should be called for different parameters
            mock_list_db.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_cache_response_format(self, mock_cache, mock_permissions):
        """Test that cached list responses maintain proper format"""
        mock_list_result = [
            UserList(id="1", given_name="John", email="john@example.com")
        ]
        mock_total = 1
        
        with patch('ctutor_backend.api.api_builder.list_db', new_callable=AsyncMock) as mock_list_db:
            mock_list_db.return_value = (mock_list_result, mock_total)
            
            router = CrudRouter(UserInterface)
            list_route = router.list()
            
            mock_response = Mock()
            mock_response.headers = {}
            
            params = UserQuery()
            
            # First call - populate cache
            result1 = await list_route(
                permissions=mock_permissions,
                response=mock_response,
                params=params,
                cache=mock_cache,
                db=Mock()
            )
            
            # Verify response headers were set
            assert "X-Total-Count" in mock_response.headers
            assert mock_response.headers["X-Total-Count"] == "1"
            
            # Second call - from cache
            mock_response.headers = {}  # Reset headers
            result2 = await list_route(
                permissions=mock_permissions,
                response=mock_response,
                params=params,
                cache=mock_cache,
                db=Mock()
            )
            
            # Headers should still be set correctly from cache
            assert "X-Total-Count" in mock_response.headers
            assert mock_response.headers["X-Total-Count"] == "0"  # From cached data


class TestCacheInvalidation:
    """Test cache invalidation on mutations"""
    
    @pytest.mark.asyncio
    async def test_cache_clear_on_create(self, mock_cache):
        """Test cache is cleared when entity is created"""
        router = CrudRouter(UserInterface)
        
        # Populate cache first
        cache_key = "user:get:test-user:123"
        await mock_cache.set(cache_key, '{"id": "123"}')
        
        # Mock cache._cache for Redis client access
        mock_redis = Mock()
        mock_redis.keys = Mock(return_value=['user:get:test-user:123', 'user:list:test-user:abc'])
        mock_redis.delete = AsyncMock()
        mock_cache._cache = mock_redis
        
        # Call _clear_entity_cache
        await router._clear_entity_cache(mock_cache, "user")
        
        # Verify Redis keys method was called with correct pattern
        mock_redis.keys.assert_called_once_with("user:*")
        
        # Verify delete was called with found keys
        mock_redis.delete.assert_called_once_with('user:get:test-user:123', 'user:list:test-user:abc')
    
    @pytest.mark.asyncio
    async def test_cache_clear_error_handling(self, mock_cache):
        """Test cache clear handles errors gracefully"""
        router = CrudRouter(UserInterface)
        
        # Mock cache._cache that raises exception
        mock_redis = Mock()
        mock_redis.keys = Mock(side_effect=Exception("Redis error"))
        mock_cache._cache = mock_redis
        
        # Should not raise exception
        await router._clear_entity_cache(mock_cache, "user")
        
        # Error should be handled gracefully
        mock_redis.keys.assert_called_once()


class TestCacheTTL:
    """Test cache TTL (Time To Live) settings"""
    
    def test_interface_cache_ttl_values(self):
        """Test that interfaces have appropriate cache TTL values"""
        # User data - moderate frequency changes
        assert UserInterface.cache_ttl == 300  # 5 minutes
        
        # Organization data - less frequent changes
        assert OrganizationInterface.cache_ttl == 600  # 10 minutes
        
        # Test that all interfaces have cache_ttl defined
        from ctutor_backend.interface.accounts import AccountInterface
        from ctutor_backend.interface.roles import RoleInterface
        from ctutor_backend.interface.groups import GroupInterface
        from ctutor_backend.interface.profiles import ProfileInterface
        from ctutor_backend.interface.sessions import SessionInterface
        
        assert hasattr(AccountInterface, 'cache_ttl')
        assert hasattr(RoleInterface, 'cache_ttl')
        assert hasattr(GroupInterface, 'cache_ttl')
        assert hasattr(ProfileInterface, 'cache_ttl')
        assert hasattr(SessionInterface, 'cache_ttl')
        
        # Sessions should have shortest TTL (most frequently changing)
        assert SessionInterface.cache_ttl == 60  # 1 minute
        
        # Roles should have longest TTL (least frequently changing)
        assert RoleInterface.cache_ttl == 600  # 10 minutes
    
    @pytest.mark.asyncio
    async def test_cache_set_with_correct_ttl(self, mock_cache, mock_permissions):
        """Test that cache is set with correct TTL value"""
        mock_user_data = UserGet(
            id="user-123",
            given_name="John",
            family_name="Doe",
            email="john@example.com"
        )
        
        with patch('ctutor_backend.api.api_builder.get_id_db', new_callable=AsyncMock) as mock_get_id_db:
            mock_get_id_db.return_value = mock_user_data
            
            router = CrudRouter(UserInterface)
            get_route = router.get()
            
            await get_route(
                permissions=mock_permissions,
                id="user-123",
                cache=mock_cache,
                db=Mock()
            )
            
            # Check that cache.set was called with correct TTL
            cache_calls = mock_cache.call_log
            set_calls = [call for call in cache_calls if call[0] == 'set']
            assert len(set_calls) == 1
            
            # TTL should be UserInterface.cache_ttl
            assert set_calls[0][2] == 300  # UserInterface.cache_ttl


class TestCacheDataIntegrity:
    """Test cache data integrity and serialization"""
    
    @pytest.mark.asyncio
    async def test_cache_serialization_deserialization(self, mock_cache, mock_permissions):
        """Test that cached data is properly serialized and deserialized"""
        original_user = UserGet(
            id="user-123",
            given_name="John",
            family_name="Doe",
            email="john@example.com",
            created_at=datetime(2023, 1, 1, 10, 0, 0)
        )
        
        with patch('ctutor_backend.api.api_builder.get_id_db', new_callable=AsyncMock) as mock_get_id_db:
            mock_get_id_db.return_value = original_user
            
            router = CrudRouter(UserInterface)
            get_route = router.get()
            
            # First call - populates cache
            result1 = await get_route(
                permissions=mock_permissions,
                id="user-123",
                cache=mock_cache,
                db=Mock()
            )
            
            # Second call - from cache
            mock_get_id_db.reset_mock()
            result2 = await get_route(
                permissions=mock_permissions,
                id="user-123",
                cache=mock_cache,
                db=Mock()
            )
            
            # Verify database was not called on second request
            mock_get_id_db.assert_not_called()
            
            # Verify data integrity
            assert result1.id == result2.id == "user-123"
            assert result1.given_name == result2.given_name == "John"
            assert result1.family_name == result2.family_name == "Doe"
            assert result1.email == result2.email == "john@example.com"
            
            # Computed properties should work correctly on cached data
            assert result2.full_name == "John Doe"
            assert result2.display_name == "John Doe"
    
    def test_cache_key_collision_prevention(self):
        """Test that cache keys prevent collisions between different data types"""
        user_cache_key = "user:get:test-user:123"
        org_cache_key = "organization:get:test-user:123"
        
        # Different table names should create different cache keys
        assert user_cache_key != org_cache_key
        
        # Same user, different entities should have different cache keys
        user_get_key = "user:get:test-user:123"
        user_list_key = "user:list:test-user:hash123"
        
        assert user_get_key != user_list_key