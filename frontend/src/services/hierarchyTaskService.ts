/**
 * Service for managing hierarchy creation tasks (Organization → Course Family → Course).
 * 
 * This service provides task-based creation with GitLab integration,
 * allowing users to create entities asynchronously and monitor progress.
 */

import { apiClient } from './apiClient';

export interface GitLabCredentials {
  gitlab_url: string;
  gitlab_token: string;
}

export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskStatus {
  task_id: string;
  task_name: string;
  status: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'RETRY' | 'REVOKED';
  created_at: string;
  started_at?: string;
  finished_at?: string;
  progress?: {
    stage?: string;
    progress?: number;
    current?: number;
    total?: number;
  };
  error?: string;
}

export interface TaskStatusResponse {
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  message?: string;
  result?: any;
}

export interface TaskResult {
  task_id: string;
  status: string;
  result?: any;
  error?: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  progress?: any;
}

export interface OrganizationTaskRequest {
  organization: {
    title: string;
    path: string;
    description?: string;
    organization_type: 'user' | 'community' | 'organization';
    number?: string;
    email?: string;
    telephone?: string;
    url?: string;
    street_address?: string;
    locality?: string;
    region?: string;
    postal_code?: string;
    country?: string;
  };
  gitlab: GitLabCredentials;
  parent_group_id: number;
}

export interface CourseFamilyTaskRequest {
  course_family: {
    title: string;
    path: string;
    description?: string;
    organization_id: string;
  };
  organization_id: string;
  gitlab?: GitLabCredentials;  // Optional - will use org's GitLab config if not provided
}

export interface CourseTaskRequest {
  course: {
    title: string;
    path: string;
    description?: string;
    course_family_id: string;
  };
  course_family_id: string;
  gitlab?: GitLabCredentials;  // Optional - will use course family's GitLab config if not provided
}

export interface HierarchyTaskRequest {
  organization: {
    title: string;
    path: string;
    description?: string;
    organization_type: 'user' | 'community' | 'organization';
  };
  course_family: {
    title: string;
    path: string;
    description?: string;
    organization_id: string;
  };
  course: {
    title: string;
    path: string;
    description?: string;
    course_family_id: string;
  };
  gitlab: GitLabCredentials;
  parent_group_id: number;
}

export class HierarchyTaskService {
  
  /**
   * Create an organization asynchronously with GitLab integration
   */
  static async createOrganization(request: OrganizationTaskRequest): Promise<TaskResponse> {
    try {
      const response = await apiClient.post<TaskResponse>('/system/hierarchy/organizations/create', request);
      return response;
    } catch (error: any) {
      console.error('Error creating organization task:', error);
      throw new Error(error.message || 'Failed to create organization task');
    }
  }

  /**
   * Create a course family asynchronously with GitLab integration
   */
  static async createCourseFamily(request: CourseFamilyTaskRequest): Promise<TaskResponse> {
    try {
      const response = await apiClient.post<TaskResponse>('/system/hierarchy/course-families/create', request);
      return response;
    } catch (error: any) {
      console.error('Error creating course family task:', error);
      throw new Error(error.message || 'Failed to create course family task');
    }
  }

  /**
   * Create a course asynchronously with GitLab integration
   */
  static async createCourse(request: CourseTaskRequest): Promise<TaskResponse> {
    try {
      const response = await apiClient.post<TaskResponse>('/system/hierarchy/courses/create', request);
      return response;
    } catch (error: any) {
      console.error('Error creating course task:', error);
      throw new Error(error.message || 'Failed to create course task');
    }
  }

  /**
   * Get task status from system endpoint
   */
  static async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    try {
      const response = await apiClient.get<TaskStatusResponse>(`/system/status/${taskId}`);
      return response;
    } catch (error: any) {
      console.error('Error getting task status:', error);
      throw new Error(error.message || 'Failed to get task status');
    }
  }


  /**
   * Get task result (waits for completion)
   */
  static async getTaskResult(taskId: string): Promise<TaskResult> {
    try {
      const response = await apiClient.get<TaskResult>(`/tasks/${taskId}/result`);
      return response;
    } catch (error: any) {
      console.error('Error getting task result:', error);
      throw new Error(error.message || 'Failed to get task result');
    }
  }

  /**
   * Wait for task completion with polling
   */
  static async waitForTaskCompletion(
    taskId: string, 
    onProgress?: (status: TaskStatus) => void,
    pollInterval: number = 2000,
    maxWaitTime: number = 300000 // 5 minutes
  ): Promise<TaskResult> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
      try {
        const status = await this.getTaskStatus(taskId);
        
        // Convert TaskStatusResponse to TaskStatus for onProgress callback
        if (onProgress && status) {
          const taskStatus: TaskStatus = {
            task_id: taskId,
            task_name: 'hierarchy_creation',
            status: status.status === 'COMPLETED' ? 'SUCCESS' : 
                   status.status === 'FAILED' ? 'FAILURE' : 
                   status.status === 'RUNNING' ? 'PROGRESS' : 'PENDING',
            created_at: new Date().toISOString(),
            progress: status.message ? { stage: status.message } : undefined,
            error: status.status === 'FAILED' ? status.message : undefined
          };
          onProgress(taskStatus);
        }
        
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          return {
            task_id: taskId,
            status: status.status,
            result: status.result,
            error: status.status === 'FAILED' ? status.message : undefined,
            created_at: new Date().toISOString(),
            finished_at: new Date().toISOString()
          };
        }
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        
      } catch (error) {
        console.error('Error polling task status:', error);
        // Continue polling in case of temporary errors
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
    }
    
    throw new Error(`Task ${taskId} did not complete within ${maxWaitTime}ms`);
  }

  /**
   * Cancel a running task
   */
  static async cancelTask(taskId: string): Promise<void> {
    try {
      await apiClient.delete(`/tasks/${taskId}/cancel`);
    } catch (error: any) {
      console.error('Error cancelling task:', error);
      throw new Error(error.message || 'Failed to cancel task');
    }
  }
}