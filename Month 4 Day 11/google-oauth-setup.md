# Day 11: Google OAuth Setup - Complete Guide

## CRITICAL RULE
> **Your app never sees the Google password.**
> User logs in directly to Google.
> Google gives your app a token.
> You use token to access user's data.

---

## Part 1: Create Google Cloud Project

### Step 1: Go to Google Cloud Console
```
https://console.cloud.google.com/
```
- Click "Sign in" (use your personal Google account)
- You'll see dashboard with projects

### Step 2: Create New Project
```
1. At top, click the project selector dropdown
2. Click "NEW PROJECT"
3. Project name: "My Auth App" (or any name)
4. Organization: Leave blank (unless using workspace)
5. Click "CREATE"
   → Project created! (may take a few seconds)
6. Wait for notification at top-right: "Project created"
```

### Step 3: Enable Google+ API
```
1. Go to APIs & Services
   Menu (☰) → "APIs & Services" → "Library"

2. Search for "Google+ API"
   (or just search "people")

3. Click "Google+ API" result

4. Click the blue "ENABLE" button
   → Now enabled for your project

5. You'll see "Google+ API" page with details
```

---

## Part 2: Create OAuth 2.0 Credentials

### Step 1: Create OAuth Consent Screen
```
1. Menu (☰) → "APIs & Services" → "OAuth consent screen"

2. Choose user type:
   ✓ External (for testing, limits to 100 test users)
   ✓ Internal (only if using Google Workspace)
   
   Select: EXTERNAL (for testing)

3. Click "CREATE"

4. Fill in the form:
   
   App name: "My Auth App"
   
   User support email: 
     (your email: example@gmail.com)
   
   Developer contact:
     (your email again)

5. Scroll down, click "SAVE AND CONTINUE"

6. Scopes page: Click "ADD OR REMOVE SCOPES"
   Required scopes:
     ✓ https://www.googleapis.com/auth/userinfo.email
     ✓ https://www.googleapis.com/auth/userinfo.profile
   
   Or search for:
     • openid
     • email
     • profile
   
   Select all three, click "UPDATE"

7. Click "SAVE AND CONTINUE"

8. Test users page: Click "ADD USERS"
   Add your email address (example@gmail.com)
   This lets you test without restrictions

9. Click "SAVE AND CONTINUE"

10. Review and click "BACK TO DASHBOARD"
```

### Step 2: Create OAuth 2.0 Client ID
```
1. Menu (☰) → "APIs & Services" → "Credentials"

2. Click blue "+ CREATE CREDENTIALS" button

3. Choose: "OAuth 2.0 Client ID"

4. You'll see: "You need to create an OAuth 2.0 Client ID"

5. First time? Click "CREATE OAUTH CLIENT ID"

6. Select application type:
   ✓ Web application (your choice)
   
   OR
   
   ✓ Desktop application (if testing locally)

7. Configure OAuth Client:
   
   Name: "Web Client 1" (or any name)
   
   Authorized JavaScript origins:
     Click "Add URI"
     Add: http://localhost:8000
     Add: http://localhost:3000 (if SPA)
   
   Authorized redirect URIs:
     Click "Add URI"
     Add: http://localhost:8000/auth/google/callback
     Add: http://localhost:8000/oauth/callback (alternative)
   
   Leave other fields blank for now

8. Click "CREATE"

9. You'll see credentials dialog:
   
   Client ID: "123456789-abcdefg.apps.googleusercontent.com"
   Client Secret: "GOCSPX-aBcDeFgHiJk..."
   
   ⚠️ IMPORTANT: Copy these values!
```

### Step 3: Download and Save Credentials
```
On the credentials dialog:

Option A: Download JSON
  1. Click "DOWNLOAD" button (right side)
  2. Saves as: google-oauth.json
  3. Keep this file SECURE (don't commit to git)

Option B: Copy to file
  1. Click on the credential
  2. Copy Client ID
  3. Copy Client Secret
  4. Save to: .env file (NOT git)
   
   .env:
   GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-aBcDeFgHiJk...
```

