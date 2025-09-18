import { useQuery } from '@tanstack/react-query';
import { organizationService, OrganizationListParams } from '../../services/organizationService';
import { OrganizationGet } from '../../types/generated/organizations';
import { CourseQueryOptions } from './courseQueries';

export const organizationKeys = {
  all: ['organizations'] as const,
  list: (params: OrganizationListParams) => [...organizationKeys.all, 'list', params] as const,
  detail: (organizationId: string) => [...organizationKeys.all, organizationId] as const,
};

export const useOrganizationListQuery = (
  params: OrganizationListParams,
  options?: CourseQueryOptions<{ items: OrganizationGet[]; total: number }>
) => {
  return useQuery({
    queryKey: organizationKeys.list(params),
    queryFn: () => organizationService.listOrganizations(params),
    ...options,
  });
};

export const useOrganizationQuery = (
  organizationId: string,
  options?: CourseQueryOptions<OrganizationGet>
) => {
  return useQuery({
    queryKey: organizationKeys.detail(organizationId),
    queryFn: () => organizationService.getOrganization(organizationId),
    enabled: Boolean(organizationId),
    ...options,
  });
};
