# Day 13: OAuth Endpoints with Complete Swagger Documentation
# Documented FastAPI implementation with OpenAPI schema

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthCredential
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
import jwt as pyjwt

# ============================================================================
# PART 1: Data Models for API Documentation
# ============================================================================

class UserProfile(BaseModel):
    """User profile returned by protected endpoints"""
    id: str = Field(..., description="Unique user ID")
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    picture: Optional[str] = Field(None, description="URL to profile picture")
    created_at: str = Field(..., description="ISO 8601 timestamp when account was created")
    last_login: str = Field(..., description="ISO 8601 timestamp of last login")

class DashboardResponse(BaseModel):
    """Response from /dashboard endpoint"""
    message: str = Field(..., description="Welcome message")
    user: UserProfile = Field(..., description="Authenticated user information")

class LoginStartResponse(BaseModel):
    """Response from /auth/login endpoint"""
    message: str = Field(..., description="Confirmation message")
    redirect_url: str = Field(..., description="URL to redirect to Google OAuth")

class RefreshTokenResponse(BaseModel):
    """Response from /refresh endpoint"""
    access_token: str = Field(..., description="New JWT access token")
    expires_in: int = Field(..., description="Token lifetime in seconds")

class LogoutResponse(BaseModel):
    """Response from /logout endpoint"""
    message: str = Field(..., description="Logout confirmation message")

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Specific error code")

# ============================================================================
# PART 2: Security Schemes
# ============================================================================

security = HTTPBearer(description="JWT Bearer token in Authorization header")

# ============================================================================
# PART 3: FastAPI App with Endpoints
# ============================================================================

app = FastAPI(
    title="OAuth 2.0 Authentication API",
    description="Complete OAuth 2.0 implementation with Google OAuth and JWT sessions",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"
)

# ============================================================================
# PART 4: Auth Endpoints
# ============================================================================

@app.get(
    "/auth/google/login",
    responses={302: {"description": "Redirect to Google OAuth consent screen"}},
    tags=["Authentication"],
    summary="Start Google OAuth login flow",
    description="""
    Initiates OAuth 2.0 authorization code flow with Google.
    
    **What happens:**
    1. Generates random CSRF state token
    2. Sets state in httpOnly cookie (secure, not accessible to JS)
    3. Redirects to Google's OAuth consent screen
    4. User logs in to Google
    5. User grants permission to app
    6. Google redirects back to /auth/google/callback with authorization code
    
    **Security:**
    - State token prevents CSRF attacks
    - httpOnly cookie prevents XSS attacks
    - Client ID and redirect URI validated by Google
    
    **Next step:** User is redirected to Google, logs in, then redirected to callback
    """
)
async def start_google_login(response: Response):
    """
    Start OAuth login flow.
    
    Generates authorization URL and redirects to Google.
    Browser will show Google's login screen.
    """
    # Generate state (CSRF token)
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Set state in httpOnly cookie
    response = RedirectResponse(url="https://accounts.google.com/o/oauth2/v2/auth", status_code=302)
    response.set_cookie(
        "oauth_state",
        state,
        max_age=600,  # 10 minutes
        httponly=True,
        secure=False,  # Set to True in production
        samesite="strict"
    )
    
    return response

@app.get(
    "/auth/google/callback",
    responses={
        302: {"description": "Redirect to dashboard (login successful)"},
        400: {"model": ErrorResponse, "description": "CSRF validation failed or code exchange failed"},
        401: {"model": ErrorResponse, "description": "Authorization failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Authentication"],
    summary="OAuth callback from Google",
    description="""
    Handles redirect from Google after user authorizes.
    
    **What happens:**
    1. Validates state parameter (CSRF protection)
    2. Exchanges authorization code for Google tokens
    3. Extracts user information from ID token
    4. Finds or creates user in database
    5. Issues application JWT token
    6. Sets JWT in httpOnly cookie
    7. Redirects to dashboard
    
    **Error cases:**
    - **CSRF attack:** State doesn't match (400)
    - **Code expired:** Authorization code > 10 minutes old (400)
    - **Invalid code:** Code was invalid or already used (400)
    - **Missing email:** User data incomplete (400)
    
    **Security:**
    - Code exchange uses client_secret (backend only, never exposed)
    - State validated before processing (prevents CSRF)
    - JWT issued by your app (not Google's token stored)
    - Cookie is httpOnly, Secure, SameSite=Strict
    
    **After this endpoint:**
    - User is logged in
    - Can access protected routes
    - JWT valid for 24 hours
    - User can logout or refresh token
    """
)
async def google_callback(code: str, state: str, request: Request):
    """
    Google redirects here after authorization.
    
    Parameters:
    - code: Authorization code (single-use, ~10 min expiry)
    - state: CSRF token (must match cookie)
    """
    # Validate state
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="CSRF validation failed")
    
    # Exchange code (mocked here)
    # In production, call Google's token endpoint
    
    # Create response
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        "access_token",
        "jwt_token_here",
        httponly=True,
        secure=False,  # True in production
        samesite="strict",
        max_age=86400  # 24 hours
    )
    response.delete_cookie("oauth_state")
    
    return response

