# Day 14: Role-Based Access Control (RBAC) — Complete Guide

---

## 🎯 What You're Building Today

Moving from **authentication** (who are you?) to **authorization** (what can you do?)

```
Week 2: Authentication        Week 3: Authorization
├─ Who are you?              ├─ What can you do?
├─ Login/logout              ├─ Admin vs Member
├─ Sessions                  ├─ Permissions
└─ JWTs                      └─ Access control
```

---

## Part 1: The Big Picture

### Without RBAC (Bad)
```python
@app.post("/api/books")
async def create_book(book: BookCreate):
    # Check if specific user ID is admin
    if user_id != "hardcoded_admin_id":
        raise HTTPException(status_code=403)
    
    # Doesn't scale to multiple admins
    # Doesn't scale to multiple roles
    # Hard to test
```

### With RBAC (Good)
```python
@app.post("/api/books")
@require_admin
async def create_book(
    book: BookCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    # Admin role allows this
    # Scales to any number of admins
    # Easy to test
    # Clean code
```

---

## Part 2: Implementation Steps

### Step 1: Add Role Field to Member Model

```python
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class RoleEnum(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

class Member(Base):
    __tablename__ = "members"
    
    id: UUID = Column(String(36), primary_key=True)
    email: str = Column(String(255), unique=True)
    name: str = Column(String(255))
    
    # NEW: Role field
    role: str = Column(
        String(20),
        nullable=False,
        default=RoleEnum.MEMBER,
        index=True
    )
```

### Step 2: Alembic Migration

```python
def upgrade():
    # Add role column
    op.add_column(
        'members',
        sa.Column('role', sa.String(20), server_default='member')
    )
    
    # Add CHECK constraint
    op.create_check_constraint(
        'check_valid_role',
        'members',
        "role IN ('admin', 'member')"
    )
    
    # Add index
    op.create_index('idx_members_role', 'members', ['role'])

# Run migration
# alembic upgrade head
```

### Step 3: Include Role in JWT

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
        payload = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,  # Include in JWT
            'iat': now.timestamp(),
            'exp': expiration.timestamp()
        }
        
        return jwt.encode(payload, self.secret)
```

### Step 4: Update get_current_user

```python
class CurrentUser(BaseModel):
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
    jwt_token = request.cookies.get("access_token")
    payload = jwt.decode(jwt_token, Config.JWT_SECRET)
    
    return CurrentUser(
        user_id=payload['user_id'],
        email=payload['email'],
        name=payload['name'],
        role=payload.get('role', 'member')  # NEW: Extract role
    )
