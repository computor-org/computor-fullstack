/**
 * Auto-generated client for UserGroupInterface.
 * Endpoint: /user-groups
 */

import type { UserGroupCreate, UserGroupGet, UserGroupList, UserGroupQuery, UserGroupUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class UserGroupClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/user-groups');
  }

  async create(payload: UserGroupCreate): Promise<UserGroupGet> {
    return this.client.post<UserGroupGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<UserGroupGet> {
    return this.client.get<UserGroupGet>(this.buildPath(id));
  }

  async list(params?: UserGroupQuery): Promise<UserGroupList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<UserGroupList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: UserGroupUpdate): Promise<UserGroupGet> {
    return this.client.patch<UserGroupGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
