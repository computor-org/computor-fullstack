/**
 * Auto-generated client for SubmissionGroupInterface.
 * Endpoint: /submission-groups
 * Generated on: 2025-09-18T12:49:52.898606
 */
import type { SubmissionGroupCreate, SubmissionGroupGet, SubmissionGroupList, SubmissionGroupQuery, SubmissionGroupUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class SubmissionGroupClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/submission-groups');
  }

  async create(payload: SubmissionGroupCreate): Promise<SubmissionGroupGet> {
    return this.client.post<SubmissionGroupGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<SubmissionGroupGet> {
    return this.client.get<SubmissionGroupGet>(this.buildPath(id));
  }

  async list(params?: SubmissionGroupQuery): Promise<SubmissionGroupList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<SubmissionGroupList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: SubmissionGroupUpdate): Promise<SubmissionGroupGet> {
    return this.client.patch<SubmissionGroupGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