---

## Part 3: Verify Setup

### Check Google OAuth Credentials
```
1. Go back to "APIs & Services" → "Credentials"

2. You should see:
   
   OAuth 2.0 Client IDs
   ┌─────────────────────────────────────┐
   │ Web Client 1                        │
   │ Client ID: 123456...                │
   │ Redirect URIs: localhost:8000/...   │
   └─────────────────────────────────────┘

3. If you need to edit:
   Click the pencil icon (✎)
   
4. To view secret again:
   Click on the credential name
```

### Verify Redirect URI
```
Your redirect URI MUST match EXACTLY:

What you registered in Google Console:
  http://localhost:8000/auth/google/callback

What your app expects:
  app.get('/auth/google/callback')
  
These must match character-for-character!

Common mistakes:
  ❌ http://localhost:8000/callback (missing /auth/google)
  ❌ http://localhost:8000/ (too generic)
  ❌ http://127.0.0.1:8000/auth/google/callback (different host)
  ❌ https://localhost:8000/... (wrong protocol)
```

---

## Part 4: Environment Setup

### Create .env file
```bash
# .env (NEVER commit to git!)

GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-aBcDeFgHiJk...
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Session secret (generate with: openssl rand -hex 32)
SESSION_SECRET=abcdef1234567890abcdef1234567890

# Server
PORT=8000
DEBUG=True
```

### Add to .gitignore
```
# .gitignore

.env
google-oauth.json
*.key
*.secret
```

### Load environment variables
```python
# Python with python-dotenv

from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
```

---

## Part 5: Install Dependencies

### Install httpx
```bash
# httpx for HTTP requests
pip install httpx

# FastAPI (if building API)
pip install fastapi uvicorn

# For .env files
pip install python-dotenv

# For JWT (if building auth)
pip install PyJWT

# For sessions
pip install python-multipart
```

### Verify Installation
```bash
python -c "import httpx; print(httpx.__version__)"
# Output: 0.24.1 (or similar)
```

---

## Part 6: Understanding Google OAuth Flow

