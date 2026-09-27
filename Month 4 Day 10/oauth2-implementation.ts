// Day 10: OAuth 2.0 Implementation
// All grant types, scope management, state validation, and security

import crypto from 'crypto';
import jwt from 'jsonwebtoken';
import axios from 'axios';

// ============================================================================
// PART 1: Configuration & Constants
// ============================================================================

interface OAuthConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
}

interface OAuthProvider {
  authorizationEndpoint: string;
  tokenEndpoint: string;
  userInfoEndpoint: string;
  scopes: Map<string, string>; // scope -> description
}

// Define supported scopes for your OAuth provider
const AVAILABLE_SCOPES = {
  'openid': 'Request ID token (authentication)',
  'profile': 'Read name, picture, profile URL',
  'email': 'Read email address',
  'read:posts': 'Read posts',
  'write:posts': 'Create and edit posts',
  'delete:posts': 'Delete posts',
  'read:comments': 'Read comments',
  'write:comments': 'Create and edit comments',
  'admin': 'Full admin access'
};

// OAuth provider configurations
const PROVIDERS = {
  google: {
    authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenEndpoint: 'https://oauth2.googleapis.com/token',
    userInfoEndpoint: 'https://www.googleapis.com/oauth2/v1/userinfo',
    scopes: AVAILABLE_SCOPES
  },
  github: {
    authorizationEndpoint: 'https://github.com/login/oauth/authorize',
    tokenEndpoint: 'https://github.com/login/oauth/access_token',
    userInfoEndpoint: 'https://api.github.com/user',
    scopes: {
      'read:user': 'Read user profile',
      'user:email': 'Read user email',
      'repo': 'Full control of repos',
      'read:repo_hook': 'Read repo webhooks'
    }
  }
};

// ============================================================================
// PART 2: State Validation (CSRF Protection)
// ============================================================================

interface StateStore {
  save(state: string, data: any, expirySeconds: number): Promise<void>;
  validate(state: string): Promise<any>;
  clear(state: string): Promise<void>;
}

/**
 * In-memory state store (for demo - use Redis in production)
 */
class InMemoryStateStore implements StateStore {
  private store: Map<string, { data: any; expiry: number }> = new Map();

  async save(state: string, data: any, expirySeconds: number = 600): Promise<void> {
    this.store.set(state, {
      data,
      expiry: Date.now() + expirySeconds * 1000
    });
  }

  async validate(state: string): Promise<any> {
    const entry = this.store.get(state);
    
    if (!entry) {
      throw new Error('State not found - possible CSRF attack');
    }
    
    if (Date.now() > entry.expiry) {
      this.store.delete(state);
      throw new Error('State expired - possible CSRF attack');
    }
    
    return entry.data;
  }

  async clear(state: string): Promise<void> {
    this.store.delete(state);
  }
}

// ============================================================================
// PART 3: Authorization Code Flow
// ============================================================================

export class OAuth2Service {
  private config: OAuthConfig;
  private provider: OAuthProvider;
  private stateStore: StateStore;

  constructor(config: OAuthConfig, providerName: string, stateStore?: StateStore) {
    this.config = config;
    this.provider = PROVIDERS[providerName as keyof typeof PROVIDERS];
    this.stateStore = stateStore || new InMemoryStateStore();
  }

  /**
   * Step 1: Generate authorization URL
   * User visits this URL to login and authorize
   */
  generateAuthorizationUrl(
    requestedScopes: string[],
    options?: { state?: string; codeChallenge?: string }
  ): string {
    // Validate requested scopes
    this.validateScopes(requestedScopes);

    // Generate state for CSRF protection
    const state = options?.state || this.generateState();

    const params = new URLSearchParams({
      client_id: this.config.clientId,
      redirect_uri: this.config.redirectUri,
      response_type: 'code',
      scope: requestedScopes.join(' '),
      state
    });

    // PKCE: Add code_challenge for extra security (mainly for SPAs)
    if (options?.codeChallenge) {
      params.append('code_challenge', options.codeChallenge);
      params.append('code_challenge_method', 'S256');
    }

    return `${this.provider.authorizationEndpoint}?${params.toString()}`;
  }

