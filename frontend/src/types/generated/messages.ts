/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-09-17T14:46:20.419292

 * Category: Messages

 */



export interface MessageCreate {
  parent_id?: string | null;
  level?: number;
  title: string;
  content: string;
  user_id?: string | null;
  course_member_id?: string | null;
  course_submission_group_id?: string | null;
  course_group_id?: string | null;
  course_content_id?: string | null;
  course_id?: string | null;
}

export interface MessageUpdate {
  title?: string | null;
  content?: string | null;
}

export interface MessageGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  title: string;
  content: string;
  level: number;
  parent_id?: string | null;
  author_id: string;
  user_id?: string | null;
  course_member_id?: string | null;
  course_submission_group_id?: string | null;
  course_group_id?: string | null;
  course_content_id?: string | null;
  course_id?: string | null;
}

export interface MessageList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  id: string;
  title: string;
  content: string;
  level: number;
  parent_id?: string | null;
  author_id: string;
  user_id?: string | null;
  course_member_id?: string | null;
  course_submission_group_id?: string | null;
  course_group_id?: string | null;
  course_content_id?: string | null;
  course_id?: string | null;
}