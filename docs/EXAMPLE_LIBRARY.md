# Example Library Documentation

## Overview

The Example Library is a comprehensive system for managing, organizing, and distributing programming examples across courses in the Computor platform. It provides a structured way to store, version, and share educational code examples with automatic metadata extraction and dependency management.

## Architecture

### Backend Components

#### Database Models
- **ExampleRepository**: Stores information about example storage locations (MinIO, Git, etc.)
- **Example**: Individual programming examples with metadata, tags, and hierarchical identifiers
- **ExampleVersion**: Versioned snapshots of examples with storage paths
- **ExampleDependency**: Relationships between examples for prerequisite tracking

#### API Endpoints
- `GET /examples` - List all examples with caching
- `GET /examples/{id}` - Get example details with versions and dependencies
- `POST /examples/upload` - Upload examples with automatic metadata extraction
- `GET /examples/download/{version_id}` - Download specific example versions
- Example repositories, versions, and dependencies have full CRUD operations

### Frontend Components

#### UI Pages
- **ExamplesPage**: Main dashboard with tabs for Examples and Repositories
- **ExampleDetailPage**: Detailed view with versions, dependencies, and metadata
  - Fixed navigation to return to `/admin/examples`
  - On-demand metadata loading when metadata tab is selected
  - Displays full `meta.yaml` and `test.yaml` content
  - Shows storage path information
  - Loading states for better UX
- **ExamplesTable**: Advanced data table with search, filtering, and actions
- **ExampleUploadDialog**: ZIP upload with automatic example detection
  - Batch upload support for multiple examples
  - Progress tracking with determinate progress bar
  - Partial failure handling
  - Auto-selection of first repository

## Key Features

### 1. Upload-Only Example Creation
Examples can only be created through the upload process, ensuring all examples have proper structure:
- No manual creation through API or UI forms
- Enforces presence of `meta.yaml` file
- Automatic parsing of metadata during upload

### 2. Automatic Directory Detection & Batch Upload
The upload dialog automatically scans ZIP files for example directories:
- Detects all directories containing `meta.yaml` files
- Allows selection of multiple examples from a single ZIP
- No manual directory input required
- Extracts metadata from each detected example
- Shows title, description, and slug for each detected example
- Provides "Select All" / "Deselect All" functionality
- Displays real-time upload progress (X of Y examples)
- Handles partial failures gracefully - successful uploads complete even if some fail
- Auto-selects the first repository in the dropdown for convenience

### 3. Metadata Management
Each example requires a `meta.yaml` file with:
```yaml
title: "Example Title"
description: "Description of the example"
slug: "hierarchical.identifier"
tags: ["python", "algorithms", "sorting"]
language: "python"  # or subject
```

Optional `test.yaml` for automated testing configuration.

### 4. Storage Integration
- Uses MinIO/S3 for file storage
- Supports multiple repository types (git, minio, s3, github, gitlab)
- Automatic file type validation and security checks
- Comprehensive download functionality with ZIP packaging

### 5. Hierarchical Organization
- Examples use Ltree for hierarchical identifiers (e.g., "python.basics.loops")
- Supports dot notation in directory names
- Enables structured browsing and categorization

### 6. Caching Strategy
- Redis caching with appropriate TTL values:
  - List operations: 5 minutes
  - Get operations: 10 minutes
- Automatic cache invalidation on updates
- JSON serialization with proper UUID handling

## Usage Guide

### Uploading Examples

1. **Prepare Example Directory Structure**:
   ```
   my-examples/
   ├── python-basics/
   │   ├── meta.yaml
   │   ├── hello_world.py
   │   └── README.md
   └── data-structures/
       ├── meta.yaml
       ├── test.yaml
       ├── linked_list.py
       └── binary_tree.py
   ```

2. **Create ZIP Archive**:
   ```bash
   zip -r examples.zip my-examples/
   ```

3. **Upload via UI**:
   - Navigate to Administration → Examples
   - Click "Upload Example"
   - Repository is auto-selected if only one exists
   - Enter version tag (defaults to v1.0)
   - Upload ZIP file containing one or more example directories
   - System automatically detects all examples with meta.yaml
   - Review detected examples with their metadata
   - Select/deselect examples to upload (all selected by default)
   - Click "Upload X Examples"
   - Monitor real-time progress
   - Handle any partial failures gracefully

