# Temporal Task System Usage Guide

This guide shows how to start tasks and observe them using the Temporal UI, similar to the previous Celery functionality.

## Prerequisites

1. **Start Temporal Services** (if not already running):
```bash
# Development mode
docker-compose -f docker-compose-dev.yaml up -d temporal-postgres temporal temporal-ui

# Or all services
bash startup.sh
```

2. **Start the Temporal Worker**:

#### Docker (Recommended):
```bash
# Worker starts automatically with services
docker-compose -f docker-compose-dev.yaml up -d temporal-worker

# View worker logs
docker logs -f temporal-worker
```

#### Manual (for development):
```bash
cd src
python -m ctutor_backend.tasks.temporal_worker
```

The worker will display:
```
Starting Temporal worker...
Registered workflows: ['example_long_running', 'example_data_processing', ...]
Worker running on queues: ['computor-tasks', 'computor-high-priority', 'computor-low-priority']
Worker started. Press Ctrl+C to stop.
```

## Using the Tasks API

### 1. Submit a Task

Submit tasks via the `/tasks/submit` endpoint:

```bash
# Example: Submit a long-running task
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_name": "example_long_running",
    "parameters": {
      "duration": 30,
      "message": "Testing Temporal task"
    },
    "priority": 0
  }'
```

Response:
```json
{
  "task_id": "example_long_running-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "submitted",
  "message": "Task 'example_long_running' submitted successfully"
}
```

### 2. Check Task Status

```bash
# Get task status
curl http://localhost:8000/tasks/{task_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "task_id": "example_long_running-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "task_name": "example_long_running",
  "status": "STARTED",
  "created_at": "2025-01-24T10:30:00Z",
  "started_at": "2025-01-24T10:30:01Z",
  "finished_at": null,
  "error": null,
  "worker": "computor-tasks",
  "queue": "computor-tasks"
}
```

### 3. Get Task Result

```bash
# Get task result (once completed)
curl http://localhost:8000/tasks/{task_id}/result \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. List Available Task Types

```bash
# See all available task types
curl http://localhost:8000/tasks/types \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
[
  "example_long_running",
  "example_data_processing",
  "example_error_handling",
  "student_testing",
  "submission_processing",
  "release_students",
  "release_course",
  "create_organization",
  "create_course_family",
  "create_course"
]
```

## Monitoring in Temporal UI

1. **Access Temporal Web UI**: http://localhost:8088

2. **View Running Workflows**:
   - Click on "Workflows" in the navigation
   - You'll see all submitted tasks with their status
   - Click on any workflow to see detailed execution history

3. **Key UI Features**:
   - **Workflow List**: Shows all workflows with status, start time, and duration
   - **Workflow Details**: Click on a workflow to see:
     - Input parameters
     - Execution history
     - Activity details
     - Error messages (if any)
   - **Task Queues**: View pending tasks in each queue
   - **Search**: Search workflows by ID, type, or status

## Example Task Submissions

### 1. Long Running Task
```bash
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_name": "example_long_running",
    "parameters": {
      "duration": 60,
      "message": "Processing data for 60 seconds"
    },
    "priority": 0
  }'
```

### 2. Data Processing Task
```bash
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_name": "example_data_processing",
    "parameters": {
      "data_size": 1000,
      "processing_type": "transform"
    },
    "priority": 5
  }'
```

### 3. High Priority Task
```bash
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_name": "example_long_running",
    "parameters": {
      "duration": 10,
      "message": "Urgent task"
    },
    "priority": 10
  }'
```

## Task Priority Mapping

- **Priority > 5**: Routes to `computor-high-priority` queue
- **Priority 0-5**: Routes to `computor-tasks` (default) queue  
- **Priority < 0**: Routes to `computor-low-priority` queue

## Development Tips

1. **Watch Worker Logs**: The worker terminal shows real-time activity
2. **Use Temporal UI**: Much more powerful than Celery Flower for debugging
3. **Workflow History**: Temporal keeps full execution history for debugging
4. **Retry Behavior**: Failed tasks automatically retry based on the retry policy

## Differences from Celery

1. **Workflow IDs**: Instead of Celery task IDs, you get Temporal workflow IDs
2. **Better UI**: Temporal UI provides more detailed execution history
3. **Durable Execution**: Workflows can survive worker restarts
4. **Built-in Retries**: Automatic retry handling with configurable policies

## Production Deployment

For production deployments, the `docker-compose-prod.yaml` includes:

1. **Primary Worker**: Handles all queues
   ```bash
   docker-compose -f docker-compose-prod.yaml up -d temporal-worker
   ```

2. **Scaled High-Priority Workers**: 2 replicas focusing on high-priority tasks
   ```bash
   docker-compose -f docker-compose-prod.yaml up -d temporal-worker-scaled
   ```

3. **Monitor Worker Health**:
   ```bash
   # Check worker status
   docker ps | grep temporal-worker
   
   # View worker logs
   docker logs temporal-worker
   docker logs temporal-worker-scaled
   ```

## Troubleshooting

1. **Worker Not Processing Tasks**:
   - Check worker is running: `docker ps | grep temporal-worker`
   - Verify Temporal connection in worker logs: `docker logs temporal-worker`
   - Check Docker containers are running

2. **Tasks Not Appearing in UI**:
   - Verify correct Temporal namespace
   - Check API response for workflow ID
   - Ensure worker is listening on the correct queue

3. **Authentication Issues**:
   - Ensure valid JWT token in Authorization header
   - Check API logs for auth errors

4. **Docker Worker Issues**:
   - Restart worker: `docker-compose restart temporal-worker`
   - Check environment variables in docker-compose files
   - Verify Temporal server connectivity