# Day 11: Google OAuth Implementation
# Complete Python implementation using FastAPI and httpx

import os
import json
import httpx
import secrets
from typing import Optional
from datetime import datetime, timedelta
from functools import lru_cache

import jwt
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PART 1: Configuration
# ============================================================================

class Config:
    """Google OAuth Configuration"""
    
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')
    
    # Google OAuth endpoints
    GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'
    
    # Scopes
    SCOPES = ['openid', 'profile', 'email']
    
    # Session
    SESSION_SECRET = os.getenv('SESSION_SECRET', 'dev-secret-change-in-production')
    SESSION_LIFETIME = 86400  # 24 hours
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_CLIENT_ID:
            raise ValueError('GOOGLE_CLIENT_ID not set in environment')
        if not cls.GOOGLE_CLIENT_SECRET:
            raise ValueError('GOOGLE_CLIENT_SECRET not set in environment')
        print(f'✓ Google OAuth configured')
        print(f'  Client ID: {cls.GOOGLE_CLIENT_ID[:20]}...')
        print(f'  Redirect URI: {cls.GOOGLE_REDIRECT_URI}')

# ============================================================================
# PART 2: Data Models
# ============================================================================

class GoogleTokenResponse(BaseModel):
    """Response from Google's token endpoint"""
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str
    token_type: str
    id_token: str

class GoogleUserInfo(BaseModel):
    """User information from Google"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    email_verified: bool

class User(BaseModel):
    """User stored in our database"""
    id: str
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: str
    last_login: str

class Session(BaseModel):
    """User session"""
    user_id: str
    session_id: str
    created_at: datetime
    expires_at: datetime

# ============================================================================
# PART 3: State Management (CSRF Protection)
# ============================================================================

class StateStore:
    """Store OAuth state for CSRF protection"""
    
    def __init__(self):
        self.states: dict = {}
    
    def generate(self) -> str:
        """Generate random state string"""
        state = secrets.token_urlsafe(32)
        self.states[state] = {
            'created_at': datetime.now(),
            'used': False
        }
        return state
    
    def validate(self, state: str) -> bool:
        """Validate state and mark as used"""
        if state not in self.states:
            return False
        
        state_data = self.states[state]
        
        # Check expiration (10 minutes)
        if datetime.now() - state_data['created_at'] > timedelta(minutes=10):
            return False
        
        # Check if already used (prevent replay attacks)
        if state_data['used']:
            return False
        
        # Mark as used
        state_data['used'] = True
        return True
    
    def cleanup(self):
        """Remove old states"""
        now = datetime.now()
        self.states = {
            state: data for state, data in self.states.items()
            if now - data['created_at'] < timedelta(minutes=15)
        }

# ============================================================================
# PART 4: Google OAuth Service
# ============================================================================

class GoogleOAuthService:
    """Handles Google OAuth authentication"""
    
    def __init__(self, config: Config, state_store: StateStore):
        self.config = config
        self.state_store = state_store
    
    def generate_authorization_url(self) -> tuple[str, str]:
        """
        Step 1: Generate URL to redirect user to Google login
        
        Returns:
            (authorization_url, state) - URL to redirect to, and state for validation
        """
        state = self.state_store.generate()
        
        params = {
            'client_id': self.config.GOOGLE_CLIENT_ID,
            'redirect_uri': self.config.GOOGLE_REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(self.config.SCOPES),
            'state': state,
            'access_type': 'offline',  # Request refresh token
            'prompt': 'consent'  # Always show consent screen
        }
        
        # Build URL
        query_string = '&'.join(
            f'{key}={value}' for key, value in params.items()
        )
        
        auth_url = f'{self.config.GOOGLE_AUTH_URL}?{query_string}'
        
        return auth_url, state
    
    async def exchange_code_for_token(self, code: str) -> GoogleTokenResponse:
        """
        Step 4-5: Exchange authorization code for access token
        
        CRITICAL: This happens on the backend (never in browser)
        Uses client_secret which must never be exposed
        """
        
        data = {
            'client_id': self.config.GOOGLE_CLIENT_ID,
            'client_secret': self.config.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.config.GOOGLE_REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.GOOGLE_TOKEN_URL,
                data=data,
                timeout=10.0
            )
        
        if response.status_code != 200:
            error_data = response.json()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code: {error_data.get('error', 'unknown')}"
            )
        
        token_data = response.json()
        
        return GoogleTokenResponse(
            access_token=token_data['access_token'],
            expires_in=token_data['expires_in'],
            refresh_token=token_data.get('refresh_token'),
            scope=token_data.get('scope', ''),
            token_type=token_data['token_type'],
            id_token=token_data['id_token']
        )
    
    def decode_id_token(self, id_token: str) -> dict:
        """
        Step 6-7: Decode ID token (JWT with user information)
        
        The id_token is a JWT that contains user info without needing
        to make an extra API call to /userinfo endpoint
        """
        
        # Decode WITHOUT verification (for simplicity)
        # In production, verify the JWT signature using Google's public key
        decoded = jwt.decode(
            id_token,
            options={'verify_signature': False}
        )
        
        return decoded
    
    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """
        Alternative to decoding ID token: Call /userinfo endpoint
        
        This makes an extra API call but is more reliable
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.config.GOOGLE_USERINFO_URL,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10.0
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail='Failed to get user info'
            )
        
        user_data = response.json()
        
        return GoogleUserInfo(
            id=user_data['id'],
            email=user_data['email'],
            name=user_data['name'],
            picture=user_data.get('picture'),
            email_verified=user_data.get('email_verified', False)
        )

