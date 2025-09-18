/**

 * Auto-generated TypeScript interfaces from Pydantic models

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

/**
 * Task execution result container.
 */
export interface TaskResult {
  task_id: string;
  status: TaskStatus;
  result?: any | null;
  error?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  progress?: Record<string, any> | null;
}

/**
 * Task submission request.
 */
export interface TaskSubmission {
  task_name: string;
  parameters?: Record<string, any>;
  queue?: string;
  workflow_id?: string | null;
  delay?: number | null;
}

/**
 * Task information for status queries.
 */
export interface TaskInfo {
  task_id: string;
  task_name: string;
  status: TaskStatus;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  progress?: Record<string, any> | null;
  error?: string | null;
  worker?: string | null;
  queue?: string | null;
  retries?: number | null;
  args?: any | null;
  kwargs?: Record<string, any> | null;
  short_task_id?: string | null;
  status_display?: string | null;
  completed_at?: string | null;
  has_result?: boolean | null;
  result_available?: string | null;
  duration?: string | null;
  workflow_id?: string | null;
  run_id?: string | null;
  execution_time?: string | null;
  history_length?: number | null;
}



export type TaskStatus = "queued" | "started" | "finished" | "failed" | "deferred" | "cancelled";