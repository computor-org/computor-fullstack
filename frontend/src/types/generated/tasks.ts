/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-09-18T17:27:35.884978

 * Category: Tasks

 */



import type { Repository } from './common';



export interface TestJob {
  user_id: string;
  course_member_id: string;
  course_content_id: string;
  execution_backend_id: string;
  execution_backend_type: string;
  module: Repository;
  reference?: Repository | null;
  test_number?: number;
  submission_number?: number;
}

/**
 * Response with task ID for async operation.
 */
export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}