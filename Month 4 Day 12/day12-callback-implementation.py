# Day 12: OAuth Callback Handler Implementation
# Exchange code for token, fetch user profile, issue JWT

import os
import json
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from functools import lru_cache

import jwt
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PART 1: Logging Setup
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PART 2: Configuration
# ============================================================================

class Config:
    """OAuth Configuration"""
    
    # Google credentials
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
    
    # Google endpoints
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'
    
    # JWT settings
    JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    # Session settings
    SESSION_TIMEOUT_SECONDS = 86400  # 24 hours
    
    @classmethod
    def validate(cls):
        if not cls.GOOGLE_CLIENT_ID or not cls.GOOGLE_CLIENT_SECRET:
            raise ValueError('Missing Google OAuth credentials')
        logger.info('✓ Configuration loaded')

# ============================================================================
# PART 3: Error Handling
# ============================================================================

class TokenExchangeError(Exception):
    """Error during token exchange"""
    pass

class UserInfoError(Exception):
    """Error fetching user info"""
    pass

class JWTGenerationError(Exception):
    """Error generating JWT"""
    pass

# ============================================================================
# PART 4: Token Exchange Service
# ============================================================================

class TokenExchanger:
    """Exchange authorization code for Google access token"""
    
    def __init__(self, config: Config):
        self.config = config
    
    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> dict:
        """
        STEP 2: Exchange authorization code for access token
        
        This is a backend-to-backend request using client_secret
        NEVER expose client_secret to browser
        
        Args:
            code: Authorization code from Google
            redirect_uri: Must match registered redirect_uri
            
        Returns:
            {
                'access_token': '...',
                'id_token': '...',
                'refresh_token': '...',
                'expires_in': 3599,
                'token_type': 'Bearer'
            }
        """
        
        logger.info(f'Exchanging code for token')
        
        # Prepare request
        token_request = {
            'client_id': self.config.GOOGLE_CLIENT_ID,
            'client_secret': self.config.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        # Make request to Google
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.GOOGLE_TOKEN_URL,
                    data=token_request,
                    timeout=10.0
                )
        except httpx.TimeoutException:
            logger.error('Token exchange timeout')
            raise TokenExchangeError('Google service timeout')
        except httpx.NetworkError as e:
            logger.error(f'Network error: {e}')
            raise TokenExchangeError('Network error')
        
        # Check status
        if response.status_code != 200:
            error_data = response.json()
            error = error_data.get('error', 'unknown_error')
            error_desc = error_data.get('error_description', '')
            
            logger.error(f'Token exchange failed: {error} - {error_desc}')
            
            # Map Google errors to user-friendly messages
            if error == 'invalid_grant':
                raise TokenExchangeError(
                    'Authorization code expired or invalid. Please login again.'
                )
            elif error == 'invalid_client':
                raise TokenExchangeError(
                    'Client authentication failed. Check credentials.'
                )
            elif error == 'invalid_code':
                raise TokenExchangeError(
                    'Authorization code is invalid.'
                )
            else:
                raise TokenExchangeError(f'Token exchange failed: {error}')
        
        tokens = response.json()
        
        logger.info(f'✓ Code exchanged for token')
        logger.info(f'  Access token expires in: {tokens.get("expires_in")}s')
        
        return tokens

# ============================================================================
# PART 5: User Info Extraction
# ============================================================================

