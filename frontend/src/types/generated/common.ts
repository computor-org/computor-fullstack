/**

 * Auto-generated TypeScript interfaces from Pydantic models

 * Generated on: 2025-08-06T13:19:53.337845

 * Category: Common

 */



import type { CourseContentGet, CourseSignupResponse } from './courses';

import type { UserGet } from './users';



export interface ProfileCreate {
  /** Associated user ID */
  user_id: string;
  /** Avatar color as RGB integer (0-16777215) */
  avatar_color?: number | null;
  /** Avatar image URL */
  avatar_image?: string | null;
  /** Unique nickname */
  nickname?: string | null;
  /** User biography */
  bio?: string | null;
  /** User website URL */
  url?: string | null;
  /** Additional profile properties */
  properties?: any | null;
}

export interface ProfileGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  /** Profile unique identifier */
  id: string;
  /** Associated user ID */
  user_id: string;
  /** Avatar color as RGB integer */
  avatar_color?: number | null;
  /** Avatar image URL */
  avatar_image?: string | null;
  /** Unique nickname */
  nickname?: string | null;
  /** User biography */
  bio?: string | null;
  /** User website URL */
  url?: string | null;
  /** Additional properties */
  properties?: any | null;
}

export interface ProfileList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  /** Profile unique identifier */
  id: string;
  /** Associated user ID */
  user_id: string;
  /** Unique nickname */
  nickname?: string | null;
  /** Avatar image URL */
  avatar_image?: string | null;
  /** Avatar color */
  avatar_color?: number | null;
}

export interface ProfileUpdate {
  /** Avatar color as RGB integer */
  avatar_color?: number | null;
  /** Avatar image URL */
  avatar_image?: string | null;
  /** Unique nickname */
  nickname?: string | null;
  /** User biography */
  bio?: string | null;
  /** User website URL */
  url?: string | null;
  /** Additional properties */
  properties?: any | null;
}

export interface CourseMemberGitLabConfig {
  settings?: any | null;
  url?: string | null;
  full_path?: string | null;
  directory?: string | null;
  registry?: string | null;
  parent?: number | null;
  group_id?: number | null;
  parent_id?: number | null;
  namespace_id?: number | null;
  namespace_path?: string | null;
  web_url?: string | null;
  visibility?: string | null;
  last_synced_at?: string | null;
  full_path_submission?: string | null;
}

export interface Repository {
  url: string;
  user?: string | null;
  token?: string | null;
  branch?: string | null;
  path?: string | null;
  commit?: string | null;
}

export interface StudentProfileCreate {
  id?: string | null;
  student_id?: string | null;
  student_email?: string | null;
  user_id?: string | null;
}

export interface StudentProfileGet {
  id: string;
  student_id?: string | null;
  student_email?: string | null;
  user_id: string;
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
}

export interface StudentProfileList {
  id: string;
  student_id?: string | null;
  student_email?: string | null;
  user_id: string;
}

export interface StudentProfileUpdate {
  student_id?: string | null;
  student_email?: string | null;
  properties?: any | null;
}

export interface ExecutionBackendCreate {
  type: string;
  slug: string;
  properties?: any | null;
}

export interface ExecutionBackendGet {
  type: string;
  slug: string;
  properties?: any | null;
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
}

export interface ExecutionBackendList {
  id: string;
  type: string;
  slug: string;
}

export interface ExecutionBackendUpdate {
  type?: string | null;
  slug?: string | null;
  properties?: any | null;
}

export interface Claims {
  general?: any;
  dependent?: any;
}

export interface Principal {
  is_admin?: boolean;
  user_id?: string | null;
  roles?: string[];
  claims?: Claims;
}

export interface GroupCreate {
  /** Group name */
  name: string;
  /** Group description */
  description?: string | null;
  /** Type of group (fixed or dynamic) */
  group_type: any;
  /** Additional group properties */
  properties?: any | null;
}

export interface GroupGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  /** Group unique identifier */
  id: string;
  /** Group name */
  name: string;
  /** Group description */
  description?: string | null;
  /** Type of group */
  group_type: any;
  /** Additional properties */
  properties?: any | null;
}

