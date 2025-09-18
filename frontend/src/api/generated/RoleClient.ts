/**
 * Auto-generated client for RoleInterface.
 * Endpoint: /roles
 * Generated on: 2025-09-18T12:49:52.898124
 */
import type { RoleGet, RoleList, RoleQuery } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class RoleClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/roles');
  }

  async get(id: string | number): Promise<RoleGet> {
    return this.client.get<RoleGet>(this.buildPath(id));
  }

  async list(params?: RoleQuery): Promise<RoleList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<RoleList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }
}
