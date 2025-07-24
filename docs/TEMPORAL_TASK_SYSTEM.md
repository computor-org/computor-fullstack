# Temporal Task System Documentation

## Overview

The Computor platform uses Temporal.io as its workflow orchestration engine for handling long-running operations that exceed FastAPI's request-response cycle. This system replaced the previous Celery implementation to provide better workflow management, reliability, and monitoring capabilities.

## Quick Start (Development Mode)

### 1. Start Temporal Services
```bash
# From project root
docker-compose -f docker-compose-dev.yaml up -d temporal-postgres temporal temporal-ui
```

### 2. Start the Worker

#### Option A: Using Docker (Recommended)
```bash
# Worker starts automatically with other services
docker-compose -f docker-compose-dev.yaml up -d temporal-worker
```

#### Option B: Manual startup (for development)
```bash
# In a new terminal
cd src
python -m ctutor_backend.tasks.temporal_worker
```

### 3. Access Temporal UI
Open http://localhost:8088 in your browser

### 4. Submit a Test Task

#### Using curl (no auth required in dev mode)
```bash
# Submit a 30-second test task
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "example_long_running",
    "parameters": {"duration": 30, "message": "Hello Temporal!"},
    "queue": "computor-tasks"
  }'
```

#### Using the test script
```bash
python scripts/test_temporal_tasks.py
```

### 5. Monitor in Temporal UI
- Go to http://localhost:8088
- Click on "Workflows" to see your running task
- Click on the workflow ID to see execution details

## Architecture

### Core Components

1. **Temporal Server**: Workflow orchestration engine with PostgreSQL backend
2. **Temporal UI**: Web-based monitoring interface at http://localhost:8088
3. **Temporal Workers**: Process workflows and activities from task queues
4. **FastAPI Integration**: RESTful API for task submission and monitoring
5. **Task Registry**: Dynamic workflow discovery and registration system

### System Flow

```
Client → FastAPI → Temporal Client → Temporal Server → Worker → Workflow/Activity
                                           ↓
                                     PostgreSQL (State)
```

## Task Queue System

### Queue Architecture

The system uses string-based queue names with workflows able to define their own queues:

- **Default Queue**: `computor-tasks` - General purpose tasks
- **High Priority**: `computor-high-priority` - Critical operations
- **Custom Queues**: Workflows can define custom queues (e.g., `computor-long-running`)

### Dynamic Queue Selection

Workflows implement the `get_task_queue()` method to specify their queue:

```python
@workflow.defn(name="example_long_running")
class ExampleLongRunningWorkflow(BaseWorkflow):
    @classmethod
    def get_task_queue(cls) -> str:
        return "computor-long-running"  # Custom queue
```

## Creating Workflows

### Basic Workflow Structure

```python
from temporalio import workflow, activity
from .temporal_base import BaseWorkflow, WorkflowResult

@register_task
@workflow.defn(name="my_workflow", sandboxed=False)
class MyWorkflow(BaseWorkflow):
    @classmethod
    def get_name(cls) -> str:
        return "my_workflow"
    
    @classmethod
    def get_task_queue(cls) -> str:
        return "computor-tasks"  # Or custom queue
    
    @workflow.run
    async def run(self, parameters: dict) -> WorkflowResult:
        # Workflow logic here
        result = await workflow.execute_activity(
            my_activity,
            args=[parameters],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return WorkflowResult(
            status="completed",
            result=result,
            metadata={"workflow_type": "custom"}
        )
```

### Activity Definition

```python
@activity.defn(name="my_activity")
async def my_activity(parameters: dict) -> dict:
    # Activity logic here
    return {"result": "success"}
```

## API Endpoints

### Task Management

- `POST /tasks/submit` - Submit a new workflow
  ```json
  {
    "task_name": "example_long_running",
    "parameters": {"duration": 60, "message": "Processing..."},
    "queue": "computor-tasks"
  }
  ```

