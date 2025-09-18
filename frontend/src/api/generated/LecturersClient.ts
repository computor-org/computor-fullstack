/**
 * Auto-generated client for LecturersClient.
 * Endpoint: /lecturers
 * Generated on: 2025-09-18T12:49:52.899630
 */
import type { CourseGet, CourseList } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class LecturersClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/lecturers');
  }

  /**
   * Lecturer Get Courses
   */
  async lecturerGetCoursesLecturersCoursesCourseIdGet({ courseId }: { courseId: string | string }): Promise<CourseGet> {
    return this.client.get<CourseGet>(this.buildPath('courses', courseId));
  }

  /**
   * Lecturer List Courses
   */
  async lecturerListCoursesLecturersCoursesGet({ skip, limit, id, title, description, path, courseFamilyId, organizationId, providerUrl, fullPath }: { skip?: number | null; limit?: number | null; id?: string | null; title?: string | null; description?: string | null; path?: string | null; courseFamilyId?: string | null; organizationId?: string | null; providerUrl?: string | null; fullPath?: string | null }): Promise<CourseList[]> {
    const queryParams: Record<string, unknown> = {
      skip,
      limit,
      id,
      title,
      description,
      path,
      course_family_id: courseFamilyId,
      organization_id: organizationId,
      provider_url: providerUrl,
      full_path: fullPath,
    };
    return this.client.get<CourseList[]>(this.buildPath('courses'), { params: queryParams });
  }
}
