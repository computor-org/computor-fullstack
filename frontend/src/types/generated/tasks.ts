/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-09-18T14:42:27.802815

 * Category: Tasks

 */



import type { Repository } from './common';



/**
 * Response with task ID for async operation.
 */
export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}

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