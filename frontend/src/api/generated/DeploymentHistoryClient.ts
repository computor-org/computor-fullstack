/**
 * Auto-generated client for DeploymentHistoryInterface.
 * Endpoint: /deployment-history
 * Generated on: 2025-09-18T12:49:52.897111
 */
import type { DeploymentHistoryCreate, DeploymentHistoryGet, DeploymentHistoryList, ListQuery } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class DeploymentHistoryClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/deployment-history');
  }

  async create(payload: DeploymentHistoryCreate): Promise<DeploymentHistoryGet> {
    return this.client.post<DeploymentHistoryGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<DeploymentHistoryGet> {
    return this.client.get<DeploymentHistoryGet>(this.buildPath(id));
  }

  async list(params?: ListQuery): Promise<DeploymentHistoryList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<DeploymentHistoryList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
