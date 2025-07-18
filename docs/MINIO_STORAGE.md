# MinIO Object Storage Integration

This document describes the MinIO object storage integration in the Computor platform, providing scalable and S3-compatible storage for files, documents, and other binary data.

## Overview

The MinIO integration provides a complete object storage solution with:
- S3-compatible API for easy integration
- Scalable storage for course materials, submissions, and documents
- Presigned URLs for secure direct access
- Bucket management and organization
- Redis caching for improved performance

## Architecture

### Components

1. **MinIO Service** (`docker-compose-*.yaml`)
   - Runs as a containerized service
   - Exposes API on port 9000 and console on port 9001
   - Data persisted in `${SYSTEM_DEPLOYMENT_PATH}/minio/data`

2. **Storage Service** (`services/storage_service.py`)
   - Singleton service managing MinIO client
   - Handles all storage operations
   - Automatic bucket creation
   - Error handling and logging

3. **API Routes** (`api/storage.py`)
   - RESTful endpoints for storage operations
   - Permission-based access control
   - Redis caching for performance
   - Streaming uploads/downloads

4. **Pydantic Models** (`interface/storage.py`)
   - Type-safe DTOs for all operations
   - Request/response validation
   - Consistent API contracts

## Configuration

### Environment Variables

```bash
# MinIO Configuration
MINIO_ROOT_USER=minioadmin          # MinIO admin username
MINIO_ROOT_PASSWORD=minioadmin      # MinIO admin password
MINIO_DEFAULT_BUCKETS=computor-storage  # Default bucket name
MINIO_REGION=us-east-1             # AWS region (for compatibility)
MINIO_ENDPOINT=minio:9000          # MinIO endpoint (internal to Docker)
MINIO_SECURE=false                 # Use HTTPS (false for local dev)

# Storage Security Configuration
MINIO_MAX_UPLOAD_SIZE=20971520     # Maximum file size (20MB default)
```

### Docker Compose

The MinIO service is configured in both development and production compose files:

```yaml
minio:
  image: minio/minio:latest
  ports:
    - "9000:9000"  # API port
    - "9001:9001"  # Console port
  volumes:
    - ${SYSTEM_DEPLOYMENT_PATH}/minio/data:/data
  environment:
    MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
    MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
  command: server /data --console-address ":9001"
```

## API Endpoints

### Object Operations

- `POST /storage/upload` - Upload a file
- `GET /storage/download/{object_key}` - Download a file
- `GET /storage/objects` - List objects with filtering
- `GET /storage/objects/{object_key}` - Get object metadata
- `DELETE /storage/objects/{object_key}` - Delete an object
- `POST /storage/copy` - Copy an object
- `POST /storage/presigned-url` - Generate presigned URL

### Bucket Operations

- `GET /storage/buckets` - List all buckets
- `POST /storage/buckets` - Create a new bucket
- `DELETE /storage/buckets/{bucket_name}` - Delete a bucket
- `GET /storage/buckets/{bucket_name}/stats` - Get bucket statistics

## Permissions

Storage operations are protected by the permission system:

- `storage:create` - Upload files, copy objects, generate upload URLs
- `storage:get` - Download files, view metadata, generate download URLs
- `storage:list` - List objects in buckets
- `storage:delete` - Delete objects, generate delete URLs
- `storage:admin` - Manage buckets (create, delete, list)

## Security Features

### File Upload Security

1. **File Size Limits** - Maximum upload size enforced (20MB default)
2. **File Type Whitelist** - Only allowed educational file types:
   - Documents: PDF, DOC, DOCX, TXT, MD
   - Spreadsheets: XLS, XLSX, CSV
   - Images: JPG, PNG, GIF, SVG
   - Code files: PY, JAVA, C, CPP, JS, HTML, CSS
   - Archives: ZIP, TAR, GZ (with content inspection)
3. **Filename Sanitization** - Prevents path traversal and special characters
4. **Content Validation** - Blocks executables and dangerous file types
5. **Metadata Tracking** - Records uploader, timestamp, and original filename

### Allowed File Extensions

The system uses a whitelist approach for maximum security. See `storage_config.py` for the complete list of allowed extensions and MIME types.

### Future Security Enhancements