class UserInfoExtractor:
    """Extract user information from Google tokens"""
    
    @staticmethod
    def decode_id_token(id_token: str) -> dict:
        """
        STEP 3: Decode ID token (JWT with user info)
        
        ID token is a JWT containing:
        - sub: Google user ID
        - email: User's email
        - name: User's name
        - picture: Profile picture URL
        - email_verified: Whether email is verified
        
        In production, verify the JWT signature using Google's public key.
        For now, we decode without verification (acceptable for ID tokens
        if you trust the token came from Google).
        """
        
        logger.info('Decoding ID token')
        
        try:
            # Decode WITHOUT signature verification (for simplicity)
            # In production, verify:
            # 1. Get Google's public key from https://www.googleapis.com/oauth2/v1/certs
            # 2. Verify JWT signature
            payload = jwt.decode(
                id_token,
                options={'verify_signature': False}
            )
        except jwt.InvalidTokenError as e:
            logger.error(f'Invalid ID token: {e}')
            raise UserInfoError('Invalid ID token')
        
        # Validate required fields
        google_id = payload.get('sub')
        email = payload.get('email')
        
        if not google_id or not email:
            logger.error(f'Missing required fields in ID token')
            raise UserInfoError('Missing email or user ID')
        
        logger.info(f'✓ ID token decoded')
        logger.info(f'  Google ID: {google_id}')
        logger.info(f'  Email: {email}')
        
        return {
            'google_id': google_id,
            'email': email,
            'name': payload.get('name', ''),
            'picture': payload.get('picture'),
            'email_verified': payload.get('email_verified', False)
        }
    
    @staticmethod
    async def get_user_info_from_api(
        access_token: str,
        userinfo_url: str
    ) -> dict:
        """
        Alternative to decoding ID token: Call Google's userinfo endpoint
        
        This requires an extra API call but is more reliable.
        """
        
        logger.info('Fetching user info from Google API')
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_url,
                    headers=headers,
                    timeout=10.0
                )
        except httpx.TimeoutException:
            logger.error('Userinfo request timeout')
            raise UserInfoError('Google service timeout')
        except httpx.NetworkError as e:
            logger.error(f'Network error: {e}')
            raise UserInfoError('Network error')
        
        if response.status_code != 200:
            logger.error(f'Failed to get userinfo: {response.status_code}')
            raise UserInfoError('Failed to fetch user info')
        
        user_data = response.json()
        
        logger.info(f'✓ User info fetched from Google')
        
        return {
            'google_id': user_data['id'],
            'email': user_data['email'],
            'name': user_data.get('name', ''),
            'picture': user_data.get('picture'),
            'email_verified': user_data.get('email_verified', False)
        }

# ============================================================================
# PART 6: User Management
# ============================================================================

class User(BaseModel):
    """User model"""
    id: str
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None
    email_verified: bool = False
    created_at: str
    last_login: str

class UserManager:
    """Find or create user from Google profile"""
    
    def __init__(self):
        self.users: dict = {}
    
    def find_by_google_id(self, google_id: str) -> Optional[User]:
        """Find existing user by Google ID"""
        for user in self.users.values():
            if user.google_id == google_id:
                return user
        return None
    
    def find_or_create(
        self,
        google_id: str,
        email: str,
        name: str,
        picture: Optional[str] = None,
        email_verified: bool = False
    ) -> Tuple[User, bool]:
        """
        STEP 4: Find or create user
        
        Returns:
            (user, is_new) - User object and whether it's newly created
        """
        
        # Try to find existing user
        user = self.find_by_google_id(google_id)
        
        if user:
            # Existing user - update last login
            logger.info(f'✓ Returning user: {email}')
            self.update_last_login(user.id)
            return user, False
        
        # New user - create in database
        import uuid
        
        user = User(
            id=str(uuid.uuid4()),
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
            email_verified=email_verified,
            created_at=datetime.now().isoformat(),
            last_login=datetime.now().isoformat()
        )
        
        self.users[user.id] = user
        
        logger.info(f'✓ New user created: {email}')
        
        return user, True
    
    def update_last_login(self, user_id: str):
        """Update user's last login time"""
        if user_id in self.users:
            self.users[user_id].last_login = datetime.now().isoformat()

# ============================================================================
# PART 7: JWT Token Management
# ============================================================================