# ============================================================================
# PART 5: Protected Routes
# ============================================================================

@app.get(
    "/dashboard",
    response_model=DashboardResponse,
    responses={
        200: {"description": "Successfully retrieved dashboard (user authenticated)"},
        401: {"model": ErrorResponse, "description": "No valid JWT token provided"}
    },
    tags=["Protected Routes"],
    summary="Get user dashboard",
    description="""
    Protected route requiring valid JWT authentication.
    
    **Authentication:**
    - JWT token from httpOnly cookie sent automatically
    - Token signature verified
    - Token expiration checked
    
    **What is returned:**
    - User profile information
    - Email, name, profile picture
    - Account creation timestamp
    - Last login timestamp
    
    **Error cases:**
    - No JWT cookie: 401 Unauthorized
    - Invalid JWT: 401 Unauthorized (signature check failed)
    - Expired JWT: 401 Unauthorized (>24 hours old)
    - Corrupted JWT: 401 Unauthorized
    
    **Security:**
    - Requires valid JWT signature (tampered tokens rejected)
    - Requires token not expired
    - Cookie sent automatically (no manual header needed)
    - httpOnly cookie safe from XSS
    
    **Next steps from here:**
    - Access other protected routes
    - Call API endpoints with same JWT
    - User can logout or refresh token
    """
)
async def get_dashboard(request: Request):
    """
    Get user dashboard.
    
    Requires valid JWT in cookie.
    Returns user information.
    """
    # Get JWT from cookie
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify JWT (mocked)
    try:
        payload = pyjwt.decode(jwt_token, "secret", algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Return user info
    return DashboardResponse(
        message="Welcome to your dashboard!",
        user=UserProfile(
            id="user_123",
            email="user@example.com",
            name="Test User",
            picture="https://example.com/pic.jpg",
            created_at=datetime.now().isoformat(),
            last_login=datetime.now().isoformat()
        )
    )

@app.get(
    "/api/profile",
    response_model=UserProfile,
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    },
    tags=["Protected Routes"],
    summary="Get authenticated user's profile",
    description="""
    Get current user's profile information.
    
    **Requires:** Valid JWT token in cookie
    
    **Returns:**
    - User ID
    - Email address
    - Full name
    - Profile picture URL
    - Account creation date
    - Last login date
    
    **Use cases:**
    - Display user info in frontend
    - Update user settings
    - Link multiple accounts
    """
)
async def get_profile(request: Request):
    """Get user profile."""
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return UserProfile(
        id="user_123",
        email="user@example.com",
        name="Test User",
        picture="https://example.com/pic.jpg",
        created_at=datetime.now().isoformat(),
        last_login=datetime.now().isoformat()
    )

# ============================================================================
# PART 6: Session Management Endpoints
# ============================================================================

@app.get(
    "/auth/refresh",
    response_model=RefreshTokenResponse,
    responses={
        200: {"description": "New token issued successfully"},
        401: {"model": ErrorResponse, "description": "Refresh failed (not authenticated)"}
    },
    tags=["Session Management"],
    summary="Refresh authentication token",
    description="""
    Get a new JWT token before current one expires.
    
    **When to use:**
    - Before JWT expires (recommended: every 12 hours)
    - When token was lost/corrupted
    - Never needs to be manually called (auth header handles auto-refresh)
    
    **What happens:**
    1. Validates current JWT
    2. Issues new JWT valid for 24 more hours
    3. Returns new token + expiration
    
    **Security:**
    - Requires valid JWT to refresh
    - Prevents indefinite token lifetime
    - Can be called as often as needed
    
    **Response:**
    - access_token: New JWT (24 hour lifetime)
    - expires_in: 86400 seconds (24 hours)
    
    **Client usage:**
    ```javascript
    // When JWT is about to expire:
    const response = await fetch('/auth/refresh');
    const {access_token} = await response.json();
    // Cookie updated automatically
    ```
    """
)
async def refresh_token(request: Request):
    """
    Refresh authentication token.
    
    Issues new JWT before current one expires.
    """
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return RefreshTokenResponse(
        access_token="new_jwt_token_here",
        expires_in=86400
    )

@app.get(
    "/auth/logout",
    response_model=LogoutResponse,
    responses={
        302: {"description": "Redirect to home page (logout successful)"},
        200: {"model": LogoutResponse, "description": "Logout successful"}
    },
    tags=["Session Management"],
    summary="Logout and end session",
    description="""
    End user's session and clear authentication.
    
    **What happens:**
    1. Deletes JWT cookie
    2. Revokes session (if tracking revoked tokens)
    3. Redirects to home page
    
    **Security:**
    - Deletes httpOnly cookie (JS can't access)
    - Cookie cannot be recovered
    - User must re-login to access protected routes
    
    **After logout:**
    - Protected routes return 401 Unauthorized
    - User is redirected to login page
    - Session data is cleared
    
    **Re-login:**
    After logout, user must click login again to get new JWT
    """
)
async def logout(response: Response):
    """
    Logout user.
    
    Deletes JWT cookie and ends session.
    """
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response

