/**
 * Auto-generated client for StudentProfileInterface.
 * Endpoint: /student-profiles
 * Generated on: 2025-09-18T12:49:52.898437
 */
import type { StudentProfileCreate, StudentProfileGet, StudentProfileList, StudentProfileQuery, StudentProfileUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class StudentProfileClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/student-profiles');
  }

  async create(payload: StudentProfileCreate): Promise<StudentProfileGet> {
    return this.client.post<StudentProfileGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<StudentProfileGet> {
    return this.client.get<StudentProfileGet>(this.buildPath(id));
  }

  async list(params?: StudentProfileQuery): Promise<StudentProfileList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<StudentProfileList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: StudentProfileUpdate): Promise<StudentProfileGet> {
    return this.client.patch<StudentProfileGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
