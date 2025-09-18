/**
 * Auto-generated client for ExampleRepositoryInterface.
 * Endpoint: /example-repositories
 * Generated on: 2025-09-18T12:49:52.897340
 */
import type { ExampleRepositoryCreate, ExampleRepositoryGet, ExampleRepositoryList, ExampleRepositoryQuery, ExampleRepositoryUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class ExampleRepositoryClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/example-repositories');
  }

  async create(payload: ExampleRepositoryCreate): Promise<ExampleRepositoryGet> {
    return this.client.post<ExampleRepositoryGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<ExampleRepositoryGet> {
    return this.client.get<ExampleRepositoryGet>(this.buildPath(id));
  }

  async list(params?: ExampleRepositoryQuery): Promise<ExampleRepositoryList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<ExampleRepositoryList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: ExampleRepositoryUpdate): Promise<ExampleRepositoryGet> {
    return this.client.patch<ExampleRepositoryGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
