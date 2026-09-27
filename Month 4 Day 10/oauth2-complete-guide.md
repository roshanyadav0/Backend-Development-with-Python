# OAuth 2.0 Complete Guide
## Understanding Authorization, Grant Types, Scopes, and OpenID Connect

---

## Part 1: OAuth 2.0 vs Authentication vs Authorization

### The Confusion
Many people confuse these three concepts:

```
Authentication: "Who are you?"
  ↓ Proves identity with password, 2FA, etc.

Authorization: "What are you allowed to do?"
  ↓ Grants access to specific resources/actions

OAuth 2.0: "Let someone access your resources (without giving your password)"
  ↓ Authorization protocol, NOT authentication
```

### OAuth 2.0 is Authorization, Not Authentication

**What OAuth 2.0 Does:**
```
User: "I want this app to access my Google Drive"
      ↓
Google (via OAuth): "I'll give the app permission to access Drive"
      ↓
App gets an access token that works for ~1 hour
App can read/write files on your behalf (only what you allowed)
```

**What OAuth 2.0 Does NOT Do:**
- It doesn't prove who you are
- It doesn't return user information
- It's just a permission mechanism

**Example:**
```
"Login with Google" = Wrong terminology
  ↓
Should be: "Authorize this app to access your Google account"
  ↓
But we use "login" because it *feels* like authentication to the user
```

### OpenID Connect Adds Authentication
OIDC = OAuth 2.0 + Identity Layer

```
OAuth 2.0 alone:
  GET https://api.example.com/drive/files (with access token)
  ← "Here are your files"

OIDC (OAuth 2.0 + OIDC):
  GET https://oauth.example.com/userinfo (with access token)
  ← "You are: name=Alice, email=alice@example.com, ..."
  ↓
  Now we KNOW who the user is (authentication)
  AND we have permission to access their resources (authorization)
```

---

## Part 2: The Four Grant Types

OAuth 2.0 defines different "flows" for different scenarios.

### 1. Authorization Code Flow (MOST COMMON)

**Use case:** User logs in via third-party OAuth provider (Google, GitHub, etc.)

**Actors:**
- Resource Owner (User): "I want to log in"
- Client (Your app): "I need permission to access the user's data"
- Authorization Server: "Google login" / "GitHub login"
- Resource Server: Google Drive API, GitHub API, etc.

