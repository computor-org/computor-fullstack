export interface ExampleRepository {
  id: string;
  name: string;
  description?: string;
  source_type: 'git' | 'minio' | 'github' | 's3' | 'gitlab';
  source_url: string;
  access_credentials?: string;
  default_version?: string;
  organization_id?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

export interface Example {
  id: string;
  example_repository_id: string;
  directory: string;
  identifier: string;
  title: string;
  description?: string;
  subject?: string;
  category?: string;
  tags: string[];
  version_identifier?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
  repository?: ExampleRepository;
  versions?: ExampleVersion[];
  dependencies?: ExampleDependency[];
}

export interface ExampleVersion {
  id: string;
  example_id: string;
  version_tag: string;
  version_number: number;
  storage_path: string;
  meta_yaml: string;
  test_yaml?: string;
  created_at: string;
  created_by?: string;
}

export interface ExampleDependency {
  id: string;
  example_id: string;
  depends_id: string;
  created_at: string;
  dependency?: Example;
}

export interface ExampleUploadRequest {
  repository_id: string;
  directory: string;
  version_tag: string;
  files: Record<string, string>;
}

export interface ExampleDownloadResponse {
  example_id: string;
  version_id: string;
  version_tag: string;
  files: Record<string, string>;
  meta_yaml: string;
  test_yaml?: string;
}

// Query interfaces for filtering and search
export interface ExampleQuery {
  repository_id?: string;
  identifier?: string;
  title?: string;
  subject?: string;
  category?: string;
  tags?: string[];
  search?: string;
  limit?: number;
  offset?: number;
}

export interface ExampleRepositoryQuery {
  name?: string;
  source_type?: string;
  organization_id?: string;
  limit?: number;
  offset?: number;
}