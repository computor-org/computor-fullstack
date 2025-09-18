/**
 * Auto-generated client for SubmissionGroupMemberInterface.
 * Endpoint: /submission-group-members
 * Generated on: 2025-09-18T12:49:52.898715
 */
import type { SubmissionGroupMemberCreate, SubmissionGroupMemberGet, SubmissionGroupMemberList, SubmissionGroupMemberQuery, SubmissionGroupMemberUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class SubmissionGroupMemberClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/submission-group-members');
  }

  async create(payload: SubmissionGroupMemberCreate): Promise<SubmissionGroupMemberGet> {
    return this.client.post<SubmissionGroupMemberGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<SubmissionGroupMemberGet> {
    return this.client.get<SubmissionGroupMemberGet>(this.buildPath(id));
  }

  async list(params?: SubmissionGroupMemberQuery): Promise<SubmissionGroupMemberList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<SubmissionGroupMemberList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: SubmissionGroupMemberUpdate): Promise<SubmissionGroupMemberGet> {
    return this.client.patch<SubmissionGroupMemberGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
