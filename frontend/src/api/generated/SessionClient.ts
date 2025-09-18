/**
 * Auto-generated client for SessionInterface.
 * Endpoint: /sessions
 * Generated on: 2025-09-18T12:49:52.898203
 */
import type { SessionCreate, SessionGet, SessionList, SessionQuery, SessionUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class SessionClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/sessions');
  }

  async create(payload: SessionCreate): Promise<SessionGet> {
    return this.client.post<SessionGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<SessionGet> {
    return this.client.get<SessionGet>(this.buildPath(id));
  }

  async list(params?: SessionQuery): Promise<SessionList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<SessionList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: SessionUpdate): Promise<SessionGet> {
    return this.client.patch<SessionGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
