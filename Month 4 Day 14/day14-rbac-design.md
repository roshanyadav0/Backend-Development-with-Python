# Day 14: Role-Based Access Control (RBAC) — Role Model & Permissions Design

---

## 🎯 What is RBAC?

```
RBAC = Role-Based Access Control

Instead of:
  if user_id == admin_id:
      allow

Do this:
  if user.role == "admin":
      allow

Simpler, scales better, cleaner code.
```

---

## Part 1: The Role Model

### Database Schema

```sql
CREATE TABLE members (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    
    -- NEW: Role field
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    CHECK (role IN ('admin', 'member')),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX (email),
    INDEX (role)
);
```

### Python Model

```python
from enum import Enum
from sqlalchemy import Column, String, Enum as SQLEnum

class RoleEnum(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    MEMBER = "member"

class Member(Base):
    __tablename__ = "members"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    google_id: Mapped[str] = mapped_column(String(255), unique=True)
    
    # NEW: Role field
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum),
        default=RoleEnum.MEMBER,
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Utility
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == RoleEnum.ADMIN
    
    @property
    def is_member(self) -> bool:
        """Check if user is member"""
        return self.role == RoleEnum.MEMBER
```

---

## Part 2: JWT with Role Claims

### JWT Payload (Before)
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "alice@example.com",
  "name": "Alice Smith",
  "iat": 1704067200,
  "exp": 1704153600
}
```

### JWT Payload (After - With Role)
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "alice@example.com",
  "name": "Alice Smith",
  "role": "admin",
  "iat": 1704067200,
  "exp": 1704153600
}
```

### JWT Generation (Code)

```python
class JWTManager:
    def generate_token(
        self,
        user_id: str,
        email: str,
        name: str,
        role: str,  # NEW
        expiration_hours: int = 24
    ) -> str:
        """Generate JWT with role"""
        
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
        
        token = jwt.encode(
            payload,
            self.secret,
            algorithm=self.algorithm
        )
        
        return token
```

---

## Part 3: Extract Role from JWT

### Updated get_current_user

```python
from pydantic import BaseModel
from typing import Optional

class CurrentUser(BaseModel):
    """Current authenticated user from JWT"""
    user_id: str
    email: str
    name: str
    role: str  # NEW
    
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    @property
    def is_member(self) -> bool:
        return self.role == "member"

async def get_current_user(request: Request) -> CurrentUser:
    """
    Extract current user from JWT cookie.
    
    Returns: CurrentUser with role
    Raises: HTTPException(401) if not authenticated
    """
    
    jwt_token = request.cookies.get("access_token")
    
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(
            jwt_token,
            Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return CurrentUser(
        user_id=payload['user_id'],
        email=payload['email'],
        name=payload['name'],
        role=payload.get('role', 'member')  # NEW: Extract role
    )
```

---

## Part 4: Role-Based Permission Decorator

### Permission Decorator

```python
from functools import wraps
from typing import Callable, List

def require_role(*allowed_roles: str):
    """
    Decorator to require specific role(s).
    
    Usage:
        @require_role("admin")  # Only admin
        @require_role("admin", "moderator")  # Admin OR moderator
    """
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: CurrentUser, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"This action requires one of: {', '.join(allowed_roles)}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_admin(func: Callable):
    """Shorthand: require admin role"""
    return require_role("admin")(func)
```

### Usage Examples

```python
@app.post("/api/admin/users")
@require_admin
async def create_user(
    user_data: UserCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Only admins can create users"""
    # Admin-only logic
    pass

@app.post("/api/books/{book_id}/borrow")
@require_role("admin", "member")
async def borrow_book(
    book_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Admin and members can borrow books"""
    # Borrow logic
    pass
```

---

## Part 5: Library API Permissions Design

### Use Case: Library Management System

#### Role Hierarchy
```
ADMIN
├─ Full access to everything
├─ Manage books (CRUD)
├─ Manage members (CRUD)
├─ View all loans
├─ Generate reports
└─ System administration

MEMBER
├─ Limited access
├─ Browse books
├─ Borrow books (limit: 5)
├─ View own loans
├─ Edit own profile
└─ No admin functions
```

#### Permission Matrix