### Downloading Examples

1. **From List View**:
   - Click the actions menu (⋮) on any example
   - Select "Download" to get the latest version

2. **From Detail View**:
   - Navigate to example details
   - Go to "Versions" tab
   - Click download icon for specific version

### Managing Repositories

1. **Create Repository**:
   - Navigate to "Repositories" tab
   - Click "Add Repository"
   - Configure storage type and credentials

2. **Default Repository**:
   - System initializes with default MinIO repository
   - Located at `example-library` bucket

## Security Considerations

1. **File Validation**:
   - File type whitelist (educational content only)
   - File size limits (20MB default)
   - Path traversal prevention
   - Content inspection for dangerous files

2. **Access Control**:
   - Role-based permissions for upload/download
   - Repository-level access control
   - Audit logging for uploads

3. **Storage Security**:
   - Encrypted credentials for repositories
   - Secure S3/MinIO integration
   - Presigned URLs for downloads

## Technical Implementation Details

### Frontend State Management
- Uses React hooks for local state
- TanStack Query for API integration
- Material-UI components for consistent UI
- JSZip for client-side ZIP handling

### Backend Processing
- YAML parsing with PyYAML
- Ltree extension for hierarchical paths
- SQLAlchemy for database operations
- MinIO client for object storage

### Database Schema
- UUID primary keys throughout
- JSONB for flexible metadata storage
- Check constraints for data validation
- Proper indexes for performance

## API Integration

### TypeScript Interfaces
```typescript
interface Example {
  id: string;
  example_repository_id: string;
  directory: string;
  identifier: string;
  title: string;
  description?: string;
  subject?: string;
  category?: string;
  tags: string[];
  // ... timestamps and relationships
}
```

### Upload Request Format
```typescript
interface ExampleUploadRequest {
  repository_id: string;
  directory: string;
  version_tag: string;
  files: Record<string, string>;
}
```

## Future Enhancements

1. **Git Integration**: Direct synchronization with Git repositories
2. **Dependency Resolution**: Automatic prerequisite checking
3. **Example Templates**: Starter templates for common patterns
4. **Bulk Operations**: Mass updates and migrations
5. **Version Comparison**: Diff view between versions
6. **Search Improvements**: Full-text search across example content

## Recent Enhancements (2025-07-30)

### Batch Upload Improvements
- **Multi-Example Detection**: ZIP files are scanned for all directories containing meta.yaml
- **Selective Upload**: Choose which examples to upload from detected list
- **Progress Tracking**: Real-time progress bar showing "X of Y examples uploaded"
- **Error Resilience**: Uses Promise.allSettled for partial failure handling
- **Auto-Selection**: First repository is automatically selected in dropdown
- **Better UX**: Clear feedback for successful and failed uploads

### Detail Page Improvements
- **Navigation Fix**: Back button correctly returns to /admin/examples
- **Metadata Loading**: On-demand loading when metadata tab is selected
- **Full Content Display**: Shows complete meta.yaml and test.yaml content
- **Loading States**: Spinner while fetching metadata
- **Storage Info**: Displays storage path for each version

### Technical Improvements
- **TypeScript**: Updated Dialog component to use slotProps instead of deprecated PaperProps
- **Performance**: Metadata loaded only when needed, not with initial page load
- **Error Handling**: Detailed error messages for each failed upload

## Troubleshooting

### Common Issues

1. **"No meta.yaml files found"**:
   - Ensure each example directory contains meta.yaml
   - Check ZIP structure doesn't have extra parent directories

2. **"Invalid directory format"**:
   - Directory names must match pattern: `^[a-zA-Z0-9._-]+$`
   - No spaces or special characters except dots, dashes, underscores

3. **Upload failures**:
   - Check repository permissions
   - Verify MinIO/S3 connectivity
   - Ensure valid YAML syntax in meta.yaml

### Debug Tools
- Check browser console for detailed errors
- Use network tab to inspect API responses
- Server logs for storage-related issues