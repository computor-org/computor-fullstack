/**
 * Auto-generated client for GroupClaimInterface.
 * Endpoint: /group-claims
 * Generated on: 2025-09-18T12:49:52.897492
 */
import type { GroupClaimCreate, GroupClaimGet, GroupClaimList, GroupClaimQuery, GroupClaimUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class GroupClaimClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/group-claims');
  }

  async create(payload: GroupClaimCreate): Promise<GroupClaimGet> {
    return this.client.post<GroupClaimGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<GroupClaimGet> {
    return this.client.get<GroupClaimGet>(this.buildPath(id));
  }

  async list(params?: GroupClaimQuery): Promise<GroupClaimList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<GroupClaimList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: GroupClaimUpdate): Promise<GroupClaimGet> {
    return this.client.patch<GroupClaimGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
