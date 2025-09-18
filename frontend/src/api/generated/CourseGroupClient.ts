/**
 * Auto-generated client for CourseGroupInterface.
 * Endpoint: /course-groups
 */

import type { CourseGroupCreate, CourseGroupGet, CourseGroupList, CourseGroupQuery, CourseGroupUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseGroupClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/course-groups');
  }

  async create(payload: CourseGroupCreate): Promise<CourseGroupGet> {
    return this.client.post<CourseGroupGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseGroupGet> {
    return this.client.get<CourseGroupGet>(this.buildPath(id));
  }

  async list(params?: CourseGroupQuery): Promise<CourseGroupList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseGroupList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseGroupUpdate): Promise<CourseGroupGet> {
    return this.client.patch<CourseGroupGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
