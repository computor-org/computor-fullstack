export interface Student {
  id: string;
  givenName: string;
  familyName: string;
  email: string;
  studentId: string;
  enrollmentDate: string;
  status: 'active' | 'inactive' | 'suspended';
  grade?: number;
}

export interface Course {
  id: string;
  title: string;
  description: string;
  code: string;
  semester: string;
  credits: number;
  instructor: string;
  enrolledStudents: number;
  maxStudents: number;
  status: 'active' | 'inactive' | 'archived';
}

export interface Assignment {
  id: string;
  title: string;
  description: string;
  courseId: string;
  dueDate: string;
  maxScore: number;
  submissionsCount: number;
  status: 'draft' | 'published' | 'closed';
}

export interface Submission {
  id: string;
  studentId: string;
  assignmentId: string;
  submittedAt: string;
  score?: number;
  status: 'submitted' | 'graded' | 'late' | 'pending';
}

export interface User {
  id: string;
  given_name: string;
  family_name: string;
  email: string;
  username?: string;
  user_type: 'user' | 'token';
  fs_number: number;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
  token_expiration?: string;
  password?: string;
  auth_token?: string;
}

export interface Account {
  id: string;
  provider: string;
  type: string;
  provider_account_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}