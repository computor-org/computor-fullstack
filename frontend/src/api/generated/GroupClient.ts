/**
 * Auto-generated client for GroupInterface.
 * Endpoint: /groups
 */

import type { GroupCreate, GroupGet, GroupList, GroupQuery, GroupUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class GroupClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/groups');
  }

  async create(payload: GroupCreate): Promise<GroupGet> {
    return this.client.post<GroupGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<GroupGet> {
    return this.client.get<GroupGet>(this.buildPath(id));
  }

  async list(params?: GroupQuery): Promise<GroupList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<GroupList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: GroupUpdate): Promise<GroupGet> {
    return this.client.patch<GroupGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
