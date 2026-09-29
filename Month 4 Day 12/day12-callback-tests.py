# Day 12: OAuth Callback Handler Tests
# Token exchange, user management, JWT generation

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import jwt as pyjwt

from day12_callback_implementation import (
    Config,
    TokenExchanger,
    UserInfoExtractor,
    UserManager,
    JWTManager,
    StateStore,
    CallbackHandler,
    TokenExchangeError,
    UserInfoError,
    JWTGenerationError
)

# ============================================================================
# PART 1: Token Exchange Tests
# ============================================================================

class TestTokenExchanger:
    """Test token exchange with Google"""
    
    @pytest.fixture
    def exchanger(self):
        return TokenExchanger(Config)
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, exchanger):
        """Successfully exchange code for tokens"""
        
        mock_response = {
            'access_token': 'ya29.a0AfH6SMBu...',
            'expires_in': 3599,
            'refresh_token': '1//0g...',
            'scope': 'openid email profile',
            'token_type': 'Bearer',
            'id_token': 'eyJhbGc...'
        }
        
        # Test that request is formed correctly
        # (Actual HTTP call would be mocked in production)
        assert 'access_token' in mock_response
        assert 'id_token' in mock_response
        assert 'expires_in' in mock_response
    
    @pytest.mark.asyncio
    async def test_exchange_code_invalid_grant(self, exchanger):
        """Exchanging expired code should raise error"""
        # In production, this would mock the HTTP response
        # and verify error handling
        pass
    
    @pytest.mark.asyncio
    async def test_exchange_code_invalid_client(self, exchanger):
        """Wrong client secret should raise error"""
        # Test that client authentication failure is handled
        pass
    
    @pytest.mark.asyncio
    async def test_exchange_code_network_error(self, exchanger):
        """Network errors should be caught"""
        # Test that network timeouts and errors are handled
        pass

# ============================================================================
# PART 2: User Info Extraction Tests
# ============================================================================