export interface GroupList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  /** Group unique identifier */
  id: string;
  /** Group name */
  name: string;
  /** Group description */
  description?: string | null;
  /** Type of group */
  group_type: any;
}

export interface GroupUpdate {
  /** Group name */
  name?: string | null;
  /** Group description */
  description?: string | null;
  /** Type of group */
  group_type?: any | null;
  /** Additional properties */
  properties?: any | null;
}

export interface ListQuery {
  skip?: number | null;
  limit?: number | null;
}

export interface BaseEntityList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
}

export interface BaseEntityGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
}

export interface StudentTemplateSettings {
  mr_default_target_self?: boolean;
  merge_method?: any;
  only_allow_merge_if_pipeline_succeeds?: boolean;
  only_allow_merge_if_all_discussions_are_resolved?: boolean;
}

export interface FilterBase {
}

export interface ResultCreate {
  submit: boolean;
  course_member_id: string;
  course_content_id: string;
  course_submission_group_id?: string;
  execution_backend_id: string;
  test_system_id: string;
  result: number;
  result_json?: any | null;
  properties?: any | null;
  version_identifier: string;
  status: any;
}

export interface ResultGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  submit: boolean;
  course_member_id: string;
  course_content_id: string;
  course_content_type_id: string;
  course_submission_group_id?: string | null;
  execution_backend_id: string;
  test_system_id: string;
  result: number;
  result_json?: any | null;
  properties?: any | null;
  version_identifier: string;
  status: any;
}

export interface ResultList {
  id: string;
  submit: boolean;
  course_member_id: string;
  course_content_id: string;
  course_content_type_id: string;
  course_submission_group_id?: string | null;
  execution_backend_id: string;
  test_system_id: string;
  result: number;
  version_identifier: string;
  status: any;
}

export interface ResultUpdate {
  submit?: boolean | null;
  result?: number | null;
  result_json?: any | null;
  status?: any | null;
  test_system_id?: string | null;
  properties?: any | null;
}

export interface Submission {
  submission: Repository;
  provider: string;
  full_path: string;
  token: string;
  assignment: CourseContentGet;
  module: Repository;
  result_id: string;
  user_id: string;
}

export interface TestCreate {
  course_member_id?: string | null;
  course_content_id?: string | null;
  course_content_path?: string | null;
  directory?: string | null;
  project?: string | null;
  provider_url?: string | null;
  version_identifier?: string | null;
  submit?: boolean | null;
}

export interface SessionCreate {
  /** Associated user ID */
  user_id: string;
  /** Session identifier/token */
  session_id: string;
  /** IP address of the session */
  ip_address: string;
  /** Additional session properties */
  properties?: any | null;
}

export interface SessionGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  /** Session unique identifier */
  id: string;
  /** Associated user ID */
  user_id: string;
  /** Session identifier/token */
  session_id: string;
  /** Logout timestamp */
  logout_time?: string | null;
  /** IP address */
  ip_address: string;
  /** Additional properties */
  properties?: any | null;
}

export interface SessionList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  /** Session unique identifier */
  id: string;
  /** Associated user ID */
  user_id: string;
  /** Session identifier/token */
  session_id: string;
  /** Logout timestamp */
  logout_time?: string | null;
  /** IP address */
  ip_address: string;
}

export interface SessionUpdate {
  /** Logout timestamp */
  logout_time?: string | null;
  /** Additional properties */
  properties?: any | null;
}

export interface GroupClaimCreate {
  /** Group ID this claim belongs to */
  group_id: string;
  /** Type of claim (e.g., 'permission', 'attribute') */
  claim_type: string;
  /** Value of the claim */
  claim_value: string;
  /** Additional claim properties */
  properties?: any | null;
}

export interface GroupClaimGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  /** Group ID */
  group_id: string;
  /** Type of claim */
  claim_type: string;
  /** Value of the claim */
  claim_value: string;
  /** Additional properties */
  properties?: any | null;
}

export interface GroupClaimList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  /** Group ID */
  group_id: string;
  /** Type of claim */
  claim_type: string;
  /** Value of the claim */
  claim_value: string;
}

export interface GroupClaimUpdate {
  /** Additional claim properties */
  properties?: any | null;
}

