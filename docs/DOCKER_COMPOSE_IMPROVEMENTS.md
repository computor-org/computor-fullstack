# Docker Compose Improvements Documentation

## Current State Analysis

### Overview
The Computor project currently has two Docker Compose configurations:
- **docker-compose-dev.yaml**: Development environment
- **docker-compose-prod.yaml**: Production environment

With corresponding environment files:
- **.env.dev**: Development environment variables
- **.env.prod**: Production environment variables
- **.env**: Copy of one of the above depending on the mode

### Current Services

#### Active Services

1. **Traefik** (Reverse Proxy)
   - Port: 8080:80
   - Routes all services through a single port
   - Current routes:
     - `/api` → uvicorn (prod only)
     - `/docs` → nginx (prod only, commented in dev)
     - `/minio` → MinIO API
     - `/minio-console` → MinIO Console
     - `/auth` → Keycloak (dev only, commented)

2. **PostgreSQL** (Main Database)
   - Dev: Port 5432:5437 (internal 5437)
   - Prod: Port 5432:${POSTGRES_PORT}
   - Volume: `${SYSTEM_DEPLOYMENT_PATH}/postgres`

3. **Redis** (Cache & Message Broker)
   - Port: ${REDIS_PORT}:6379
   - Used for: Session management, caching, Celery message broker
   - Password protected

4. **Celery Workers**
   - **celery-system-worker**: Handles all system tasks
   - Processes all queues: high_priority, default, low_priority
   - Concurrency: 4
   - Replicas in prod: ${CELERY_SYSTEM_WORKER_REPLICAS:-1}

5. **MinIO** (Object Storage)
   - Ports: 9000 (API), 9001 (Console)
   - S3-compatible storage
   - Default bucket: computor-storage

6. **uvicorn** (API Server - Prod only)
   - Port: 8000
   - FastAPI application
   - In dev mode, started via `bash api.sh`

#### Commented/Deprecated Services

1. **Prefect** (Workflow Orchestration) - TO BE REMOVED
   - Service: prefect + prefect_db
   - Database: PostgreSQL 15.2
   - Port: 4200
   - Status: Commented in dev, active in prod

2. **nginx** (Static File Server)
   - Port: 8081:80
   - Serves: `${SYSTEM_DEPLOYMENT_PATH}/execution-backend/shared/documents`
   - Status: Commented in dev, active in prod
   - Redundant with Traefik

3. **Keycloak** (SSO Provider - Dev only)
   - Service: keycloak + keycloak-db
   - Port: 8180:8080
   - Database: Dedicated PostgreSQL on port 5438
   - Status: Commented in both configs

4. **backup** (Backup Service)
   - Alpine-based cron backup
   - Status: Commented, possibly deprecated

5. **system-agent** (Prefect Worker)
   - Based on Prefect image
   - To be migrated to Celery

6. **python-agent** (Prefect Worker)
   - For Python test execution
   - Status: Commented
   - To be migrated to Celery

## Prefect Usage Analysis

### Current Prefect Flows
Based on code analysis, Prefect is used for:

1. **Student Test Execution** (`flows/utils.py`)
   - `student_test_flow`: Executes student code tests
   - Git cloning of reference and student repositories
   - Test execution with meta.yaml configuration
   - Result submission to the API
   - Uses flow_run.get_id() for tracking

2. **System Operations** (`docker/system-agent/flows.py`)
   - `release_student_flow`: Creates student projects in GitLab
   - `release_course_flow`: Releases course content to GitLab
   - `submit_result_flow`: Submits test results
   - Uses Prefect deployments and work queues

### Migration Requirements
- Replace `@flow` and `@task` decorators with Celery tasks
- Replace flow_run.get_id() with Celery task IDs
- Migrate work queue system to Celery queues
- Update CLI commands that track flow runs
- Maintain async/await support where needed

## Issues Identified

### 1. Environment Variables
- **Redundancy**: Three env files (.env, .env.dev, .env.prod)
- **Inconsistencies**:
  - Different paths: `/tmp/computor` (dev) vs `/tmp/codeability` (prod)
  - Different Redis hosts: `localhost` (dev) vs `172.17.0.1` (prod)
  - Missing MinIO config in .env.prod
  - Prefect variables still present despite migration to Celery

### 2. Service Architecture
- **Prefect remnants**: Still configured but should be removed
- **nginx redundancy**: Both nginx and Traefik serve as reverse proxies
- **Agent architecture**: system-agent and python-agent need Celery migration
- **Unused files**: `init-keycloak-schema.sql` not referenced

### 3. Docker Directory Structure
- Mixed Dockerfile naming (Dockerfile vs dockerfile)
- Prefect directory still exists
- Backup service unclear status
- Note: docker/postgres/init-keycloak-schema.sql requires root permissions to remove

### 4. Security Concerns
- Admin interfaces need authentication
- All services exposed through single port (good) but some lack authentication

## Proposed Improvements

### 1. Environment Variable Consolidation

#### Structure
```
.env.common      # Shared variables
.env.dev         # Dev-specific overrides
.env.prod        # Prod-specific overrides
.env             # Symlink or generated file
```

#### Key Changes
- Remove Prefect-related variables
- Standardize paths and hostnames
- Add missing MinIO config to prod
- Consolidate Redis configuration

### 2. Service Cleanup

#### Remove
- Prefect and prefect_db services
- Prefect-related environment variables
- docker/prefect directory

#### Replace nginx with Traefik
- Configure Traefik to serve static files directly
- Remove nginx service and docker/nginx directory
- Update routing rules

#### Migrate Agents to Celery
- Create unified celery-worker image
- Support different worker types via environment variables:
  - WORKER_TYPE: system, python, matlab
  - WORKER_QUEUES: Specific queue configuration
