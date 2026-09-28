# Day 11: Google OAuth Implementation Checklist

---

## Part 1: Google Cloud Setup ✓

### Create Google Cloud Project
- [ ] Go to https://console.cloud.google.com/
- [ ] Click "NEW PROJECT"
- [ ] Name: "My Auth App"
- [ ] Click "CREATE"
- [ ] Wait for project to be created

### Enable Google+ API
- [ ] Go to "APIs & Services" → "Library"
- [ ] Search for "Google+ API" (or "People")
- [ ] Click on result
- [ ] Click "ENABLE"

### Create OAuth Consent Screen
- [ ] Go to "OAuth consent screen"
- [ ] Choose: "External"
- [ ] Fill in:
  - [ ] App name: "My Auth App"
  - [ ] User support email: your@email.com
  - [ ] Developer contact: your@email.com
- [ ] "SAVE AND CONTINUE"
- [ ] Add scopes:
  - [ ] openid
  - [ ] email
  - [ ] profile
- [ ] "UPDATE"
- [ ] "SAVE AND CONTINUE"
- [ ] Add test users:
  - [ ] Add your email address
- [ ] "SAVE AND CONTINUE"
- [ ] Review and done!

### Create OAuth 2.0 Credentials
- [ ] Go to "Credentials"
- [ ] Click "+ CREATE CREDENTIALS"
- [ ] Choose "OAuth 2.0 Client ID"
- [ ] Select "Web application"
- [ ] Name: "Web Client 1"
- [ ] Authorized JavaScript origins:
  - [ ] http://localhost:8000
  - [ ] http://localhost:3000 (optional)
- [ ] Authorized redirect URIs:
  - [ ] http://localhost:8000/auth/google/callback
- [ ] Click "CREATE"
- [ ] Copy credentials:
  - [ ] Client ID: ___________________
  - [ ] Client Secret: ___________________

---

## Part 2: Local Setup ✓

### Create Project Directory
- [ ] Create folder: `mkdir my-auth-app && cd my-auth-app`
- [ ] Create `.env` file with:
  ```
  GOOGLE_CLIENT_ID=paste_here
  GOOGLE_CLIENT_SECRET=paste_here
  GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
  SESSION_SECRET=dev-secret-change-in-production
  DEBUG=True
  PORT=8000
  ```
- [ ] Create `.gitignore`:
  ```
  .env
  __pycache__/
  *.pyc
  .pytest_cache/
  ```

### Install Python Packages
- [ ] `pip install -r requirements.txt` contains:
  - [ ] fastapi==0.104.1
  - [ ] uvicorn==0.24.0
  - [ ] httpx==0.25.1
  - [ ] python-dotenv==1.0.0
  - [ ] PyJWT==2.8.1
  - [ ] pytest==7.4.3
  - [ ] pytest-asyncio==0.21.1
  - [ ] pydantic==2.5.0

### Verify Installation
- [ ] `python -c "import httpx; print(httpx.__version__)"`
- [ ] `python -c "import fastapi; print(fastapi.__version__)"`
- [ ] `python -c "import jwt; print(jwt.__version__)"`

---

## Part 3: Implementation ✓

### OAuth Service (`oauth2-google-implementation.py`)
- [ ] Config class with:
  - [ ] GOOGLE_CLIENT_ID
  - [ ] GOOGLE_CLIENT_SECRET
  - [ ] GOOGLE_REDIRECT_URI
  - [ ] Google endpoints (auth, token, userinfo)
  - [ ] Scopes
  - [ ] Session configuration
  - [ ] validate() method

- [ ] StateStore class:
  - [ ] generate() - Create random state
  - [ ] validate() - Check and mark as used
  - [ ] CSRF protection (prevent replay)
  - [ ] Expiration (10 minutes)
  - [ ] cleanup() - Remove old states

- [ ] GoogleOAuthService class:
  - [ ] generate_authorization_url() - Step 1-2
  - [ ] exchange_code_for_token() - Step 4-5 (async)
  - [ ] decode_id_token() - Step 6-7
  - [ ] get_user_info() - Alternative to decode (async)

