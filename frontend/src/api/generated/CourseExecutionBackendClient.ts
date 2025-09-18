/**
 * Auto-generated client for CourseExecutionBackendInterface.
 * Endpoint: /course-execution-backends
 */

import type { CourseExecutionBackendCreate, CourseExecutionBackendGet, CourseExecutionBackendList, CourseExecutionBackendQuery, CourseExecutionBackendUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseExecutionBackendClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/course-execution-backends');
  }

  async create(payload: CourseExecutionBackendCreate): Promise<CourseExecutionBackendGet> {
    return this.client.post<CourseExecutionBackendGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseExecutionBackendGet> {
    return this.client.get<CourseExecutionBackendGet>(this.buildPath(id));
  }

  async list(params?: CourseExecutionBackendQuery): Promise<CourseExecutionBackendList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseExecutionBackendList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseExecutionBackendUpdate): Promise<CourseExecutionBackendGet> {
    return this.client.patch<CourseExecutionBackendGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
