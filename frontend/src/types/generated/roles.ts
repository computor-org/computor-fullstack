/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-09-03T14:23:27.604951

 * Category: Roles

 */



export interface RoleGet {
  /** Role unique identifier */
  id: string;
  /** Role title */
  title?: string | null;
  /** Role description */
  description?: string | null;
  /** Whether this is a built-in role */
  builtin: boolean;
}

export interface RoleList {
  /** Role unique identifier */
  id: string;
  /** Role title */
  title?: string | null;
  /** Whether this is a built-in role */
  builtin: boolean;
}

export interface RoleClaimGet {
  role_id: string;
  claim_type: string;
  claim_value: string;
  properties?: any | null;
}

export interface RoleClaimList {
  role_id: string;
  claim_type: string;
  claim_value: string;
}