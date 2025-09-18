/**
 * Auto-generated client for CourseContentKindInterface.
 * Endpoint: /course-content-kinds
 * Generated on: 2025-09-18T12:49:52.896045
 */
import type { CourseContentKindCreate, CourseContentKindGet, CourseContentKindList, CourseContentKindQuery, CourseContentKindUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseContentKindClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/course-content-kinds');
  }

  async create(payload: CourseContentKindCreate): Promise<CourseContentKindGet> {
    return this.client.post<CourseContentKindGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseContentKindGet> {
    return this.client.get<CourseContentKindGet>(this.buildPath(id));
  }

  async list(params?: CourseContentKindQuery): Promise<CourseContentKindList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseContentKindList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseContentKindUpdate): Promise<CourseContentKindGet> {
    return this.client.patch<CourseContentKindGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
