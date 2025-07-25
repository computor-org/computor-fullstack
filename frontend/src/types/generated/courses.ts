/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-07-21T09:06:47.326009

 * Category: Courses

 */



import type { ComputorDeploymentConfig, CourseMemberGitLabConfig, GitLabConfig, GitLabConfigGet } from './common';

import type { OrganizationGet } from './organizations';

import type { UserList } from './users';



export interface TutorCourseMemberCourseContent {
  id: string;
  path: string;
}

export interface TutorCourseMemberGet {
  id: string;
  properties?: CourseMemberProperties | null;
  user_id: string;
  course_id: string;
  course_group_id?: string | null;
  course_role_id: string;
  unreviewed_course_contents?: TutorCourseMemberCourseContent[];
  user: UserList;
}

export interface TutorCourseMemberList {
  id: string;
  user_id: string;
  course_id: string;
  course_group_id?: string | null;
  course_role_id: string;
  unreviewed?: boolean | null;
  user: UserList;
}

export interface CourseProperties {
  gitlab?: GitLabConfig | null;
}

export interface CoursePropertiesGet {
  gitlab?: GitLabConfigGet | null;
}

export interface CourseCreate {
  id?: string | null;
  title?: string | null;
  description?: string | null;
  path: string;
  course_family_id: string;
  version_identifier?: string | null;
  properties?: CourseProperties | null;
}

export interface CourseGet {
  id: string;
  title?: string | null;
  description?: string | null;
  path: string;
  course_family_id: string;
  version_identifier?: string | null;
  properties?: CoursePropertiesGet | null;
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  organization_id: string;
  course_family?: CourseFamilyGet | null;
}

export interface CourseList {
  id: string;
  title?: string | null;
  course_family_id?: string | null;
  organization_id?: string | null;
  version_identifier?: string | null;
  path: string;
  properties?: CoursePropertiesGet | null;
}

export interface CourseUpdate {
  title?: string | null;
  description?: string | null;
  version_identifier?: string | null;
  properties?: CourseProperties | null;
}

export interface CourseMemberProperties {
  gitlab?: CourseMemberGitLabConfig | null;
}

export interface CourseMemberCreate {
  id?: string | null;
  properties?: CourseMemberProperties | null;
  user_id: string;
  course_id: string;
  course_group_id?: string | null;
  course_role_id: string;
}

export interface CourseMemberGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  properties?: CourseMemberProperties | null;
  user_id: string;
  course_id: string;
  course_group_id?: string | null;
  course_role_id: string;
  user?: UserList | null;
}

export interface CourseMemberList {
  id: string;
  user_id: string;
  course_id: string;
  course_group_id?: string | null;
  course_role_id: string;
  user: UserList;
}

export interface CourseMemberUpdate {
  properties?: CourseMemberProperties | null;
  course_group_id?: string | null;
  course_role_id?: string | null;
}

export interface CourseExecutionBackendCreate {
  execution_backend_id: string;
  course_id: string;
  properties?: any | null;
}

export interface CourseExecutionBackendGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  execution_backend_id: string;
  course_id: string;
  properties?: any | null;
}

export interface CourseExecutionBackendList {
  execution_backend_id: string;
  course_id: string;
}

export interface CourseExecutionBackendUpdate {
  properties?: any | null;
}

export interface CourseRoleGet {
  id: string;
  title?: string | null;
  description?: string | null;
}

export interface CourseContentTypeCreate {
  slug: string;
  title?: string | null;
  description?: string | null;
  color?: string | null;
  properties?: any | null;
  course_id: string;
  course_content_kind_id: string;
}

export interface CourseContentTypeGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  slug: string;
  title?: string | null;
  description?: string | null;
  color: string;
  properties?: any | null;
  course_id: string;
  course_content_kind_id: string;
  course_content_kind?: CourseContentKindGet | null;
}

export interface CourseContentTypeList {
  id: string;
  slug: string;
  title?: string | null;
  color: string;
  course_id: string;
  course_content_kind_id: string;
}

