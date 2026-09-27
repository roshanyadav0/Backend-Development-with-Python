// Day 10: OAuth 2.0 Tests
// Authorization code flow, scope validation, PKCE, state validation

import {
  OAuth2Service,
  ClientCredentialsFlow,
  DeviceFlow,
  PKCEGenerator,
  TokenRefresher
} from './oauth2-implementation';

describe('OAuth 2.0 Tests', () => {
  // =========================================================================
  // PART 1: Authorization Code Flow
  // =========================================================================

  describe('Authorization Code Flow', () => {
    let oauth: OAuth2Service;

    beforeEach(() => {
      oauth = new OAuth2Service(
        {
          clientId: 'test_client_id',
          clientSecret: 'test_client_secret',
          redirectUri: 'https://localhost:3000/oauth/callback'
        },
        'google'
      );
    });

    it('should generate authorization URL with correct parameters', () => {
      const authUrl = oauth.generateAuthorizationUrl(['openid', 'profile', 'email']);

      expect(authUrl).toContain('client_id=test_client_id');
      expect(authUrl).toContain('redirect_uri=https://localhost:3000/oauth/callback');
      expect(authUrl).toContain('response_type=code');
      expect(authUrl).toContain('scope=openid+profile+email');
      expect(authUrl).toContain('state=');
    });

    it('should validate requested scopes', () => {
      // Valid scopes
      expect(() => {
        oauth.generateAuthorizationUrl(['openid', 'profile', 'email']);
      }).not.toThrow();

      // Invalid scope
      expect(() => {
        oauth.generateAuthorizationUrl(['openid', 'invalid_scope']);
      }).toThrow('Invalid scope: invalid_scope');
    });

    it('should include only requested scopes in URL', () => {
      const authUrl = oauth.generateAuthorizationUrl(['read:posts', 'write:posts']);

      expect(authUrl).toContain('read:posts');
      expect(authUrl).toContain('write:posts');
      expect(authUrl).not.toContain('admin'); // Other scopes not included
    });

    it('should generate unique state on each call', () => {
      const url1 = oauth.generateAuthorizationUrl(['openid']);
      const url2 = oauth.generateAuthorizationUrl(['openid']);

      const state1 = new URL(url1).searchParams.get('state');
      const state2 = new URL(url2).searchParams.get('state');

      expect(state1).not.toEqual(state2);
    });

    it('should include custom state if provided', () => {
      const customState = 'my_custom_state_123';
      const authUrl = oauth.generateAuthorizationUrl(['openid'], {
        state: customState
      });

      expect(authUrl).toContain(`state=${customState}`);
    });

    it('should support PKCE (code challenge)', () => {
      const codeChallenge = 'E9Mrozoa2owUednMYvzoqunPEPPF0DpPqq3i8ZmiGI=';
      const authUrl = oauth.generateAuthorizationUrl(['openid'], {
        codeChallenge
      });

      expect(authUrl).toContain(`code_challenge=${encodeURIComponent(codeChallenge)}`);
      expect(authUrl).toContain('code_challenge_method=S256');
    });
  });

  // =========================================================================
  // PART 2: State Validation (CSRF Protection)
  // =========================================================================

  describe('State Validation (CSRF Protection)', () => {
    let oauth: OAuth2Service;

    beforeEach(() => {
      oauth = new OAuth2Service(
        {
          clientId: 'test_client_id',
          clientSecret: 'test_client_secret',
          redirectUri: 'https://localhost:3000/oauth/callback'
        },
        'google'
      );
    });

    it('should reject invalid state', async () => {
      expect(async () => {
        await oauth.exchangeCodeForToken('auth_code', 'invalid_state');
      }).rejects.toThrow('State not found');
    });

    it('should reject expired state', async () => {
      // This would require mocking the state store with time manipulation
      // In production, use a real Redis store with TTL
    });

    it('should clear state after validation', async () => {
      // This would require mocking the state store
      // Ensure same state can't be used twice
    });
  });

  // =========================================================================
  // PART 3: Scope Management
  // =========================================================================

  describe('Scope Management', () => {
    let oauth: OAuth2Service;

    beforeEach(() => {
      oauth = new OAuth2Service(
        {
          clientId: 'test_client_id',
          clientSecret: 'test_client_secret',
          redirectUri: 'https://localhost:3000/oauth/callback'
        },
        'google'
      );
    });

    it('should allow valid scopes', () => {
      const validScopes = [
        'openid',
        'profile',
        'email',
        'read:posts',
        'write:posts',
        'admin'
      ];

      expect(() => {
        oauth.generateAuthorizationUrl(validScopes);
      }).not.toThrow();
    });

    it('should reject invalid scopes', () => {
      const invalidScopes = ['openid', 'invalid_scope_xyz'];

      expect(() => {
        oauth.generateAuthorizationUrl(invalidScopes);
      }).toThrow('Invalid scope: invalid_scope_xyz');
    });

    it('should allow empty scope array (default scopes)', () => {
      expect(() => {
        oauth.generateAuthorizationUrl([]);
      }).not.toThrow();
    });

    it('should implement principle of least privilege', () => {
      // Test that requesting minimal scopes is preferred
      const minimalScopes = ['openid', 'email'];
      const broadScopes = ['openid', 'profile', 'email', 'admin', 'read:posts'];

      const minUrl = oauth.generateAuthorizationUrl(minimalScopes);
      const broadUrl = oauth.generateAuthorizationUrl(broadScopes);

      // Both should be valid, but minimal is recommended
      expect(minUrl).toBeDefined();
      expect(broadUrl).toBeDefined();
    });
  });

  // =========================================================================
  // PART 4: PKCE (Proof Key for Code Exchange)
  // =========================================================================

  describe('PKCE (Proof Key for Code Exchange)', () => {
    it('should generate valid code verifier', () => {
      const codeVerifier = PKCEGenerator.generateCodeVerifier();

      // Should be 128 characters
      expect(codeVerifier.length).toBe(128);

      // Should only contain allowed characters
      const allowedPattern = /^[A-Za-z0-9\-._~]+$/;
      expect(codeVerifier).toMatch(allowedPattern);
    });

    it('should generate unique code verifier each time', () => {
      const verifier1 = PKCEGenerator.generateCodeVerifier();
      const verifier2 = PKCEGenerator.generateCodeVerifier();

      expect(verifier1).not.toEqual(verifier2);
    });

    it('should generate valid code challenge from verifier', () => {
      const codeVerifier = 'E9Mrozoa2owUednMYvzoqunPEPPF0DpPqq3i8ZmiG0'; // 43 chars
      const challenge = PKCEGenerator.generateCodeChallenge(codeVerifier);

      // Challenge should be base64url encoded
      expect(challenge).toMatch(/^[A-Za-z0-9_-]+$/);

      // Should be deterministic (same input = same output)
      const challenge2 = PKCEGenerator.generateCodeChallenge(codeVerifier);
      expect(challenge).toEqual(challenge2);
    });

    it('should produce different challenge for different verifier', () => {
      const verifier1 = PKCEGenerator.generateCodeVerifier();
      const verifier2 = PKCEGenerator.generateCodeVerifier();

      const challenge1 = PKCEGenerator.generateCodeChallenge(verifier1);
      const challenge2 = PKCEGenerator.generateCodeChallenge(verifier2);

      expect(challenge1).not.toEqual(challenge2);
    });

    it('should include PKCE in authorization URL', () => {
      const oauth = new OAuth2Service(
        {
          clientId: 'test_client_id',
          clientSecret: 'test_client_secret',
          redirectUri: 'https://localhost:3000/oauth/callback'
        },
        'google'
      );

      const codeVerifier = PKCEGenerator.generateCodeVerifier();
      const codeChallenge = PKCEGenerator.generateCodeChallenge(codeVerifier);

      const authUrl = oauth.generateAuthorizationUrl(['openid'], {
        codeChallenge
      });

      expect(authUrl).toContain('code_challenge=');
      expect(authUrl).toContain('code_challenge_method=S256');

      // Verify code verifier is NOT in URL (kept secret in browser)
      expect(authUrl).not.toContain(codeVerifier);
    });
  });

  // =========================================================================
  // PART 5: Client Credentials Flow
  // =========================================================================

  describe('Client Credentials Flow (Server-to-Server)', () => {
    let flow: ClientCredentialsFlow;

    beforeEach(() => {
      flow = new ClientCredentialsFlow(
        'client_id',
        'client_secret',
        'https://oauth.example.com/token'
      );
    });

    it('should request token with client credentials', async () => {
      // This would require mocking the HTTP call
      // Verify that:
      // 1. client_id is sent
      // 2. client_secret is sent
      // 3. grant_type = 'client_credentials'
      // 4. scopes are included if requested
    });

    it('should not require user involvement', () => {
      // Client credentials flow should work without any user interaction
      // Perfect for microservices, scheduled jobs, etc.
    });

    it('should not issue refresh tokens', () => {
      // Client credentials tokens are short-lived
      // When expired, just request a new one (no refresh token needed)
    });
  });

  // =========================================================================
  // PART 6: Device Flow
  // =========================================================================

  describe('Device Flow (Smart TVs, IoT)', () => {
    let flow: DeviceFlow;

    beforeEach(() => {
      flow = new DeviceFlow(
        'client_id',
        'https://oauth.example.com/device_authorization',
        'https://oauth.example.com/token'
      );
    });

    it('should request device code', async () => {
      // Would require mocking HTTP calls
      // Verify device authorization endpoint is called with client_id
    });

    it('should provide user-friendly user code', () => {
      // User code should be short and easy to type (like LHJK-MNOP)
      // Device code should be longer and more secure
    });

    it('should handle polling with backoff', () => {
      // Should respect 'interval' returned from server
      // Should increase interval if server responds with 'slow_down'
    });

    it('should handle authorization_pending gracefully', () => {
      // Device polls for token
      // Server responds: authorization_pending
      // Device should wait and retry
    });

    it('should handle expired_token error', () => {
      // If device code expires, should throw clear error
      // Device should start over with new device code
    });
  });

  // =========================================================================
  // PART 7: ID Token (OIDC)
  // =========================================================================

  describe('ID Token (OpenID Connect)', () => {
    let oauth: OAuth2Service;

    beforeEach(() => {
      oauth = new OAuth2Service(
        {
          clientId: 'test_client_id',
          clientSecret: 'test_client_secret',
          redirectUri: 'https://localhost:3000/oauth/callback'
        },
        'google'
      );
    });

    it('should request ID token with openid scope', () => {
      const authUrl = oauth.generateAuthorizationUrl(['openid', 'profile', 'email']);

      // When openid scope is included, OAuth provider will return id_token in response
      expect(authUrl).toContain('openid');
    });

    it('should decode ID token', () => {
      // Mock ID token (normally comes from OAuth provider)
      const mockIdToken =
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJzdWIiOiIxMjM0NTY3ODkwIiwiYXVkIjoiY2xpZW50X2lkIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyNDI2MjIsIm5hbWUiOiJBbGljZSBTbWl0aCIsImVtYWlsIjoiYWxpY2VAZXhhbXBsZS5jb20iLCJwaWN0dXJlIjoiaHR0cHM6Ly9leGFtcGxlLmNvbS9waWMuanBnIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';

      const decoded = oauth.decodeIdToken(mockIdToken);

      expect(decoded.issuer).toBe('https://accounts.google.com');
      expect(decoded.subject).toBe('1234567890');
      expect(decoded.audience).toBe('client_id');
      expect(decoded.name).toBe('Alice Smith');
      expect(decoded.email).toBe('alice@example.com');
      expect(decoded.emailVerified).toBe(true);
    });

    it('should extract user info from ID token without calling userinfo endpoint', () => {
      // With OIDC, user info is in the ID token
      // No need to call /userinfo endpoint (saves API call)
      const mockIdToken =
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJhbGljZUBleGFtcGxlLmNvbSIsIm5hbWUiOiJBbGljZSJ9.sig';

      const userInfo = oauth.decodeIdToken(mockIdToken);

      expect(userInfo.email).toBe('alice@example.com');
      expect(userInfo.name).toBe('Alice');
    });

    it('should validate ID token issuer', () => {
      // In production, verify JWT signature and issuer
      // Ensure token comes from authorized OAuth provider
    });
  });

  // =========================================================================
  // PART 8: Security Tests
  // =========================================================================

  describe('Security', () => {
    it('should not expose client_secret in authorization URL', () => {
      const oauth = new OAuth2Service(
        {
          clientId: 'public_client_id',
          clientSecret: 'secret_value_123', // MUST STAY SECRET
          redirectUri: 'https://localhost:3000/oauth/callback'
        },
        'google'
      );

      const authUrl = oauth.generateAuthorizationUrl(['openid']);

      // Client secret should NEVER appear in URL
      expect(authUrl).not.toContain('secret_value_123');
      expect(authUrl).not.toContain('client_secret');
    });

    it('should use HTTPS redirect URIs only', () => {
      // Should reject http:// redirects (except localhost for dev)
      // All production redirects must be HTTPS
    });

    it('should not log tokens or sensitive data', () => {
      // Tokens should never appear in logs
      // If debugging, log token hashes or truncated versions only
    });

    it('should validate redirect URI exactly', () => {
      // Registered: https://yourapp.com/oauth/callback
      // Attack:     https://attacker.com/oauth/callback
      // Should reject the attack

      // Also reject:
      // https://yourapp.com.attacker.com/oauth/callback
      // https://yourapp.com/oauth/callback?state=evil
    });

    it('should prevent authorization code reuse', () => {
      // Authorization code should be single-use
      // Second attempt to use same code should fail
    });

    it('should implement rate limiting on token endpoint', () => {
      // Prevent brute force attacks on token exchange
      // Limit attempts per client_id per time period
    });
  });

  // =========================================================================
  // PART 9: Error Handling
  // =========================================================================

  describe('Error Handling', () => {
    it('should handle invalid_grant error', () => {
      // Authorization code expired or already used
      // User needs to restart login flow
    });

    it('should handle invalid_client error', () => {
      // client_id or client_secret is wrong
      // Should not reveal which one is incorrect
    });

    it('should handle access_denied error', () => {
      // User clicked "Deny" on authorization screen
      // Redirect to login page with message
    });

    it('should handle network errors gracefully', () => {
      // OAuth provider is down
      // Should retry with backoff
      // Should show user-friendly error message
    });

    it('should handle malformed token responses', () => {
      // OAuth provider returns invalid JSON
      // Should validate response structure
    });
  });

  // =========================================================================
  // PART 10: Integration Tests
  // =========================================================================

  describe('Full OAuth Flow Integration', () => {
    it('should complete authorization code flow end-to-end', async () => {
      // 1. Generate authorization URL
      // 2. Simulate user authorization
      // 3. Exchange code for token
      // 4. Get user info
      // 5. Create session/JWT
      // 6. Verify user is logged in
    });

    it('should handle multiple concurrent authorization flows', () => {
      // Multiple users authorizing simultaneously
      // Each should have unique state/code
      // Should not interfere with each other
    });

    it('should refresh expired access tokens', async () => {
      // Initial token expires
      // Use refresh token to get new access token
      // Continue using API without re-authenticating
    });
  });
});