# ============================================================================
# PART 5: User Database (Mock)
# ============================================================================

class UserDatabase:
    """Mock database for storing users"""
    
    def __init__(self):
        self.users: dict[str, User] = {}
    
    def find_by_google_id(self, google_id: str) -> Optional[User]:
        """Find user by Google ID"""
        for user in self.users.values():
            if user.google_id == google_id:
                return user
        return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create_user(
        self,
        google_id: str,
        email: str,
        name: str,
        picture: Optional[str] = None
    ) -> User:
        """Create new user"""
        user = User(
            id=secrets.token_urlsafe(16),
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
            created_at=datetime.now().isoformat(),
            last_login=datetime.now().isoformat()
        )
        self.users[user.id] = user
        return user
    
    def update_last_login(self, user_id: str):
        """Update user's last login time"""
        if user_id in self.users:
            self.users[user_id].last_login = datetime.now().isoformat()

# ============================================================================
# PART 6: Session Management
# ============================================================================

class SessionManager:
    """Manage user sessions"""
    
    def __init__(self, secret: str, lifetime: int):
        self.secret = secret
        self.lifetime = lifetime
        self.sessions: dict[str, Session] = {}
    
    def create_session(self, user_id: str) -> str:
        """Create new session, return session token"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now()
        
        session = Session(
            user_id=user_id,
            session_id=session_id,
            created_at=now,
            expires_at=now + timedelta(seconds=self.lifetime)
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """Validate session, return user_id if valid"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        if datetime.now() > session.expires_at:
            del self.sessions[session_id]
            return None
        
        return session.user_id
    
    def revoke_session(self, session_id: str):
        """Revoke session (logout)"""
        if session_id in self.sessions:
            del self.sessions[session_id]

# ============================================================================
# PART 7: FastAPI Application
# ============================================================================

app = FastAPI(title='Google OAuth Demo')

# Initialize components
Config.validate()
state_store = StateStore()
oauth_service = GoogleOAuthService(Config, state_store)
user_db = UserDatabase()
session_manager = SessionManager(Config.SESSION_SECRET, Config.SESSION_LIFETIME)

# ============================================================================
# PART 8: Routes
# ============================================================================

@app.get('/')
async def home():
    """Home page - show login button"""
    return {
        'message': 'Welcome to Google OAuth Demo',
        'login_url': '/auth/google/login'
    }

