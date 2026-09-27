# OAuth 2.0 Implementation Checklist & Quick Reference

---

## Part 1: OAuth Concepts Checklist

### Core Concepts
- ✅ Understand OAuth 2.0 is **authorization**, not authentication
- ✅ Know the difference: Authentication (who are you) vs Authorization (what can you do)
- ✅ Understand OpenID Connect (OIDC) = OAuth 2.0 + identity layer
- ✅ Know when to use OIDC vs pure OAuth 2.0

### Grant Types
- ✅ Authorization Code Flow: User login via third-party (most common)
- ✅ Implicit Flow: Deprecated, don't use
- ✅ Client Credentials: Server-to-server (no user)
- ✅ Device Flow: Smart TVs, IoT devices
- ✅ Know which grant type to use for each scenario

---

## Part 2: Authorization Code Flow Checklist

### Setup
- ✅ Register OAuth application with provider (Google, GitHub, etc.)
- ✅ Get client_id and client_secret
- ✅ Set redirect_uri (must be HTTPS in production)
- ✅ Define scopes needed for your app

### Step 1: Generate Authorization URL
- ✅ Include client_id
- ✅ Include redirect_uri (must match registered value exactly)
- ✅ Set response_type='code'
- ✅ Include scope (space-separated)
- ✅ Generate and store unique state (CSRF protection)
- ✅ (Optional) Include code_challenge for PKCE

```typescript
https://oauth-provider.com/authorize
  ?client_id=YOUR_ID
  &redirect_uri=https://yourapp.com/callback
  &response_type=code
  &scope=openid+profile+email
  &state=random_string_123
```

### Step 2: User Authorizes
- ✅ User clicks login button
- ✅ Redirected to OAuth provider's login
- ✅ User sees permission screen
- ✅ User clicks "Approve" or "Deny"
- ✅ OAuth provider redirects back with code (or error)

### Step 3: Handle Callback
- ✅ Receive authorization code
- ✅ Receive state parameter
- ✅ Validate state matches what we sent (CSRF check)
- ✅ Check for error parameter (user denied, etc.)
- ✅ Don't expose code in browser logs

### Step 4: Exchange Code for Token (Backend Only)
- ✅ Make POST request to token endpoint
- ✅ Include client_id
- ✅ Include client_secret (NEVER in browser)
- ✅ Include authorization code
- ✅ Include grant_type='authorization_code'
- ✅ Include redirect_uri (must match original)
- ✅ (If using PKCE) Include code_verifier
- ✅ Verify response includes access_token
- ✅ Store access_token and refresh_token securely

```typescript
POST https://oauth-provider.com/token
Content-Type: application/x-www-form-urlencoded

client_id=YOUR_ID
&client_secret=YOUR_SECRET
&code=AUTH_CODE
&grant_type=authorization_code
&redirect_uri=https://yourapp.com/callback
```

