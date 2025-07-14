/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-07-15T01:10:05.970668

 * Category: Tasks

 */



import type { Repository } from './common';



export interface TestJob {
  user_id: string;
  course_member_id: string;
  course_content_id: string;
  execution_backend_id: string;
  module: Repository;
  reference?: Repository | null;
  test_number?: number;
  submission_number?: number;
}