- [ ] UserDatabase class:
  - [ ] create_user()
  - [ ] find_by_google_id()
  - [ ] find_by_email()
  - [ ] update_last_login()

- [ ] SessionManager class:
  - [ ] create_session()
  - [ ] validate_session()
  - [ ] revoke_session()
  - [ ] Session expiration

- [ ] FastAPI Application:
  - [ ] Initialize all components
  - [ ] Validate configuration on startup

### Routes
- [ ] GET `/` - Home page (login button)
- [ ] GET `/auth/google/login` - Start OAuth flow
  - [ ] Generate authorization URL
  - [ ] Set state in secure cookie
  - [ ] Redirect to Google
  
- [ ] GET `/auth/google/callback` - Handle Google callback
  - [ ] Validate state (CSRF)
  - [ ] Exchange code for token
  - [ ] Decode ID token
  - [ ] Find or create user
  - [ ] Create session
  - [ ] Redirect to dashboard
  
- [ ] GET `/dashboard` - Protected route
  - [ ] Check session cookie
  - [ ] Validate session
  - [ ] Return user info
  
- [ ] GET `/auth/logout` - Logout
  - [ ] Delete session cookie
  - [ ] Revoke session
  - [ ] Redirect to home

- [ ] GET `/health` - Health check

- [ ] GET `/users` - Debug endpoint (remove in production)

---

## Part 4: Testing ✓

### Unit Tests
- [ ] Config validation
- [ ] State generation and validation
- [ ] CSRF protection (state single-use)
- [ ] State expiration
- [ ] User creation
- [ ] User lookup (by Google ID, by email)
- [ ] Session creation
- [ ] Session validation
- [ ] Session expiration
- [ ] Session revocation

### Integration Tests
- [ ] Complete OAuth flow simulation
- [ ] Multiple concurrent flows
- [ ] State cleanup

### Security Tests
- [ ] State prevents CSRF
- [ ] Client secret not in URL
- [ ] Session expiration works
- [ ] Session revocation works

### Run Tests
- [ ] `pytest oauth2-google-tests.py -v`
- [ ] All tests pass ✓

---

## Part 5: Manual Testing ✓

### Test Locally
1. [ ] Start server: `python oauth2-google-implementation.py`
2. [ ] Visit: http://localhost:8000
3. [ ] Click "Login with Google"
4. [ ] Browser redirects to Google login
5. [ ] Log in with your Google account
6. [ ] See consent screen:
   - [ ] "My Auth App wants to access"
   - [ ] Shows: name, profile, email
7. [ ] Click [Allow]
8. [ ] Redirected to dashboard
9. [ ] See your info:
   - [ ] Email
   - [ ] Name
   - [ ] Picture
   - [ ] Created date
   - [ ] Last login date
10. [ ] Click logout
11. [ ] Redirected to home
12. [ ] Try to access /dashboard - should redirect to login

### Test Error Cases
- [ ] Deny permissions - should show error
- [ ] Expire session - should require login
- [ ] Manually clear session cookie - should require login
- [ ] Use wrong redirect URL - should get error from Google
- [ ] Use expired code - should fail

---

## Part 6: Security Hardening ✓

### Credentials
- [ ] Never commit .env to git
- [ ] Add .env to .gitignore
- [ ] Use strong SESSION_SECRET (generate: `openssl rand -hex 32`)
- [ ] Keep CLIENT_SECRET secret
- [ ] Don't log sensitive data

### Cookies
- [ ] httpOnly=True (prevent JavaScript access)
- [ ] Secure=False for localhost, True for production
- [ ] SameSite=strict (CSRF protection)

### State Management
- [ ] Generate random state
- [ ] Validate on callback
- [ ] Mark as used (single-use)
- [ ] Expire after 10 minutes
- [ ] Clean up old states

### Authorization Code
- [ ] Single-use enforcement
- [ ] Expires quickly (~10 minutes)
- [ ] Tied to specific client_id
- [ ] Never log or expose