export interface CourseContentTypeUpdate {
  slug?: string | null;
  title?: string | null;
  color?: string | null;
  description?: string | null;
  properties?: any | null;
}

export interface CourseGroupCreate {
  title?: string | null;
  description?: string | null;
  course_id: string;
  properties?: any | null;
}

export interface CourseGroupGet {
  title?: string | null;
  description?: string | null;
  course_id: string;
  properties?: any | null;
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
}

export interface CourseGroupList {
  id: string;
  title?: string | null;
  course_id: string;
}

export interface CourseGroupUpdate {
  title?: string | null;
  description?: string | null;
  course_id?: string | null;
  properties?: any | null;
}

export interface SubmissionGroupStudentList {
  id?: string | null;
  status?: string | null;
  grading?: number | null;
  count: number;
  max_submissions?: number | null;
}

export interface ResultStudentList {
  execution_backend_id?: string | null;
  test_system_id?: string | null;
  version_identifier?: string | null;
  status?: any | null;
  result?: number | null;
  result_json?: any | null;
  submit?: boolean | null;
}

export interface CourseContentStudentProperties {
  gitlab?: GitLabConfigGet | null;
}

export interface CourseContentStudentGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  archived_at?: string | null;
  title?: string | null;
  description?: string | null;
  path: string;
  course_id: string;
  course_content_type_id: string;
  course_content_kind_id: string;
  version_identifier: string;
  position: number;
  max_group_size?: number | null;
  submitted?: boolean | null;
  course_content_types: CourseContentTypeGet;
  result_count: number;
  max_test_runs?: number | null;
}

export interface CourseContentStudentList {
  id: string;
  title?: string | null;
  path: string;
  course_id: string;
  course_content_type_id: string;
  course_content_kind_id: string;
  version_identifier: string;
  position: number;
  max_group_size?: number | null;
  submitted?: boolean | null;
  course_content_type: CourseContentTypeList;
  result_count: number;
  max_test_runs?: number | null;
  directory: string;
  color: string;
  result?: ResultStudentList | null;
  submission?: SubmissionGroupStudentList | null;
}

export interface CourseContentStudentUpdate {
  status?: any | null;
  grading?: number | null;
}

export interface CourseStudentRepository {
  provider_url?: string | null;
  full_path?: string | null;
}

export interface CourseStudentGet {
  id: string;
  title?: string | null;
  course_family_id?: string | null;
  organization_id?: string | null;
  version_identifier?: string | null;
  course_content_types: CourseContentTypeGet[];
  path: string;
  repository: CourseStudentRepository;
}

export interface CourseStudentList {
  id: string;
  title?: string | null;
  course_family_id?: string | null;
  organization_id?: string | null;
  version_identifier?: string | null;
  path: string;
  course_content_types: CourseContentTypeList[];
  repository: CourseStudentRepository;
}

export interface CourseContentKindCreate {
  title?: string | null;
  description?: string | null;
  has_ascendants: boolean;
  has_descendants: boolean;
  submittable: boolean;
}

export interface CourseContentKindGet {
  title?: string | null;
  description?: string | null;
  has_ascendants: boolean;
  has_descendants: boolean;
  submittable: boolean;
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
}

export interface CourseContentKindList {
  id: string;
  title?: string | null;
  has_ascendants: boolean;
  has_descendants: boolean;
  submittable: boolean;
}

export interface CourseContentKindUpdate {
  title?: string | null;
  description?: string | null;
}

export interface CourseFamilyProperties {
  gitlab?: GitLabConfig | null;
}

export interface CourseFamilyPropertiesGet {
  gitlab?: GitLabConfigGet | null;
}

export interface CourseFamilyCreate {
  title?: string | null;
  description?: string | null;
  path: string;
  organization_id: string;
  properties?: CourseFamilyProperties | null;
}

export interface CourseFamilyGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  title?: string | null;
  description?: string | null;
  path: string;
  organization_id: string;
  properties?: CourseFamilyPropertiesGet | null;
  organization?: OrganizationGet | null;
}