  /**
   * Step 2: Validate authorization code and exchange for tokens
   * Called on callback URL after user authorizes
   */
  async exchangeCodeForToken(
    code: string,
    state: string,
    codeVerifier?: string // For PKCE
  ): Promise<TokenResponse> {
    // Validate state (CSRF protection)
    const stateData = await this.stateStore.validate(state);
    console.log(`State validated for scopes: ${stateData.scopes.join(', ')}`);

    // Exchange authorization code for access token
    const tokenResponse = await axios.post<TokenResponse>(
      this.provider.tokenEndpoint,
      {
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
        code,
        grant_type: 'authorization_code',
        redirect_uri: this.config.redirectUri,
        ...(codeVerifier && { code_verifier: codeVerifier })
      },
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Accept: 'application/json'
        }
      }
    );

    // Clear used state
    await this.stateStore.clear(state);

    return tokenResponse.data;
  }

  /**
   * Step 3: Get user information using access token
   */
  async getUserInfo(accessToken: string): Promise<UserInfo> {
    const response = await axios.get<any>(
      this.provider.userInfoEndpoint,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: 'application/json'
        }
      }
    );

    // Normalize response (different providers use different field names)
    return {
      id: response.data.id || response.data.sub,
      email: response.data.email,
      name: response.data.name,
      picture: response.data.picture || response.data.avatar_url,
      emailVerified: response.data.email_verified
    };
  }

  /**
   * Decode ID token (if using OIDC)
   * ID token is a JWT that contains user information
   */
  decodeIdToken(idToken: string): DecodedIdToken {
    // Note: In production, verify the JWT signature using the provider's public key
    const decoded = jwt.decode(idToken, { complete: false }) as any;
    
    if (!decoded) {
      throw new Error('Invalid ID token');
    }

    return {
      issuer: decoded.iss,
      subject: decoded.sub,
      audience: decoded.aud,
      issuedAt: decoded.iat,
      expiresAt: decoded.exp,
      name: decoded.name,
      email: decoded.email,
      picture: decoded.picture,
      emailVerified: decoded.email_verified
    };
  }

  // ========================================================================
  // HELPER METHODS
  // ========================================================================

  /**
   * Validate requested scopes
   */
  private validateScopes(scopes: string[]): void {
    for (const scope of scopes) {
      if (!AVAILABLE_SCOPES[scope as keyof typeof AVAILABLE_SCOPES]) {
        throw new Error(`Invalid scope: ${scope}`);
      }
    }
  }

  /**
   * Generate cryptographically secure state string
   */
  private generateState(): string {
    return crypto.randomBytes(32).toString('hex');
  }
}

// ============================================================================
// PART 4: Client Credentials Flow (Server-to-Server)
// ============================================================================

/**
 * Client Credentials: OAuth 2.0 grant for server-to-server communication
 * No user involved, app authenticates as itself
 */
export class ClientCredentialsFlow {
  constructor(
    private clientId: string,
    private clientSecret: string,
    private tokenEndpoint: string
  ) {}

  async getAccessToken(scopes: string[] = []): Promise<string> {
    const response = await axios.post<TokenResponse>(
      this.tokenEndpoint,
      {
        client_id: this.clientId,
        client_secret: this.clientSecret,
        grant_type: 'client_credentials',
        scope: scopes.join(' ')
      },
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Accept: 'application/json'
        }
      }
    );

    return response.data.access_token;
  }
}

// ============================================================================
// PART 5: Device Flow (Smart TVs, IoT)
// ============================================================================

export interface DeviceAuthorizationResponse {
  deviceCode: string;
  userCode: string;
  verificationUri: string;
  expiresIn: number;
  interval: number;
}

export interface DeviceTokenResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  refreshToken?: string;
}

/**
 * Device Flow: For devices without browsers (TVs, IoT, CLI tools)
 */
export class DeviceFlow {
  constructor(
    private clientId: string,
    private deviceAuthorizationEndpoint: string,
    private tokenEndpoint: string
  ) {}