### Redirect URI
- [ ] Registered in Google Console
- [ ] Must match exactly (case-sensitive)
- [ ] Use HTTPS in production
- [ ] Validate against whitelist

---

## Part 7: Database Setup ✓

### Current (Mock)
- [ ] UserDatabase class
- [ ] In-memory storage
- [ ] Good for testing

### For Production
- [ ] Replace with real database:
  - [ ] PostgreSQL, MongoDB, or other
  - [ ] ORM: SQLAlchemy, Tortoise, etc.
- [ ] Add schema:
  - [ ] users table
  - [ ] sessions table
  - [ ] refresh_tokens table
- [ ] Add indexes:
  - [ ] google_id (for lookups)
  - [ ] email (for lookups)
  - [ ] session_id (for lookups)

---

## Part 8: Logging and Monitoring ✓

### Add Logging
- [ ] Log successful logins
- [ ] Log failed authentication
- [ ] Log state validation failures
- [ ] Log token exchange errors
- [ ] Don't log tokens, passwords, or personal data

### Monitor
- [ ] Track failed logins
- [ ] Track suspicious activity
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Alert on repeated failures

---

## Part 9: Documentation ✓

### Create Docs
- [ ] README.md with setup instructions
- [ ] API documentation (FastAPI docs at /docs)
- [ ] Configuration guide
- [ ] Troubleshooting guide
- [ ] Architecture diagram

### Comments in Code
- [ ] Document each function
- [ ] Explain CSRF protection
- [ ] Explain HTTPS requirements
- [ ] Security notes
- [ ] TODO items for production

---

## Part 10: Deployment Prep ✓

### Before Production
- [ ] Change DEBUG=False
- [ ] Use strong SESSION_SECRET
- [ ] Set up HTTPS/SSL
- [ ] Use production database
- [ ] Configure email notifications
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test full flow in staging
- [ ] Register production URL in Google Console
- [ ] Get new client ID/secret for production

### Deployment Steps
- [ ] Update google-oauth-setup.md with production URL
- [ ] Register redirect URI: https://example.com/auth/google/callback
- [ ] Get new client ID and secret
- [ ] Update .env variables
- [ ] Deploy to server
- [ ] Test login flow
- [ ] Monitor for errors

### Post-Deployment
- [ ] Verify HTTPS works
- [ ] Test complete flow
- [ ] Monitor error logs
- [ ] Monitor user signups
- [ ] Respond to issues
- [ ] Collect feedback

---

## Part 11: Advanced Features (Optional)

- [ ] Refresh tokens (auto-refresh access tokens)
- [ ] Remember device (don't ask for consent again)
- [ ] Link multiple providers (Google + GitHub)
- [ ] Email verification
- [ ] 2FA (two-factor authentication)
- [ ] Rate limiting
- [ ] Account linking
- [ ] Profile updates from provider

---

## Summary

**What you have:**
- ✅ Google OAuth credentials
- ✅ Complete Python implementation
- ✅ Working login/logout
- ✅ Session management
- ✅ CSRF protection
- ✅ Test suite
- ✅ Security hardening
- ✅ Production checklist

**Key insights:**
1. App never sees password (Google handles login)
2. Authorization code is single-use (CSRF safe)
3. Client secret stays backend-only (never browser)
4. State prevents CSRF attacks (validate on callback)
5. Sessions are time-limited (auto-expire)

**Files created:**
- google-oauth-setup.md (Step-by-step setup)
- oauth2-google-implementation.py (Working code)
- oauth2-google-tests.py (Test suite)
- requirements.txt (Dependencies)
- DAY11_QUICK_START.md (Quick reference)
- This checklist

**Total time invested:**
- Setup: 15-30 minutes
- Implementation: 1-2 hours
- Testing: 30 minutes
- Understanding: Priceless!

---

## Status

- [x] Day 11 Complete!
- [x] Google OAuth working locally
- [x] All tests passing
- [x] Ready for production (with security updates)
- [x] Well documented

**Next steps:** Deploy to production! 🚀