- `GET /tasks/{task_id}` - Get workflow status
- `GET /tasks/{task_id}/result` - Get workflow result
- `GET /tasks/{task_id}/status` - Get detailed status information
- `DELETE /tasks/{task_id}` - Returns 501 (Not Implemented) - Temporal doesn't support deletion
- `GET /tasks/types` - List available workflow types
- `GET /tasks/workers/status` - Check worker status

### System Endpoints

- `POST /release/students` - Release students with GitLab integration
- `POST /release/courses` - Release course structure
- `POST /hierarchy/organizations/create` - Create organization (async)
- `POST /hierarchy/course-families/create` - Create course family (async)
- `POST /hierarchy/courses/create` - Create course (async)

## Worker Management

### CLI Commands

```bash
# Start worker with default queue
ctutor worker start

# Start worker with specific queues
ctutor worker start --queues=computor-tasks,computor-high-priority

# Check worker status
ctutor worker status

# Submit test job
ctutor worker test-job example_long_running --params='{"duration": 10}' --wait
```

### Docker Deployment

Workers run as Docker containers with configurable replicas:

```yaml
# docker-compose-dev.yaml / docker-compose-prod.yaml
temporal-worker:
  image: ghcr.io/ls1intum/computor/api:latest
  command: python -m ctutor_backend.tasks.temporal_worker
  deploy:
    replicas: ${TEMPORAL_WORKER_REPLICAS:-1}
  environment:
    - TEMPORAL_HOST=temporal
    - TEMPORAL_PORT=7233
```

## Configuration

### Environment Variables

```bash
# Temporal Configuration
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
TEMPORAL_NAMESPACE=default

# Worker Scaling
TEMPORAL_WORKER_REPLICAS=2  # Number of worker instances

# API Configuration
EXECUTION_BACKEND_API_URL=http://uvicorn:8000
EXECUTION_BACKEND_API_USER=admin
EXECUTION_BACKEND_API_PASSWORD=your_password
```

### Workflow Types

Currently implemented workflows:

1. **Example Workflows**
   - `example_long_running` - Simulates long-running work
     ```json
     {
       "task_name": "example_long_running",
       "parameters": {
         "duration": 60,
         "message": "Processing..."
       }
     }
     ```
   
   - `example_data_processing` - Processes data in chunks
     ```json
     {
       "task_name": "example_data_processing", 
       "parameters": {
         "data_size": 1000,
         "chunk_size": 10,
         "operation": "sum"
       }
     }
     ```
   
   - `example_error_handling` - Demonstrates error handling
     ```json
     {
       "task_name": "example_error_handling",
       "parameters": {
         "should_fail": true,
         "retry_count": 2,
         "fail_at_step": 1
       }
     }
     ```

2. **Student Testing**
   - `student_testing` - Execute student tests
   - `submission_processing` - Process Git submissions

3. **System Management**
   - `release_students` - GitLab student release
   - `release_course` - Course structure release

4. **Hierarchy Management**
   - `create_organization` - Create organization with GitLab
   - `create_course_family` - Create course family
   - `create_course` - Create course

## Frontend Integration

### Task List Display

The React frontend at `/admin/tasks` displays:

- **Task ID**: Short form (last 12 chars) for readability
- **Status**: Color-coded status indicators
- **Completed At**: Proper timestamp field
- **Duration**: Human-readable format (e.g., "5m 30s")
- **Result Available**: Yes/No indicator
- **Actions**: View details, delete (returns 501)

### Status Mapping

Backend statuses are mapped for display:

```typescript
const getStatusColor = (status: string) => {
  const upperStatus = status.toUpperCase();
  switch (upperStatus) {
    case 'SUCCESS':
    case 'FINISHED':
      return 'success';
    case 'PENDING':
    case 'QUEUED':
      return 'warning';
    case 'FAILED':
      return 'error';
    // ... etc
  }
}
```

## Monitoring

### Temporal UI

