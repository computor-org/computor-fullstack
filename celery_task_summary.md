# Celery Task Executor Summary

## Overview

The `src/ctutor_backend/tasks/` directory contains a comprehensive Celery-based task execution framework for handling long-running operations in the Computor platform. This framework was recently migrated from Redis Queue (RQ) to Celery for better scalability and production readiness.

## Directory Structure

```
src/ctutor_backend/tasks/
├── __init__.py          # Module exports
├── celery_app.py        # Celery application configuration
├── base.py              # Base classes (BaseTask, TaskStatus, TaskResult)
├── executor.py          # TaskExecutor class for task management
├── registry.py          # Task registry for managing implementations
├── examples.py          # Example task implementations
└── student_testing.py   # Real-world task for student test execution
```

## Simple Example: How to Use Celery

### Important Note on Architecture
The `_execute_task_with_celery` utility function is a core utility that bridges Celery's synchronous execution model with the async BaseTask interface. This function is properly located in `executor.py` as it's a fundamental part of the task execution framework.

### 1. Create a Task Function

To create a Celery task, you need to:
1. Create a class that inherits from `BaseTask`
2. Register it with the `@register_task` decorator
3. Create a Celery wrapper function

```python
# my_tasks.py
from ctutor_backend.tasks import BaseTask, register_task, app
from typing import Dict, Any
import asyncio

@register_task
class MySimpleTask(BaseTask):
    @property
    def name(self) -> str:
        return "my_simple_task"
    
    @property
    def timeout(self) -> int:
        return 300  # 5 minutes
    
    async def execute(self, message: str, count: int = 1) -> Dict[str, Any]:
        # Your task logic here
        results = []
        for i in range(count):
            await asyncio.sleep(1)  # Simulate work
            results.append(f"{message} - iteration {i+1}")
        
        return {
            "status": "completed",
            "results": results,
            "total_iterations": count
        }

# Celery wrapper - this is what gets registered with Celery
@app.task(bind=True, name='ctutor_backend.tasks.my_simple_task')
def my_simple_task_celery(self, **kwargs):
    """Celery wrapper for MySimpleTask."""
    from ctutor_backend.tasks.executor import _execute_task_with_celery
    return _execute_task_with_celery(self, MySimpleTask, **kwargs)
```

### 2. Task Registration

Tasks are automatically registered when:
- The class uses the `@register_task` decorator
- The Celery wrapper function is defined with `@app.task`

The registration happens in two places:
- **TaskRegistry**: Manages the BaseTask classes
- **Celery**: Manages the actual task execution

### 3. Start a Task on a Worker

There are three ways to start a task:

#### Method 1: Using Python Code
```python
from ctutor_backend.tasks import get_task_executor, TaskSubmission

async def start_my_task():
    executor = get_task_executor()
    
    # Submit the task
    submission = TaskSubmission(
        task_name="my_simple_task",
        parameters={
            "message": "Hello Celery",
            "count": 5
        },
        priority=5  # 0-10, higher = more important
    )
    
    task_id = await executor.submit_task(submission)
    print(f"Task submitted with ID: {task_id}")
    return task_id
```

#### Method 2: Using REST API
```bash
# Submit a task via HTTP POST
curl -X POST http://localhost:8000/api/tasks/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_name": "my_simple_task",
    "parameters": {
      "message": "Hello from API",
      "count": 3
    },
    "priority": 7
  }'
```

#### Method 3: Direct Celery Call (Low-level)
```python
# Not recommended, but possible
from ctutor_backend.tasks.celery_app import app

result = app.send_task(
    'ctutor_backend.tasks.my_simple_task',
    kwargs={"message": "Direct call", "count": 2},
    queue='default',
    priority=5
)
task_id = result.id
```

### 4. Get the Result

#### Using Python Code:
```python
async def get_task_result(task_id: str):
    executor = get_task_executor()
    
    # Check status
    status = await executor.get_task_status(task_id)
    print(f"Status: {status.status}")
    print(f"Progress: {status.progress}%")
    
    # Wait for completion and get result
    if status.status == "SUCCESS":
        result = await executor.get_task_result(task_id)
        print(f"Result: {result.result}")
        return result.result
    elif status.status == "FAILURE":
        print(f"Task failed: {status.error}")
    else:
        print("Task still running...")
```

#### Using REST API:
```bash
# Get task status
curl http://localhost:8000/api/tasks/{task_id}/status

# Get task result (blocks until complete)
curl http://localhost:8000/api/tasks/{task_id}/result
```

## Starting Workers