### Step 5: Get User Info
- ✅ Option A (No OIDC): Call /userinfo endpoint with access_token
- ✅ Option B (OIDC): Decode id_token (it's a JWT)
- ✅ Verify user info (email, etc.)
- ✅ Find or create user in your database

### Step 6: Create Session
- ✅ Create session token or JWT
- ✅ Set httpOnly cookie
- ✅ Store user information in session
- ✅ Redirect to dashboard

---

## Part 3: Scope Management Checklist

### Defining Scopes
- ✅ Define available scopes for your OAuth provider
- ✅ Assign clear descriptions to each scope
- ✅ Follow naming conventions (read:*, write:*, admin)
- ✅ Document what each scope can do

### Requesting Scopes
- ✅ Only request scopes you actually need
- ✅ Don't request all scopes "just in case"
- ✅ Request minimal permissions (principle of least privilege)
- ✅ Explain to user why you need each scope

### Scope Validation
- ✅ Validate requested scopes against available scopes
- ✅ Reject invalid scope requests
- ✅ Check if user granted all requested scopes
- ✅ Check if access_token has required scopes before API calls

### Example Scopes
```
openid              ← Always needed for OIDC (authentication)
profile             ← Name, picture, profile URL
email               ← Email address
read:posts          ← Can read posts
write:posts         ← Can create/edit posts
delete:posts        ← Can delete posts
admin               ← Full admin access
```

---

## Part 4: Security Checklist

### HTTPS & Transport
- ✅ Use HTTPS only (no HTTP except localhost dev)
- ✅ Validate SSL certificates
- ✅ Set security headers (HSTS, etc.)

### Client Secret
- ✅ Never expose client_secret in browser
- ✅ Never commit client_secret to git
- ✅ Store in environment variables or secrets vault
- ✅ Rotate regularly
- ✅ Use different secrets for dev/staging/production

### State Parameter (CSRF Protection)
- ✅ Generate random state for each authorization request
- ✅ Store state in server-side session (not URL)
- ✅ Validate state matches on callback
- ✅ State should expire after ~10 minutes
- ✅ Reject expired or mismatched state

### Authorization Code
- ✅ Code should be single-use (reject second use)
- ✅ Code should expire quickly (~10 minutes)
- ✅ Code should be tied to specific client_id
- ✅ Never expose code in logs

### Tokens
- ✅ Access tokens should have short lifetime (~1 hour)
- ✅ Refresh tokens should have longer lifetime (~7 days)
- ✅ Store refresh tokens in httpOnly cookies (not localStorage)
- ✅ Never log tokens, only log token IDs or hashes
- ✅ Don't trust token claims directly; verify signature

### Redirect URI
- ✅ Redirect URI must be registered with OAuth provider
- ✅ Validate redirect_uri exactly matches registered value
- ✅ Reject http:// in production (only https://)
- ✅ Prevent open redirect attacks (validate against whitelist)

### API Calls
- ✅ Include access_token in Authorization header
- ✅ Use `Authorization: Bearer <token>` format
- ✅ Include token in request body if needed (not URL)
- ✅ Handle 401 Unauthorized (token expired)
- ✅ Use refresh token to get new access token

### Rate Limiting
- ✅ Rate limit /authorize endpoint (prevent abuse)
- ✅ Rate limit /token endpoint (prevent brute force)
- ✅ Rate limit /userinfo endpoint
- ✅ Include rate limit headers in response

---

## Part 5: PKCE Checklist (For SPAs)

### When to Use PKCE
- ✅ Single-page applications (SPA)
- ✅ Mobile apps
- ✅ Desktop apps
- ✅ Basically any OAuth client without a secure backend

### How PKCE Works
1. Generate code_verifier (128 random characters)
2. Generate code_challenge = SHA256(code_verifier) encoded in base64url
3. Include code_challenge in authorization URL
4. User authorizes
5. Exchange code + code_verifier for token
6. Server verifies: SHA256(code_verifier) == code_challenge

### Implementation
- ✅ Generate strong code_verifier (128 bytes of random data)
- ✅ Generate code_challenge from verifier
- ✅ Include code_challenge in authorization URL
- ✅ Store code_verifier securely (memory, IndexedDB)
- ✅ Include code_verifier when exchanging code
- ✅ Don't expose verifier in URL

```typescript
// Generate
const verifier = PKCEGenerator.generateCodeVerifier();
const challenge = PKCEGenerator.generateCodeChallenge(verifier);

// Store verifier (in memory)
sessionStorage.setItem('pkce_verifier', verifier);

// Use in auth URL
authUrl.searchParams.set('code_challenge', challenge);
authUrl.searchParams.set('code_challenge_method', 'S256');

// Exchange (send verifier)
POST /token
  code=...
  code_verifier=... ← Include verifier
```

---

## Part 6: OpenID Connect (OIDC) Checklist

### OIDC Setup
- ✅ Add 'openid' to scope
- ✅ Response will include id_token (JWT)
- ✅ id_token contains user information
- ✅ No need to call /userinfo endpoint

### Using ID Token
- ✅ id_token is a JWT (decode it)
- ✅ Verify JWT signature (optional but recommended)
- ✅ Check token expiration
- ✅ Extract user info from token
- ✅ Verify 'aud' (audience) claim matches your client_id
- ✅ Verify 'iss' (issuer) matches OAuth provider

### ID Token Claims
```
iss         Issuer (who issued token)
sub         Subject (user ID)
aud         Audience (your client_id)
iat         Issued at (timestamp)
exp         Expires at (timestamp)
name        User's name
email       User's email
picture     User's profile picture
email_verified  Is email verified?
```

### Example
```javascript
// Scope includes openid
scope='openid profile email'

// Response includes id_token
{
  access_token: '...',
  id_token: 'eyJhbGc...', ← This is new!
  expires_in: 3600
}

// Decode id_token (JWT)
const user = jwt.decode(idToken);
console.log(user.email, user.name);
```

---

## Part 7: Error Handling Checklist

### OAuth Provider Errors
- ✅ Handle `error=invalid_grant` (code expired/reused)
- ✅ Handle `error=invalid_client` (bad client_id/secret)
- ✅ Handle `error=access_denied` (user clicked deny)
- ✅ Handle `error=unsupported_response_type`
- ✅ Handle `error=invalid_scope` (bad scope requested)
- ✅ Handle `error=server_error` (provider issue)

### Network Errors
- ✅ Handle timeout errors
- ✅ Handle DNS resolution errors
- ✅ Implement retry with exponential backoff
- ✅ Show user-friendly error messages

### Response Validation
- ✅ Check response includes required fields
- ✅ Check token_type='Bearer'
- ✅ Check expires_in is a valid number
- ✅ Reject invalid JSON responses
- ✅ Log errors for debugging (not sensitive data)

---

## Part 8: Testing Checklist

### Unit Tests
- ✅ Test authorization URL generation
- ✅ Test scope validation
- ✅ Test state generation and validation
- ✅ Test PKCE code generation
- ✅ Test ID token decoding

### Integration Tests
- ✅ Test full OAuth flow with mock provider
- ✅ Test token exchange
- ✅ Test user info retrieval
- ✅ Test session creation
- ✅ Test error handling
- ✅ Test multiple concurrent flows

### Security Tests
- ✅ Test state validation (CSRF protection)
- ✅ Test authorization code is single-use
- ✅ Test client_secret not exposed
- ✅ Test redirect URI validation
- ✅ Test token not logged
- ✅ Test HTTPS redirect URIs only

### Manual Testing
- ✅ Test with actual OAuth provider (Google, GitHub)
- ✅ Test login flow end-to-end
- ✅ Test permission screen shows all scopes
- ✅ Test deny scenario (error handling)
- ✅ Test token refresh
- ✅ Test logout

---

## Part 9: Deployment Checklist

### Configuration
- ✅ Use environment variables for credentials
- ✅ Different client_id/secret for each environment
- ✅ Use production OAuth provider URLs
- ✅ Set correct redirect_uri for each environment

### Monitoring
- ✅ Log OAuth errors (not tokens)
- ✅ Monitor token endpoint latency
- ✅ Monitor failed authorizations
- ✅ Alert on repeated errors

### Maintenance
- ✅ Rotate client_secret regularly
- ✅ Update OAuth provider SDKs
- ✅ Monitor OAuth provider status page
- ✅ Review scope usage (remove unused scopes)

---

## Part 10: Quick Reference

### OAuth 2.0 Grant Types

| Type | Use Case | Client Secret | Flow |
|------|----------|--------|------|
| Authorization Code | User login | Yes (backend) | /authorize → code → /token → token |
| Implicit | SPA (deprecated) | No | /authorize → token (in URL) |
| Client Credentials | Server-to-server | Yes | /token → token (no user) |
| Device | Smart TV, IoT | Yes | /device → code → poll /token |
| Refresh | Get new access token | Yes | /token with refresh_token |

### HTTPS & Redirect URIs

| Environment | Allowed? | Example |
|------------|----------|---------|
| Production | HTTPS only | https://myapp.com/oauth/callback |
| Staging | HTTPS | https://staging.myapp.com/oauth/callback |
| Local dev | http | http://localhost:3000/oauth/callback |

### Token Lifetimes

| Token | Lifetime | Refresh | Storage |
|-------|----------|---------|---------|
| Access | 1 hour | No | Memory (or httpOnly cookie) |
| Refresh | 7 days | Yes | httpOnly cookie |
| Auth code | 10 min | No | N/A (single-use) |
| State | 10 min | No | Server-side session |

### Scope Naming Conventions

```
By action:
  read:*      Can read this resource
  write:*     Can create/edit this resource
  delete:*    Can delete this resource
  admin:*     Admin access to this resource

Standard OIDC:
  openid      Request ID token (authentication)
  profile     Name, picture, URL
  email       Email address
  address     Mailing address
  phone       Phone number
```

### Common URLS

```
Google:
  Authorization: https://accounts.google.com/o/oauth2/v2/auth
  Token: https://oauth2.googleapis.com/token
  UserInfo: https://www.googleapis.com/oauth2/v1/userinfo
  Config: https://accounts.google.com/.well-known/openid-configuration

GitHub:
  Authorization: https://github.com/login/oauth/authorize
  Token: https://github.com/login/oauth/access_token
  UserInfo: https://api.github.com/user
```

---

## Implementation Summary

```typescript
// 1. Generate login URL
const authUrl = oauth.generateAuthorizationUrl(['openid', 'profile', 'email']);

// 2. User visits authUrl, authorizes, and is redirected back with code

// 3. Exchange code for token (backend)
const tokens = await oauth.exchangeCodeForToken(code, state);

// 4. Get user info (either method works)
// Option A: Call userinfo endpoint
const user = await oauth.getUserInfo(tokens.access_token);

// Option B: Decode id_token (OIDC)
const user = oauth.decodeIdToken(tokens.id_token);

// 5. Create user session
const session = await createSession(user);

// 6. Set session cookie
res.cookie('session', session, { httpOnly: true, secure: true });
```

**That's OAuth 2.0!** 🎉