**Step-by-step:**

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: User clicks "Login with Google"                         │
│ Browser: GET /login on your-app.com                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: App redirects to Google                                 │
│ Browser: GET https://accounts.google.com/o/oauth2/auth         │
│          ?client_id=YOUR_CLIENT_ID                             │
│          &redirect_uri=https://your-app.com/oauth/callback     │
│          &scope=profile email                                  │
│          &state=random_string                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: User logs in and authorizes                             │
│ Google shows: "your-app.com wants to access:"                  │
│   • Your name and profile picture                              │
│   • Your email address                                         │
│ [Accept] [Deny]                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Google redirects back with authorization code           │
│ Browser: GET https://your-app.com/oauth/callback              │
│          ?code=4/0AX4XfW...                                   │
│          &state=random_string                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Your app backend exchanges code for token              │
│ Backend: POST https://oauth2.googleapis.com/token              │
│   client_id=YOUR_CLIENT_ID                                    │
│   client_secret=YOUR_SECRET (NEVER in browser)                │
│   code=4/0AX4XfW...                                           │
│   grant_type=authorization_code                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Google returns access token (+ optional refresh token) │
│ Response:                                                       │
│ {                                                               │
│   "access_token": "ya29.a0AfH6SMBu...",                       │
│   "expires_in": 3599,                                          │
│   "refresh_token": "1//0g...",                                 │
│   "scope": "profile email",                                    │
│   "token_type": "Bearer"                                       │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: App uses access token to get user info                 │
│ Backend: GET https://www.googleapis.com/oauth2/v1/userinfo    │
│          Authorization: Bearer ya29.a0AfH6SMBu...             │
│ Response: { id, name, email, picture }                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: App creates user session, logs user in                 │
│ Sets session cookie / JWT token                                │
└─────────────────────────────────────────────────────────────────┘
```

**Key Security Points:**
- Authorization code is single-use and expires quickly (10 minutes)
- Client secret is NEVER exposed to browser (backend only)
- `state` parameter prevents CSRF attacks
- User never gives password to your app

**Parameters Explained:**

| Param | Purpose | Example |
|-------|---------|---------|
| `client_id` | Identifies your app | 1234567890.apps.googleusercontent.com |
| `client_secret` | Proves your app is legit (backend only) | aBc123_XyZ... |
| `redirect_uri` | Where OAuth provider sends user back | https://yourapp.com/oauth/callback |
| `scope` | What permissions to request | profile email openid |
| `state` | Random string to prevent CSRF | a7f4h8k2m9p1 |
| `code` | Single-use authorization code | 4/0AX4XfWa... |

### 2. Implicit Flow (DEPRECATED - Don't Use)

**Was used for:** Single-page apps (SPAs) that can't securely store client_secret

**Why deprecated:**
- No client_secret means less secure
- Token exposed in URL fragments
- No refresh tokens

**What to use instead:** Authorization Code Flow with PKCE (Proof Key for Code Exchange)

### 3. Client Credentials Flow

**Use case:** Server-to-server communication (no user involved)

**Example:**
```
Your app backend wants to call another API.
Not on behalf of a user, but as itself.

POST https://oauth-provider.com/token
  client_id=your_app_id
  client_secret=your_app_secret
  grant_type=client_credentials
  scope=api.write

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**When to use:**
- Your backend calling another backend API
- Microservice authentication
- Admin operations
- Scheduled jobs accessing APIs

**Security:**
- No user involvement
- Client secret needed
- No refresh tokens (just request a new one when expired)

### 4. Device Flow

**Use case:** Devices without browsers (smart TVs, IoT devices, CLI tools)

**Flow:**

```
Step 1: Device requests device code
  POST /device_authorization
  client_id=my_app

Step 2: Server responds with user code + device code
  {
    "device_code": "ABC123DEF456...",
    "user_code": "LHJK-MNOP",
    "expires_in": 1800,
    "interval": 5,
    "verification_uri": "https://oauth.example.com/device"
  }

Step 3: Device shows user code to user
  "Please go to https://oauth.example.com/device"
  "Enter code: LHJK-MNOP"

Step 4: User opens browser, goes to URL, enters code

Step 5: Device polls for token (every 5 seconds)
  POST /token
  client_id=my_app
  device_code=ABC123DEF456...
  grant_type=urn:ietf:params:oauth:grant-type:device_code

Step 6: Once user authorizes, device gets token
  {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600
  }

Step 7: Device can now use token
```

**When to use:**
- Smart TVs requesting Netflix login
- IoT devices
- CLI tools (like AWS CLI, GitHub CLI)
- Devices without keyboards

---

## Part 3: Scopes (Permissions)

Scopes define what an app can do with your data.

### Scope Naming Conventions

Different OAuth providers use different formats:

**Google:**
```
https://www.googleapis.com/auth/drive.readonly
https://www.googleapis.com/auth/calendar
```

**GitHub:**
```
repo              # Full control of private and public repos
read:user         # Read user profile
write:repo_hook   # Write to repo webhooks
```

**Generic (OIDC standard):**
```
openid            # Request ID token (authentication)
profile           # Name, picture, etc.
email             # Email address
address           # User's address
phone             # Phone number
```

**Your own app (RESTful convention):**
```
read:books        # Can read books
write:books       # Can create/edit books
delete:books      # Can delete books
admin:users       # Can manage users
```

### Scope Best Practices

**DO:**
```
✅ Request only what you need
   scope=profile email
   NOT scope=profile email read:files write:files delete:files

✅ Use specific scopes
   scope=read:books
   NOT scope=*

✅ Explain why you need each scope
   "We need your email to send notifications"
   "We need your calendar to show free time slots"
```

**DON'T:**
```
❌ Request all scopes even if you don't use them
❌ Use overly broad scopes
❌ Hide what you're asking for
```

### Scope Validation

**On OAuth provider side:**

```javascript
// Define available scopes
const AVAILABLE_SCOPES = {
  'openid': 'Get your ID token (authentication)',
  'profile': 'Read your name and profile picture',
  'email': 'Read your email address',
  'write:posts': 'Create and edit posts',
  'read:comments': 'Read comments on posts',
  'admin': 'Full admin access'
};

// Validate requested scopes
function validateScopes(requestedScopes, availableScopes) {
  for (const scope of requestedScopes) {
    if (!availableScopes[scope]) {
      throw new Error(`Invalid scope: ${scope}`);
    }
  }
  return true;
}

// Check if token has required scope
function hasScope(token, requiredScope) {
  const tokenScopes = token.scope.split(' ');
  return tokenScopes.includes(requiredScope);
}
```

---

## Part 4: Authorization Code Flow Implementation

### Step-by-Step Implementation

**Step 1: Register your app**
```
Go to https://accounts.google.com/o/oauth2/console

Fill in:
- Redirect URIs: https://yourapp.com/oauth/callback
- Get: client_id, client_secret (KEEP SECRET!)
```

**Step 2: Login button on frontend**
```html
<a href="/login/google">Login with Google</a>
```

**Step 3: Backend route to initiate OAuth**
```typescript
app.get('/login/google', (req, res) => {
  const params = new URLSearchParams({
    client_id: process.env.GOOGLE_CLIENT_ID,
    redirect_uri: 'https://yourapp.com/oauth/callback',
    response_type: 'code',
    scope: 'openid profile email',
    state: generateRandomString(32) // CSRF protection
  });
  
  res.redirect(
    `https://accounts.google.com/o/oauth2/auth?${params.toString()}`
  );
});
```

**Step 4: Callback route**
```typescript
app.get('/oauth/callback', async (req, res) => {
  const { code, state } = req.query;
  
  // Verify state (prevent CSRF)
  if (!verifyState(state)) {
    return res.status(403).json({ error: 'Invalid state' });
  }
  
  // Exchange code for token
  const tokenResponse = await fetch(
    'https://oauth2.googleapis.com/token',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_id: process.env.GOOGLE_CLIENT_ID,
        client_secret: process.env.GOOGLE_CLIENT_SECRET,
        code,
        grant_type: 'authorization_code',
        redirect_uri: 'https://yourapp.com/oauth/callback'
      })
    }
  );
  
  const tokens = await tokenResponse.json();
  // { access_token, expires_in, refresh_token, ... }
  
  // Get user info
  const userInfoResponse = await fetch(
    'https://www.googleapis.com/oauth2/v1/userinfo',
    {
      headers: {
        Authorization: `Bearer ${tokens.access_token}`
      }
    }
  );
  
  const userInfo = await userInfoResponse.json();
  // { id, name, email, picture }
  
  // Find or create user in your DB
  let user = await User.findByEmail(userInfo.email);
  if (!user) {
    user = await User.create({
      email: userInfo.email,
      name: userInfo.name,
      googleId: userInfo.id,
      picture: userInfo.picture
    });
  }
  
  // Create session/JWT for your app
  const sessionToken = createSessionToken(user.id);
  
  res.cookie('sessionToken', sessionToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict'
  });
  
  res.redirect('/');
});
```

---

## Part 5: OpenID Connect (OIDC)

### What is OpenID Connect?

```
OAuth 2.0 = Authorization only
  "What can you access?"
  Returns: access_token (for calling APIs)

