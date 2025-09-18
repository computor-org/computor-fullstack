/**
 * Auto-generated client for CourseMemberCommentInterface.
 * Endpoint: /course-member-comments
 * Generated on: 2025-09-18T12:49:52.896637
 */
import type { CourseMemberCommentCreate, CourseMemberCommentGet, CourseMemberCommentList, CourseMemberCommentQuery, CourseMemberCommentUpdate } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class CourseMemberCommentClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/course-member-comments');
  }

  async create(payload: CourseMemberCommentCreate): Promise<CourseMemberCommentGet> {
    return this.client.post<CourseMemberCommentGet>(this.basePath, payload);
  }

  async get(id: string | number): Promise<CourseMemberCommentGet> {
    return this.client.get<CourseMemberCommentGet>(this.buildPath(id));
  }

  async list(params?: CourseMemberCommentQuery): Promise<CourseMemberCommentList[]> {
    const queryParams = params ? (params as unknown as Record<string, unknown>) : undefined;
    return this.client.get<CourseMemberCommentList[]>(this.basePath, queryParams ? { params: queryParams } : undefined);
  }

  async update(id: string | number, payload: CourseMemberCommentUpdate): Promise<CourseMemberCommentGet> {
    return this.client.patch<CourseMemberCommentGet>(this.buildPath(id), payload);
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete<void>(this.buildPath(id));
  }
}