@app.get('/auth/google/login')
async def google_login():
    """
    Step 1-2: Redirect user to Google login
    
    This is what happens when user clicks "Login with Google"
    """
    auth_url, state = oauth_service.generate_authorization_url()
    
    # Create response that redirects to Google
    response = RedirectResponse(url=auth_url)
    
    # Store state in secure cookie (for CSRF protection)
    response.set_cookie(
        'oauth_state',
        state,
        max_age=600,  # 10 minutes
        httponly=True,  # Can't be accessed by JavaScript
        secure=False,  # Set to True in production (HTTPS)
        samesite='strict'  # CSRF protection
    )
    
    return response

@app.get('/auth/google/callback')
async def google_callback(
    code: str,
    state: str,
    request: Request
):
    """
    Step 3-7: Handle callback from Google
    
    Google redirects user back here with authorization code
    """
    
    # Step 1: Validate state (CSRF protection)
    cookie_state = request.cookies.get('oauth_state')
    
    if not cookie_state or not state_store.validate(cookie_state):
        raise HTTPException(status_code=400, detail='Invalid state (possible CSRF attack)')
    
    if cookie_state != state:
        raise HTTPException(status_code=400, detail='State mismatch')
    
    print(f'✓ State validated')
    
    # Step 2: Exchange code for token (backend only)
    try:
        token_response = await oauth_service.exchange_code_for_token(code)
        print(f'✓ Code exchanged for token')
    except HTTPException as e:
        print(f'✗ Token exchange failed: {e.detail}')
        raise
    
    # Step 3: Decode ID token to get user info
    user_info_dict = oauth_service.decode_id_token(token_response.id_token)
    
    print(f'✓ ID token decoded')
    print(f'  Email: {user_info_dict.get("email")}')
    print(f'  Name: {user_info_dict.get("name")}')
    
    # Step 4: Find or create user in database
    google_id = user_info_dict['sub']
    email = user_info_dict['email']
    name = user_info_dict.get('name', '')
    picture = user_info_dict.get('picture')
    
    user = user_db.find_by_google_id(google_id)
    
    if not user:
        # First time login - create user
        user = user_db.create_user(google_id, email, name, picture)
        print(f'✓ New user created: {email}')
    else:
        # Existing user - update last login
        user_db.update_last_login(user.id)
        print(f'✓ Returning user: {email}')
    
    # Step 5: Create session
    session_id = session_manager.create_session(user.id)
    print(f'✓ Session created: {session_id[:20]}...')
    
    # Step 6: Set session cookie and redirect to dashboard
    response = RedirectResponse(url='/dashboard', status_code=302)
    response.set_cookie(
        'session_id',
        session_id,
        max_age=Config.SESSION_LIFETIME,
        httponly=True,
        secure=False,  # Set to True in production
        samesite='strict'
    )
    
    # Clear oauth_state cookie
    response.delete_cookie('oauth_state')
    
    return response

@app.get('/dashboard')
async def dashboard(request: Request):
    """Protected route - show user info"""
    
    session_id = request.cookies.get('session_id')
    
    if not session_id:
        raise HTTPException(status_code=401, detail='Not logged in')
    
    user_id = session_manager.validate_session(session_id)
    
    if not user_id:
        raise HTTPException(status_code=401, detail='Session expired')
    
    user = user_db.users.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    
    return {
        'message': 'Welcome!',
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'picture': user.picture,
            'created_at': user.created_at,
            'last_login': user.last_login
        }
    }

@app.get('/auth/logout')
async def logout(response: Response):
    """Logout - revoke session"""
    response.delete_cookie('session_id')
    return RedirectResponse(url='/', status_code=302)

@app.get('/users')
async def list_users():
    """Debug endpoint - list all users (remove in production)"""
    return {
        'users': list(user_db.users.values())
    }

@app.get('/health')
async def health():
    """Health check"""
    return {'status': 'ok'}

# ============================================================================
# PART 9: Main
# ============================================================================

if __name__ == '__main__':
    import uvicorn
    
    print('\n' + '='*60)
    print('Google OAuth Demo Starting')
    print('='*60)
    print(f'Server: http://localhost:8000')
    print(f'Login: http://localhost:8000/auth/google/login')
    print(f'Callback: http://localhost:8000/auth/google/callback')
    print('='*60 + '\n')
    
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        reload=True
    )
