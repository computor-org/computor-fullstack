import { apiClient } from './apiClient';
import {
  CourseContentGet,
  CourseContentKindGet,
  CourseContentTypeGet,
  CourseCreate,
  CourseGet,
  CourseUpdate,
} from '../types/generated/courses';

const DEFAULT_PAGE_SIZE = 500;

export const courseService = {
  async listCourses(params: {
    limit?: number;
    offset?: number;
    title?: string;
  } = {}) {
    const { data, headers } = await apiClient.getWithMeta<CourseGet[]>(`/courses`, {
      params,
    });

    const total = Number(headers.get('X-Total-Count') ?? data.length ?? 0);

    return {
      items: data,
      total,
    };
  },

  async getCourse(courseId: string) {
    return apiClient.get<CourseGet>(`/courses/${courseId}`);
  },

  async getCourseContents(courseId: string) {
    return apiClient.get<CourseContentGet[]>(`/course-contents`, {
      params: {
        course_id: courseId,
        limit: DEFAULT_PAGE_SIZE,
      },
    });
  },

  async getCourseContentTypes(courseId: string) {
    return apiClient.get<CourseContentTypeGet[]>(`/course-content-types`, {
      params: {
        course_id: courseId,
        limit: DEFAULT_PAGE_SIZE,
      },
    });
  },

  async getCourseContentKinds() {
    return apiClient.get<CourseContentKindGet[]>(`/course-content-kinds`, {
      params: {
        limit: DEFAULT_PAGE_SIZE,
      },
    });
  },

  async createCourse(payload: CourseCreate) {
    return apiClient.post<CourseGet>(`/courses`, payload);
  },

  async updateCourse(courseId: string, payload: CourseUpdate) {
    return apiClient.patch<CourseGet>(`/courses/${courseId}`, payload);
  },

  async deleteCourse(courseId: string) {
    await apiClient.delete(`/courses/${courseId}`);
  },
};
