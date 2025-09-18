/**
 * Auto-generated client for TestsClient.
 * Endpoint: /tests
 * Generated on: 2025-09-18T12:49:52.899280
 */
import type { TestCreate, TestRunResponse } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class TestsClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/tests');
  }

  /**
   * Create Test
   * Create and execute a test for a course assignment.
   * Tests are now executed via Temporal workflows.
   * Submit flag is stored as a boolean in the Result model.
   */
  async createTestTestsPost({ body }: { body: TestCreate }): Promise<TestRunResponse> {
    return this.client.post<TestRunResponse>(this.basePath, body);
  }
}