Access the Temporal Web UI at http://localhost:8088 for:

- Workflow execution history
- Real-time workflow status
- Worker health monitoring
- Namespace management
- Search and filtering capabilities

### Health Checks

Check system health via API:

```bash
# Worker status
curl -u admin:admin http://localhost:8000/tasks/workers/status

# Temporal connection
ctutor worker status
```

## Best Practices

### Workflow Design

1. **Idempotency**: Design workflows to be safely retryable
2. **Timeouts**: Set appropriate activity timeouts
3. **Error Handling**: Use retry policies and handle failures gracefully
4. **Progress Tracking**: Update workflow state for monitoring
5. **Resource Cleanup**: Ensure temporary resources are cleaned up

### Queue Management

1. **Queue Selection**: Choose appropriate queue based on priority
2. **Custom Queues**: Create dedicated queues for specialized workflows
3. **Worker Allocation**: Scale workers based on queue depth
4. **Monitoring**: Watch queue metrics in Temporal UI

### Security

1. **Input Validation**: Validate all workflow parameters
2. **Authentication**: All API endpoints require authentication
3. **Resource Limits**: Set appropriate timeouts and retries
4. **Secrets Management**: Use environment variables for sensitive data

## Migration from Celery

### Key Differences

1. **Workflow vs Tasks**: Temporal uses workflows with activities instead of simple tasks
2. **State Management**: Temporal handles state persistence automatically
3. **Queue System**: String-based queue names instead of numeric priorities
4. **Deletion**: Temporal doesn't support workflow deletion (use retention policies)
5. **UI**: Temporal UI instead of Flower

### Benefits

1. **Better Reliability**: Built-in retry and error handling
2. **Workflow Orchestration**: Complex multi-step workflows
3. **State Management**: Automatic persistence and recovery
4. **Monitoring**: Rich UI with execution history
5. **Scalability**: Better horizontal scaling capabilities

## Troubleshooting

### Common Issues

1. **Worker Not Starting**
   - Check Temporal server is running: `docker ps | grep temporal`
   - Verify environment variables
   - Check Docker logs: `docker-compose logs temporal-worker`

2. **Workflow Timeout**
   - Increase workflow/activity timeouts
   - Check for blocking operations
   - Monitor resource usage

3. **Queue Not Found**
   - Ensure worker is listening on the queue
   - Check workflow's `get_task_queue()` method
   - Verify queue name in task submission

### Debug Commands

```bash
# View worker logs
docker-compose logs -f temporal-worker

# Check Temporal server
docker-compose logs temporal

# Test workflow submission
ctutor worker test-job example_long_running --params='{"duration": 5}' --wait

# Direct workflow inspection (if temporal CLI available)
temporal workflow describe --workflow-id <workflow-id>
```

## Stopping Services

```bash
# Stop all Temporal services including worker
docker-compose -f docker-compose-dev.yaml down temporal-worker temporal temporal-postgres temporal-ui

# Or stop individual services
docker-compose -f docker-compose-dev.yaml stop temporal-worker
```

## Tips and Best Practices

1. **Worker logs** show real-time activity - useful for debugging
2. **Temporal UI** auto-refreshes every 15 seconds
3. **Failed workflows** show detailed error information in the UI
4. **Workflows persist** even if worker restarts - ensuring reliability
5. **Use appropriate timeouts** - Set realistic timeouts for activities
6. **Monitor queue depth** - Scale workers based on workload

## Useful URLs

- **API Documentation**: http://localhost:8000/docs
- **Temporal UI**: http://localhost:8088
- **Task Management UI**: http://localhost:3000/admin/tasks

## Future Enhancements

1. **Advanced Workflows**: Multi-language test execution support
2. **Saga Patterns**: Distributed transaction support
3. **Event Sourcing**: Activity event streaming
4. **Custom Metrics**: Prometheus integration
5. **WebSocket Updates**: Real-time workflow status updates