/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-09-17T14:46:20.418279

 * Category: Sso

 */



/**
 * Information about an authentication provider.
 */
export interface ProviderInfo {
  /** Provider name */
  name: string;
  /** Display name */
  display_name: string;
  /** Authentication type */
  type: string;
  /** Whether provider is enabled */
  enabled: boolean;
  /** Login URL if applicable */
  login_url?: string | null;
}

/**
 * OAuth callback parameters.
 */
export interface CallbackRequest {
  /** Authorization code */
  code: string;
  /** State parameter */
  state?: string | null;
}