/**
 * Auto-generated client for CourseContentDeploymentInterface.
 * Endpoint: /deployments
 */

import type { CourseContentDeploymentCreate, CourseContentDeploymentGet, CourseContentDeploymentList, CourseContentDeploymentQuery, CourseContentDeploymentUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseContentDeploymentClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/deployments');
  }

  async create(payload: CourseContentDeploymentCreate): Promise<CourseContentDeploymentGet> {
    return this.client.post<CourseContentDeploymentGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseContentDeploymentGet> {
    return this.client.get<CourseContentDeploymentGet>(this.buildPath(id));
  }

  async list(params?: CourseContentDeploymentQuery): Promise<CourseContentDeploymentList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseContentDeploymentList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseContentDeploymentUpdate): Promise<CourseContentDeploymentGet> {
    return this.client.patch<CourseContentDeploymentGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
