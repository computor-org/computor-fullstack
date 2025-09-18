import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { courseService } from '../../services/courseService';
import {
  CourseContentGet,
  CourseContentKindGet,
  CourseContentTypeGet,
  CourseGet,
} from '../../types/generated/courses';

export const courseKeys = {
  all: ['courses'] as const,
  list: (params: Record<string, unknown>) => [...courseKeys.all, 'list', params] as const,
  detail: (courseId: string) => [...courseKeys.all, courseId] as const,
  contents: (courseId: string) => [...courseKeys.detail(courseId), 'contents'] as const,
  contentTypes: (courseId: string) => [...courseKeys.detail(courseId), 'content-types'] as const,
  contentKinds: () => [...courseKeys.all, 'content-kinds'] as const,
};

export type CourseQueryOptions<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

export const useCourseQuery = (
  courseId: string,
  options?: CourseQueryOptions<CourseGet>
) => {
  return useQuery({
    queryKey: courseKeys.detail(courseId),
    queryFn: () => courseService.getCourse(courseId),
    enabled: Boolean(courseId),
    ...options,
  });
};

export type CourseListParams = {
  limit?: number;
  offset?: number;
  title?: string;
};

export const useCourseListQuery = (
  params: CourseListParams,
  options?: CourseQueryOptions<{ items: CourseGet[]; total: number }>
) => {
  return useQuery({
    queryKey: courseKeys.list(params),
    queryFn: () => courseService.listCourses(params),
    ...options,
  });
};

export const useCourseContentsQuery = (
  courseId: string,
  options?: CourseQueryOptions<CourseContentGet[]>
) => {
  return useQuery({
    queryKey: courseKeys.contents(courseId),
    queryFn: () => courseService.getCourseContents(courseId),
    enabled: Boolean(courseId),
    ...options,
  });
};

export const useCourseContentTypesQuery = (
  courseId: string,
  options?: CourseQueryOptions<CourseContentTypeGet[]>
) => {
  return useQuery({
    queryKey: courseKeys.contentTypes(courseId),
    queryFn: () => courseService.getCourseContentTypes(courseId),
    enabled: Boolean(courseId),
    ...options,
  });
};

export const useCourseContentKindsQuery = (
  options?: CourseQueryOptions<CourseContentKindGet[]>
) => {
  return useQuery({
    queryKey: courseKeys.contentKinds(),
    queryFn: () => courseService.getCourseContentKinds(),
    ...options,
  });
};
