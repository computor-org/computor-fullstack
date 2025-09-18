/**
 * Auto-generated client for MiscClient.
 * Endpoint: /
 * Generated on: 2025-09-18T12:49:52.900451
 */
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class MiscClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/');
  }

  /**
   * Get Status Head
   */
  async getStatusHeadHead(): Promise<void> {
    return this.client.request<void>(this.basePath, { method: 'HEAD' });
  }
}
