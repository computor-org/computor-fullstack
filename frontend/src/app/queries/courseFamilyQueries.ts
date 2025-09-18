import { useQuery } from '@tanstack/react-query';
import { courseFamilyService, CourseFamilyListParams } from '../../services/courseFamilyService';
import { CourseFamilyGet } from '../../types/generated/courses';
import { CourseQueryOptions } from './courseQueries';

export const courseFamilyKeys = {
  all: ['course-families'] as const,
  list: (params: CourseFamilyListParams) => [...courseFamilyKeys.all, 'list', params] as const,
  detail: (courseFamilyId: string) => [...courseFamilyKeys.all, courseFamilyId] as const,
};

export const useCourseFamilyListQuery = (
  params: CourseFamilyListParams,
  options?: CourseQueryOptions<{ items: CourseFamilyGet[]; total: number }>
) => {
  return useQuery({
    queryKey: courseFamilyKeys.list(params),
    queryFn: () => courseFamilyService.listCourseFamilies(params),
    ...options,
  });
};

export const useCourseFamilyQuery = (
  courseFamilyId: string,
  options?: CourseQueryOptions<CourseFamilyGet>
) => {
  return useQuery({
    queryKey: courseFamilyKeys.detail(courseFamilyId),
    queryFn: () => courseFamilyService.getCourseFamily(courseFamilyId),
    enabled: Boolean(courseFamilyId),
    ...options,
  });
};