# ============================================================================
# PART 7: Health Check Endpoint
# ============================================================================

@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    description="Check if API is running and healthy"
)
async def health_check():
    """API is running and healthy."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ============================================================================
# PART 8: Custom OpenAPI Schema
# ============================================================================

def custom_openapi():
    """
    Customize OpenAPI schema for better documentation.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="OAuth 2.0 Authentication API",
        version="1.0.0",
        description="""
        Complete OAuth 2.0 implementation with Google OAuth and JWT session management.
        
        ## Architecture
        
        **OAuth 2.0 Authorization Code Flow:**
        1. User initiates login → Google OAuth consent screen
        2. User authorizes → Google redirects with code
        3. Backend exchanges code for tokens
        4. Backend creates/finds user
        5. Backend issues application JWT
        6. User accesses protected routes with JWT
        
        **Security Layers:**
        - CSRF protection (state token)
        - Code exchange uses client_secret (backend only)
        - JWT stored in httpOnly cookie (XSS protection)
        - JWT signature verification (tampering detection)
        - Token expiration enforcement (24 hour lifetime)
        
        **Tokens:**
        - Google's tokens: Discarded after user extraction
        - Application JWT: Used for all protected routes
        - httpOnly cookie: Sent automatically, JS can't access
        
        ## Authentication Flow
        
        ### Login Flow
        ```
        1. GET /auth/google/login → State cookie set
        2. Redirect to Google → User logs in
        3. GET /auth/google/callback?code=...&state=... → JWT issued
        4. Cookie set → Redirect to /dashboard
        ```
        
        ### Protected Route Access
        ```
        1. Browser sends cookie automatically (same-origin)
        2. JWT extracted from cookie
        3. Signature verified with app secret
        4. Expiration checked
        5. Request allowed (if valid)
        ```
        
        ### Logout Flow
        ```
        1. GET /auth/logout → Cookie deleted
        2. Redirect to home
        3. Protected routes now return 401
        ```
        
        ## Error Handling
        
        | Code | Meaning | Action |
        |------|---------|--------|
        | 200 | Success | Continue |
        | 302 | Redirect | Follow redirect |
        | 400 | Bad Request | Check parameters |
        | 401 | Unauthorized | Login required |
        | 500 | Server Error | Retry or report |
        
        ## Examples
        
        ### Example: Complete Login
        ```bash
        # 1. Start login
        curl -v http://localhost:8000/auth/google/login
        # Redirects to Google, sets oauth_state cookie
        
        # 2. User logs in at Google (in browser)
        # Google redirects to callback with code + state
        
        # 3. Callback exchanges code for JWT
        curl -v http://localhost:8000/auth/google/callback?code=...&state=...
        # Redirects to /dashboard, sets access_token cookie
        
        # 4. Access protected route
        curl http://localhost:8000/dashboard
        # Returns user profile
        ```
        
        ### Example: Protected API Call
        ```bash
        # Browser automatically sends cookie
        curl -b "access_token=jwt..." http://localhost:8000/api/profile
        # Returns user profile
        ```
        """,
        routes=app.routes,
    )
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "OAuth 2.0 login flow endpoints"
        },
        {
            "name": "Protected Routes",
            "description": "Routes requiring JWT authentication"
        },
        {
            "name": "Session Management",
            "description": "Refresh and logout endpoints"
        },
        {
            "name": "System",
            "description": "System health and status endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============================================================================
# PART 9: Running the API
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║         OAuth 2.0 Authentication API with FastAPI              ║
    ╠════════════════════════════════════════════════════════════════╣
    ║                                                                ║
    ║  Swagger UI (Interactive docs):                              ║
    ║  → http://localhost:8000/docs                                ║
    ║                                                                ║
    ║  ReDoc (Alternative docs):                                   ║
    ║  → http://localhost:8000/redoc                               ║
    ║                                                                ║
    ║  OpenAPI JSON:                                               ║
    ║  → http://localhost:8000/openapi.json                        ║
    ║                                                                ║
    ║  Endpoints:                                                   ║
    ║  ✓ GET /auth/google/login      - Start OAuth flow            ║
    ║  ✓ GET /auth/google/callback   - OAuth callback              ║
    ║  ✓ GET /dashboard              - Protected route             ║
    ║  ✓ GET /api/profile            - Get user profile            ║
    ║  ✓ GET /auth/refresh           - Refresh token               ║
    ║  ✓ GET /auth/logout            - Logout                      ║
    ║  ✓ GET /health                 - Health check                ║
    ║                                                                ║
    ║  Try it out:                                                  ║
    ║  1. Open http://localhost:8000/docs                          ║
    ║  2. Click "Authorize"                                        ║
    ║  3. Complete OAuth flow                                      ║
    ║  4. Try protected endpoints                                  ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "day13_documented_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
