/**
 * Auto-generated client for CourseFamilyInterface.
 * Endpoint: /course-families
 */

import type { CourseFamilyCreate, CourseFamilyGet, CourseFamilyList, CourseFamilyQuery, CourseFamilyUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseFamilyClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/course-families');
  }

  async create(payload: CourseFamilyCreate): Promise<CourseFamilyGet> {
    return this.client.post<CourseFamilyGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseFamilyGet> {
    return this.client.get<CourseFamilyGet>(this.buildPath(id));
  }

  async list(params?: CourseFamilyQuery): Promise<CourseFamilyList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseFamilyList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseFamilyUpdate): Promise<CourseFamilyGet> {
    return this.client.patch<CourseFamilyGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
