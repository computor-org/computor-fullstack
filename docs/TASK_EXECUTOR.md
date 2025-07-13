# Task Executor Framework

The Task Executor framework provides a Redis Queue (RQ) based solution for handling long-running operations that exceed FastAPI's request-response cycle.

## Overview

### Problem Statement
FastAPI handles all operations within the request-response cycle, which causes issues for:
- Student test execution and grading workflows (30+ seconds)
- Repository mirroring and GitLab operations (60+ seconds)
- Course content generation and processing
- Bulk data operations

### Solution
A task executor system using Redis Queue that provides:
- Asynchronous task execution outside the request-response cycle
- Task status tracking and progress monitoring
- Retry mechanisms and error handling
- Priority-based queue management
- FastAPI integration for task submission and monitoring

## Architecture

### Components

1. **Task Executor (`TaskExecutor`)**: Core service managing Redis queues and job execution
2. **Base Task (`BaseTask`)**: Abstract base class for all task implementations
3. **Task Registry**: Discovery system for registering and managing task types
4. **FastAPI Endpoints**: RESTful API for task submission and monitoring
5. **CLI Worker**: Command-line interface for starting worker processes

### Infrastructure Requirements

- **Redis**: Required for queue management and job persistence
- **Python 3.10+**: For async/await support and type hints
- **RQ 2.0**: Redis Queue library for job management

## Quick Start

### 1. Install Dependencies

The task executor framework requires RQ, which is already added to `requirements.txt`:

```bash
pip install -r src/requirements.txt
```

### 2. Start a Worker

Start a worker process to handle queued tasks:

```bash
# Start worker with all queues
ctutor worker start

# Start worker in burst mode (exit after processing all jobs)
ctutor worker start --burst

# Start worker with specific queues
ctutor worker start --queues=high_priority,default
```

### 3. Submit a Task

Use the FastAPI endpoints to submit tasks:

```bash
# Submit a task
curl -X POST "http://localhost:8000/tasks/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "example_long_running",
    "parameters": {"duration": 60, "message": "Processing data..."},
    "priority": 5
  }'

# Check task status
curl "http://localhost:8000/tasks/{task_id}/status"

# Get task result
curl "http://localhost:8000/tasks/{task_id}/result"
```

## Creating Custom Tasks

### 1. Define Task Class

Create a task by inheriting from `BaseTask`:

```python
from ctutor_backend.tasks import BaseTask, register_task

@register_task
class MyCustomTask(BaseTask):
    @property
    def name(self) -> str:
        return "my_custom_task"
    
    @property
    def timeout(self) -> int:
        return 600  # 10 minutes
    
    @property
    def retry_limit(self) -> int:
        return 3
    
    async def execute(self, param1: str, param2: int = 100) -> dict:
        # Your task logic here
        await asyncio.sleep(5)  # Simulate work
        
        return {
            "result": f"Processed {param1} with value {param2}",
            "completed_at": datetime.utcnow().isoformat()
        }
    
    async def on_success(self, result: Any, **kwargs) -> None:
        print(f"Task completed: {result}")
    
    async def on_failure(self, error: Exception, **kwargs) -> None:
        print(f"Task failed: {str(error)}")
```

### 2. Register Task

Tasks are automatically registered when decorated with `@register_task`. Alternatively:

```python
from ctutor_backend.tasks import task_registry

task_registry.register(MyCustomTask)
```

### 3. Submit Task

```python
from ctutor_backend.tasks import get_task_executor, TaskSubmission

executor = get_task_executor()
submission = TaskSubmission(
    task_name="my_custom_task",
    parameters={"param1": "hello", "param2": 200},
    priority=5
)

task_id = await executor.submit_task(submission)
```

## API Reference

### Task Submission

**POST** `/tasks/submit`

Submit a task for asynchronous execution.

**Request Body:**
```json
{
  "task_name": "string",
  "parameters": {},
  "priority": 0,
  "delay": null
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "submitted",
  "message": "Task submitted successfully"
}
```

### Task Status

**GET** `/tasks/{task_id}/status`

Get task execution status and information.

**Response:**
```json
{
  "task_id": "string",
  "task_name": "string",
  "status": "queued|started|finished|failed|deferred|cancelled",
  "created_at": "2024-01-01T00:00:00Z",
  "started_at": "2024-01-01T00:00:30Z",
  "finished_at": "2024-01-01T00:01:00Z",
  "progress": {},
  "error": null
}
```

### Task Result

**GET** `/tasks/{task_id}/result`

Get task execution result.

**Response:**
```json
{
  "task_id": "string",
  "status": "finished",
  "result": {},
  "error": null,
  "created_at": "2024-01-01T00:00:00Z",
  "started_at": "2024-01-01T00:00:30Z",
  "finished_at": "2024-01-01T00:01:00Z",
  "progress": {}
}
```

### Cancel Task

**DELETE** `/tasks/{task_id}/cancel`

Cancel a queued or running task.

**Response:**
```json
{
  "task_id": "string",
  "status": "cancelled",
  "message": "Task cancelled successfully"
}
```

### List Task Types

**GET** `/tasks/types`

Get list of available task types.

**Response:**
```json
[
  "example_long_running",
  "example_data_processing",
  "student_test_execution"
]
```

## Task Priority and Queues

The framework uses three priority queues:

- **High Priority** (`priority > 5`): Critical operations, processed first
- **Default** (`0 <= priority <= 5`): Normal operations
- **Low Priority** (`priority < 0`): Background operations, processed last

Workers process queues in order: High Priority → Default → Low Priority

## Error Handling and Retries

### Automatic Retries

Tasks can specify retry behavior:

```python
@property
def retry_limit(self) -> int:
    return 3  # Retry up to 3 times
```

### Error Handling

Tasks should handle errors gracefully:

```python
async def execute(self, **kwargs) -> dict:
    try:
        # Task logic
        return {"status": "success"}
    except ValidationError as e:
        # Don't retry validation errors
        raise
    except TemporaryError as e:
        # Retry temporary errors
        raise
```

### Custom Error Results

For controlled failures:

```python
async def execute(self, **kwargs) -> dict:
    if invalid_input:
        return {
            "status": "failed",
            "error": "Invalid input provided",
            "error_code": "VALIDATION_ERROR"
        }
```

## Monitoring and Observability

### Worker Status

Check worker and queue status:

```bash
ctutor worker status
```

### Redis Queue Monitoring

Connect to Redis to inspect queues:

```bash
redis-cli
> LLEN rq:queue:default
> LLEN rq:queue:high_priority
> LLEN rq:queue:low_priority
```

### Task Metrics

Monitor task execution through:
- Task completion rates
- Average execution times
- Error rates by task type
- Queue depth over time

## Production Deployment

### Environment Configuration

Set required environment variables:

```bash
export REDIS_URL="redis://localhost:6379"
export REDIS_PASSWORD="your_redis_password"
export EXECUTION_BACKEND_API_URL="http://localhost:8000"
export EXECUTION_BACKEND_API_USER="admin"
export EXECUTION_BACKEND_API_PASSWORD="password"
```

### Worker Deployment

Deploy workers as separate processes or containers:

```bash
# Production worker (runs continuously)
ctutor worker start

# Using Docker
docker run -d --name task-worker \
  -e REDIS_URL="redis://redis:6379" \
  computor-backend:latest \
  ctutor worker start
```

### Scaling Workers

Scale horizontally by running multiple worker processes:

```bash
# Run multiple workers
for i in {1..3}; do
  nohup ctutor worker start &
done
```

### Health Checks

Monitor worker health:

```bash
# Check if workers are processing jobs
ctutor worker status

# Monitor Redis connection
redis-cli ping
```

## Migration from Prefect

### Student Test Execution

The framework includes a `StudentTestExecutionTask` that replaces Prefect flows:

```python
# Old Prefect flow submission
from ctutor_backend.flows.utils import student_test_flow

# New task executor submission
from ctutor_backend.tasks import get_task_executor, TaskSubmission

submission = TaskSubmission(
    task_name="student_test_execution",
    parameters={
        "test_job_data": test_job.dict(),
        "execution_backend_callable": "docker_execution"
    },
    priority=7  # High priority for student tests
)

task_id = await get_task_executor().submit_task(submission)
```

### Migration Benefits

1. **Better Integration**: Native FastAPI integration vs external Prefect server
2. **Simpler Deployment**: No separate Prefect server required
3. **Immediate Feedback**: Task IDs returned immediately for tracking
4. **Consistent Infrastructure**: Uses existing Redis instance
5. **Fine-grained Control**: Per-task retry and timeout configuration

## Best Practices

### Task Design

1. **Idempotent Tasks**: Tasks should be safe to retry
2. **Parameter Validation**: Validate inputs early
3. **Progress Reporting**: Update task progress for long operations
4. **Resource Cleanup**: Always clean up temporary resources
5. **Error Context**: Provide meaningful error messages

### Performance

1. **Batch Operations**: Group small operations into batches
2. **Resource Limits**: Set appropriate timeouts and memory limits
3. **Queue Management**: Use appropriate priority levels
4. **Worker Scaling**: Scale workers based on queue depth

### Security

1. **Input Sanitization**: Validate and sanitize all task parameters
2. **Resource Limits**: Prevent resource exhaustion attacks
3. **Access Control**: Secure task submission endpoints
4. **Audit Logging**: Log task submissions and results

## Troubleshooting

### Common Issues

**Task Stuck in Queue**
- Check if workers are running: `ctutor worker status`
- Verify Redis connection
- Check worker logs for errors

**Task Fails Immediately**
- Verify task is registered: `GET /tasks/types`
- Check parameter validation
- Review task implementation

**High Memory Usage**
- Implement resource cleanup in tasks
- Set appropriate worker memory limits
- Monitor task result sizes

**Redis Connection Issues**
- Verify Redis server is running
- Check connection credentials
- Test network connectivity

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Task Inspection

Inspect failed tasks:

```python
from rq import Job
from ctutor_backend.tasks import get_task_executor

executor = get_task_executor()
job = Job.fetch(task_id, connection=executor.redis_client)
print(f"Status: {job.status}")
print(f"Exception: {job.exc_info}")
print(f"Result: {job.result}")
```

## Future Enhancements

- **Progress Tracking**: Real-time progress updates via WebSocket
- **Task Scheduling**: Cron-like scheduling for recurring tasks
- **Result Storage**: Persistent result storage beyond Redis TTL
- **Distributed Workers**: Multi-node worker deployment
- **Monitoring Dashboard**: Web-based monitoring interface
- **Workflow Engine**: Chaining tasks into complex workflows