  /**
   * Step 1: Request device code and user code
   */
  async requestDeviceCode(): Promise<DeviceAuthorizationResponse> {
    const response = await axios.post<any>(
      this.deviceAuthorizationEndpoint,
      {
        client_id: this.clientId
      },
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    return {
      deviceCode: response.data.device_code,
      userCode: response.data.user_code,
      verificationUri: response.data.verification_uri,
      expiresIn: response.data.expires_in,
      interval: response.data.interval
    };
  }

  /**
   * Step 2-3: Poll for token until user authorizes
   */
  async pollForToken(
    deviceCode: string,
    expiresIn: number,
    interval: number = 5
  ): Promise<DeviceTokenResponse> {
    const deadline = Date.now() + expiresIn * 1000;

    while (Date.now() < deadline) {
      try {
        const response = await axios.post<TokenResponse>(
          this.tokenEndpoint,
          {
            client_id: this.clientId,
            device_code: deviceCode,
            grant_type: 'urn:ietf:params:oauth:grant-type:device_code'
          },
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          }
        );

        // Success
        return {
          accessToken: response.data.access_token,
          tokenType: response.data.token_type,
          expiresIn: response.data.expires_in,
          refreshToken: response.data.refresh_token
        };
      } catch (error: any) {
        const errorCode = error.response?.data?.error;

        if (errorCode === 'authorization_pending') {
          // User hasn't authorized yet, wait and retry
          await this.sleep(interval * 1000);
          continue;
        } else if (errorCode === 'slow_down') {
          // Server says we're polling too fast
          interval += 5;
          await this.sleep(interval * 1000);
          continue;
        } else if (errorCode === 'expired_token') {
          // Device code expired
          throw new Error('Device code expired. Please try again.');
        } else {
          throw error;
        }
      }
    }

    throw new Error('Device authorization timed out');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ============================================================================
// PART 6: Token Refresh
// ============================================================================

/**
 * Refresh access token using refresh token
 */
export class TokenRefresher {
  constructor(
    private clientId: string,
    private clientSecret: string,
    private tokenEndpoint: string
  ) {}

  async refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
    const response = await axios.post<TokenResponse>(
      this.tokenEndpoint,
      {
        client_id: this.clientId,
        client_secret: this.clientSecret,
        grant_type: 'refresh_token',
        refresh_token: refreshToken
      },
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    return response.data;
  }
}

// ============================================================================
// PART 7: PKCE (For SPAs)
// ============================================================================

/**
 * PKCE (Proof Key for Code Exchange)
 * Makes authorization code flow secure for SPAs without backend
 */
export class PKCEGenerator {
  /**
   * Generate code verifier (128 characters)
   */
  static generateCodeVerifier(): string {
    const allowedCharacters =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
    let codeVerifier = '';

    const randomValues = crypto.getRandomValues(new Uint8Array(96));
    for (let i = 0; i < randomValues.length; i++) {
      codeVerifier += allowedCharacters[randomValues[i] % allowedCharacters.length];
    }

    return codeVerifier;
  }

  /**
   * Generate code challenge from verifier
   * code_challenge = BASE64URL(SHA256(code_verifier))
   */
  static generateCodeChallenge(codeVerifier: string): string {
    const hash = crypto.createHash('sha256').update(codeVerifier).digest();
    return Buffer.from(hash).toString('base64url');
  }
}

// ============================================================================
// TYPES
// ============================================================================

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope?: string;
  id_token?: string; // Only in OIDC
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  picture?: string;
  emailVerified?: boolean;
}

export interface DecodedIdToken {
  issuer: string;
  subject: string;
  audience: string;
  issuedAt: number;
  expiresAt: number;
  name?: string;
  email?: string;
  picture?: string;
  emailVerified?: boolean;
}

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/**
 * Example: Authorization Code Flow with OIDC
 */
export async function exampleAuthorizationCodeFlow() {
  const oauth = new OAuth2Service(
    {
      clientId: process.env.OAUTH_CLIENT_ID!,
      clientSecret: process.env.OAUTH_CLIENT_SECRET!,
      redirectUri: 'https://yourapp.com/oauth/callback'
    },
    'google'
  );

  // Step 1: Generate login URL
  const authUrl = oauth.generateAuthorizationUrl(
    ['openid', 'profile', 'email']
  );
  console.log('Send user to:', authUrl);

  // Step 2: (In callback handler) Exchange code for token
  // const tokens = await oauth.exchangeCodeForToken(code, state);

  // Step 3: Get user info
  // const user = await oauth.getUserInfo(tokens.access_token);
  // OR if using OIDC:
  // const user = oauth.decodeIdToken(tokens.id_token);
}

/**
 * Example: Client Credentials (Server-to-Server)
 */
export async function exampleClientCredentials() {
  const flow = new ClientCredentialsFlow(
    process.env.CLIENT_ID!,
    process.env.CLIENT_SECRET!,
    'https://oauth.example.com/token'
  );

  const token = await flow.getAccessToken(['api.read', 'api.write']);
  console.log('Got token:', token);
}

/**
 * Example: Device Flow (Smart TV)
 */
export async function exampleDeviceFlow() {
  const flow = new DeviceFlow(
    process.env.CLIENT_ID!,
    'https://oauth.example.com/device_authorization',
    'https://oauth.example.com/token'
  );

  // Step 1: Get device code
  const auth = await flow.requestDeviceCode();
  console.log(`Please visit: ${auth.verificationUri}`);
  console.log(`Enter code: ${auth.userCode}`);

  // Step 2-3: Poll until user authorizes
  const tokenResponse = await flow.pollForToken(
    auth.deviceCode,
    auth.expiresIn,
    auth.interval
  );

  console.log('Got token:', tokenResponse.accessToken);
}
