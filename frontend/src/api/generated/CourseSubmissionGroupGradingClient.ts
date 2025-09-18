/**
 * Auto-generated client for CourseSubmissionGroupGradingInterface.
 * Endpoint: /submission-group-gradings
 */

import type { CourseSubmissionGroupGradingCreate, CourseSubmissionGroupGradingGet, CourseSubmissionGroupGradingList, CourseSubmissionGroupGradingQuery, CourseSubmissionGroupGradingUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseSubmissionGroupGradingClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/submission-group-gradings');
  }

  async create(payload: CourseSubmissionGroupGradingCreate): Promise<CourseSubmissionGroupGradingGet> {
    return this.client.post<CourseSubmissionGroupGradingGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseSubmissionGroupGradingGet> {
    return this.client.get<CourseSubmissionGroupGradingGet>(this.buildPath(id));
  }

  async list(params?: CourseSubmissionGroupGradingQuery): Promise<CourseSubmissionGroupGradingList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseSubmissionGroupGradingList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseSubmissionGroupGradingUpdate): Promise<CourseSubmissionGroupGradingGet> {
    return this.client.patch<CourseSubmissionGroupGradingGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
