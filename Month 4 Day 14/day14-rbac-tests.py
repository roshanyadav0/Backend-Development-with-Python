# Day 14: RBAC Tests
# Test role-based access control

import pytest
import jwt as pyjwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# These would import from your implementation
# from day14_rbac_implementation import (
#     JWTManager, get_current_user, require_admin, require_member,
#     RoleEnum, CurrentUser, Config
# )

# ============================================================================
# PART 1: JWT Manager Tests
# ============================================================================

class TestJWTWithRole:
    """Test JWT generation and verification with role"""
    
    def test_generate_token_includes_role(self):
        """JWT should include role claim"""
        
        manager = JWTManager('secret', 'HS256')
        
        token = manager.generate_token(
            user_id='user123',
            email='user@example.com',
            name='Alice',
            role='admin'
        )
        
        # Decode and verify role is included
        payload = pyjwt.decode(token, 'secret', algorithms=['HS256'])
        
        assert payload['role'] == 'admin'
        assert payload['user_id'] == 'user123'
        assert payload['email'] == 'user@example.com'
    
    def test_member_token_includes_member_role(self):
        """JWT for member should have member role"""
        
        manager = JWTManager('secret', 'HS256')
        
        token = manager.generate_token(
            user_id='user456',
            email='bob@example.com',
            name='Bob',
            role='member'
        )
        
        payload = pyjwt.decode(token, 'secret', algorithms=['HS256'])
        
        assert payload['role'] == 'member'
    
    def test_verify_token_returns_role(self):
        """Verify should return role in payload"""
        
        manager = JWTManager('secret', 'HS256')
        
        token = manager.generate_token(
            user_id='user789',
            email='charlie@example.com',
            name='Charlie',
            role='admin'
        )
        
        payload = manager.verify_token(token)
        
        assert payload['role'] == 'admin'
    
    def test_different_roles_different_tokens(self):
        """Different roles should produce different tokens"""
        
        manager = JWTManager('secret', 'HS256')
        
        admin_token = manager.generate_token(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        
        member_token = manager.generate_token(
            user_id='user2',
            email='member@example.com',
            name='Member',
            role='member'
        )
        
        assert admin_token != member_token
        
        admin_payload = pyjwt.decode(admin_token, 'secret', algorithms=['HS256'])
        member_payload = pyjwt.decode(member_token, 'secret', algorithms=['HS256'])
        
        assert admin_payload['role'] == 'admin'
        assert member_payload['role'] == 'member'

# ============================================================================
# PART 2: CurrentUser Model Tests
# ============================================================================

class TestCurrentUser:
    """Test CurrentUser model"""
    
    def test_current_user_is_admin(self):
        """is_admin property should work"""
        
        user = CurrentUser(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        
        assert user.is_admin == True
        assert user.is_member == False
    
    def test_current_user_is_member(self):
        """is_member property should work"""
        
        user = CurrentUser(
            user_id='user2',
            email='member@example.com',
            name='Member',
            role='member'
        )
        
        assert user.is_admin == False
        assert user.is_member == True

# ============================================================================
# PART 3: Role Decorator Tests
# ============================================================================

class TestRoleDecorators:
    """Test role-based access control decorators"""
    
    @pytest.mark.asyncio
    async def test_require_admin_allows_admin(self):
        """Admin should be allowed by @require_admin"""
        
        @require_admin
        async def admin_endpoint(current_user: CurrentUser):
            return {"message": "success"}
        
        admin_user = CurrentUser(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        
        # Should not raise exception
        result = await admin_endpoint(current_user=admin_user)
        assert result['message'] == 'success'
    
    @pytest.mark.asyncio
    async def test_require_admin_denies_member(self):
        """Member should be denied by @require_admin"""
        
        @require_admin
        async def admin_endpoint(current_user: CurrentUser):
            return {"message": "success"}
        
        member_user = CurrentUser(
            user_id='user2',
            email='member@example.com',
            name='Member',
            role='member'
        )
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await admin_endpoint(current_user=member_user)
        
        assert exc_info.value.status_code == 403
        assert 'Insufficient permissions' in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_role_multiple_roles(self):
        """require_role with multiple roles should allow both"""
        
        @require_role('admin', 'member')
        async def endpoint(current_user: CurrentUser):
            return {"message": "success"}
        
        # Admin should be allowed
        admin_user = CurrentUser(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        result = await endpoint(current_user=admin_user)
        assert result['message'] == 'success'
        
        # Member should be allowed
        member_user = CurrentUser(
            user_id='user2',
            email='member@example.com',
            name='Member',
            role='member'
        )
        result = await endpoint(current_user=member_user)
        assert result['message'] == 'success'
    
    @pytest.mark.asyncio
    async def test_require_member_allows_admin_and_member(self):
        """Admin should be allowed by member endpoints"""
        
        @require_member
        async def member_endpoint(current_user: CurrentUser):
            return {"message": "success"}
        
        # Admin should be allowed (admin can do member things)
        admin_user = CurrentUser(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        result = await member_endpoint(current_user=admin_user)
        assert result['message'] == 'success'
        
        # Member should be allowed
        member_user = CurrentUser(
            user_id='user2',
            email='member@example.com',
            name='Member',
            role='member'
        )
        result = await member_endpoint(current_user=member_user)
        assert result['message'] == 'success'

# ============================================================================
# PART 4: get_current_user Tests
# ============================================================================

class TestGetCurrentUser:
    """Test extracting current user from JWT"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_jwt(self):
        """Valid JWT should return CurrentUser with role"""
        
        # Create JWT
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='user1',
            email='user@example.com',
            name='Alice',
            role='admin'
        )
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies = {'access_token': token}
        
        # Get current user
        current_user = await get_current_user(mock_request)
        
        assert current_user.user_id == 'user1'
        assert current_user.email == 'user@example.com'
        assert current_user.role == 'admin'
    
    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self):
        """Missing JWT should raise 401"""
        
        # Mock request without cookie
        mock_request = MagicMock()
        mock_request.cookies = {}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        assert 'Not authenticated' in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_expired_token(self):
        """Expired JWT should raise 401"""
        
        # Create expired JWT
        now = datetime.utcnow()
        payload = {
            'user_id': 'user1',
            'email': 'user@example.com',
            'name': 'Alice',
            'role': 'admin',
            'exp': (now - timedelta(hours=1)).timestamp()  # Expired
        }
        token = pyjwt.encode(payload, 'secret', algorithm='HS256')
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies = {'access_token': token}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        assert 'Token expired' in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self):
        """Invalid JWT should raise 401"""
        
        # Mock request with invalid token
        mock_request = MagicMock()
        mock_request.cookies = {'access_token': 'not_a_valid_jwt'}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        assert 'Invalid token' in exc_info.value.detail

# ============================================================================
# PART 5: API Endpoint Tests
# ============================================================================

class TestPublicEndpoints:
    """Test public endpoints (no auth required)"""
    
    @pytest.mark.asyncio
    async def test_list_books_no_auth(self):
        """Public endpoint should work without auth"""
        
        # from fastapi.testclient import TestClient
        # client = TestClient(app)
        # response = client.get('/api/books')
        # assert response.status_code == 200
        pass

class TestMemberEndpoints:
    """Test member endpoints (auth required)"""
    
    @pytest.mark.asyncio
    async def test_member_can_borrow_book(self):
        """Member should be able to borrow book"""
        
        # Create JWT for member
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='user1',
            email='member@example.com',
            name='Alice',
            role='member'
        )
        
        # Make request with token in cookie
        # client = TestClient(app)
        # response = client.post(
        #     '/api/books/1/borrow',
        #     cookies={'access_token': token}
        # )
        # assert response.status_code == 200
        pass
    
    @pytest.mark.asyncio
    async def test_member_cannot_create_book(self):
        """Member should NOT be able to create book"""
        
        # Create JWT for member
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='user1',
            email='member@example.com',
            name='Alice',
            role='member'
        )
        
        # Make request to admin-only endpoint
        # client = TestClient(app)
        # response = client.post(
        #     '/api/books',
        #     json={'title': 'New Book', 'author': 'Author'},
        #     cookies={'access_token': token}
        # )
        # assert response.status_code == 403
        pass

class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    @pytest.mark.asyncio
    async def test_admin_can_create_book(self):
        """Admin should be able to create book"""
        
        # Create JWT for admin
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        
        # Make request
        # client = TestClient(app)
        # response = client.post(
        #     '/api/books',
        #     json={'title': 'New Book', 'author': 'Author'},
        #     cookies={'access_token': token}
        # )
        # assert response.status_code == 200
        pass
    
    @pytest.mark.asyncio
    async def test_admin_can_view_all_members(self):
        """Admin should be able to view all members"""
        
        # Create JWT for admin
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        
        # Make request
        # client = TestClient(app)
        # response = client.get(
        #     '/api/admin/members',
        #     cookies={'access_token': token}
        # )
        # assert response.status_code == 200
        # data = response.json()
        # assert 'members' in data
        pass
    
    @pytest.mark.asyncio
    async def test_member_cannot_view_all_members(self):
        """Member should NOT be able to view all members"""
        
        # Create JWT for member
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='user2',
            email='member@example.com',
            name='Alice',
            role='member'
        )
        
        # Make request to admin endpoint
        # client = TestClient(app)
        # response = client.get(
        #     '/api/admin/members',
        #     cookies={'access_token': token}
        # )
        # assert response.status_code == 403
        pass

# ============================================================================
# PART 6: Security Tests
# ============================================================================

class TestRBACSecurity:
    """Test RBAC security properties"""
    
    def test_role_case_sensitive(self):
        """Roles should be case-sensitive (lowercase)"""
        
        user = CurrentUser(
            user_id='user1',
            email='user@example.com',
            name='User',
            role='admin'
        )
        
        assert user.role == 'admin'
        assert user.role != 'Admin'  # Case sensitive
        assert user.role != 'ADMIN'
    
    def test_role_only_valid_values(self):
        """Role should only accept valid values"""
        
        # These should only work with 'admin' or 'member'
        
        admin_user = CurrentUser(
            user_id='user1',
            email='admin@example.com',
            name='Admin',
            role='admin'
        )
        assert admin_user.is_admin
        
        member_user = CurrentUser(
            user_id='user2',
            email='member@example.com',
            name='Member',
            role='member'
        )
        assert member_user.is_member
    
    def test_admin_no_privilege_escalation(self):
        """Admin role from JWT can't be escalated"""
        
        # Even if someone tampers with JWT, we verify signature
        # Invalid tokens are rejected
        
        # Create JWT with wrong secret
        tampered_payload = {
            'user_id': 'user1',
            'email': 'user@example.com',
            'role': 'super_admin'  # Try to escalate
        }
        tampered_token = pyjwt.encode(
            tampered_payload,
            'wrong_secret',  # Different secret
            algorithm='HS256'
        )
        
        manager = JWTManager('secret')  # Correct secret
        
        # Should fail verification
        with pytest.raises(pyjwt.InvalidTokenError):
            manager.verify_token(tampered_token)

# ============================================================================
# PART 7: Integration Tests
# ============================================================================

class TestRBACIntegration:
    """Integration tests combining multiple RBAC features"""
    
    @pytest.mark.asyncio
    async def test_admin_workflow(self):
        """Test complete admin workflow"""
        
        # 1. Login as admin (get JWT with admin role)
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='admin1',
            email='admin@example.com',
            name='Admin User',
            role='admin'
        )
        
        # 2. Extract user from token
        payload = manager.verify_token(token)
        current_user = CurrentUser(**payload)
        
        # 3. Verify is admin
        assert current_user.is_admin
        
        # 4. Can access admin endpoints (decorator would allow)
        # In real test, would call actual endpoint
    
    @pytest.mark.asyncio
    async def test_member_workflow(self):
        """Test complete member workflow"""
        
        # 1. Login as member (get JWT with member role)
        manager = JWTManager('secret')
        token = manager.generate_token(
            user_id='member1',
            email='member@example.com',
            name='Member User',
            role='member'
        )
        
        # 2. Extract user from token
        payload = manager.verify_token(token)
        current_user = CurrentUser(**payload)
        
        # 3. Verify is member
        assert current_user.is_member
        assert not current_user.is_admin
        
        # 4. Can access member endpoints but not admin
        # In real test, would call actual endpoints

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
