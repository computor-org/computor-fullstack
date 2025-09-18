/**
 * Auto-generated client for AccountInterface.
 * Endpoint: /accounts
 * Generated on: 2025-09-18T12:49:52.895588
 */
import type { AccountCreate, AccountGet, AccountList, AccountQuery, AccountUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class AccountClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/accounts');
  }

  async create(payload: AccountCreate): Promise<AccountGet> {
    return this.client.post<AccountGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<AccountGet> {
    return this.client.get<AccountGet>(this.buildPath(id));
  }

  async list(params?: AccountQuery): Promise<AccountList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<AccountList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: AccountUpdate): Promise<AccountGet> {
    return this.client.patch<AccountGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