export interface CourseFamilyList {
  id: string;
  title?: string | null;
  organization_id: string;
  path: string;
}

export interface CourseFamilyUpdate {
  title?: string | null;
  description?: string | null;
  path?: string | null;
  organization_id?: string | null;
  properties?: CourseFamilyProperties | null;
}

export interface CourseContentProperties {
  gitlab?: GitLabConfig | null;
}

export interface CourseContentPropertiesGet {
  gitlab?: GitLabConfigGet | null;
}

export interface CourseContentCreate {
  title?: string | null;
  description?: string | null;
  path: string;
  course_id: string;
  course_content_type_id: string;
  properties?: CourseContentProperties | null;
  version_identifier: string;
  position?: number;
  max_group_size?: number | null;
  max_test_runs?: number | null;
  max_submissions?: number | null;
  execution_backend_id?: string | null;
}

export interface CourseContentGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  archived_at?: string | null;
  title?: string | null;
  description?: string | null;
  path: string;
  course_id: string;
  course_content_type_id: string;
  course_content_kind_id: string;
  properties?: CourseContentPropertiesGet | null;
  version_identifier: string;
  position: number;
  max_group_size?: number | null;
  max_test_runs?: number | null;
  max_submissions?: number | null;
  execution_backend_id?: string | null;
  course_content_type?: CourseContentTypeGet | null;
}

export interface CourseContentList {
  id: string;
  title?: string | null;
  path: string;
  course_id: string;
  course_content_type_id: string;
  course_content_kind_id: string;
  version_identifier: string;
  position: number;
  max_group_size?: number | null;
  max_test_runs?: number | null;
  max_submissions?: number | null;
  execution_backend_id?: string | null;
}

export interface CourseContentUpdate {
  path?: string | null;
  title?: string | null;
  description?: string | null;
  properties?: CourseContentProperties | null;
  version_identifier?: string | null;
  position?: number | null;
  max_group_size?: number | null;
  max_test_runs?: number | null;
  max_submissions?: number | null;
  execution_backend_id?: string | null;
}

export interface CourseMemberCommentCreate {
  id?: string | null;
  transmitter_id?: string;
  course_member_id: string;
  message: string;
}

export interface CourseMemberCommentGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  transmitter_id?: string;
  transmitter: CourseMemberGet;
  course_member_id: string;
  message: string;
}

export interface CourseMemberCommentList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  transmitter_id?: string;
  transmitter: CourseMemberList;
  course_member_id: string;
  message: string;
}

export interface CourseMemberCommentUpdate {
  message?: string | null;
}

export interface CourseTutorRepository {
  provider_url?: string | null;
  full_path_reference?: string | null;
}

export interface CourseTutorGet {
  id: string;
  title?: string | null;
  course_family_id?: string | null;
  organization_id?: string | null;
  version_identifier?: string | null;
  path: string;
  repository: CourseTutorRepository;
}

export interface CourseTutorList {
  id: string;
  title?: string | null;
  course_family_id?: string | null;
  organization_id?: string | null;
  version_identifier?: string | null;
  path: string;
  repository: CourseTutorRepository;
}

export interface CourseSignupResponse {
  course_id: string;
  course_title: string;
  role: string;
  repository: string;
}

export interface ReleaseCourseCreate {
  course_id?: string | null;
  gitlab_url?: string | null;
  descendants?: boolean | null;
  deployment?: ComputorDeploymentConfig | null;
}

export interface ReleaseCourseContentCreate {
  release_dir?: string | null;
  course_id?: string | null;
  gitlab_url?: string | null;
  ascendants?: boolean;
  descendants?: boolean;
  release_dir_list?: string[];
}

export interface CourseReleaseUpdate {
  course?: CourseUpdate | null;
  course_content_types: CourseContentTypeCreate[];
}

export interface CourseContentMessage {
  body: string;
}

export interface CourseContentFileQuery {
  filename?: string | null;
}

export interface CourseMemberCommentTutorCreate {
  message: string;
}

export interface CourseMemberCommentTutorUpdate {
  message: string;
}