### Development
```bash
# Start a worker (after activating venv)
ctutor worker start

# Start with specific queues
ctutor worker start --queues=high_priority,default

# Start in burst mode (process existing tasks and exit)
ctutor worker start --burst
```

### Docker Compose Setup

The project includes two Docker Compose files in the root directory with complete Celery infrastructure:

#### Development (`docker-compose-dev.yaml`)
```bash
# Start all services including Celery system worker and Flower
docker-compose -f docker-compose-dev.yaml up -d

# Services included:
# - celery-system-worker: Handles all system tasks (concurrency=4)
# - flower: Web UI for monitoring at http://localhost:5555
# - redis: Message broker on port 6379
# - postgres: Database on port 5432
# - Plus: traefik, nginx, prefect services
```

#### Production (`docker-compose-prod.yaml`)
```bash
# Start all services with configurable replicas
docker-compose -f docker-compose-prod.yaml up -d

# Scale system workers using environment variable:
# CELERY_SYSTEM_WORKER_REPLICAS=1 (default)

# Example: Scale system workers to 3 instances
CELERY_SYSTEM_WORKER_REPLICAS=3 docker-compose -f docker-compose-prod.yaml up -d

# Production features:
# - Automatic scaling with replica configuration
# - Health checks for dependencies
# - Traefik integration for Flower UI at /flower path
# - Shared volumes for task execution
```

### Worker Configuration Details

Both Docker Compose files configure:

1. **System Worker** (`celery-system-worker`):
   - Queues: `high_priority`, `default`, `low_priority`
   - Concurrency: 4 workers
   - Use case: System-dependent tasks like releases, filesystem operations, and background tasks

3. **Flower Monitoring** (`flower`):
   - Port: 5555 (development) or via Traefik at `/flower` (production)
   - Basic Auth: Configured via `FLOWER_USER` and `FLOWER_PASSWORD`
   - Real-time monitoring of tasks and workers

### Monitoring with Flower
```bash
# Development - Direct access
http://localhost:5555

# Production - Via Traefik
http://your-domain/flower

# Default credentials (configurable via environment variables):
# Username: admin (FLOWER_USER)
# Password: flower123 (FLOWER_PASSWORD)

# To customize, add to your .env file:
# FLOWER_USER=your-username
# FLOWER_PASSWORD=your-secure-password

# Using test script helper
./test_celery_docker.sh ui  # Shows Flower UI access info
```

## Priority Queues

The system uses three priority queues:
- `high_priority` (priority 10): For critical tasks like student testing
- `default` (priority 5): For general tasks
- `low_priority` (priority 1): For background operations

## Complete Working Example

Here's a minimal complete example:

```python
# example_task.py
from ctutor_backend.tasks import BaseTask, register_task, app, get_task_executor, TaskSubmission
from ctutor_backend.tasks.executor import _execute_task_with_celery
import asyncio

# Step 1: Define the task
@register_task
class CalculateFactorialTask(BaseTask):
    @property
    def name(self) -> str:
        return "calculate_factorial"
    
    @property
    def timeout(self) -> int:
        return 60
    
    async def execute(self, number: int) -> dict:
        factorial = 1
        for i in range(1, number + 1):
            factorial *= i
            await asyncio.sleep(0.1)  # Simulate work
        
        return {
            "number": number,
            "factorial": factorial
        }

# Step 2: Create Celery wrapper
@app.task(bind=True, name='ctutor_backend.tasks.calculate_factorial')
def calculate_factorial_celery(self, **kwargs):
    from ctutor_backend.tasks.executor import _execute_task_with_celery
    return _execute_task_with_celery(self, CalculateFactorialTask, **kwargs)

# Step 3: Submit and get result
async def main():
    executor = get_task_executor()
    
    # Submit task
    submission = TaskSubmission(
        task_name="calculate_factorial",
        parameters={"number": 10}
    )
    task_id = await executor.submit_task(submission)
    
    # Wait and get result
    result = await executor.get_task_result(task_id)
    print(f"10! = {result.result['factorial']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Hybrid Storage Architecture

The framework uses a **hybrid approach** for optimal performance and persistence:

**Redis (Message Broker):**
```bash
REDIS_HOST=localhost          # Redis server hostname
REDIS_PORT=6379              # Redis server port (default: 6379)
REDIS_PASSWORD=redis_password # Redis authentication password (optional)
```

**PostgreSQL (Result Backend):**
```bash
POSTGRES_HOST=localhost       # PostgreSQL server hostname
POSTGRES_PORT=5432           # PostgreSQL server port (default: 5432)
POSTGRES_USER=postgres       # PostgreSQL username
POSTGRES_PASSWORD=postgres_secret # PostgreSQL password
POSTGRES_DB=codeability      # PostgreSQL database name
```

### Why This Hybrid Approach?

**Redis for Message Broker:**
- ⚡ **High Performance**: Sub-millisecond message delivery
- 🔄 **Real-time**: Instant task queue processing
- 📊 **Low Latency**: Optimal for task distribution

**PostgreSQL for Task Results:**
- 💾 **Permanent Storage**: Task results survive system restarts
- 🔍 **Rich Queries**: Advanced filtering and analytics
- 📈 **Scalability**: Production-grade persistence
- 🔒 **ACID Compliance**: Data integrity guarantees
- 📊 **Reporting**: Join task data with business data

This provides the **best of both worlds**: Redis speed for task queuing + PostgreSQL reliability for results.

### Flower UI Configuration
Flower monitoring is configured via environment variables with built-in defaults:

```bash
# Optional Flower Configuration (add to .env if customization needed)
FLOWER_USER=admin             # Default: admin
FLOWER_PASSWORD=flower123     # Default: flower123
```

Configuration is handled automatically by Docker Compose with fallback values, eliminating the need for separate configuration files.

## Key Features

1. **Async Support**: Tasks can use async/await
2. **Priority Scheduling**: Tasks can have different priorities
3. **Progress Tracking**: Tasks can update their progress
4. **Error Handling**: Built-in retry and failure callbacks
5. **Monitoring**: Real-time monitoring with Flower UI
6. **Horizontal Scaling**: Multiple workers can process tasks in parallel
7. **Result Storage**: Results stored in Redis with configurable TTL
8. **Clean Configuration**: Structured Redis configuration with host/port separation

## Task Persistence & Recovery

### Enhanced Persistence Capabilities ✅

The framework provides **production-grade** task persistence through PostgreSQL:

**Task Results & History:**
- Task results stored **permanently** in PostgreSQL database
- Complete task history with execution metadata
- Full state tracking (PENDING → STARTED → SUCCESS/FAILURE)
- Error messages, timing, and worker information preserved
- **Advanced querying**: Filter, sort, and analyze task data with SQL

**Data Persistence:**
- **PostgreSQL backend**: ACID-compliant permanent storage
- **Database tables**: Structured schema with proper indexing
- **Backup-friendly**: Standard database backup/restore procedures
- **Survives everything**: System reboots, container restarts, Redis failures

**Message Broker:**
- **Redis**: High-performance task queuing and distribution
- **Persistent queues**: Tasks survive worker restarts
- **Volume mounting**: `${SYSTEM_DEPLOYMENT_PATH}/redis-data:/data`

**Celery Configuration:**
- `task_acks_late=True` - prevents task loss during worker crashes
- `task_track_started=True` - records all state changes
- `database_short_lived_sessions=True` - optimized DB connections

### Recovery Behavior After Shutdown ⚠️

**What Survives:**
- ✅ **All completed tasks**: Permanent storage in PostgreSQL (no expiration)
- ✅ **Queued tasks**: Will be processed when workers restart
- ✅ **Complete task history**: All execution metadata and error details
- ✅ **Database integrity**: ACID compliance ensures data consistency

**What's Lost:**
- ❌ **Running tasks**: Tasks being executed during shutdown (but can be retried)
- ❌ **Worker state**: Workers need manual restart (but task queue persists)

**Recovery Steps:**
```bash
# 1. Restart Redis (if needed)
docker-compose -f docker-compose-dev.yaml up -d redis

# 2. Start workers
ctutor worker start

# 3. Check task status
curl http://localhost:8000/api/tasks/{task_id}/status
```

### Recommendations for Enhanced Persistence

For mission-critical deployments, consider:

**1. Database Backend** (optional):
```python
# Use PostgreSQL instead of Redis for results
CELERY_RESULT_BACKEND = 'db+postgresql://user:pass@localhost/celery'
```

**2. Monitoring & Alerts:**
- Set up Flower UI alerts for failed tasks
- Monitor Redis persistence and backup
- Configure worker auto-restart with systemd

**3. Task Retry Strategies:**
```python
# Add retry configuration to critical tasks
@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def critical_task(self, data):
    # Task implementation
```

## Testing

The framework includes comprehensive tests in `test_task_executor.py` covering:
- Task submission and execution
- Error handling and retries
- Worker status monitoring
- Docker integration
- API endpoints

Run tests with:
```bash
pytest src/ctutor_backend/tests/test_task_executor.py -v
```