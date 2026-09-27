// Day 10: OAuth 2.0 Concepts - Complete Summary

/**
 * CORE INSIGHT: OAuth 2.0 is AUTHORIZATION, not AUTHENTICATION
 * 
 * Authentication: "Who are you?"
 *   Proved with: Password, 2FA, fingerprint, etc.
 * 
 * Authorization: "What are you allowed to do?"
 *   Proved with: Scopes, permissions, access tokens, etc.
 * 
 * OAuth 2.0: "Let this app access your resources (without your password)"
 *   = Authorization protocol
 *   ≠ Authentication protocol
 * 
 * To add authentication to OAuth 2.0: Use OIDC (OpenID Connect)
 *   OIDC = OAuth 2.0 + Identity Layer (ID Token)
 */

// ============================================================================
// THE FOUR GRANT TYPES
// ============================================================================

1. AUTHORIZATION CODE FLOW (MOST COMMON)
   ────────────────────────────────────
   Use: User logs in via third-party (Google, GitHub, etc.)
   Flow:
     1. User clicks "Login with Google"
     2. App redirects to Google login
     3. User authorizes permissions
     4. Google redirects back with code
     5. App backend exchanges code for token (with client_secret)
     6. App can now access user's resources
   
   Best for: Web apps, traditional login flows
   Security: HIGH (client_secret never exposed)
   Example:
     https://accounts.google.com/o/oauth2/auth
       ?client_id=123...
       &redirect_uri=https://yourapp.com/callback
       &scope=openid+profile+email
       &response_type=code
       &state=random_string

