/**
 * Auto-generated client for CourseTutorInterface.
 * Endpoint: /tutor-courses
 */

import type { CourseTutorList, CourseTutorQuery } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseTutorClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/tutor-courses');
  }

  async list(params?: CourseTutorQuery): Promise<CourseTutorList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseTutorList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }
}
