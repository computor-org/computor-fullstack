/**
 * Auto-generated client for CourseContentStudentInterface.
 * Endpoint: /student-course-contents
 * Generated on: 2025-09-18T12:49:52.896130
 */
import type { CourseContentStudentGet, CourseContentStudentList, CourseContentStudentQuery, CourseContentStudentUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseContentStudentClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/student-course-contents');
  }

  async get(id: string | number): Promise<CourseContentStudentGet> {
    return this.client.get<CourseContentStudentGet>(this.buildPath(id));
  }

  async list(params?: CourseContentStudentQuery): Promise<CourseContentStudentList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseContentStudentList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseContentStudentUpdate): Promise<CourseContentStudentGet> {
    return this.client.patch<CourseContentStudentGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
