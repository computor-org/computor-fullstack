# Docker Task Workers Setup

This document describes the Docker configuration for running task workers alongside the FastAPI application.

## Overview

The task executor framework uses Redis Queue (RQ) workers that run as separate Docker containers. This provides:

- **Horizontal Scaling**: Multiple worker instances can run concurrently
- **Priority Queues**: Separate workers for high-priority and default/low-priority tasks
- **Fault Tolerance**: Workers can restart independently of the main application
- **Resource Isolation**: Workers consume resources only when processing tasks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Redis         │    │   PostgreSQL    │
│   (uvicorn)     │◄──►│   (Queue)       │    │   (Database)    │
│   Port 8000     │    │   Port 6379     │    │   Port 5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        ▲                        ▲
         │                        │                        │
         ▼                        │                        │
┌─────────────────┐              │                        │
│   Task Worker   │              │                        │
│   High Priority │◄─────────────┼────────────────────────┘
│                 │              │
└─────────────────┘              │
                                 │
┌─────────────────┐              │
│   Task Worker   │              │
│   Default/Low   │◄─────────────┘
│   Priority      │
└─────────────────┘
```

## Services Configuration

### Development Environment (docker-compose-dev.yaml)

```yaml
services:
  # FastAPI Backend
  uvicorn:
    build: ./docker/api/Dockerfile
    ports: ["8000:8000"]
    command: ["uvicorn", "server:app", "--reload"]
    
  # High Priority Task Worker
  task-worker-high:
    build: ./docker/task-worker/Dockerfile
    environment:
      TASK_QUEUES: high_priority
      
  # Default/Low Priority Task Worker  
  task-worker-default:
    build: ./docker/task-worker/Dockerfile
    environment:
      TASK_QUEUES: default,low_priority
```

### Production Environment (docker-compose-prod.yaml)

```yaml
services:
  # High Priority Task Workers (1 replica)
  task-worker-high:
    deploy:
      replicas: ${TASK_WORKER_HIGH_REPLICAS:-1}
    environment:
      TASK_QUEUES: high_priority
      
  # Default Priority Task Workers (2 replicas)
  task-worker-default:
    deploy:
      replicas: ${TASK_WORKER_DEFAULT_REPLICAS:-2}
    environment:
      TASK_QUEUES: default,low_priority
```

## Environment Variables

### Required Variables

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=your_redis_password

# API Configuration
EXECUTION_BACKEND_API_URL=http://uvicorn:8000
EXECUTION_BACKEND_API_USER=admin
EXECUTION_BACKEND_API_PASSWORD=your_api_password

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_URL=postgresql://user:pass@postgres:5432/db
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_database

# Application Configuration
DEBUG_MODE=production
TOKEN_SECRET=your_token_secret
API_LOCAL_STORAGE_DIR=/app/storage
```

### Optional Variables (Production)

```bash
# Worker Scaling
TASK_WORKER_HIGH_REPLICAS=1      # High priority workers
TASK_WORKER_DEFAULT_REPLICAS=2   # Default/low priority workers

# Storage Configuration
SYSTEM_DEPLOYMENT_PATH=/data
API_ROOT_PATH=/app
```

## Task Queue Configuration

### Queue Priority Levels

1. **High Priority** (`high_priority`)
   - Student test submissions
   - Critical system operations
   - Time-sensitive tasks
   - **Workers**: 1 dedicated worker

2. **Default Priority** (`default`)
   - Regular course operations
   - Content generation
   - Data processing
   - **Workers**: 2 shared workers

3. **Low Priority** (`low_priority`)
   - Background maintenance
   - Analytics processing
   - Non-urgent operations
   - **Workers**: Shared with default priority

### Worker Assignment

- **task-worker-high**: Processes only `high_priority` queue
- **task-worker-default**: Processes `default` and `low_priority` queues

This ensures high-priority tasks always have dedicated processing capacity.

## Docker Image Details

