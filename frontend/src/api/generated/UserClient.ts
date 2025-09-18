/**
 * Auto-generated client for UserClient.
 * Endpoint: /user
 */

import type { UserGet, UserPassword } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class UserClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/user');
  }

  /**
   * Get Current User
   * Get the current authenticated user
   */
  async getCurrentUserUserGet(): Promise<UserGet> {
    return this.client.get<UserGet>(this.basePath);
  }

  /**
   * Set User Password
   */
  async setUserPasswordUserPasswordPost({ body }: { body: UserPassword }): Promise<void> {
    return this.client.post<void>(this.buildPath('password'), body);
  }
}
