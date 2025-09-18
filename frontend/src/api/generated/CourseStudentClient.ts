/**
 * Auto-generated client for CourseStudentInterface.
 * Endpoint: /student-courses
 */

import type { CourseStudentList, CourseStudentQuery } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseStudentClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/student-courses');
  }

  async list(params?: CourseStudentQuery): Promise<CourseStudentList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseStudentList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }
}