/**
 * DTO for creating a student.
 */
export interface StudentCreate {
  user_id?: (string | string) | null;
  user?: UserGet | null;
  course_group_id?: (string | string) | null;
  course_group_title?: string | null;
  role?: string | null;
}

/**
 * DTO for releasing multiple students.
 */
export interface ReleaseStudentsCreate {
  students?: StudentCreate[];
  course_id: any;
}

/**
 * DTO for TUG student export data.
 */
export interface TUGStudentExport {
  course_group_title: string;
  family_name: string;
  given_name: string;
  matriculation_number: string;
  created_at: string;
}

/**
 * DTO for status query parameters.
 */
export interface StatusQuery {
  course_id?: string | null;
}

/**
 * GitLab connection credentials.
 */
export interface GitLabCredentials {
  gitlab_url: string;
  gitlab_token: string;
}

/**
 * Represents a pending change for template generation.
 */
export interface PendingChange {
  /** new, update, remove */
  type: string;
  content_id: string;
  path: string;
  title: string;
}

/**
 * Response for pending changes check.
 */
export interface PendingChangesResponse {
  total_changes: number;
  changes: PendingChange[];
  last_release?: Record<string, any> | null;
}

/**
 * Request to generate student template.
 */
export interface GenerateTemplateRequest {
  /** Custom commit message (optional) */
  commit_message?: string | null;
}

/**
 * Response for template generation request.
 */
export interface GenerateTemplateResponse {
  workflow_id: string;
  status?: string;
  contents_to_process: number;
}

export interface GitCommit {
  hash: string;
  date: string;
  message: string;
  author: string;
}

/**
 * Represents a test dependency with slug and version constraint.
 */
export interface TestDependency {
  /** Hierarchical slug of the dependency example (e.g., 'physics.math.vectors') */
  slug: string;
  /** Version constraint (e.g., '>=1.2.0', '^2.1.0', '1.0.0'). If not specified, uses latest version. */
  version?: string | null;
}

/**
 * Base class for all CodeAbility meta models.
 */
export interface CodeAbilityBase {
}

export interface SubmissionGroupProperties {
  gitlab?: GitLabConfig | null;
}

export interface SubmissionGroupCreate {
  properties?: SubmissionGroupProperties | null;
  max_group_size?: number;
  max_submissions?: number | null;
  course_content_id: string;
  status?: string | null;
}

export interface SubmissionGroupGet {
  properties?: SubmissionGroupProperties | null;
  max_group_size?: number;
  max_submissions?: number | null;
  course_content_id: string;
  status?: string | null;
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  course_id: string;
}

export interface SubmissionGroupList {
  id: string;
  properties?: SubmissionGroupProperties | null;
  max_group_size: number;
  max_submissions?: number | null;
  course_id: string;
  course_content_id: string;
  status?: string | null;
}

export interface SubmissionGroupUpdate {
  properties?: SubmissionGroupProperties | null;
  max_group_size?: number | null;
  max_submissions?: number | null;
  status?: string | null;
}

/**
 * Single deployment history action entry.
 */
export interface DeploymentHistoryAction {
  /** Type of deployment action */
  action: any;
  /** When the action occurred */
  timestamp: string;
  /** Example ID involved in the action */
  example_id?: string | null;
  /** Example version at time of action */
  example_version?: string | null;
  /** Previous example ID (for reassignment) */
  previous_example_id?: string | null;
  /** Previous example version (for reassignment) */
  previous_example_version?: string | null;
  /** Reason for the action (optional) */
  reason?: string | null;
  /** User ID who performed the action */
  performed_by?: string | null;
  /** Temporal workflow ID if applicable */
  workflow_id?: string | null;
  /** Error message if action failed */
  error_message?: string | null;
}

/**
 * Complete deployment history for a CourseContent.
 */
export interface DeploymentHistory {
  /** List of deployment actions in chronological order */
  actions?: DeploymentHistoryAction[];
  /** Timestamp of last successful deployment */
  last_successful_deployment?: string | null;
  /** Example ID of last successful deployment */
  last_successful_example_id?: string | null;
  /** Example version of last successful deployment */
  last_successful_example_version?: string | null;
}

