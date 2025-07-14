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
# Start all services including Celery workers and Flower
docker-compose -f docker-compose-dev.yaml up -d

# Services included:
# - celery-worker-high: Handles high_priority queue (concurrency=2)
# - celery-worker-default: Handles default and low_priority queues (concurrency=3)
# - flower: Web UI for monitoring at http://localhost:5555
# - redis: Message broker on port 6379
# - postgres: Database on port 5432
# - Plus: traefik, nginx, prefect services
```

#### Production (`docker-compose-prod.yaml`)
```bash
# Start all services with configurable replicas
docker-compose -f docker-compose-prod.yaml up -d

# Scale workers using environment variables:
# TASK_WORKER_HIGH_REPLICAS=1 (default)
# TASK_WORKER_DEFAULT_REPLICAS=2 (default)

# Example: Scale high priority workers to 3 instances
TASK_WORKER_HIGH_REPLICAS=3 docker-compose -f docker-compose-prod.yaml up -d

# Production features:
# - Automatic scaling with replica configuration
# - Health checks for dependencies
# - Traefik integration for Flower UI at /flower path
# - Shared volumes for task execution
```

### Worker Configuration Details

Both Docker Compose files configure:

1. **High Priority Worker** (`celery-worker-high`):
   - Queues: `high_priority` only
   - Concurrency: 2 workers
   - Use case: Critical tasks like student test execution

2. **Default Worker** (`celery-worker-default`):
   - Queues: `default`, `low_priority`
   - Concurrency: 3 workers
   - Use case: General tasks and background operations

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

### Redis Configuration
The framework uses a clean Redis configuration approach with separate environment variables:

```bash
# Environment Variables
REDIS_HOST=localhost          # Redis server hostname
REDIS_PORT=6379              # Redis server port (default: 6379)
REDIS_PASSWORD=redis_password # Redis authentication password (optional)
```

The system automatically builds Redis URLs from these components:
- With password: `redis://:{password}@{host}:{port}`
- Without password: `redis://{host}:{port}`

This approach provides:
- **Clear separation** of connection parameters
- **Docker compatibility** with service names (e.g., `REDIS_HOST=redis`)
- **Consistent URL building** across all modules
- **Environment-specific configuration** for dev/staging/production

## Key Features

1. **Async Support**: Tasks can use async/await
2. **Priority Scheduling**: Tasks can have different priorities
3. **Progress Tracking**: Tasks can update their progress
4. **Error Handling**: Built-in retry and failure callbacks
5. **Monitoring**: Real-time monitoring with Flower UI
6. **Horizontal Scaling**: Multiple workers can process tasks in parallel
7. **Result Storage**: Results stored in Redis with configurable TTL
8. **Clean Configuration**: Structured Redis configuration with host/port separation

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