```
┌──────────────────────┬─────────┬────────┐
│ Action               │ Admin   │ Member │
├──────────────────────┼─────────┼────────┤
│ List all books       │ ✓ View  │ ✓ View │
│ Search books         │ ✓       │ ✓      │
│ Create book          │ ✓       │ ✗      │
│ Edit book            │ ✓       │ ✗      │
│ Delete book          │ ✓       │ ✗      │
│ Set book as lost     │ ✓       │ ✗      │
├──────────────────────┼─────────┼────────┤
│ Borrow book          │ ✓       │ ✓      │
│ Return book          │ ✓       │ ✓ own  │
│ View all loans       │ ✓       │ ✗      │
│ View own loans       │ ✓       │ ✓      │
│ Mark as overdue      │ ✓       │ ✗      │
├──────────────────────┼─────────┼────────┤
│ List all members     │ ✓       │ ✗      │
│ View member profile  │ ✓       │ ✓ own  │
│ Edit member          │ ✓       │ ✓ own  │
│ Delete member        │ ✓       │ ✗      │
│ Suspend member       │ ✓       │ ✗      │
├──────────────────────┼─────────┼────────┤
│ View reports         │ ✓       │ ✗      │
│ Generate reports     │ ✓       │ ✗      │
│ System settings      │ ✓       │ ✗      │
└──────────────────────┴─────────┴────────┘
```

### Endpoint Design with Roles

#### Book Management Endpoints

```python
# Public (no auth needed)
@app.get("/api/books")
async def list_books():
    """Anyone can browse books"""
    pass

@app.get("/api/books/{book_id}")
async def get_book(book_id: str):
    """Anyone can view book details"""
    pass

# Members only
@app.post("/api/books/{book_id}/borrow")
@require_role("admin", "member")
async def borrow_book(
    book_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Borrow a book (max 5 per member)"""
    pass

@app.post("/api/loans/{loan_id}/return")
@require_role("admin", "member")
async def return_book(
    loan_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Return a borrowed book"""
    pass

# Admin only
@app.post("/api/books")
@require_admin
async def create_book(
    book_data: BookCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create new book (admin only)"""
    pass

@app.put("/api/books/{book_id}")
@require_admin
async def update_book(
    book_id: str,
    book_data: BookUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update book (admin only)"""
    pass

@app.delete("/api/books/{book_id}")
@require_admin
async def delete_book(
    book_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete book (admin only)"""
    pass

@app.get("/api/admin/loans")
@require_admin
async def list_all_loans(
    current_user: CurrentUser = Depends(get_current_user)
):
    """View all loans (admin only)"""
    pass

@app.get("/api/admin/members")
@require_admin
async def list_all_members(
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all members (admin only)"""
    pass

# Member-only (own resource)
@app.get("/api/my/loans")
async def list_my_loans(
    current_user: CurrentUser = Depends(get_current_user)
):
    """View your own loans"""
    pass

@app.get("/api/my/profile")
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user)
):
    """View your own profile"""
    pass

@app.put("/api/my/profile")
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update your own profile"""
    pass
```

#### Admin Dashboard Endpoints

```python
@app.get("/api/admin/dashboard")
@require_admin
async def admin_dashboard(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Admin dashboard with statistics"""
    return {
        "total_books": count_books(),
        "total_members": count_members(),
        "active_loans": count_active_loans(),
        "overdue_loans": count_overdue_loans(),
        "last_updated": datetime.now()
    }

@app.get("/api/admin/reports/books")
@require_admin
async def books_report(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Book inventory report"""
    pass

@app.get("/api/admin/reports/loans")
@require_admin
async def loans_report(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Loan statistics report"""
    pass

@app.post("/api/admin/members/{member_id}/suspend")
@require_admin
async def suspend_member(
    member_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Suspend a member account"""
    pass
```

---

## Part 6: Error Responses by Role

### 401 Unauthorized (Not logged in)
```json
{
  "detail": "Not authenticated",
  "status_code": 401
}
```

### 403 Forbidden (Logged in but insufficient role)
```json
{
  "detail": "This action requires one of: admin",
  "status_code": 403
}
```

### 404 Not Found (Resource doesn't exist)
```json
{
  "detail": "Book not found",
  "status_code": 404
}
```

### Security Rule
```
Never reveal why access was denied to attackers.

BAD:  "401: Not admin. Only admins can delete books"
      (Reveals the action exists)

GOOD: "403: Insufficient permissions"
      (Doesn't reveal what the action is)
```

---

## Part 7: Checking Owner (Own Resource)

Sometimes you need to check both role AND resource ownership.

### Pattern: Check Owner

```python
async def check_owner_or_admin(
    resource_id: str,
    current_user: CurrentUser
) -> bool:
    """
    Check if user is:
    - Admin (can access anything), OR
    - Owner of the resource
    """
    
    if current_user.is_admin:
        return True
    
    # Check if user owns this resource
    resource = db.get(resource_id)
    if resource and resource.owner_id == current_user.user_id:
        return True
    
    return False
```

