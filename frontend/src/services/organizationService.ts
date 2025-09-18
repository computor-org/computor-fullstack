import { apiClient } from './apiClient';
import {
  OrganizationCreate,
  OrganizationGet,
  OrganizationUpdate,
} from '../types/generated/organizations';

export interface OrganizationListParams {
  limit?: number;
  offset?: number;
  title?: string;
}

export const organizationService = {
  async listOrganizations(params: OrganizationListParams = {}) {
    const queryParams = {
      ...params,
    } as Record<string, string | number | boolean | null | undefined>;

    const { data, headers } = await apiClient.getWithMeta<OrganizationGet[]>(`/organizations`, {
      params: queryParams,
    });

    const total = Number(headers.get('X-Total-Count') ?? data.length ?? 0);

    return {
      items: data,
      total,
    };
  },

  async getOrganization(organizationId: string) {
    return apiClient.get<OrganizationGet>(`/organizations/${organizationId}`);
  },

  async createOrganization(payload: OrganizationCreate) {
    return apiClient.post<OrganizationGet>(`/organizations`, payload);
  },

  async updateOrganization(organizationId: string, payload: OrganizationUpdate) {
    return apiClient.patch<OrganizationGet>(`/organizations/${organizationId}`, payload);
  },

  async deleteOrganization(organizationId: string) {
    await apiClient.delete(`/organizations/${organizationId}`);
  },
};
