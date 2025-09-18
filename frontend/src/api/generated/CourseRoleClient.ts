/**
 * Auto-generated client for CourseRoleInterface.
 * Endpoint: /course-roles
 */

import type { CourseRoleGet, CourseRoleList, CourseRoleQuery } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseRoleClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/course-roles');
  }

  async get(id: string | number): Promise<CourseRoleGet> {
    return this.client.get<CourseRoleGet>(this.buildPath(id));
  }

  async list(params?: CourseRoleQuery): Promise<CourseRoleList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseRoleList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }
}
