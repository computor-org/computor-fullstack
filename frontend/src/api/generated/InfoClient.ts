/**
 * Auto-generated client for InfoClient.
 * Endpoint: /info
 */

import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class InfoClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/info');
  }

  /**
   * Get Server Info
   */
  async getServerInfoInfoGet(): Promise<Record<string, unknown> & Record<string, unknown>> {
    return this.client.get<Record<string, unknown> & Record<string, unknown>>(this.basePath);
  }
}
