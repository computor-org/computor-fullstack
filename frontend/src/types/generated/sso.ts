/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-09-18T17:27:35.884831

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