export interface SubmissionGroupMemberProperties {
  gitlab?: GitLabConfig | null;
}

export interface SubmissionGroupMemberCreate {
  course_member_id: string;
  course_submission_group_id: string;
  grading?: number | null;
  properties?: SubmissionGroupMemberProperties | null;
}

export interface SubmissionGroupMemberGet {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  id: string;
  course_id: string;
  course_content_id: string;
  course_member_id: string;
  course_submission_group_id: string;
  grading?: number | null;
  status?: string | null;
  properties?: SubmissionGroupMemberProperties | null;
}

export interface SubmissionGroupMemberList {
  id: string;
  course_id: string;
  course_content_id: string;
  course_member_id: string;
  course_submission_group_id: string;
  grading?: number | null;
  status?: string | null;
}

export interface SubmissionGroupMemberUpdate {
  course_id?: string | null;
  grading?: number | null;
  status?: string | null;
  properties?: SubmissionGroupMemberProperties | null;
}

/**
 * Metadata for storage objects
 */
export interface StorageObjectMetadata {
  /** MIME type of the object */
  content_type: string;
  /** Size of the object in bytes */
  size: number;
  /** Entity tag of the object */
  etag: string;
  /** Last modification timestamp */
  last_modified: string;
  /** Custom metadata */
  metadata?: Record<string, string> | null;
}

/**
 * DTO for creating/uploading a storage object
 */
export interface StorageObjectCreate {
  /** Key/path for the object in the bucket */
  object_key: string;
  /** Target bucket name */
  bucket_name?: string | null;
  /** Custom metadata for the object */
  metadata?: Record<string, string> | null;
  /** MIME type of the object */
  content_type?: string | null;
}

/**
 * DTO for retrieving a storage object
 */
export interface StorageObjectGet {
  /** MIME type of the object */
  content_type: string;
  /** Size of the object in bytes */
  size: number;
  /** Entity tag of the object */
  etag: string;
  /** Last modification timestamp */
  last_modified: string;
  /** Custom metadata */
  metadata?: Record<string, string> | null;
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  /** Storage object ID */
  id: number;
  /** Object key/path in the bucket */
  object_key: string;
  /** Bucket name */
  bucket_name: string;
  /** Presigned download URL */
  download_url?: string | null;
}

/**
 * DTO for listing storage objects
 */
export interface StorageObjectList {
  /** Creation timestamp */
  created_at?: string | null;
  /** Update timestamp */
  updated_at?: string | null;
  /** Storage object ID */
  id: number;
  /** Object key/path in the bucket */
  object_key: string;
  /** Bucket name */
  bucket_name: string;
  /** MIME type of the object */
  content_type: string;
  /** Size of the object in bytes */
  size: number;
  /** Last modification timestamp */
  last_modified: string;
}

/**
 * DTO for updating storage object metadata
 */
export interface StorageObjectUpdate {
  /** Updated custom metadata */
  metadata?: Record<string, string> | null;
  /** Updated MIME type */
  content_type?: string | null;
}

/**
 * DTO for creating a storage bucket
 */
export interface BucketCreate {
  /** Name of the bucket to create */
  bucket_name: string;
  /** Region for the bucket */
  region?: string | null;
}

/**
 * DTO for bucket information
 */
export interface BucketInfo {
  /** Name of the bucket */
  bucket_name: string;
  /** Bucket creation date */
  creation_date?: string | null;
  /** Bucket region */
  region?: string | null;
}

/**
 * DTO for listing buckets
 */
export interface BucketList {
  /** List of buckets */
  buckets: BucketInfo[];
}

/**
 * DTO for generating presigned URLs
 */
export interface PresignedUrlRequest {
  /** Object key/path in the bucket */
  object_key: string;
  /** Bucket name */
  bucket_name?: string | null;
  /** URL expiry time in seconds */
  expiry_seconds?: number | null;
  /** HTTP method for the presigned URL */
  method?: string | null;
}

/**
 * DTO for presigned URL response
 */
export interface PresignedUrlResponse {
  /** The presigned URL */
  url: string;
  /** URL expiration timestamp */
  expires_at: string;
  /** HTTP method for the URL */
  method: string;
}

