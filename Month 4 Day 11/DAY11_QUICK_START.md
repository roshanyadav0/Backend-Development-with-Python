# Day 11: Google OAuth Quick Start

## 5-Minute Setup

### Step 1: Create .env file
```bash
# .env
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
SESSION_SECRET=dev-secret-change-in-production
DEBUG=True
PORT=8000
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the app
```bash
python oauth2-google-implementation.py
```

### Step 4: Test
```
Visit: http://localhost:8000
Click: "Login with Google"
Login with your Google account
See your profile!
```

---

## File Structure

```
project/
├── .env                                  # Credentials (don't commit!)
├── requirements.txt                      # Python packages
├── oauth2-google-implementation.py       # Main app
├── oauth2-google-tests.py               # Tests
├── google-oauth-setup.md                # Setup guide
├── DAY11_CHECKLIST.md                   # Checklist
└── .gitignore                            # Ignore .env
```

---

## Endpoints

### Public
- `GET /` - Home page
- `GET /auth/google/login` - Start OAuth flow
- `GET /auth/google/callback` - Google redirects here
- `GET /health` - Health check

### Protected (require session)
- `GET /dashboard` - Show user info
- `GET /auth/logout` - Logout

### Debug (remove in production)
- `GET /users` - List all users

---

## The Complete Flow

```
User                  Your App              Google
 │                        │                   │
 ├──────Login──────────→   │                   │
 │                   [Generate state]         │
 │                   [Redirect URL]           │
 │                        │                   │
 │◄──────Redirect to Google's login───────   │
 │                                            │
 ├─────────────Login to Google──────────────→│
 │                                            │
 │                                   [Consent screen]
 │                                            │
 │◄───────Redirect + code────────────────────┤
 │         (back to your app)                 │
 │                                            │
 │              Exchange code for token       │
 │                   (backend)                │
 │                        │                   │
 │                        ├──Post token req──→│
 │                        │                   │
 │                        │◄──Return token────┤
 │                        │                   │
 │              [Decode ID token]            │
 │              [Create user/session]         │
 │                        │                   │
 │◄────────Logged in!─────┤                   │
```

---

## Key Files

### requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.1
pydantic==2.5.0
python-dotenv==1.0.0
PyJWT==2.8.1
pytest==7.4.3
pytest-asyncio==0.21.1
```

### .gitignore
```
.env
*.key
*.secret
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
```

---

## Security Checklist

✅ **DO:**
- Use .env file for credentials
- Add .env to .gitignore
- Use httpOnly cookies for session
- Validate state on callback
- Exchange code on backend (not browser)
- Use HTTPS in production
- Rotate client_secret regularly

❌ **DON'T:**
- Expose client_secret in browser
- Commit .env to git
- Use plain HTTP in production
- Skip state validation
- Trust tokens without verification
- Log sensitive data

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | From Google Console | `123456789-abcdefg.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | From Google Console | `GOCSPX-aBcDeFgHiJk...` |
| `GOOGLE_REDIRECT_URI` | Must match registered | `http://localhost:8000/auth/google/callback` |
| `SESSION_SECRET` | For signing sessions | `openssl rand -hex 32` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `True` |

---

## Testing

### Run all tests
```bash
pytest oauth2-google-tests.py -v
```

### Run specific test class
```bash
pytest oauth2-google-tests.py::TestStateStore -v
```

### Run specific test
```bash
pytest oauth2-google-tests.py::TestStateStore::test_generate_state_creates_unique_strings -v
```

### Run with coverage
```bash
pytest oauth2-google-tests.py --cov=oauth2_google_implementation
```

---

## Troubleshooting

### "redirect_uri_mismatch"
**Problem:** URL in code doesn't match Google Console
**Solution:** Copy redirect_uri from Google Console, paste into code

### "invalid_client"
**Problem:** Client ID or secret is wrong
**Solution:** 
1. Check .env file
2. Verify credentials in Google Console
3. Copy/paste again (no typos)

### "State validation failed"
**Problem:** CSRF attack detected or state expired
**Solution:**
1. Make sure cookies are enabled
2. Complete flow within 10 minutes
3. Check for multiple tabs/windows

### Port already in use
**Problem:** Port 8000 is already taken
**Solution:**
```bash
# Change in code or use:
python oauth2-google-implementation.py --port 8001
```

---

## Production Checklist

- [ ] Change `GOOGLE_REDIRECT_URI` to production URL
- [ ] Register production URL in Google Console
- [ ] Set `DEBUG=False`
- [ ] Use HTTPS only
- [ ] Use strong `SESSION_SECRET` (generate with: `openssl rand -hex 32`)
- [ ] Set up HTTPS certificates
- [ ] Move secrets to environment (not .env file)
- [ ] Set up database (replace mock UserDatabase)
- [ ] Add rate limiting
- [ ] Add logging
- [ ] Monitor for errors
- [ ] Test full flow
- [ ] Set up backups
- [ ] Document for team

---

## Common Questions

**Q: Why use httpOnly cookies?**
A: Prevents XSS attacks from stealing session tokens

**Q: Why validate state?**
A: Prevents CSRF attacks (ensures code is for request we made)

**Q: Why exchange code on backend?**
A: To keep client_secret safe (never expose to browser)

**Q: What if user denies permission?**
A: Google redirects with error parameter, show login page again

**Q: Can I use authorization code twice?**
A: No - it's single-use by design

**Q: How long is access token valid?**
A: Usually ~1 hour, use refresh_token to get new one

**Q: Do I need PKCE?**
A: Only for SPAs without backend (we have backend, so no)

---

## Next Steps

1. **Complete setup:** Follow google-oauth-setup.md
2. **Understand flow:** Read oauth2-complete-guide.md
3. **Test locally:** Run `python oauth2-google-implementation.py`
4. **Write tests:** Use oauth2-google-tests.py as reference
5. **Add database:** Replace UserDatabase mock with real DB
6. **Deploy:** Move to production (HTTPS, real secrets)

---

## Files Reference

| File | Purpose |
|------|---------|
| `google-oauth-setup.md` | Step-by-step Google Console setup |
| `oauth2-google-implementation.py` | Complete working implementation |
| `oauth2-google-tests.py` | Test suite |
| `DAY11_CHECKLIST.md` | Implementation checklist |
| `requirements.txt` | Python package dependencies |

---

## Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
python oauth2-google-implementation.py

# Run tests
pytest oauth2-google-tests.py -v

# Run with coverage
pytest oauth2-google-tests.py --cov

# Generate SESSION_SECRET
openssl rand -hex 32

# Check if port is in use
lsof -i :8000

# Kill process on port 8000
kill -9 $(lsof -t -i :8000)
```

---

## Summary

**What you'll have after this:**
- Working "Login with Google" button
- User registration on first login
- Session management
- Protected routes
- Logout functionality
- Complete test suite
- Production-ready code

**Key security features:**
- CSRF protection (state validation)
- Client secret hidden (backend only)
- Session expiration
- httpOnly cookies
- Single-use authorization codes

That's Day 11! 🎉
