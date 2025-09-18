/**
 * Auto-generated client for ProfileInterface.
 * Endpoint: /profiles
 */

import type { ProfileCreate, ProfileGet, ProfileList, ProfileQuery, ProfileUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class ProfileClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/profiles');
  }

  async create(payload: ProfileCreate): Promise<ProfileGet> {
    return this.client.post<ProfileGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<ProfileGet> {
    return this.client.get<ProfileGet>(this.buildPath(id));
  }

  async list(params?: ProfileQuery): Promise<ProfileList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<ProfileList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: ProfileUpdate): Promise<ProfileGet> {
    return this.client.patch<ProfileGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