class JWTManager:
    """Generate and verify JWT tokens"""
    
    def __init__(self, secret: str, algorithm: str = 'HS256'):
        self.secret = secret
        self.algorithm = algorithm
    
    def generate_token(
        self,
        user_id: str,
        email: str,
        name: str,
        picture: Optional[str] = None,
        expiration_hours: int = 24
    ) -> str:
        """
        STEP 5: Generate JWT token for our app
        
        This is the token YOUR APP uses, not Google's token.
        
        JWT contains:
        - user_id: YOUR user ID (not Google's)
        - email: User's email
        - name: User's name
        - picture: Profile picture
        - iat: Issued at (now)
        - exp: Expires at (now + hours)
        """
        
        logger.info(f'Generating JWT for user: {email}')
        
        now = datetime.utcnow()
        expiration = now + timedelta(hours=expiration_hours)
        
        payload = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'picture': picture,
            'iat': now.timestamp(),
            'exp': expiration.timestamp()
        }
        
        try:
            token = jwt.encode(
                payload,
                self.secret,
                algorithm=self.algorithm
            )
        except Exception as e:
            logger.error(f'JWT generation failed: {e}')
            raise JWTGenerationError('Failed to generate token')
        
        logger.info(f'✓ JWT generated (expires in {expiration_hours}h)')
        
        return token
    
    def verify_token(self, token: str) -> dict:
        """
        Verify and decode JWT token
        
        Called on each request to verify token is valid and not expired
        """
        
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning('Token expired')
            raise HTTPException(status_code=401, detail='Token expired')
        except jwt.InvalidTokenError:
            logger.warning('Invalid token')
            raise HTTPException(status_code=401, detail='Invalid token')

# ============================================================================
# PART 8: State Management (CSRF)
# ============================================================================

class StateStore:
    """Store and validate OAuth state (CSRF protection)"""
    
    def __init__(self):
        self.states: dict = {}
    
    def generate(self) -> str:
        """Generate random state string"""
        import secrets
        state = secrets.token_urlsafe(32)
        self.states[state] = {
            'created_at': datetime.now(),
            'used': False
        }
        logger.info(f'State generated: {state[:20]}...')
        return state
    
    def validate(self, state: str) -> bool:
        """Validate state and mark as used"""
        
        if state not in self.states:
            logger.warning(f'Unknown state (CSRF attack?)')
            return False
        
        state_data = self.states[state]
        
        # Check expiration (10 minutes)
        age = datetime.now() - state_data['created_at']
        if age > timedelta(minutes=10):
            logger.warning(f'State expired ({age.total_seconds()}s old)')
            return False
        
        # Check if already used
        if state_data['used']:
            logger.error(f'State already used (replay attack?)')
            return False
        
        # Mark as used
        state_data['used'] = True
        logger.info(f'✓ State validated')
        
        return True

# ============================================================================
# PART 9: Complete Callback Handler
# ============================================================================

