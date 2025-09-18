import { apiClient } from './apiClient';
import {
  CourseFamilyCreate,
  CourseFamilyGet,
  CourseFamilyUpdate,
} from '../types/generated/courses';

export interface CourseFamilyListParams {
  limit?: number;
  offset?: number;
  title?: string;
  organization_id?: string;
}

export const courseFamilyService = {
  async listCourseFamilies(params: CourseFamilyListParams = {}) {
    const queryParams = {
      ...params,
    } as Record<string, string | number | boolean | null | undefined>;

    const { data, headers } = await apiClient.getWithMeta<CourseFamilyGet[]>(`/course-families`, {
      params: queryParams,
    });

    const total = Number(headers.get('X-Total-Count') ?? data.length ?? 0);

    return {
      items: data,
      total,
    };
  },

  async getCourseFamily(courseFamilyId: string) {
    return apiClient.get<CourseFamilyGet>(`/course-families/${courseFamilyId}`);
  },

  async createCourseFamily(payload: CourseFamilyCreate) {
    return apiClient.post<CourseFamilyGet>(`/course-families`, payload);
  },

  async updateCourseFamily(courseFamilyId: string, payload: CourseFamilyUpdate) {
    return apiClient.patch<CourseFamilyGet>(`/course-families/${courseFamilyId}`, payload);
  },

  async deleteCourseFamily(courseFamilyId: string) {
    await apiClient.delete(`/course-families/${courseFamilyId}`);
  },
};