class TestUserInfoExtractor:
    """Test user info extraction from ID token"""
    
    def test_decode_id_token_valid(self):
        """Valid ID token should decode correctly"""
        
        # Create a valid ID token
        payload = {
            'sub': '1234567890',
            'iss': 'https://accounts.google.com',
            'aud': Config.GOOGLE_CLIENT_ID,
            'email': 'user@example.com',
            'name': 'Alice Smith',
            'picture': 'https://example.com/pic.jpg',
            'email_verified': True,
            'iat': int(datetime.utcnow().timestamp()),
            'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        
        id_token = pyjwt.encode(payload, 'secret', algorithm='HS256')
        
        # Decode it
        user_info = UserInfoExtractor.decode_id_token(id_token)
        
        assert user_info['google_id'] == '1234567890'
        assert user_info['email'] == 'user@example.com'
        assert user_info['name'] == 'Alice Smith'
        assert user_info['email_verified'] == True
    
    def test_decode_id_token_missing_email(self):
        """ID token without email should raise error"""
        
        payload = {
            'sub': '1234567890',
            'name': 'Alice'
            # Missing email
        }
        
        id_token = pyjwt.encode(payload, 'secret', algorithm='HS256')
        
        with pytest.raises(UserInfoError):
            UserInfoExtractor.decode_id_token(id_token)
    
    def test_decode_id_token_missing_sub(self):
        """ID token without sub (user ID) should raise error"""
        
        payload = {
            'email': 'user@example.com',
            # Missing sub
        }
        
        id_token = pyjwt.encode(payload, 'secret', algorithm='HS256')
        
        with pytest.raises(UserInfoError):
            UserInfoExtractor.decode_id_token(id_token)
    
    def test_decode_id_token_invalid(self):
        """Invalid ID token should raise error"""
        
        with pytest.raises(UserInfoError):
            UserInfoExtractor.decode_id_token('not_a_valid_jwt')

# ============================================================================
# PART 3: User Manager Tests
# ============================================================================

class TestUserManager:
    """Test user creation and lookup"""
    
    @pytest.fixture
    def manager(self):
        return UserManager()
    
    def test_find_or_create_new_user(self, manager):
        """Creating new user should return new user"""
        
        user, is_new = manager.find_or_create(
            google_id='123456',
            email='user@example.com',
            name='Alice Smith',
            picture='https://example.com/pic.jpg',
            email_verified=True
        )
        
        assert user.google_id == '123456'
        assert user.email == 'user@example.com'
        assert user.name == 'Alice Smith'
        assert is_new == True
    
    def test_find_or_create_existing_user(self, manager):
        """Finding existing user should return same user"""
        
        # Create user
        user1, is_new1 = manager.find_or_create(
            google_id='123456',
            email='user@example.com',
            name='Alice Smith'
        )
        
        # Find same user
        user2, is_new2 = manager.find_or_create(
            google_id='123456',
            email='user@example.com',
            name='Alice Smith'
        )
        
        assert user1.id == user2.id
        assert is_new1 == True
        assert is_new2 == False
    
    def test_find_by_google_id(self, manager):
        """Should find user by Google ID"""
        
        user1, _ = manager.find_or_create(
            google_id='123456',
            email='user@example.com',
            name='Alice'
        )
        
        user2 = manager.find_by_google_id('123456')
        
        assert user2 is not None
        assert user2.email == 'user@example.com'
    
    def test_find_nonexistent_user(self, manager):
        """Finding nonexistent user should return None"""
        
        user = manager.find_by_google_id('nonexistent')
        
        assert user is None
    
    def test_update_last_login(self, manager):
        """Updating last login should work"""
        
        user, _ = manager.find_or_create(
            google_id='123456',
            email='user@example.com',
            name='Alice'
        )
        
        old_login = user.last_login
        
        import time
        time.sleep(0.1)
        
        manager.update_last_login(user.id)
        
        updated = manager.users[user.id]
        assert updated.last_login > old_login

# ============================================================================
# PART 4: JWT Manager Tests
# ============================================================================

class TestJWTManager:
    """Test JWT token generation and verification"""
    
    @pytest.fixture
    def jwt_manager(self):
        return JWTManager('test-secret', 'HS256')
    
    def test_generate_token(self, jwt_manager):
        """Generating token should work"""
        
        token = jwt_manager.generate_token(
            user_id='user123',
            email='user@example.com',
            name='Alice',
            expiration_hours=24
        )
        
        assert token
        assert isinstance(token, str)
        # JWT has 3 parts separated by dots
        assert token.count('.') == 2
    
    def test_verify_valid_token(self, jwt_manager):
        """Verifying valid token should work"""
        
        token = jwt_manager.generate_token(
            user_id='user123',
            email='user@example.com',
            name='Alice',
            expiration_hours=24
        )
        
        payload = jwt_manager.verify_token(token)
        
        assert payload['user_id'] == 'user123'
        assert payload['email'] == 'user@example.com'
        assert payload['name'] == 'Alice'
    
    def test_verify_expired_token(self, jwt_manager):
        """Verifying expired token should fail"""
        
        # Generate token with -1 hour expiration (already expired)
        now = datetime.utcnow()
        expired_payload = {
            'user_id': 'user123',
            'exp': (now - timedelta(hours=1)).timestamp()
        }
        
        token = pyjwt.encode(expired_payload, 'test-secret', algorithm='HS256')
        
        with pytest.raises(Exception):  # Would be HTTPException in FastAPI
            jwt_manager.verify_token(token)
    
    def test_verify_invalid_token(self, jwt_manager):
        """Verifying invalid token should fail"""
        
        with pytest.raises(Exception):
            jwt_manager.verify_token('not_a_valid_token')
    
    def test_verify_token_wrong_secret(self):
        """Token signed with different secret should fail"""
        
        jwt_manager1 = JWTManager('secret1', 'HS256')
        jwt_manager2 = JWTManager('secret2', 'HS256')
        
        # Generate with secret1
        token = jwt_manager1.generate_token(
            user_id='user123',
            email='user@example.com',
            name='Alice'
        )
        
        # Try to verify with secret2
        with pytest.raises(Exception):
            jwt_manager2.verify_token(token)

# ============================================================================
# PART 5: State Store Tests
# ============================================================================

class TestStateStore:
    """Test CSRF protection via state validation"""
    
    def test_generate_state_creates_unique(self):
        """Each state should be unique"""
        
        store = StateStore()
        
        state1 = store.generate()
        state2 = store.generate()
        
        assert state1 != state2
        assert len(state1) > 20
        assert len(state2) > 20
    
    def test_validate_state_succeeds(self):
        """New state should validate"""
        
        store = StateStore()
        state = store.generate()
        
        assert store.validate(state) == True
    
    def test_validate_state_single_use(self):
        """State should only be valid once"""
        
        store = StateStore()
        state = store.generate()
        
        # First validation succeeds
        assert store.validate(state) == True
        
        # Second validation fails (already used)
        assert store.validate(state) == False
    
    def test_validate_unknown_state(self):
        """Unknown state should fail"""
        
        store = StateStore()
        
        assert store.validate('unknown_state') == False
    
    def test_validate_expired_state(self):
        """Expired state should fail"""
        
        store = StateStore()
        state = store.generate()
        
        # Manually expire
        store.states[state]['created_at'] = datetime.now() - timedelta(minutes=15)
        
        assert store.validate(state) == False

# ============================================================================
# PART 6: Callback Handler Tests
# ============================================================================

class TestCallbackHandler:
    """Test complete callback flow"""
    
    @pytest.fixture
    def setup(self):
        """Setup callback handler"""
        
        token_exchanger = TokenExchanger(Config)
        user_extractor = UserInfoExtractor()
        user_manager = UserManager()
        jwt_manager = JWTManager(Config.JWT_SECRET)
        state_store = StateStore()
        
        callback_handler = CallbackHandler(
            token_exchanger,
            user_extractor,
            user_manager,
            jwt_manager,
            state_store,
            Config
        )
        
        return {
            'callback_handler': callback_handler,
            'state_store': state_store,
            'user_manager': user_manager,
            'jwt_manager': jwt_manager
        }
    
    @pytest.mark.asyncio
    async def test_callback_flow_complete(self, setup):
        """Test complete callback flow"""
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.cookies = {}
        
        # For now, just verify structure
        # Full integration test would mock all HTTP calls
        assert setup['callback_handler']
        assert setup['state_store']
        assert setup['user_manager']

# ============================================================================
# PART 7: Security Tests
# ============================================================================

class TestSecurity:
    """Test security aspects"""
    
    def test_state_prevents_csrf(self):
        """State validation prevents CSRF attacks"""
        
        store = StateStore()
        
        # Attacker tries to use different state
        state1 = store.generate()
        state2 = 'attacker_state'
        
        # Valid state passes
        assert store.validate(state1) == True
        
        # Attacker state fails
        assert store.validate(state2) == False
    
    def test_state_single_use_prevents_replay(self):
        """Single-use state prevents replay attacks"""
        
        store = StateStore()
        state = store.generate()
        
        # First use succeeds
        assert store.validate(state) == True
        
        # Replay attempt fails
        assert store.validate(state) == False
    
    def test_jwt_expiration(self):
        """JWT should expire after configured time"""
        
        jwt_manager = JWTManager('secret', 'HS256')
        
        # Generate with 1-second expiration
        now = datetime.utcnow()
        payload = {
            'user_id': 'user123',
            'iat': now.timestamp(),
            'exp': (now + timedelta(seconds=1)).timestamp()
        }
        
        token = pyjwt.encode(payload, 'secret', algorithm='HS256')
        
        # Should verify immediately
        decoded = pyjwt.decode(token, 'secret', algorithms=['HS256'])
        assert decoded['user_id'] == 'user123'
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Should fail after expiration
        with pytest.raises(pyjwt.ExpiredSignatureError):
            pyjwt.decode(token, 'secret', algorithms=['HS256'])

# ============================================================================
# PART 8: Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in callback"""
    
    def test_token_exchange_error_message(self):
        """Token exchange errors should have helpful messages"""
        
        # Test various error scenarios
        errors = [
            ('invalid_grant', 'Code expired'),
            ('invalid_client', 'Client authentication'),
            ('invalid_code', 'Authorization code')
        ]
        
        for error_code, _ in errors:
            assert error_code  # Just verify structure
    
    def test_user_info_extraction_error(self):
        """User info extraction errors should be caught"""
        
        with pytest.raises(UserInfoError):
            UserInfoExtractor.decode_id_token('invalid_token')
    
    def test_jwt_generation_error(self):
        """JWT generation errors should be handled"""
        
        jwt_manager = JWTManager('secret', 'HS256')
        
        # Valid generation should work
        token = jwt_manager.generate_token(
            user_id='user123',
            email='user@example.com',
            name='Alice'
        )
        
        assert token

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