/**
 * DTO for storage usage statistics
 */
export interface StorageUsageStats {
  /** Bucket name */
  bucket_name: string;
  /** Number of objects in the bucket */
  object_count: number;
  /** Total size of all objects in bytes */
  total_size: number;
  /** Last statistics update timestamp */
  last_updated: string;
}

/**
 * Base class for all deployment configurations.
 */
export interface BaseDeployment {
}

/**
 * GitLab repository configuration.
 */
export interface GitLabConfig {
  /** GitLab instance URL */
  url?: string | null;
  /** GitLab API token */
  token?: string | null;
  /** Parent group ID */
  parent?: number | null;
  /** Full path in GitLab */
  full_path?: string | null;
  /** GitLab group ID */
  group_id?: number | null;
  /** Parent group ID */
  parent_id?: number | null;
  /** Namespace ID */
  namespace_id?: number | null;
  /** Namespace path */
  namespace_path?: string | null;
  /** Web URL */
  web_url?: string | null;
  /** Visibility level */
  visibility?: string | null;
  /** Last sync timestamp */
  last_synced_at?: string | null;
}

/**
 * GitHub repository configuration (future support).
 */
export interface GitHubConfig {
  /** GitHub instance URL */
  url?: string | null;
  /** GitHub API token */
  token?: string | null;
  /** GitHub organization */
  organization?: string | null;
}

/**
 * Execution backend configuration for courses.
 */
export interface ExecutionBackendConfig {
  /** Unique identifier for the backend */
  slug: string;
  /** Type of execution backend (e.g., python, matlab) */
  type: string;
  /** Backend version */
  version?: string | null;
  /** Backend-specific settings */
  settings?: Record<string, any> | null;
}

/**
 * Course content type configuration for deployment.
 */
export interface CourseContentTypeConfig {
  /** Unique identifier for the content type */
  slug: string;
  /** Display title for the content type */
  title?: string | null;
  /** Description of the content type */
  description?: string | null;
  /** Display color (hex, rgb, hsl, or named color) */
  color?: string | null;
  /** Additional properties */
  properties?: Record<string, any> | null;
  /** ID of the course content kind (e.g., 'assignment', 'unit') */
  course_content_kind_id: string;
}

/**
 * Configuration for course-related GitLab projects.
 */
export interface CourseProjects {
  /** Path for tests project */
  tests?: string | null;
  /** Path for student template project */
  student_template?: string | null;
  /** Path for reference solution project */
  reference?: string | null;
  /** Path for examples project */
  examples?: string | null;
  /** Path for documents project */
  documents?: string | null;
}

/**
 * Organization configuration.
 */
export interface OrganizationConfig {
  /** Organization display name */
  name: string;
  /** Organization path/slug */
  path: string;
  /** Organization description */
  description?: string | null;
  /** Organization-specific settings */
  settings?: Record<string, any> | null;
  /** GitLab configuration */
  gitlab?: GitLabConfig | null;
  /** GitHub configuration (future) */
  github?: GitHubConfig | null;
}

/**
 * Course family configuration.
 */
export interface CourseFamilyConfig {
  /** Course family display name */
  name: string;
  /** Course family path/slug */
  path: string;
  /** Course family description */
  description?: string | null;
  /** Course family-specific settings */
  settings?: Record<string, any> | null;
}

/**
 * Course configuration.
 */
export interface CourseConfig {
  /** Course display name */
  name: string;
  /** Course path/slug */
  path: string;
  /** Course description */
  description?: string | null;
  /** Course project structure */
  projects?: CourseProjects | null;
  /** Available execution backends for this course */
  execution_backends?: ExecutionBackendConfig[] | null;
  /** Course content types to be created (assignments, units, etc.) */
  content_types?: CourseContentTypeConfig[] | null;
  /** Course-specific settings */
  settings?: Record<string, any> | null;
}

/**
 * Course configuration for hierarchical deployment.
 */