```

### Step 5: Role-Based Decorators

```python
def require_role(*allowed_roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: CurrentUser, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(status_code=403)
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_admin(func):
    return require_role("admin")(func)
```

### Step 6: Use Decorators on Endpoints

```python
@app.post("/api/books")
@require_admin
async def create_book(
    book: BookCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    # Only admins can reach this
    return {"message": "Book created"}
```

---

## Part 3: Permission Design for Library API

### Role Hierarchy
```
ADMIN (Superuser)
├─ Full system access
├─ CRUD books
├─ CRUD members
├─ View all loans
└─ View statistics

MEMBER (Regular user)
├─ Limited access
├─ View books
├─ Borrow books (max 5)
├─ View own loans
└─ Edit own profile
```

### Permission Matrix

| Action | Admin | Member |
|--------|-------|--------|
| Create book | ✓ | ✗ |
| Edit book | ✓ | ✗ |
| Delete book | ✓ | ✗ |
| List books | ✓ View all | ✓ View all |
| Borrow book | ✓ | ✓ |
| Return book | ✓ | ✓ own |
| List all loans | ✓ | ✗ |
| List own loans | ✓ | ✓ |
| List members | ✓ | ✗ |
| View profile | ✓ | ✓ own |
| Edit profile | ✓ | ✓ own |
| Promote member | ✓ | ✗ |

### Endpoint Examples

```python
# Public (no auth)
@app.get("/api/books")
async def list_books():
    pass

# Member+ (member or admin)
@app.post("/api/books/{id}/borrow")
@require_member
async def borrow_book(current_user: CurrentUser):
    pass

# Admin only
@app.post("/api/books")
@require_admin
async def create_book(current_user: CurrentUser):
    pass

@app.get("/api/admin/members")
@require_admin
async def list_all_members(current_user: CurrentUser):
    pass
```

---

## Part 4: JWT Payload Examples

### Admin User
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@library.com",
  "name": "Admin User",
  "role": "admin",
  "iat": 1704067200,
  "exp": 1704153600
}
```

### Member User
```json
{
  "user_id": "660e8400-e29b-41d4-a716-446655440111",
  "email": "alice@example.com",
  "name": "Alice Smith",
  "role": "member",
  "iat": 1704067200,
  "exp": 1704153600
}
```

**Key difference:** Only `role` field differs!

---

## Part 5: Error Responses

### 401 Unauthorized (Not logged in)
```
Request: GET /api/my/profile (no cookie)

Response:
{
  "detail": "Not authenticated",
  "status_code": 401
}
```

### 403 Forbidden (Insufficient role)
```
Request: POST /api/books (member user)

Response:
{
  "detail": "Insufficient permissions",
  "status_code": 403
}
```

### 404 Not Found
```
Request: GET /api/books/999 (book doesn't exist)

Response:
{
  "detail": "Book not found",
  "status_code": 404
}
```

**Security rule:** Don't reveal WHY access was denied (could leak info)

```
❌ BAD: "403: Only admins can delete. You are member"
✓ GOOD: "403: Insufficient permissions"
```

---

## Part 6: Database Schema

### Members Table (Updated)
```sql
CREATE TABLE members (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- NEW: Role column
    role VARCHAR(20) NOT NULL DEFAULT 'member'
        CHECK (role IN ('admin', 'member')),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX (email),
    INDEX (role)  -- NEW: Index for fast role lookups
);
```

### Why Index Role?
```
Common queries:
- "Get all admins" → WHERE role = 'admin'
- "Count members" → WHERE role = 'member'

Index makes these fast!
```

---

## Part 7: Testing RBAC

### Unit Test: JWT with Role
```python
def test_jwt_includes_role():
    manager = JWTManager('secret')
    token = manager.generate_token(
        user_id='user1',
        email='user@example.com',
        name='User',
        role='admin'
    )
    
    payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    assert payload['role'] == 'admin'
```

### Unit Test: CurrentUser Properties
```python
def test_current_user_is_admin():
    user = CurrentUser(
        user_id='user1',
        email='admin@example.com',
        name='Admin',
        role='admin'
    )
    
    assert user.is_admin == True
    assert user.is_member == False
```

### Unit Test: Decorators
```python
@pytest.mark.asyncio
async def test_require_admin_denies_member():
    @require_admin
    async def admin_endpoint(current_user: CurrentUser):
        return {"message": "success"}
    
    member_user = CurrentUser(
        user_id='user2',
        email='member@example.com',
        name='Member',
        role='member'
    )
    
    with pytest.raises(HTTPException) as exc:
        await admin_endpoint(current_user=member_user)
    
    assert exc.value.status_code == 403
```

### Integration Test: Full Flow
```python
@pytest.mark.asyncio
async def test_admin_can_create_book():
    # Create JWT for admin
    manager = JWTManager('secret')
    token = manager.generate_token(
        user_id='admin1',
        email='admin@example.com',
        name='Admin',
        role='admin'
    )
    
    # Make request with token
    client = TestClient(app)
    response = client.post(
        '/api/books',
        json={'title': 'New Book', 'author': 'Author'},
        cookies={'access_token': token}
    )
    
    # Should succeed
    assert response.status_code == 200
```

---

## Part 8: Promoting Users to Admin

### Admin Promotion Endpoint

```python
@app.post("/api/admin/members/{member_id}/promote")
@require_admin
async def promote_to_admin(
    member_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Promote member to admin (admin only)"""
    
    # 1. Find member
    member = db.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404)
    
    # 2. Update role
    old_role = member.role
    member.role = "admin"
    db.commit()
    
    # 3. Audit log
    logger.info(
        f"Admin {current_user.email} promoted {member.email}: "
        f"{old_role} → admin"
    )
    
    return {"message": f"{member.email} is now admin"}
```

**Important:** Member can't immediately use new role until re-login (JWT doesn't update). They'd get new JWT on next login.

---

## Part 9: Owner-Based Access (Own Resource)

Sometimes permissions depend on both role AND resource ownership.

### Pattern: Admin OR Owner

```python
async def can_access_resource(
    resource_id: str,
    current_user: CurrentUser
) -> bool:
    """Check if user is admin OR owner of resource"""
    
    if current_user.is_admin:
        return True  # Admin can access anything
    
    resource = db.get_resource(resource_id)
    if resource.owner_id == current_user.user_id:
        return True  # Owner can access own resource
    
    return False

@app.put("/api/my/profile/{member_id}")
async def update_profile(
    member_id: str,
    profile_data: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update profile (admin or owner)"""
    
    if not await can_access_resource(member_id, current_user):
        raise HTTPException(status_code=403)
    
    # Safe to update
    member = db.get_member(member_id)
    member.update(profile_data)
    db.commit()
    
    return member
```

---

## Part 10: Best Practices

### ✅ DO:
```python
# ✓ Include role in JWT
payload = {'user_id': uid, 'email': email, 'role': role}

# ✓ Use decorators for role checks
@require_admin
async def endpoint(current_user: CurrentUser):
    pass

# ✓ Keep role in database indexed
CREATE INDEX idx_role ON members(role)

# ✓ Log role changes
logger.info(f"Admin {admin} changed {user} role: {old} → {new}")

# ✓ Check both role AND ownership
if not (user.is_admin or resource.owner_id == user.id):
    raise HTTPException(403)
```

### ❌ DON'T:
```python
# ✗ Store role only in database
# (need DB call for every request)

# ✗ Hardcode user IDs
if user_id == "admin123":
    allow()

# ✗ Pass role to browser in localStorage
# (JWT in httpOnly cookie is safe)

# ✗ Trust role from request parameters
# (use role from JWT only)

# ✗ Reveal why access was denied
# ("Admin only" leaks info)
```

---

## Part 11: Common Patterns

### Pattern 1: Multiple Roles with Permissions
```python
ROLE_PERMISSIONS = {
    'admin': ['create_book', 'edit_book', 'delete_book', 'manage_members'],
    'member': ['borrow_book', 'return_book', 'view_profile'],
    'guest': ['view_books']
}

def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])
```

### Pattern 2: Role Hierarchy
```python
# Later, when adding more roles:
class RoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"  # Level 3 (highest)
    ADMIN = "admin"              # Level 2
    MEMBER = "member"            # Level 1
    GUEST = "guest"              # Level 0 (lowest)

def has_at_least_role(user_role: str, required_role: str) -> bool:
    """Check if user has required role or higher"""
    role_hierarchy = ['guest', 'member', 'admin', 'super_admin']
    user_level = role_hierarchy.index(user_role)
    required_level = role_hierarchy.index(required_role)
    return user_level >= required_level
```

### Pattern 3: Resource-Based Access
```python
# User can edit book if:
# 1. They're admin, OR
# 2. They created it, OR
# 3. They're the library owner

async def can_edit_book(
    book_id: str,
    current_user: CurrentUser,
    library_owner_id: str
) -> bool:
    if current_user.is_admin:
        return True
    
    book = db.get_book(book_id)
    if book.creator_id == current_user.user_id:
        return True
    
    if current_user.user_id == library_owner_id:
        return True
    
    return False
```

---

## Part 12: Audit & Logging

Always log access decisions:

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/books")
@require_admin
async def create_book(
    book: BookCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    # Log the action
    logger.info(
        f"Book created: {book.title} "
        f"by {current_user.email} (admin)"
    )
    
    # Create book
    db.add_book(book)
    db.commit()
    
    return book

@app.post("/api/admin/members/{id}/promote")
@require_admin
async def promote_to_admin(
    member_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    member = db.get_member(member_id)
    
    # Log with audit trail
    logger.warning(
        f"AUDIT: {current_user.email} promoted {member.email} to admin"
    )
    
    member.role = "admin"
    db.commit()
    
    return {"message": f"{member.email} is now admin"}
```

---

## Summary Checklist

- [ ] Add `role` column to `members` table
- [ ] Create Alembic migration
- [ ] Add `RoleEnum` class
- [ ] Update `JWTManager` to include role
- [ ] Update `CurrentUser` model
- [ ] Update `get_current_user()` function
- [ ] Create `@require_admin` decorator
- [ ] Create `@require_role()` decorator
- [ ] Test JWT with role
- [ ] Test decorators (allow/deny)
- [ ] Write integration tests
- [ ] Document permission matrix
- [ ] Add role to admin promotion endpoint
- [ ] Add audit logging
- [ ] Test in Swagger UI

---

## What You Can Do Now

After Day 14, you can:

```
✅ Design role hierarchies
✅ Implement RBAC in any API
✅ Add admin & member roles
✅ Protect endpoints with @require_admin
✅ Test role-based access
✅ Audit permission changes
✅ Explain RBAC to others
✅ Scale from 1 to N admin users
✅ Handle resource ownership checks
✅ Extend with more roles
```

---

**Day 14 Complete!** 🎉

You've moved from "who are you?" to "what can you do?"

That's the difference between authentication and authorization.

Next: Day 15 could cover:
- Audit trail storage
- Permission denials tracking
- Token revocation
- Advanced role patterns
- Or any new feature you want!