### The Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User clicks "Login with Google"                    │
│ Browser: GET /auth/google/login                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Your app redirects to Google                        │
│ Browser: GET https://accounts.google.com/o/oauth2/v2/auth  │
│   ?client_id=YOUR_ID                                        │
│   &redirect_uri=http://localhost:8000/auth/google/callback │
│   &response_type=code                                       │
│   &scope=openid+profile+email                              │
│   &state=random_string                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Google's consent screen                             │
│ User sees: "My Auth App wants to access:"                  │
│   ☑ Your name and profile picture                           │
│   ☑ Your email address                                      │
│ User clicks: [Allow]                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Google redirects back to YOUR app                   │
│ Browser: GET http://localhost:8000/auth/google/callback    │
│   ?code=4/0AX4XfW7...                                      │
│   &state=random_string                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Your app backend exchanges code for token           │
│ Backend: POST https://oauth2.googleapis.com/token           │
│   client_id=YOUR_ID                                         │
│   client_secret=YOUR_SECRET                                 │
│   code=4/0AX4XfW7...                                       │
│   grant_type=authorization_code                             │
│   redirect_uri=http://localhost:8000/auth/google/callback  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Google returns access token                         │
│ Response:                                                   │
│ {                                                           │
│   "access_token": "ya29.a0AfH6SMBu...",                   │
│   "expires_in": 3599,                                       │
│   "refresh_token": "1//0g...",                             │
│   "scope": "openid email profile",                          │
│   "token_type": "Bearer",                                   │
│   "id_token": "eyJhbGc..."  ← JWT with user info!          │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Get user info from ID token                         │
│ Decode JWT (id_token):                                      │
│ {                                                           │
│   "iss": "https://accounts.google.com",                    │
│   "sub": "1234567890",                                      │
│   "aud": "YOUR_CLIENT_ID",                                  │
│   "iat": 1516239022,                                        │
│   "exp": 1516242622,                                        │
│   "email": "user@gmail.com",                                │
│   "email_verified": true,                                   │
│   "name": "Alice Smith",                                    │
│   "picture": "https://..."                                  │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Create user in database if needed                   │
│ Backend: INSERT INTO users (email, name, picture)          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: Create session/JWT                                  │
│ Backend: Create session token                               │
│ Set session cookie (httpOnly)                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 10: User is logged in!                                 │
│ Browser redirects to: /dashboard                            │
└─────────────────────────────────────────────────────────────┘
```

### Key Points

**Your app never sees user's password:**
- User logs in directly to Google
- Google asks user for permission
- Google gives your app a token
- Your app uses token to access user data

**The Authorization Code is single-use:**
- Google generates: 4/0AX4XfW7...
- You exchange it for token (one time only)
- Code expires in ~10 minutes
- If code is stolen, can only be used once

**The ID Token is a JWT:**
- Contains user info (email, name, picture)
- No need to call /userinfo endpoint
- Decode it with PyJWT: jwt.decode(id_token, options={"verify_signature": False})

---

## Part 7: Common Mistakes

### ❌ Mistake 1: Redirect URI Mismatch
```
Registered: http://localhost:8000/auth/google/callback
Code:       GET /auth/google/callback

Google responds:
  error=redirect_uri_mismatch
  
FIX: Make sure they match EXACTLY
```

### ❌ Mistake 2: Forgetting Scopes
```
Registered with scopes: openid, email, profile
Requested with scopes: (empty)

Google might ask user again for permission
or return limited data

FIX: Always request the scopes you registered
```

### ❌ Mistake 3: Using Development Redirect in Production
```
Development: http://localhost:8000/auth/google/callback
Production:  https://example.com/auth/google/callback

These are DIFFERENT URIs!
Need separate Google OAuth credentials for each

FIX: Register both URIs, or use different projects
```

### ❌ Mistake 4: Exposing Client Secret
```
❌ WRONG:
  GOOGLE_CLIENT_SECRET in frontend code
  GOOGLE_CLIENT_SECRET in public GitHub repo
  GOOGLE_CLIENT_SECRET in git history

✅ CORRECT:
  Keep in backend .env file (don't commit)
  Load at runtime from environment variables
  Use .gitignore to exclude .env
```

### ❌ Mistake 5: Not Validating State
```
Attacker:
  1. Takes your authorization code
  2. Tries to use it with different 'state'
  3. Your app should reject it

FIX: Always validate state matches
```

### ❌ Mistake 6: Trusting Token Claims Without Verification
```
❌ Just decode JWT without verification
  jwt.decode(id_token)  # Don't do this!

✅ Verify the JWT signature
  jwt.decode(id_token, key=public_key, algorithms=['RS256'])
```

---

## Part 8: Testing Your Setup

### Test 1: Verify Credentials Work
```bash
# Simple test to verify client_id and client_secret

python
```

```python
import httpx

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REDIRECT_URI = "http://localhost:8000/auth/google/callback"

# Test token exchange (with fake code)
# Don't worry if this fails - we're just checking connectivity

response = httpx.post(
    'https://oauth2.googleapis.com/token',
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': 'fake_code',  # This will fail, that's OK
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
)

print(response.status_code)
# Should be 400 (bad request) because code is fake
# If it's 401 or 403, credentials are wrong
# If connection error, check internet/firewall
```

### Test 2: Build and Run Login Endpoint
```python
# See implementation in oauth2-google-implementation.py
# Test by visiting: http://localhost:8000/auth/google/login
```

### Test 3: Test Consent Screen
```
1. Start your app: python app.py
2. Visit: http://localhost:8000/auth/google/login
3. Browser redirects to Google login
4. You should see:
   "Sign in with your Google Account"
5. Log in
6. You should see consent screen:
   "My Auth App wants to access:
    ☑ Your name and profile picture
    ☑ Your email address
    [Allow] [Deny]"
7. Click [Allow]
8. Browser redirects back to: 
   http://localhost:8000/auth/google/callback?code=...&state=...
```

---

## Part 9: Troubleshooting

### Issue: "redirect_uri_mismatch"
```
Error: redirect_uri_mismatch

Causes:
  1. Redirect URI in code doesn't match Google Console
  2. Case sensitivity (http vs https)
  3. Extra slash (/ vs //)
  4. Different port (8000 vs 8001)
  5. Domain typo (localhost vs 127.0.0.1)

Fix:
  1. Copy from Google Console
  2. Paste into code exactly
  3. Use string comparison to verify they match
```

### Issue: "invalid_client"
```
Error: invalid_client

Causes:
  1. Client ID is wrong
  2. Client Secret is wrong
  3. Using wrong project (multiple projects)

Fix:
  1. Verify credentials in Google Console
  2. Copy/paste again (no typos)
  3. Check you're using correct project
```

### Issue: "Invalid Scopes"
```
Error: Invalid Scopes: ["https://www.googleapis.com/auth/invalid"]

Causes:
  1. Typo in scope name
  2. Using scope not enabled for app

Fix:
  1. Check scope spelling
  2. Verify scope is enabled in Google Console
```

### Issue: "The redirect_uri does not start with the registered URI"
```
Error: This error might be shown if:
  Registered: http://localhost:8000/auth/google/callback
  But passed:  http://localhost:8000/auth/google/callback?extra=param

Causes:
  1. URL parameters added to redirect_uri

Fix:
  1. Don't add query params to redirect_uri in auth URL
```

### Issue: "User hasn't granted app permission"
```
Error when exchanging code for token

Causes:
  1. User clicked [Deny] on consent screen
  2. Code expired
  3. Code already used

Fix:
  1. Ask user to log in again
  2. Start from beginning
```

---

## Part 10: Quick Reference

### Google OAuth URLs

```
Authorization: https://accounts.google.com/o/oauth2/v2/auth
Token: https://oauth2.googleapis.com/token
UserInfo: https://www.googleapis.com/oauth2/v1/userinfo
Config: https://accounts.google.com/.well-known/openid-configuration
```

### Required Query Parameters

| Param | Value | Example |
|-------|-------|---------|
| client_id | From Google Console | 123456789-abcdefg.apps.googleusercontent.com |
| redirect_uri | Must be registered | http://localhost:8000/auth/google/callback |
| response_type | Always "code" | code |
| scope | Space-separated | openid profile email |
| state | Random string | abc123def456 |

### Response from /oauth2/v2/auth (if user allows)

```
HTTP 302 Redirect to:
  http://localhost:8000/auth/google/callback?
    code=4/0AX4XfW7...&
    state=abc123def456&
    scope=openid+profile+email+https://...
```

### Request to /token

```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
code=4/0AX4XfW7...&
grant_type=authorization_code&
redirect_uri=http://localhost:8000/auth/google/callback
```

### Response from /token

```json
{
  "access_token": "ya29.a0AfH6SMBu...",
  "expires_in": 3599,
  "refresh_token": "1//0g...",
  "scope": "openid email profile ...",
  "token_type": "Bearer",
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

---

## Summary

1. **Create Google Cloud Project** - Console setup
2. **Enable Google+ API** - Let your project use OAuth
3. **Create OAuth Consent Screen** - Configure what user sees
4. **Create OAuth Credentials** - Get client_id and client_secret
5. **Add Redirect URI** - Register where Google sends user back
6. **Save to .env** - Keep credentials secure
7. **Install httpx** - For making HTTP requests
8. **Understand the flow** - User → Google → Your app
9. **Test** - Verify everything works
10. **Deploy** - Change to production redirect URI

**Key insight**: Your app never sees the password. Google handles login. You get a token. Done.