### Usage in Endpoint

```python
@app.put("/api/my/profile/{member_id}")
async def update_member_profile(
    member_id: str,
    profile_data: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update member profile (own profile or admin)"""
    
    # Check: is user admin OR owner of profile?
    if not await check_owner_or_admin(member_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="Cannot modify this resource"
        )
    
    # Safe to update
    member = db.get_member(member_id)
    member.update(profile_data)
    db.commit()
    
    return member
```

---

## Part 8: Role Hierarchy (For Future)

If you add more roles later:

```python
class RoleEnum(str, Enum):
    """User roles with hierarchy"""
    SUPER_ADMIN = "super_admin"  # Full access
    ADMIN = "admin"              # Manage books & members
    LIBRARIAN = "librarian"      # Manage books, view loans
    MEMBER = "member"            # Limited: borrow/return
    GUEST = "guest"              # View only

# Permission helper
ROLE_PERMISSIONS = {
    "super_admin": ["all"],
    "admin": ["manage_books", "manage_members", "view_reports"],
    "librarian": ["manage_books", "view_loans"],
    "member": ["borrow_books", "view_own_loans"],
    "guest": ["view_books"]
}

def has_permission(user_role: str, required_permission: str) -> bool:
    """Check if role has permission"""
    if user_role not in ROLE_PERMISSIONS:
        return False
    
    permissions = ROLE_PERMISSIONS[user_role]
    return "all" in permissions or required_permission in permissions
```

---

## Part 9: Default Role Assignment

### On User Creation (OAuth Callback)

```python
async def google_callback(code: str, state: str, request: Request):
    """Handle Google callback"""
    
    # ... validate state, exchange code, get user info ...
    
    # Find or create user
    user = user_db.find_by_google_id(user_info['google_id'])
    
    if not user:
        # NEW USER: Assign default role
        user = user_db.create_user(
            google_id=user_info['google_id'],
            email=user_info['email'],
            name=user_info['name'],
            role="member"  # Default role
        )
    
    # Issue JWT with role
    jwt_token = jwt_manager.generate_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=user.role  # Include role
    )
    
    return response_with_jwt(jwt_token)
```

### Promote User to Admin (Admin-only endpoint)

```python
@app.post("/api/admin/members/{member_id}/promote")
@require_admin
async def promote_to_admin(
    member_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Promote member to admin"""
    
    member = db.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member.role = "admin"
    db.commit()
    
    # Log for audit trail
    logger.info(f"Admin {current_user.email} promoted {member.email} to admin")
    
    return {"message": f"{member.email} is now admin"}
```

---

## Part 10: Audit Trail (Who Changed What?)

For security, log all role changes:

```python
@app.post("/api/admin/members/{member_id}/promote")
@require_admin
async def promote_to_admin(
    member_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Promote member to admin (with audit trail)"""
    
    member = db.get_member(member_id)
    old_role = member.role
    new_role = "admin"
    
    # Make change
    member.role = new_role
    db.commit()
    
    # Log for audit trail
    audit_log = AuditLog(
        admin_id=current_user.user_id,
        action="role_change",
        resource_type="member",
        resource_id=member_id,
        details={
            "old_role": old_role,
            "new_role": new_role,
            "member_email": member.email
        },
        timestamp=datetime.now()
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"AUDIT: {current_user.email} changed {member.email} role: {old_role} → {new_role}")
    
    return {"message": f"{member.email} is now admin"}
```

---

## Summary: RBAC Best Practices

```
✓ Define roles clearly
  - What permissions does each role have?
  - Write permission matrix

✓ Include role in JWT
  - No DB lookup needed for role check
  - Faster authorization
  - Clear in logs who could access what

✓ Use decorators for role checks
  - Keep code DRY
  - Consistent across endpoints
  - Easy to audit

✓ Check both role AND resource ownership
  - Admin: can do anything
  - Owner: can do their own things
  - Others: denied

✓ Log all role changes
  - Audit trail for compliance
  - Detect unauthorized changes
  - Accountability

✓ Use clear error messages (but not too clear)
  - Don't reveal system details
  - Help legitimate users debug
  - Protect against info leakage

✓ Test all combinations
  - Admin can access X
  - Member can't access X
  - Owner can access their own X
```

---

That's the complete RBAC design! 🎉

Next: Implementation in database & code.
