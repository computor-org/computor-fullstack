/**
 * Auto-generated client for CourseContentTypeInterface.
 * Endpoint: /course-content-types
 * Generated on: 2025-09-18T12:49:52.896215
 */
import type { CourseContentTypeCreate, CourseContentTypeGet, CourseContentTypeList, CourseContentTypeQuery, CourseContentTypeUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseContentTypeClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/course-content-types');
  }

  async create(payload: CourseContentTypeCreate): Promise<CourseContentTypeGet> {
    return this.client.post<CourseContentTypeGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseContentTypeGet> {
    return this.client.get<CourseContentTypeGet>(this.buildPath(id));
  }

  async list(params?: CourseContentTypeQuery): Promise<CourseContentTypeList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseContentTypeList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseContentTypeUpdate): Promise<CourseContentTypeGet> {
    return this.client.patch<CourseContentTypeGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
