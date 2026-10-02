# Week 2 Review: Complete OAuth 2.0 Flow Diagram

## The Full OAuth Flow (Without Notes)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE OAUTH 2.0 FLOW                                   │
│                    (Authorization Code Grant with JWT)                              │
└─────────────────────────────────────────────────────────────────────────────────────┘


USER BROWSER              YOUR APP                  GOOGLE OAUTH                GOOGLE API
     │                        │                           │                           │
     │ 1. Click "Login"       │                           │                           │
     ├───────────────────────>│                           │                           │
     │                        │ 2. Generate auth URL      │                           │
     │                        │    with scopes & state    │                           │
     │                        │                           │                           │
     │<───────Redirect to Google ──────────────────────────>                           │
     │    /oauth2/v2/auth                                 │                           │
     │                        │                           │                           │
     │                        │                           │ 3. Show login form        │
     │                        │                           │                           │
     ├──────────Login & authorize ──────────────────────>│                           │
     │   (user enters password here, NOT in your app)     │                           │
     │                        │                           │                           │
     │                        │                           │ 4. Generate auth code    │
     │<────────Redirect with code & state ────────────────┤                           │
     │    /callback?code=...&state=...                    │                           │
     │                        │                           │                           │
     │                        │ 5. Validate state         │                           │
     │                        │    (CSRF check)           │                           │
     │                        │                           │                           │
     │                        │ 6. Exchange code          │                           │
     │                        │    (POST /token)          │                           │
     │                        ├──client_id                │                           │
     │                        ├──client_secret ──────────>│                           │
     │                        │  ├──code                  │                           │
     │                        │  └──grant_type            │                           │
     │                        │                           │                           │
     │                        │<─────Token Response───────┤                           │
     │                        │  ├─access_token           │                           │
     │                        │  ├─id_token (JWT)         │                           │
     │                        │  ├─refresh_token          │                           │
     │                        │  └─expires_in             │                           │
     │                        │                           │                           │
     │                        │ 7. Decode ID token        │                           │
     │                        │    (extract user info)    │                           │
     │                        │    ├─sub (Google ID)      │                           │
     │                        │    ├─email                │                           │
     │                        │    ├─name                 │                           │
     │                        │    └─picture              │                           │
     │                        │                           │                           │
     │                        │ 8. Find or create user    │                           │
     │                        │    (check database)       │                           │
     │                        │                           │                           │
     │                        │ 9. Issue YOUR OWN JWT     │                           │
     │                        │    (not Google's token)   │                           │
     │                        │    ├─user_id (yours)      │                           │
     │                        │    ├─email                │                           │
     │                        │    ├─exp: +24 hours       │                           │
     │                        │    └─signed with          │                           │
     │                        │      YOUR_JWT_SECRET      │                           │
     │                        │                           │                           │
     │<──────Set cookie + redirect to /dashboard ────────┤                           │
     │   Set-Cookie: access_token=eyJhbGc...             │                           │
     │   httpOnly, Secure, SameSite=Strict               │                           │
     │                        │                           │                           │
     │ 10. Access protected route (with JWT cookie)      │                           │
     ├──────────GET /dashboard + Cookie ────────────────>│                           │
     │                        │                           │                           │
     │                        │ 11. Verify JWT            │                           │
     │                        │     ├─Check signature     │                           │
     │                        │     ├─Check expiration    │                           │
     │                        │     └─Get user_id         │                           │
     │                        │                           │                           │
     │<──────────User profile JSON ─────────────────────┤                           │
     │   {                                                │                           │
     │     "email": "user@example.com",                  │                           │
     │     "name": "Alice",                              │                           │
     │     "picture": "https://..."                      │                           │
     │   }                                                │                           │
     │                        │                           │                           │
     │ ✓ USER AUTHENTICATED!  │                           │                           │
     │                        │                           │                           │
     │ 12. Later: Refresh token (if JWT expires)         │                           │
     ├──────GET /refresh ────>│                           │                           │
     │                        │ Generate new JWT          │                           │
     │                        │ (same as step 9)          │                           │
     │<────New JWT ───────────┤                           │                           │
     │                        │                           │                           │
     │ 13. Logout (revoke session)                        │                           │
     ├──────GET /logout ─────>│                           │                           │
     │                        │ Delete cookie             │                           │
     │<────Redirect to / ─────┤                           │                           │
     │                        │                           │                           │

```

---

## Data Structures at Each Step

### Step 2: Authorization URL Parameters
```
GET /oauth2/v2/auth?
  client_id=YOUR_ID
  &redirect_uri=http://localhost:8000/auth/google/callback
  &response_type=code
  &scope=openid+profile+email
  &state=random_string_123
```

### Step 4: Authorization Code
```
GET /callback?
  code=4/0AX4XfW7...            ← Single-use (expires ~10 min)
  &state=random_string_123      ← Must match what we sent
```

### Step 6: Token Exchange Request
```
POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET    ← BACKEND ONLY
code=4/0AX4XfW7...
grant_type=authorization_code
redirect_uri=http://localhost:8000/auth/google/callback
```

### Step 6: Token Exchange Response
```json
{
  "access_token": "ya29.a0AfH6SMBu...",
  "expires_in": 3599,
  "refresh_token": "1//0g...",
  "scope": "openid email profile",
  "token_type": "Bearer",
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ..."
}
```

### Step 7: ID Token (JWT) Decoded
```json
{
  "iss": "https://accounts.google.com",
  "azp": "YOUR_CLIENT_ID",
  "aud": "YOUR_CLIENT_ID",
  "sub": "1234567890",                    ← Google's user ID
  "email": "alice@example.com",
  "email_verified": true,
  "name": "Alice Smith",
  "picture": "https://lh3.googleusercontent.com/...",
  "given_name": "Alice",
  "family_name": "Smith",
  "iat": 1516239022,
  "exp": 1516242622
}
```

### Step 9: Your Own JWT (What You Issue)
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",     ← YOUR user ID
  "email": "alice@example.com",
  "name": "Alice Smith",
  "picture": "https://lh3.googleusercontent.com/...",
  "iat": 1704067200,
  "exp": 1704153600                       ← Expires in 24 hours
}

// Signed with YOUR_JWT_SECRET using HS256
```

---

## Decision Points in Flow

### At Step 5: Validate State
```
┌─────────────────────────────┐
│ Is state == cookie_state?   │
└──────────────┬──────────────┘
           ├─ NO  → ❌ REJECT (CSRF attack)
           └─ YES ↓
                ┌─────────────────────┐
                │ Is state not used?  │
                └─────────┬───────────┘
                      ├─ NO  → ❌ REJECT (replay attack)
                      └─ YES ↓
                           ✓ CONTINUE
```

### At Step 8: User Lookup
```
┌─────────────────────────────────────┐
│ User exists with this Google ID?    │
└────────────────┬────────────────────┘
             ├─ YES ↓ Update last_login
             │      └→ ✓ Use existing user
             └─ NO  ↓ Create new user
                    └→ ✓ Register & use new user
```

### At Step 11: Protected Route Access
```
┌──────────────────────────┐
│ JWT in cookie?           │
└────────┬─────────────────┘
      ├─ NO  → ❌ REJECT (401 Unauthorized)
      └─ YES ↓
           ┌──────────────────────┐
           │ Signature valid?     │
           └─────┬────────────────┘
              ├─ NO  → ❌ REJECT
              └─ YES ↓
                   ┌──────────────────┐
                   │ Not expired?     │
                   └────┬─────────────┘
                    ├─ NO  → ❌ REJECT (401 Token expired)
                    └─ YES ↓
                         ✓ ALLOW REQUEST
```

---

## Security Layers

```
Layer 1: CSRF Protection
├─ Random state per request
├─ State stored in httpOnly cookie
├─ State validated on callback
└─ Single-use (can't replay)

Layer 2: Authentication (Google)
├─ User logs in directly to Google
├─ Google verifies password
└─ User never gives password to your app

Layer 3: Authorization Code Exchange
├─ Code is single-use
├─ Code expires quickly (~10 min)
├─ Exchange uses client_secret
└─ client_secret never exposed to browser

Layer 4: Session Management
├─ JWT stored in httpOnly cookie
├─ Cookie marked Secure (HTTPS only)
├─ Cookie marked SameSite=Strict (CSRF)
└─ JWT has expiration (24 hours)

Layer 5: Token Verification
├─ Check JWT signature
├─ Check not expired
└─ Reject on any validation failure
```

---

## Comparison: With vs Without OAuth

### Without OAuth (Password-Based)
```
User enters password → Your app stores password hash → User logs in
├─ You handle password security (complex)
├─ You handle password reset (complex)
├─ You handle password strength (complexity)
├─ Users reuse passwords (security risk)
└─ Database breach exposes passwords (catastrophic)
```

### With OAuth (Google-Based)
```
User logs in to Google → Google gives permission → Your app gets token
├─ Google handles password security (they're experts)
├─ Google handles password reset
├─ Users don't reuse passwords (separate from yours)
├─ Database breach doesn't expose passwords
└─ Users can manage permissions in Google Security settings
```

---

## Token Lifetime Strategy

```
Authorization Code
├─ Lifetime: ~10 minutes
├─ Purpose: Exchange for tokens
├─ Single-use: YES
└─ Revocation: Not needed (auto-expires)

Google's Access Token
├─ Lifetime: ~1 hour
├─ Purpose: Call Google APIs
├─ Usage: Discard after callback
└─ Note: We DON'T store this long-term

Google's Refresh Token
├─ Lifetime: ~7 days
├─ Purpose: Get new access token
├─ Usage: Only if you need to call Google APIs later
└─ Note: We typically don't use this

Your JWT (Access Token)
├─ Lifetime: 24 hours
├─ Purpose: Session & protected routes
├─ Auto-refresh: User gets new JWT on refresh endpoint
└─ Revocation: Delete cookie on logout

Your JWT (Refresh Token - Optional)
├─ Lifetime: 7 days
├─ Purpose: Get new access token when old expires
├─ Usage: Optional (can just require re-login)
└─ Storage: Separate httpOnly cookie
```

---

## Critical Security Rules (In Order of Importance)

```
1. NEVER expose client_secret to browser
   └─ Token exchange MUST happen on backend

2. ALWAYS use HTTPS in production
   └─ Cookies marked Secure=True
   └─ No HTTP fallback

3. ALWAYS validate state on callback
   └─ Prevents CSRF attacks
   └─ Must be single-use

4. ALWAYS use httpOnly cookies for tokens
   └─ Prevents XSS attacks
   └─ JavaScript can't access cookie

5. ALWAYS verify JWT signature
   └─ Ensure token wasn't tampered with
   └─ Use your JWT_SECRET

6. ALWAYS check JWT expiration
   └─ Reject expired tokens
   └─ Issue new ones before expiry

7. ALWAYS log authentication events
   └─ Track successful logins
   └─ Alert on failed attempts
   └─ Monitor for suspicious activity

8. ALWAYS handle errors gracefully
   └─ Show generic messages to users
   └─ Log detailed errors for debugging
```

---

## What Happens If...

### ...State Validation Fails?
```
Cause: Attacker trying to complete another user's callback
Action: Reject callback (CSRF attack prevented)
User sees: "Authentication failed"
Log: CSRF_ATTACK_ATTEMPT
```

### ...Code Exchange Fails?
```
Cause: Code expired, already used, or invalid
Action: Reject callback, ask user to login again
User sees: "Code expired. Please try again."
Log: INVALID_CODE
```

### ...User Doesn't Exist?
```
Cause: First time login
Action: Create new user in database
Result: User registered automatically
Log: NEW_USER_REGISTERED
```

### ...JWT Expires?
```
Cause: Token is older than 24 hours
Action: User redirected to login
User sees: "Session expired. Please login again."
Log: TOKEN_EXPIRED
```

### ...Cookie is Missing?
```
Cause: User has cookies disabled or deleted cookie
Action: Reject request (401 Unauthorized)
User sees: "Please login"
Redirect: To /auth/google/login
```

---

## The Minimal OAuth Flow (What's Actually Required)

```
User Browser              Your Backend              Google
     │                        │                       │
     ├──Login ───────────────>│                       │
     │                        │  Generate URL         │
     │<───────Redirect to Google auth endpoint─────────>
     │                        │                       │
     │                    User logs in at Google      │
     │                        │                       │
     │<────────Redirect with code────────────────────┤
     │                        │                       │
     │                        │──Exchange code ──────>│
     │                        │<─── tokens ──────────┤
     │<────Set JWT cookie─────┤                       │
     │                        │                       │
     │      Logged in!        │                       │
```

**That's it!** Everything else is details and security.

---

## Common Flow Variations

### Variation 1: Multiple OAuth Providers
```
Add GitHub, Facebook, etc.
Same flow for each provider
Different endpoints, same structure
User can link multiple accounts
Database stores: google_id, github_id, facebook_id
```

### Variation 2: With Refresh Tokens
```
Step 9b: Store refresh_token in DB (encrypted)
Step 12: On JWT expiration, use refresh_token to get new token
Benefit: Don't require re-login
Complexity: Need to rotate refresh tokens
```

### Variation 3: With Role-Based Access
```
Step 8b: Fetch user roles from database
Step 9b: Add roles to JWT payload
Step 11b: Check roles before allowing resource access
Benefit: Fine-grained access control
Example: admin, user, premium, etc.
```

### Variation 4: With Logout Tracking
```
Add logout table to track revoked tokens
Step 13b: On logout, add JWT to logout table
Step 11b: Check if JWT is in logout table
Step 11c: If revoked, reject request
Benefit: Immediate logout (not waiting for expiry)
Cost: Need to check DB on every request
```

---

## Summary Table: OAuth vs Your JWT

| Aspect | Google's Token | Your JWT |
|--------|---|---|
| **When received** | After code exchange | After user lookup |
| **How long stored** | Not stored (discarded) | 24 hours in httpOnly cookie |
| **Who issued** | Google | You |
| **Who can verify** | Anyone with Google's key | Anyone with your secret |
| **Can be revoked** | By Google | By deleting cookie |
| **Single-use** | No (reusable) | Yes (JWT in cookie) |
| **Expiration** | ~1 hour | 24 hours |
| **Refresh method** | Use refresh_token | Issue new JWT |
| **Used for** | Calling Google APIs | Your app's protected routes |
| **Stateless** | No (tied to Google) | Yes (can validate anywhere) |

---

**That's the complete OAuth 2.0 flow!**

All the moving parts, all the decisions, all the security layers.

If you can draw this flow and explain why each step exists, you understand OAuth. 🎉
