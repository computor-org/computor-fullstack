/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-07-21T09:06:47.330911

 * Category: Organizations

 */



import type { GitLabConfig, GitLabConfigGet } from './common';



export interface OrganizationProperties {
  gitlab?: GitLabConfig | null;
}

export interface OrganizationPropertiesGet {
  gitlab?: GitLabConfigGet | null;
}

export interface OrganizationCreate {
  /** Organization title */
  title?: string | null;
  /** Organization description */
  description?: string | null;
  /** Hierarchical path (ltree format) */
  path: string;
  /** Type of organization */
  organization_type: any;
  /** Associated user ID (for user type organizations) */
  user_id?: string | null;
  /** Additional properties */
  properties?: OrganizationProperties | null;
  /** Organization number/identifier */
  number?: string | null;
  /** Contact email address */
  email?: any | null;
  /** Phone number */
  telephone?: string | null;
  /** Fax number */
  fax_number?: string | null;
  /** Organization website URL */
  url?: string | null;
  /** Postal/ZIP code */
  postal_code?: string | null;
  /** Street address */
  street_address?: string | null;
  /** City/locality */
  locality?: string | null;
  /** State/region */
  region?: string | null;
  /** Country */
  country?: string | null;
}

export interface OrganizationGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  /** Organization unique identifier */
  id: string;
  /** Hierarchical path */
  path: string;
  /** Organization title */
  title?: string | null;
  /** Organization description */
  description?: string | null;
  /** Type of organization */
  organization_type: any;
  /** Associated user ID */
  user_id?: string | null;
  /** Additional properties */
  properties?: OrganizationPropertiesGet | null;
  /** Organization number */
  number?: string | null;
  /** Contact email */
  email?: any | null;
  /** Phone number */
  telephone?: string | null;
  /** Fax number */
  fax_number?: string | null;
  /** Website URL */
  url?: string | null;
  /** Postal code */
  postal_code?: string | null;
  /** Street address */
  street_address?: string | null;
  /** City/locality */
  locality?: string | null;
  /** State/region */
  region?: string | null;
  /** Country */
  country?: string | null;
}

export interface OrganizationList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  /** Organization unique identifier */
  id: string;
  /** Hierarchical path */
  path: string;
  /** Organization title */
  title?: string | null;
  /** Type of organization */
  organization_type: any;
  /** Associated user ID */
  user_id?: string | null;
  /** Contact email */
  email?: any | null;
}

export interface OrganizationUpdate {
  title?: string | null;
  description?: string | null;
  path?: string | null;
  organization_type?: any | null;
  user_id?: string | null;
  properties?: OrganizationProperties | null;
  number?: string | null;
  email?: string | null;
  telephone?: string | null;
  fax_number?: string | null;
  url?: string | null;
  postal_code?: string | null;
  street_address?: string | null;
  locality?: string | null;
  region?: string | null;
  country?: string | null;
}