- Remove system-agent and python-agent directories

### 3. Improved Worker Architecture

```yaml
celery-worker:
  build:
    context: ./
    dockerfile: ./docker/celery-worker/Dockerfile
  environment:
    WORKER_TYPE: ${WORKER_TYPE:-system}
    WORKER_QUEUES: ${WORKER_QUEUES:-high_priority,default,low_priority}
    WORKER_CONCURRENCY: ${WORKER_CONCURRENCY:-4}
```

### 4. Authentication for Internal Services

#### Traefik Middleware Options
1. **Basic Auth**: Simple but effective for internal tools
2. **Forward Auth**: Integrate with Keycloak/SSO
3. **IP Whitelisting**: For production environments

### 5. Docker Directory Cleanup

```
docker/
├── api/           # FastAPI/uvicorn service
├── celery-worker/ # Unified worker image
├── postgres/      # Remove unused init-keycloak-schema.sql
└── traefik/       # Traefik configuration
```

### 6. Development vs Production Separation

#### Development
- Keycloak enabled for SSO testing
- Hot reload for API (via bash api.sh)
- All services accessible locally
- Debug logging enabled

#### Production
- External auth provider support
- uvicorn in container
- Scaled workers
- Production logging
- Backup service (if needed)

## Implementation Summary

### Completed Changes

#### ✅ Phase 1: Environment Cleanup
- Created `.env.common` for shared variables
- Updated `.env.dev` and `.env.prod` with mode-specific values
- Removed all Prefect-related variables
- Added `setup_env.sh` utility script
- Standardized Redis and PostgreSQL configurations
- Fixed database connection by updating database.py to use POSTGRES_HOST and POSTGRES_PORT directly

#### ✅ Phase 2: Prefect Removal
- Removed prefect and prefect_db services from docker-compose files
- Deleted Docker directories: prefect, system-agent, python-agent
- Cleaned up Prefect environment variables

#### ✅ Phase 3: Celery Migration
- Created `tasks/system.py` with Celery tasks for:
  - `release_student_task`: Student project creation
  - `release_course_task`: Course content releases
  - `submit_result_task`: Test result submission
- Updated API endpoints to use Celery instead of Prefect
- Migrated status endpoint to use Celery AsyncResult
- Removed Prefect from requirements.txt
- Deleted flows directory

#### ✅ Phase 4: Unified Worker Architecture
- Created `docker/celery-worker/Dockerfile`
- Supports worker types via `WORKER_TYPE` environment variable
- Configurable queues, concurrency, and log levels
- Example configuration for Python test workers

#### ✅ Phase 5: nginx Removal
- Replaced nginx with `halverneus/static-file-server`
- Configured Traefik routing for static files at `/docs`
- Removed nginx Docker directory
- Marked backup service as deprecated

## Migration Plan

### Phase 1: Environment Cleanup
1. Create consolidated env structure
2. Remove Prefect variables
3. Standardize service configurations

### Phase 2: Prefect Removal
1. Remove Prefect services from docker-compose
2. Delete Prefect-related Docker files
3. Update documentation

### Phase 3: Worker Migration
1. Create unified celery-worker Dockerfile
2. Implement worker type configuration
3. Test system and python execution workers

### Phase 4: nginx/Traefik Consolidation
1. Configure Traefik for static file serving
2. Migrate nginx routes to Traefik
3. Remove nginx service

### Phase 5: Authentication
1. Implement Traefik auth middleware
2. Secure admin interfaces
3. Document access patterns

## Benefits

1. **Simplified Architecture**: Fewer services, clearer responsibilities
2. **Better Maintainability**: Consistent naming, structure
3. **Improved Security**: Centralized authentication
4. **Reduced Redundancy**: Single reverse proxy, unified workers
5. **Easier Deployment**: Cleaner environment management

## Results

### Simplified Architecture
- **Services Reduced**: From 10+ services to 8 core services
- **Single Reverse Proxy**: Traefik handles all routing
- **Unified Workers**: One Dockerfile for all worker types
- **Clean Environment**: Organized environment variables

### Key Improvements
1. **Better Maintainability**: Consistent service patterns
2. **Improved Security**: Centralized routing and authentication
3. **Reduced Complexity**: Fewer moving parts
4. **Enhanced Scalability**: Easy worker scaling with Celery
5. **Modern Stack**: Replaced legacy Prefect with production-ready Celery

### Usage

#### Development Setup
```bash
# Set up environment
./scripts/utilities/setup_env.sh dev

# Start services
docker-compose -f docker-compose-dev.yaml up -d

# Check status
docker-compose -f docker-compose-dev.yaml ps

# Access services
# - MinIO Console: http://localhost:9001 (direct access)
# - MinIO API: http://localhost:9000 (direct access)
# - Keycloak: http://localhost:8180 (direct access, dev only)
# - PostgreSQL: localhost:5432 (maps to internal port 5437)
# - Redis: localhost:6379
```

#### Important Configuration Notes
- Database connection: Uses POSTGRES_HOST and POSTGRES_PORT directly (not POSTGRES_URL)
- Docker services communicate using service names (e.g., `postgres`, `redis`)
- Workers run inside Docker and connect to services via Docker network
- All services use proper authentication (passwords in .env files)

#### Production Setup
```bash
# Set up environment
./scripts/utilities/setup_env.sh prod

# Start services with scaling
docker-compose -f docker-compose-prod.yaml up -d --scale celery-system-worker=3

# Check worker status
docker-compose -f docker-compose-prod.yaml logs celery-system-worker
```

### Service URLs (via Traefik on port 8080)
- `/api` - FastAPI application
- `/docs` - Static file server
- `/minio` - MinIO API
- `/minio-console` - MinIO Console
- `/auth` - Keycloak (dev only)