class CallbackHandler:
    """Handle OAuth callback from Google"""
    
    def __init__(
        self,
        token_exchanger: TokenExchanger,
        user_extractor: UserInfoExtractor,
        user_manager: UserManager,
        jwt_manager: JWTManager,
        state_store: StateStore,
        config: Config
    ):
        self.token_exchanger = token_exchanger
        self.user_extractor = user_extractor
        self.user_manager = user_manager
        self.jwt_manager = jwt_manager
        self.state_store = state_store
        self.config = config
    
    async def handle(
        self,
        code: str,
        state: str,
        request: Request
    ) -> Tuple[User, str]:
        """
        Handle OAuth callback - 6 steps
        
        Returns:
            (user, jwt_token)
        """
        
        logger.info('=' * 60)
        logger.info('OAuth Callback Handler Starting')
        logger.info('=' * 60)
        
        # STEP 1: Validate state (CSRF protection)
        logger.info('\nSTEP 1: Validating state (CSRF protection)')
        cookie_state = request.cookies.get('oauth_state')
        
        if not cookie_state:
            logger.error('State cookie missing')
            raise HTTPException(status_code=400, detail='CSRF check failed')
        
        if cookie_state != state:
            logger.error(f'State mismatch: {cookie_state} != {state}')
            raise HTTPException(status_code=400, detail='CSRF check failed')
        
        if not self.state_store.validate(cookie_state):
            logger.error('State validation failed')
            raise HTTPException(status_code=400, detail='CSRF check failed')
        
        # STEP 2: Exchange code for token
        logger.info('\nSTEP 2: Exchanging code for Google token')
        try:
            token_response = await self.token_exchanger.exchange_code_for_token(
                code,
                self.config.GOOGLE_REDIRECT_URI
            )
        except TokenExchangeError as e:
            logger.error(f'Token exchange error: {e}')
            raise HTTPException(status_code=400, detail=str(e))
        
        # STEP 3: Extract user info
        logger.info('\nSTEP 3: Extracting user information')
        try:
            user_info = self.user_extractor.decode_id_token(
                token_response['id_token']
            )
        except UserInfoError as e:
            logger.error(f'User info extraction error: {e}')
            raise HTTPException(status_code=400, detail=str(e))
        
        # STEP 4: Find or create user
        logger.info('\nSTEP 4: Finding or creating user')
        user, is_new = self.user_manager.find_or_create(
            google_id=user_info['google_id'],
            email=user_info['email'],
            name=user_info['name'],
            picture=user_info['picture'],
            email_verified=user_info['email_verified']
        )
        
        # STEP 5: Generate JWT token
        logger.info('\nSTEP 5: Generating JWT token')
        try:
            jwt_token = self.jwt_manager.generate_token(
                user_id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
                expiration_hours=self.config.JWT_EXPIRATION_HOURS
            )
        except JWTGenerationError as e:
            logger.error(f'JWT generation error: {e}')
            raise HTTPException(status_code=500, detail=str(e))
        
        logger.info('\n' + '=' * 60)
        logger.info('✓ OAuth Callback Completed Successfully')
        logger.info('=' * 60)
        logger.info(f'User: {user.email}')
        logger.info(f'New user: {is_new}')
        logger.info('=' * 60 + '\n')
        
        return user, jwt_token

# ============================================================================
# PART 10: FastAPI Integration
# ============================================================================

app = FastAPI()

# Initialize components
Config.validate()
token_exchanger = TokenExchanger(Config)
user_extractor = UserInfoExtractor()
user_manager = UserManager()
jwt_manager = JWTManager(Config.JWT_SECRET, Config.JWT_ALGORITHM)
state_store = StateStore()

callback_handler = CallbackHandler(
    token_exchanger,
    user_extractor,
    user_manager,
    jwt_manager,
    state_store,
    Config
)

@app.get('/auth/google/callback')
async def google_callback(
    code: str,
    state: str,
    request: Request
):
    """
    Handle OAuth callback from Google
    
    Google redirects here with:
    - code: Authorization code (single-use)
    - state: State parameter (CSRF protection)
    """
    
    try:
        # Handle callback (6 steps)
        user, jwt_token = await callback_handler.handle(code, state, request)
        
        # STEP 6: Set cookie and redirect
        response = RedirectResponse(url='/dashboard', status_code=302)
        
        response.set_cookie(
            'access_token',
            jwt_token,
            max_age=Config.SESSION_TIMEOUT_SECONDS,
            httponly=True,  # Prevent XSS
            secure=False,   # Set to True in production (HTTPS)
            samesite='strict'  # CSRF protection
        )
        
        # Clear oauth_state cookie
        response.delete_cookie('oauth_state')
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Unexpected error in callback: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')

@app.get('/dashboard')
async def dashboard(request: Request):
    """Protected route - requires valid JWT"""
    
    # Get JWT from cookie
    jwt_token = request.cookies.get('access_token')
    
    if not jwt_token:
        raise HTTPException(status_code=401, detail='Not logged in')
    
    # Verify JWT
    try:
        payload = jwt_manager.verify_token(jwt_token)
    except HTTPException:
        raise
    
    # Get user
    user = user_manager.find_by_google_id(payload.get('google_id'))
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
    """Logout - clear session"""
    response.delete_cookie('access_token')
    return {'message': 'Logged out'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