### Base Image
- **prefecthq/prefect:2.20.3-python3.10**: Provides Python 3.10 + async support

### Task Worker Dockerfile Features
- **Non-root user**: Security with `taskworker` user
- **Health checks**: Redis connectivity monitoring
- **Startup script**: Automatic service discovery and initialization
- **Volume mounts**: Source code and storage directories

### Startup Process

1. **Wait for Redis**: Ensures queue backend is available
2. **Wait for API**: Ensures FastAPI backend is ready
3. **Import tasks**: Registers all available task types
4. **Start worker**: Begins processing queued tasks

## Usage Commands

### Start All Services (Development)
```bash
docker-compose -f docker-compose-dev.yaml up -d
```

### Start All Services (Production)
```bash
docker-compose -f docker-compose-prod.yaml up -d
```

### Scale Workers (Production)
```bash
# Scale high priority workers to 2
TASK_WORKER_HIGH_REPLICAS=2 docker-compose -f docker-compose-prod.yaml up -d

# Scale default workers to 4  
TASK_WORKER_DEFAULT_REPLICAS=4 docker-compose -f docker-compose-prod.yaml up -d
```

### Monitor Worker Logs
```bash
# All task workers
docker-compose logs -f task-worker-high task-worker-default

# Specific worker
docker-compose logs -f task-worker-high
```

### Check Worker Status
```bash
# Connect to API container
docker-compose exec uvicorn bash

# Check queue status
python -m ctutor_backend.cli.cli worker status
```

## Health Monitoring

### Service Health Checks

1. **Redis Connectivity**: Workers ping Redis every 30 seconds
2. **API Availability**: Startup script waits for API readiness
3. **Task Registration**: Verifies all task types are loaded

### Monitoring Commands

```bash
# Check worker container health
docker-compose ps

# View worker startup logs
docker-compose logs task-worker-high

# Monitor Redis queue depth
docker-compose exec redis redis-cli llen rq:queue:high_priority
docker-compose exec redis redis-cli llen rq:queue:default
docker-compose exec redis redis-cli llen rq:queue:low_priority
```

## Troubleshooting

### Common Issues

**Workers not starting**
- Check Redis connectivity: `docker-compose logs redis`
- Verify environment variables are set
- Check worker startup logs: `docker-compose logs task-worker-high`

**Tasks not being processed**
- Verify workers are running: `docker-compose ps`
- Check queue status via API: `GET /tasks/types`
- Monitor Redis queues: `redis-cli llen rq:queue:default`

**High memory usage**
- Monitor worker resource usage: `docker stats`
- Consider reducing worker replicas
- Check for memory leaks in task implementations

### Debug Commands

```bash
# Enter worker container
docker-compose exec task-worker-high bash

# Check task registration
python -c "from ctutor_backend.tasks import task_registry; print(task_registry.list_tasks())"

# Test Redis connection
python -c "import redis; r=redis.Redis.from_url('$REDIS_URL', password='$REDIS_PASSWORD'); print(r.ping())"

# Submit test task
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{"task_name": "example_long_running", "parameters": {"duration": 5}}'
```

## Scaling Guidelines

### Development
- **1 high priority worker**: Sufficient for testing
- **1 default worker**: Handles background tasks

### Production
- **1-2 high priority workers**: Based on concurrent student submissions
- **2-4 default workers**: Based on general workload
- **Monitor queue depth**: Scale up if queues consistently have >10 waiting jobs

### Performance Tuning
- **CPU-bound tasks**: Increase worker replicas
- **I/O-bound tasks**: Consider increasing workers per container
- **Memory-intensive tasks**: Monitor container memory limits
- **Network latency**: Ensure workers are co-located with database/Redis

## Security Considerations

- **Non-root containers**: Workers run as `taskworker` user
- **Network isolation**: Workers communicate only with Redis, API, and database
- **Secret management**: Use Docker secrets for sensitive environment variables
- **Resource limits**: Set memory and CPU limits in production
- **Health monitoring**: Enable container health checks and monitoring alerts