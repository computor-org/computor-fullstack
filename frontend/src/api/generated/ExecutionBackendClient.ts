/**
 * Auto-generated client for ExecutionBackendInterface.
 * Endpoint: /execution-backends
 * Generated on: 2025-09-18T12:49:52.897416
 */
import type { ExecutionBackendCreate, ExecutionBackendGet, ExecutionBackendList, ExecutionBackendQuery, ExecutionBackendUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class ExecutionBackendClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/execution-backends');
  }

  async create(payload: ExecutionBackendCreate): Promise<ExecutionBackendGet> {
    return this.client.post<ExecutionBackendGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<ExecutionBackendGet> {
    return this.client.get<ExecutionBackendGet>(this.buildPath(id));
  }

  async list(params?: ExecutionBackendQuery): Promise<ExecutionBackendList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<ExecutionBackendList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: ExecutionBackendUpdate): Promise<ExecutionBackendGet> {
    return this.client.patch<ExecutionBackendGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