2. IMPLICIT FLOW (DEPRECATED - DON'T USE)
   ──────────────────────────────────────
   Was used for: Single-page apps
   Why deprecated: No client_secret = less secure
   Use instead: Authorization Code + PKCE
   
3. CLIENT CREDENTIALS FLOW
   ──────────────────────
   Use: Server-to-server (no user involved)
   Flow:
     1. App backend sends client_id + client_secret
     2. OAuth provider returns access token
     3. App uses token to call other APIs
   
   Best for: Microservices, scheduled jobs, admin operations
   Security: HIGH (only between servers)
   No user involvement
   No refresh tokens (just request new one when expired)
   Example:
     POST /token
       client_id=my_app
       client_secret=secret
       grant_type=client_credentials

4. DEVICE FLOW
   ──────────
   Use: Devices without browsers (Smart TVs, IoT, CLI tools)
   Flow:
     1. Device requests device code
     2. Server gives device code + user code
     3. Device shows: "Go to https://oauth.provider.com/device"
     4. Device shows: "Enter code: LHJK-MNOP"
     5. User opens browser, enters code
     6. Device polls for token until user authorizes
     7. Device gets access token
   
   Best for: Smart TVs, Alexa, CLI tools, devices without keyboard
   Example: GitHub CLI, AWS CLI auth, Netflix login on smart TV

// ============================================================================
// AUTHORIZATION CODE FLOW - STEP BY STEP
// ============================================================================

STEP 1: Generate Authorization URL
─────────────────────────────────
What: App creates a URL pointing to OAuth provider
When: User clicks "Login with [Provider]"
Example:
  const authUrl = `https://accounts.google.com/o/oauth2/auth?
    client_id=${CLIENT_ID}&
    redirect_uri=${REDIRECT_URI}&
    response_type=code&
    scope=openid+profile+email&
    state=${RANDOM_STATE}`
  window.location.href = authUrl;

Parameters:
  • client_id: Identifies your app (public, safe to show)
  • redirect_uri: Where to send user back (must be registered)
  • response_type: Always "code" (not "token")
  • scope: What permissions to request
  • state: Random string for CSRF protection


STEP 2: User Authorizes
──────────────────────
What: User logs in and clicks "Allow"
OAuth provider shows:
  "yourapp.com wants to access:
   ☑ Your name and profile picture
   ☑ Your email address
   [Allow] [Deny]"
User clicks [Allow]


STEP 3: OAuth Provider Redirects Back
─────────────────────────────────────
What: User redirected to your callback URL with authorization code
URL:
  https://yourapp.com/callback?
    code=4/0AX4XfW7...&
    state=abc123...

Authorization code:
  • Single-use (can only be exchanged once)
  • Expires quickly (~10 minutes)
  • Tied to your client_id


STEP 4: Validate State Parameter (CSRF Protection)
──────────────────────────────────────────────────
What: Check that 'state' matches what we sent
Purpose: Prevent CSRF attacks
Code:
  const savedState = session.state;
  const returnedState = req.query.state;
  if (savedState !== returnedState) {
    throw new Error('CSRF attack detected!');
  }


STEP 5: Exchange Code for Token (Backend Only!)
───────────────────────────────────────────────
What: Backend makes secure request to OAuth provider
Purpose: Convert single-use code into access token
CRITICAL: This happens BACKEND-TO-BACKEND
  NOT in browser (would expose client_secret)

Request:
  POST https://oauth2.googleapis.com/token
  {
    client_id: YOUR_CLIENT_ID,           // OK to send
    client_secret: YOUR_SECRET,          // MUST STAY SECRET (backend only)
    code: 4/0AX4XfW7...,                 // Single-use code
    grant_type: 'authorization_code',
    redirect_uri: https://yourapp.com/callback
  }

Response:
  {
    access_token: 'ya29.a0AfH6SMBu...',  // Use this for API calls
    token_type: 'Bearer',
    expires_in: 3599,                     // ~1 hour
    refresh_token: '1//0g...',            // (Optional) Use to refresh token
    scope: 'openid profile email'
  }


STEP 6: Get User Information
────────────────────────────
Option A: Call userinfo endpoint (plain OAuth)
  GET https://www.googleapis.com/oauth2/v1/userinfo
  Authorization: Bearer ya29.a0AfH6SMBu...
  
  Response:
  {
    id: '123456789',
    email: 'user@example.com',
    name: 'Alice Smith',
    picture: 'https://...'
  }

Option B: Decode id_token (OIDC - more efficient)
  Receive id_token in token response (if scope includes 'openid')
  Decode JWT (no API call needed):
  {
    iss: 'https://accounts.google.com',
    sub: '123456789',
    aud: 'YOUR_CLIENT_ID',
    iat: 1516239022,
    exp: 1516242622,
    name: 'Alice Smith',
    email: 'user@example.com',
    picture: 'https://...'
  }


STEP 7: Create User Session
───────────────────────────
What: Log user into your app
Code:
  const user = await getUserInfo(accessToken);
  const session = await createSession({
    userId: user.id,
    email: user.email,
    name: user.name
  });
  
  // Set session cookie
  res.cookie('sessionId', session.id, {
    httpOnly: true,    // Can't be accessed by JavaScript
    secure: true,      // Only HTTPS
    sameSite: 'strict' // CSRF protection
  });


STEP 8: Use Access Token for API Calls
──────────────────────────────────────
What: Make authenticated requests to Google/GitHub API
Format: Authorization: Bearer <token>
Example:
  GET https://www.googleapis.com/drive/v3/files
  Authorization: Bearer ya29.a0AfH6SMBu...
  
  → Returns user's Google Drive files
  → If token expires: Use refresh_token to get new one

// ============================================================================
// SCOPES (PERMISSIONS)
// ============================================================================

What: Define what your app can access
Example: scope=openid profile email write:posts delete:posts

Scope Naming Patterns:

OIDC Standard Scopes:
  openid      ← ALWAYS include this for authentication
  profile     → Name, picture, profile URL
  email       → Email address
  address     → Mailing address
  phone       → Phone number

RESTful Convention:
  read:*      → Can read this resource (read-only)
  write:*     → Can create/edit this resource
  delete:*    → Can delete this resource
  admin:*     → Full admin access

Examples:
  read:posts
  write:comments
  delete:files
  admin:users

Best Practices:
  ✅ ONLY request scopes you need
  ✅ Use principle of least privilege
  ✅ Explain why you need each scope to user
  ❌ DON'T request all scopes "just in case"
  ❌ DON'T hide what scopes you're requesting

// ============================================================================
// SECURITY: CRITICAL POINTS
// ============================================================================

✅ DO:
  ✅ Use HTTPS (always, in production)
  ✅ Generate unique 'state' for each authorization
  ✅ Validate 'state' on callback
  ✅ Keep client_secret secret (backend only)
  ✅ Exchange code on backend (not in browser)
  ✅ Use short-lived access tokens (~1 hour)
  ✅ Store refresh tokens in httpOnly cookies
  ✅ Validate redirect_uri exactly
  ✅ Implement rate limiting on token endpoint
  ✅ Make authorization code single-use

❌ DON'T:
  ❌ Expose client_secret in browser
  ❌ Put client_secret in git (use env variables)
  ❌ Skip state validation (CSRF vulnerability)
  ❌ Trust access_token claims (verify signature)
  ❌ Store tokens in localStorage (XSS vulnerable)
  ❌ Use http:// redirect URIs (HTTPS only)
  ❌ Request admin scope without good reason
  ❌ Log tokens (log IDs or hashes only)
  ❌ Use implicit flow (deprecated)

// ============================================================================
// OPENID CONNECT (OIDC)
// ============================================================================

What: OAuth 2.0 + Authentication Layer

Difference:
  OAuth 2.0 alone:
    scope=profile+email
    → Returns: access_token (for API access)
    → GET /userinfo?token=... → User info
  
  OIDC (OAuth 2.0 + identity):
    scope=openid+profile+email
    → Returns: access_token + id_token (JWT)
    → ID token already contains user info!
    → No /userinfo call needed (saves API call)

Key difference: 'openid' scope

When to use OIDC:
  ✅ You need authentication (prove identity)
  ✅ You need user info (name, email)
  ✅ You want to be efficient (fewer API calls)

When to use just OAuth:
  ✅ You only need authorization (API access)
  ✅ You don't need user identity
  ✅ Third-party API doesn't support OIDC

ID Token (JWT inside):
  {
    "iss": "https://accounts.google.com",     // Issuer
    "sub": "1234567890",                      // Subject (user ID)
    "aud": "YOUR_CLIENT_ID",                  // Audience
    "iat": 1516239022,                        // Issued at
    "exp": 1516242622,                        // Expires
    "name": "Alice Smith",                    // User info
    "email": "alice@example.com",
    "picture": "https://...",
    "email_verified": true
  }

// ============================================================================
// PKCE (Proof Key for Code Exchange)
// ============================================================================

What: Extra security for SPAs (Single-Page Apps)
Purpose: Make authorization code flow safe without secure backend

When to use:
  ✅ Single-page apps (React, Vue, Angular)
  ✅ Mobile apps
  ✅ Desktop apps
  ✅ Any app that can't securely store client_secret

How:
  1. Frontend generates code_verifier (128 random chars)
  2. Frontend generates code_challenge = SHA256(code_verifier)
  3. Frontend includes code_challenge in auth URL
  4. User authorizes
  5. Frontend exchanges code + code_verifier
  6. Server verifies: SHA256(code_verifier) == code_challenge

Benefit:
  Even if authorization code is intercepted,
  attacker can't exchange it (needs code_verifier)

// ============================================================================
// COMMON MISTAKES
// ============================================================================

❌ Mistake 1: Confusing OAuth with Authentication
   ✅ Correct: "OAuth is authorization, OIDC adds authentication"

❌ Mistake 2: Storing client_secret in browser
   ✅ Correct: Keep secret in backend environment variables

❌ Mistake 3: Skipping state validation
   ✅ Correct: Always validate state (CSRF protection)

❌ Mistake 4: Exposing tokens in logs
   ✅ Correct: Log token hashes or IDs, never plaintext

❌ Mistake 5: Not validating redirect_uri
   ✅ Correct: Validate redirect_uri matches registered value exactly

❌ Mistake 6: Using implicit flow (deprecated)
   ✅ Correct: Use authorization code + PKCE for SPAs

❌ Mistake 7: Requesting all scopes
   ✅ Correct: Request only what you need

// ============================================================================
// QUICK CHECKLIST
// ============================================================================

□ Understand OAuth is authorization, not authentication
□ Know the 4 grant types (Auth code, Implicit, Client creds, Device)
□ Understand Authorization Code flow step-by-step
□ Implement state validation (CSRF protection)
□ Define and validate scopes
□ Keep client_secret secret
□ Use HTTPS only
□ Test with real OAuth provider
□ Handle errors gracefully
□ Implement rate limiting
□ Log securely (no tokens)
□ Use PKCE for SPAs
□ Consider OIDC if you need authentication
□ Validate redirect_uri strictly
□ Use short-lived access tokens
□ Store refresh tokens in httpOnly cookies
□ Test full flow end-to-end

// ============================================================================
// FILES CREATED FOR DAY 10
// ============================================================================

1. oauth2-complete-guide.md
   → Comprehensive guide to OAuth 2.0 concepts
   → Grant types explained
   → OIDC explained
   → Security best practices

2. oauth2-implementation.ts
   → Complete implementation of all grant types
   → State management
   → Scope validation
   → PKCE support
   → Token refresh

3. oauth2-tests.ts
   → Unit tests for all components
   → Integration tests
   → Security tests
   → Error handling tests

4. oauth2-checklist.md
   → Implementation checklist
   → Quick reference guide
   → Deployment checklist
   → Common mistakes

5. Interactive diagram (above)
   → Visual representation of auth code flow
   → Shows all steps and actors
   → Clickable for more details

// ============================================================================
// SUMMARY
// ============================================================================

OAuth 2.0: Authorization protocol (not authentication)

Four grant types:
  1. Authorization Code: User login (most common) ⭐
  2. Implicit: SPAs (deprecated)
  3. Client Credentials: Server-to-server
  4. Device: Smart TVs, IoT

Key insight: Authorization Code flow is 8 steps
  1. Generate auth URL with scopes
  2. User authorizes
  3. OAuth provider sends back authorization code
  4. Exchange code for token (backend, use client_secret)
  5. Get user info (either userinfo endpoint or OIDC id_token)
  6. Create user session
  7. Use access_token for API calls
  8. Refresh when needed

Scopes: Define what app can do (principle of least privilege)

Security:
  • HTTPS only
  • State validation (CSRF)
  • Keep client_secret secret
  • Short-lived access tokens
  • httpOnly cookies for refresh tokens

OIDC: OAuth 2.0 + authentication (id_token as JWT)

PKCE: Extra security for SPAs (no client_secret needed)

That's OAuth 2.0! 🎉