OpenID Connect = OAuth 2.0 + Authentication
  "Who are you?" + "What can you access?"
  Returns: access_token + id_token (JSON Web Token with user info)
```

### OIDC vs OAuth 2.0

| Aspect | OAuth 2.0 | OIDC |
|--------|-----------|------|
| Purpose | Authorization | Authentication + Authorization |
| Tokens | access_token | access_token + id_token |
| User info | Call /userinfo endpoint | Decode id_token (JWT) |
| Scope | read, write, etc. | openid, profile, email |
| Discovery | No | Yes (/well-known/openid-configuration) |
| Use case | "What can you do?" | "Who are you?" |

### Getting an ID Token with OIDC

**The key difference: Add `openid` scope**

```typescript
// OAuth 2.0 (just authorization)
scope=profile email

// OIDC (authentication + authorization)
scope=openid profile email

// Response includes:
{
  "access_token": "eyJhbGc...",
  "id_token": "eyJhbGc...",  // ← This is new in OIDC
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Decoding ID Token

ID token is a JWT. Decode it to get user info:

```typescript
const jwt = require('jsonwebtoken');

// Get the id_token from OAuth response
const idToken = oauthResponse.id_token;

// Decode (verify signature if needed)
const decoded = jwt.decode(idToken);

console.log(decoded);
// {
//   iss: "https://accounts.google.com",
//   sub: "1234567890",
//   aud: "YOUR_CLIENT_ID",
//   iat: 1516239022,
//   exp: 1516242622,
//   name: "Alice Smith",
//   email: "alice@example.com",
//   picture: "https://...",
//   email_verified: true
// }
```

### OIDC Discovery

OIDC providers publish their configuration at a well-known URL:

```
GET /.well-known/openid-configuration

Response:
{
  "issuer": "https://accounts.google.com",
  "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
  "token_endpoint": "https://oauth2.googleapis.com/token",
  "userinfo_endpoint": "https://www.googleapis.com/oauth2/v1/userinfo",
  "jwks_uri": "https://www.googleapis.com/oauth2/v1/certs",
  "scopes_supported": ["openid", "profile", "email"],
  ...
}
```

---

## Part 6: Security Best Practices

### Authorization Code Flow Security

```
✅ ALWAYS:
  - Use HTTPS
  - Validate state parameter (CSRF protection)
  - Keep client_secret secret (backend only)
  - Verify authorization code is single-use
  - Set code expiry to ~10 minutes
  - Validate redirect_uri matches registered

❌ NEVER:
  - Send authorization code in URLs (use POST)
  - Expose client_secret in browser
  - Skip state validation
  - Trust access_token claims directly
  - Use client credentials in SPAs
```

### Scope Security

```
✅ Minimal scope principle
  Only request what you need

✅ Explain scope to user
  "We need your email to send receipts"
  NOT just a checkbox

❌ Don't request admin scope if you only need read
❌ Don't request scopes "just in case"
```

### Token Security

```
✅ Access tokens:
  - Store in memory (if possible)
  - OR httpOnly cookie (best)
  - Include in Authorization header

✅ Refresh tokens:
  - Store in httpOnly cookie
  - NEVER send to frontend
  - Rotate on use

❌ Don't store tokens in localStorage (XSS vulnerability)
❌ Don't expose tokens in URLs
```

### PKCE (For SPAs)

For single-page apps, use PKCE to make code grant safer:

```typescript
// Frontend: Generate code_challenge
const codeVerifier = generateRandomString(128);
const codeChallenge = base64url(sha256(codeVerifier));

// Redirect with code_challenge
window.location.href = `https://oauth.example.com/auth
  ?client_id=...
  &code_challenge=${codeChallenge}
  &code_challenge_method=S256
  ...`;

// Backend: Use code_verifier when exchanging code
POST /token
  code=...
  code_verifier=${codeVerifier}
  ...
```

---

## Part 7: Common Mistakes

### Mistake 1: Confusing OAuth with Authentication

```
❌ WRONG: "We use OAuth for authentication"
✅ CORRECT: "We use OAuth for authorization; we use OIDC for authentication"
          OR "We use OAuth to let users sign in with their Google account"
```

### Mistake 2: Using Implicit Flow

```
❌ WRONG:
  response_type=token  (returns access_token directly)

✅ CORRECT:
  response_type=code   (returns authorization code)
  (Then exchange for token on backend)
```

### Mistake 3: Storing Tokens Unsafely

```
❌ WRONG:
  localStorage.setItem('accessToken', token);
  // XSS vulnerability: token exposed if JavaScript is compromised

✅ CORRECT:
  Set-Cookie: refreshToken=...; HttpOnly; Secure; SameSite=Strict
  // Token inaccessible to JavaScript
```

### Mistake 4: Not Validating Scope

```
❌ WRONG:
  User requests admin scope
  Just give it to them

✅ CORRECT:
  Define available scopes
  Validate requested scopes
  Only grant what's registered
```

### Mistake 5: Exposing Client Secret

```
❌ WRONG:
  client_secret in frontend code
  client_secret in GitHub repo (public)

✅ CORRECT:
  Keep in backend environment variables
  Use secrets management (vault, etc)
  Rotate regularly
```

---

## Summary

**OAuth 2.0 is authorization** - decides what you can access
**OpenID Connect adds authentication** - proves who you are

**Authorization Code Flow:**
1. User clicks "Login with [Provider]"
2. App redirects to provider's login
3. User authorizes
4. Provider gives app an authorization code
5. App backend exchanges code for token (using client_secret)
6. App can now access user's resources

**Four grant types:**
- Authorization Code: User login (most common)
- Implicit: SPAs (deprecated)
- Client Credentials: Server-to-server
- Device: Smart TVs, IoT devices

**Always use HTTPS, validate state, protect secrets, and request minimal scopes.**
