/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-07-15T01:10:05.967475

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