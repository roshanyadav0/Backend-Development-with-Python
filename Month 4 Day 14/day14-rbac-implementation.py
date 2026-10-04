# Day 14: Role-Based Access Control (RBAC) Implementation
# Updated models, JWT with role, decorators, and endpoints

import jwt as pyjwt
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps
from uuid import uuid4, UUID

from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Enum as SQLEnum, Index
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ============================================================================
# PART 1: Role Enum & Model
# ============================================================================

class RoleEnum(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    MEMBER = "member"

Base = declarative_base()

class Member(Base):
    """Member model with role field"""
    __tablename__ = "members"
    
    id: UUID = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    google_id: str = Column(String(255), unique=True, nullable=False)
    
    # NEW: Role field
    role: str = Column(
        String(20),
        nullable=False,
        default=RoleEnum.MEMBER,
        index=True  # Index for fast queries
    )
    
    created_at: datetime = Column(datetime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(datetime, default=datetime.utcnow, nullable=False)
    
    # Utility properties
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == RoleEnum.ADMIN
    
    @property
    def is_member(self) -> bool:
        """Check if user is member"""
        return self.role == RoleEnum.MEMBER

# ============================================================================
# PART 2: Pydantic Models (API)
# ============================================================================

class CurrentUser(BaseModel):
    """Current authenticated user from JWT"""
    user_id: str = Field(..., description="User ID from JWT")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    role: str = Field(..., description="User role (admin or member)")
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == RoleEnum.ADMIN
    
    @property
    def is_member(self) -> bool:
        """Check if user is member"""
        return self.role == RoleEnum.MEMBER

class MemberProfile(BaseModel):
    """Member profile for API responses"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="Email")
    name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role")
    created_at: str = Field(..., description="Account creation date")
    is_admin: bool = Field(..., description="Whether user is admin")

class AdminOnlyResponse(BaseModel):
    """Response that only admins can see"""
    message: str = Field(..., description="Message")
    admin_email: str = Field(..., description="Admin who performed action")

# ============================================================================
# PART 3: JWT Manager with Role
# ============================================================================

class Config:
    """Configuration"""
    JWT_SECRET = "your-secret-key"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

class JWTManager:
    """Generate and verify JWT tokens with role"""
    
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm
    
    def generate_token(
        self,
        user_id: str,
        email: str,
        name: str,
        role: str,  # NEW: Include role
        expiration_hours: int = 24
    ) -> str:
        """
        Generate JWT token with role.
        
        Args:
            user_id: User's unique ID
            email: User's email
            name: User's name
            role: User's role (admin, member)
            expiration_hours: Token lifetime in hours
        
        Returns:
            JWT token string
        """
        
        now = datetime.utcnow()
        expiration = now + timedelta(hours=expiration_hours)
        
        payload = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,  # NEW: Include role in JWT
            'iat': now.timestamp(),
            'exp': expiration.timestamp()
        }
        
        token = pyjwt.encode(
            payload,
            self.secret,
            algorithm=self.algorithm
        )
        
        logger.info(f"JWT issued for {email} (role: {role})")
        
        return token
    
    def verify_token(self, token: str) -> dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Token payload (includes role)
        
        Raises:
            jwt.ExpiredSignatureError: Token expired
            jwt.InvalidTokenError: Token invalid
        """
        
        try:
            payload = pyjwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            return payload
        except pyjwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise
        except pyjwt.InvalidTokenError:
            logger.warning("Invalid token")
            raise

# ============================================================================
# PART 4: Extract Current User (with Role)
# ============================================================================

async def get_current_user(request: Request) -> CurrentUser:
    """
    Extract current user from JWT cookie.
    
    Returns: CurrentUser object with role
    Raises: HTTPException(401) if not authenticated
    """
    
    jwt_token = request.cookies.get("access_token")
    
    if not jwt_token:
        logger.warning("Request without access_token")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    try:
        jwt_manager = JWTManager(Config.JWT_SECRET)
        payload = jwt_manager.verify_token(jwt_token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
    return CurrentUser(
        user_id=payload['user_id'],
        email=payload['email'],
        name=payload['name'],
        role=payload.get('role', RoleEnum.MEMBER)  # NEW: Extract role
    )

# ============================================================================
# PART 5: Role-Based Access Control Decorators
# ============================================================================

def require_role(*allowed_roles: str):
    """
    Decorator to require specific role(s).
    
    Usage:
        @require_role("admin")  # Only admin
        @require_role("admin", "moderator")  # Admin OR moderator
    
    Args:
        allowed_roles: Role name(s) that are allowed
    
    Raises:
        HTTPException(403) if user doesn't have required role
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: CurrentUser, **kwargs):
            if current_user.role not in allowed_roles:
                logger.warning(
                    f"Access denied for {current_user.email}: "
                    f"requires {allowed_roles}, has {current_user.role}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_admin(func):
    """
    Shorthand decorator to require admin role.
    
    Usage:
        @require_admin
        async def admin_endpoint(current_user: CurrentUser):
            pass
    """
    return require_role(RoleEnum.ADMIN)(func)

def require_member(func):
    """
    Shorthand decorator to require member role (or admin).
    
    Members are people with explicit member role.
    Admins can also access member endpoints.
    
    Usage:
        @require_member
        async def member_endpoint(current_user: CurrentUser):
            pass
    """
    return require_role(RoleEnum.ADMIN, RoleEnum.MEMBER)(func)

# ============================================================================
# PART 6: Library API Endpoints (Example)
# ============================================================================

app = FastAPI()
jwt_manager = JWTManager(Config.JWT_SECRET)

# ─────────────────────────────────────────────────────────────────────────
# Public Endpoints (No auth needed)
# ─────────────────────────────────────────────────────────────────────────

@app.get("/api/books", tags=["Books"])
async def list_books():
    """
    List all books (public).
    Anyone can browse books.
    """
    return {
        "books": [
            {"id": "1", "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
            {"id": "2", "title": "1984", "author": "George Orwell"},
        ]
    }

# ─────────────────────────────────────────────────────────────────────────
# Member Endpoints (Member or Admin)
# ─────────────────────────────────────────────────────────────────────────

@app.get("/api/my/profile", tags=["Member"])
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current user's profile.
    Requires: Authentication
    """
    return MemberProfile(
        id=current_user.user_id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=datetime.now().isoformat(),
        is_admin=current_user.is_admin
    )

@app.post("/api/books/{book_id}/borrow", tags=["Member"])
@require_member
async def borrow_book(
    book_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Borrow a book.
    Requires: Member or Admin
    Limit: 5 books per member
    """
    logger.info(f"{current_user.email} borrowed book {book_id}")
    
    return {
        "message": "Book borrowed",
        "book_id": book_id,
        "member": current_user.email,
        "due_date": (datetime.now() + timedelta(days=14)).isoformat()
    }

@app.get("/api/my/loans", tags=["Member"])
async def list_my_loans(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List your own loans.
    Requires: Authentication
    """
    return {
        "member": current_user.email,
        "loans": [
            {
                "id": "L1",
                "book_id": "1",
                "borrowed_date": "2024-01-10",
                "due_date": "2024-01-24"
            }
        ]
    }

@app.put("/api/my/profile", tags=["Member"])
async def update_my_profile(
    name: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update your own profile.
    Requires: Authentication
    """
    logger.info(f"{current_user.email} updated profile")
    
    return {
        "message": "Profile updated",
        "email": current_user.email,
        "name": name,
        "role": current_user.role
    }

# ─────────────────────────────────────────────────────────────────────────
# Admin Endpoints (Admin only)
# ─────────────────────────────────────────────────────────────────────────

@app.post("/api/books", tags=["Admin"])
@require_admin
async def create_book(
    title: str,
    author: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new book.
    Requires: Admin
    """
    logger.info(f"Admin {current_user.email} created book: {title}")
    
    return AdminOnlyResponse(
        message=f"Book '{title}' created",
        admin_email=current_user.email
    )

@app.put("/api/books/{book_id}", tags=["Admin"])
@require_admin
async def update_book(
    book_id: str,
    title: str,
    author: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a book.
    Requires: Admin
    """
    logger.info(f"Admin {current_user.email} updated book {book_id}")
    
    return AdminOnlyResponse(
        message=f"Book {book_id} updated",
        admin_email=current_user.email
    )

@app.delete("/api/books/{book_id}", tags=["Admin"])
@require_admin
async def delete_book(
    book_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a book.
    Requires: Admin
    """
    logger.info(f"Admin {current_user.email} deleted book {book_id}")
    
    return AdminOnlyResponse(
        message=f"Book {book_id} deleted",
        admin_email=current_user.email
    )

@app.get("/api/admin/members", tags=["Admin"])
@require_admin
async def list_all_members(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all members.
    Requires: Admin
    """
    logger.info(f"Admin {current_user.email} viewed all members")
    
    return {
        "members": [
            {
                "id": "M1",
                "email": "alice@example.com",
                "name": "Alice",
                "role": "member",
                "loans": 2
            },
            {
                "id": "M2",
                "email": "bob@example.com",
                "name": "Bob",
                "role": "member",
                "loans": 1
            }
        ]
    }

@app.get("/api/admin/loans", tags=["Admin"])
@require_admin
async def list_all_loans(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all loans (admin view).
    Requires: Admin
    """
    logger.info(f"Admin {current_user.email} viewed all loans")
    
    return {
        "total_loans": 42,
        "overdue": 3,
        "loans": [
            {
                "id": "L1",
                "member": "alice@example.com",
                "book_id": "1",
                "due_date": "2024-01-24",
                "overdue": False
            }
        ]
    }

@app.post("/api/admin/members/{member_id}/promote", tags=["Admin"])
@require_admin
async def promote_to_admin(
    member_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Promote a member to admin.
    Requires: Admin
    """
    logger.info(f"Admin {current_user.email} promoted member {member_id}")
    
    return AdminOnlyResponse(
        message=f"Member {member_id} promoted to admin",
        admin_email=current_user.email
    )

@app.get("/api/admin/dashboard", tags=["Admin"])
@require_admin
async def admin_dashboard(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Admin dashboard with statistics.
    Requires: Admin
    """
    logger.info(f"Admin {current_user.email} viewed dashboard")
    
    return {
        "admin": current_user.email,
        "statistics": {
            "total_books": 256,
            "total_members": 42,
            "active_loans": 89,
            "overdue_loans": 3
        },
        "last_updated": datetime.now().isoformat()
    }

# ============================================================================
# PART 7: Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom error handler for HTTP exceptions"""
    
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

# ============================================================================
# PART 8: Running the API
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        RBAC Implementation - Library API                   ║
    ║                                                             ║
    ║  Swagger UI: http://localhost:8000/docs                   ║
    ║  ReDoc: http://localhost:8000/redoc                       ║
    ║                                                             ║
    ║  Test Endpoints:                                          ║
    ║  ✓ GET /api/books                 (public)               ║
    ║  ✓ GET /api/my/profile            (auth required)        ║
    ║  ✓ POST /api/books/{id}/borrow    (member+)              ║
    ║  ✓ POST /api/books                (admin only)           ║
    ║  ✓ GET /api/admin/members         (admin only)           ║
    ║  ✓ GET /api/admin/dashboard       (admin only)           ║
    ║                                                             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "day14_rbac_implementation:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