- **Rate Limiting** - Prevent abuse with per-IP limits (using slowapi)
- **Virus Scanning** - Integration with ClamAV or similar
- **Storage Quotas** - Per-user and per-course limits
- **Encryption** - Server-side encryption at rest
- **Access Logs** - Detailed audit trail of all operations

## Usage Examples

### Upload a File

```python
import requests

# Upload file with basic auth
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/storage/upload',
        auth=('admin', 'admin'),
        files={'file': f},
        data={'object_key': 'courses/cs101/document.pdf'}
    )
```

### Generate Presigned URL

```python
# Generate a presigned URL for direct download
response = requests.post(
    'http://localhost:8000/storage/presigned-url',
    auth=('admin', 'admin'),
    json={
        'object_key': 'courses/cs101/document.pdf',
        'method': 'GET',
        'expiry_seconds': 3600
    }
)
presigned_url = response.json()['url']
```

### List Objects with Filtering

```python
# List all objects in a specific prefix
response = requests.get(
    'http://localhost:8000/storage/objects',
    auth=('admin', 'admin'),
    params={
        'prefix': 'courses/cs101/',
        'content_type': 'application/pdf'
    }
)
objects = response.json()
```

## Storage Organization

Recommended object key structure for different use cases:

```
courses/{course_id}/materials/{filename}      # Course materials
courses/{course_id}/submissions/{user_id}/{filename}  # Student submissions
organizations/{org_id}/documents/{filename}   # Organization documents
users/{user_id}/profile/{filename}           # User profile assets
temp/{session_id}/{filename}                 # Temporary files
```

## Caching Strategy

- Object listings are cached for 60 seconds
- Bucket statistics are cached for 5 minutes
- Cache keys include query parameters for accurate invalidation
- Cache is cleared on object deletion

## Error Handling

The integration handles common storage errors:

- `NotFoundException` - Object or bucket not found
- `BadRequestException` - Invalid parameters or bucket already exists
- `ForbiddenException` - Insufficient permissions
- `ServiceUnavailableException` - MinIO connection issues

## Testing

### Integration Test Script

A comprehensive test script is available for validating the integration:

```python
# Create test_minio_integration.py with the test code
python test_minio_integration.py
```

The test covers:
- Authentication
- File upload/download
- Object listing and metadata
- Presigned URL generation
- Object copying
- Bucket operations
- Object deletion

### Direct MinIO Testing

For testing MinIO directly:

```python
from minio import Minio

client = Minio(
    'localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)

# List buckets
for bucket in client.list_buckets():
    print(bucket.name)
```

## MinIO Console

Access the MinIO web console at http://localhost:9001 with:
- Username: `minioadmin`
- Password: `minioadmin`

The console provides:
- Visual bucket management
- Object browser
- Access policy configuration
- User management
- Server diagnostics

## Production Considerations

1. **Security**
   - Change default credentials
   - Enable HTTPS (`MINIO_SECURE=true`)
   - Configure proper access policies
   - Use IAM roles for production

2. **Performance**
   - Consider dedicated MinIO nodes
   - Enable erasure coding for redundancy
   - Configure appropriate cache TTLs
   - Monitor storage metrics

3. **Backup**
   - Regular backup of MinIO data directory
   - Consider MinIO mirror/replication
   - Test restore procedures

4. **Scaling**
   - MinIO supports distributed mode
   - Can scale horizontally with multiple nodes
   - Load balance across MinIO instances

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check MinIO container is running: `docker ps | grep minio`
   - Verify environment variables are set
   - Check Docker network connectivity

2. **Permission Denied**
   - Verify user has appropriate storage permissions
   - Check bucket policies in MinIO console
   - Ensure authentication is working

3. **Bucket Not Found**
   - Default bucket is created automatically
   - Check `MINIO_DEFAULT_BUCKET` environment variable
   - Manually create bucket if needed

### Debug Commands

```bash
# Check MinIO health
curl http://localhost:9000/minio/health/live

# View MinIO logs
docker logs computor-minio

# Test MinIO connectivity from API container
docker exec -it computor-fullstack-celery-system-worker-1 \
  curl http://minio:9000/minio/health/live
```

## Future Enhancements

1. **Lifecycle Policies** - Automatic expiration of temporary files
2. **Versioning** - Track file versions for assignments
3. **Encryption** - Server-side encryption for sensitive data
4. **CDN Integration** - CloudFront or similar for global distribution
5. **Quota Management** - Per-user or per-course storage limits