export interface HierarchicalCourseConfig {
  /** Course display name */
  name: string;
  /** Course path/slug */
  path: string;
  /** Course description */
  description?: string | null;
  /** Course project structure */
  projects?: CourseProjects | null;
  /** Available execution backends for this course */
  execution_backends?: ExecutionBackendConfig[] | null;
  /** Course content types to be created (assignments, units, etc.) */
  content_types?: CourseContentTypeConfig[] | null;
  /** Course-specific settings */
  settings?: Record<string, any> | null;
}

/**
 * Course family configuration with nested courses.
 */
export interface HierarchicalCourseFamilyConfig {
  /** Course family display name */
  name: string;
  /** Course family path/slug */
  path: string;
  /** Course family description */
  description?: string | null;
  /** Course family-specific settings */
  settings?: Record<string, any> | null;
  /** List of courses in this course family */
  courses?: HierarchicalCourseConfig[];
}

/**
 * Organization configuration with nested course families.
 */
export interface HierarchicalOrganizationConfig {
  /** Organization display name */
  name: string;
  /** Organization path/slug */
  path: string;
  /** Organization description */
  description?: string | null;
  /** Organization-specific settings */
  settings?: Record<string, any> | null;
  /** GitLab configuration */
  gitlab?: GitLabConfig | null;
  /** GitHub configuration (future) */
  github?: GitHubConfig | null;
  /** List of course families in this organization */
  course_families?: HierarchicalCourseFamilyConfig[];
}

/**
 * Hierarchical deployment configuration for creating organization -> course family -> course structures.
 * 
 * Supports deploying multiple organizations, each with multiple course families and courses.
 */
export interface ComputorDeploymentConfig {
  /** List of organizations with nested course families and courses */
  organizations: HierarchicalOrganizationConfig[];
  /** Global deployment settings */
  settings?: Record<string, any> | null;
}

export interface GitlabGroupProjectConfig {
  name?: string | null;
  path: string;
}

export interface CourseProjectsConfig {
  tests: GitlabGroupProjectConfig;
  student_template: GitlabGroupProjectConfig;
  reference: GitlabGroupProjectConfig;
  images: GitlabGroupProjectConfig;
  documents: GitlabGroupProjectConfig;
}

export interface ApiConfig {
  user: string;
  password: string;
  url: string;
}

export interface RepositoryConfig {
  settings?: any | null;
}

export interface GitLabConfigGet {
  settings?: any | null;
  url?: string | null;
  full_path?: string | null;
  directory?: string | null;
  registry?: string | null;
  parent?: number | null;
  group_id?: number | null;
  parent_id?: number | null;
  namespace_id?: number | null;
  namespace_path?: string | null;
  web_url?: string | null;
  visibility?: string | null;
  last_synced_at?: string | null;
}

export interface TypeConfig {
  kind: string;
  slug: string;
  title: string;
  color?: string | null;
  description?: string | null;
  properties?: any;
}

export interface CourseGroupConfig {
  name: string;
}

export interface CourseExecutionBackendConfig {
  slug: string;
  settings?: any | null;
}

export interface FileSourceConfig {
  url: string;
  token?: string | null;
}

export interface CourseSettingsConfig {
  source?: FileSourceConfig | null;
}

export interface CodeAbilityTestCommon {
  failureMessage?: string | null;
  successMessage?: string | null;
  qualification?: any | null;
  relativeTolerance?: number | null;
  absoluteTolerance?: number | null;
  allowedOccuranceRange?: number[] | null;
  occuranceType?: string | null;
  verbosity?: number | null;
}

export interface VSCExtensionConfig {
  project_id: number;
  gitlab_url: string;
  file_path: string;
  download_link: string;
}

/**
 * Request model for deployment from configuration.
 */
export interface DeploymentRequest {
  /** Deployment configuration as dictionary */
  deployment_config: Record<string, any>;
  /** If true, only validate the configuration without deploying */
  validate_only?: boolean;
}

/**
 * Response model for deployment operations.
 */
export interface DeploymentResponse {
  /** Temporal workflow ID */
  workflow_id: string;
  /** Deployment status */
  status: string;
  /** Status message */
  message: string;
  /** Full deployment path */
  deployment_path?: string | null;
}

export interface GitlabSignup {
  provider: string;
  token: string;
}

export interface GitlabSignupResponse {
  courses?: CourseSignupResponse[];
}