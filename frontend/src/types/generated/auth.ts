/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-08-06T13:19:53.331709

 * Category: Auth

 */



export interface AuthConfig {
}

export interface OrganizationUpdateTokenQuery {
  type: string;
}

export interface OrganizationUpdateTokenUpdate {
  token: string;
}

/**
 * SSO Bearer token credentials.
 */
export interface SSOAuthCredentials {
  token: string;
  scheme?: string;
}

export interface HeaderAuthCredentials {
  type: any;
  credentials: any;
}

/**
 * Login request for SSO.
 */
export interface LoginRequest {
  /** Provider name */
  provider: string;
  /** Redirect URI after login */
  redirect_uri?: string | null;
}

/**
 * Response after successful SSO authentication.
 */
export interface SSOAuthResponse {
  /** User ID */
  user_id: string;
  /** Account ID */
  account_id: string;
  /** Access token if available */
  access_token?: string | null;
  /** Whether this is a new user */
  is_new_user: boolean;
}

/**
 * Token refresh request.
 */
export interface TokenRefreshRequest {
  /** Refresh token from initial authentication */
  refresh_token: string;
  /** Authentication provider */
  provider?: string;
}

/**
 * Response after successful token refresh.
 */
export interface TokenRefreshResponse {
  /** New access token */
  access_token: string;
  /** Token expiration time in seconds */
  expires_in?: number | null;
  /** New refresh token if rotated */
  refresh_token?: string | null;
}