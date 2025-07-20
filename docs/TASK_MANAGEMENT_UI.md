# Task Management UI Documentation

## Overview

This document describes the Task Management UI implementation for the Computor platform, which provides a web interface for monitoring and managing Celery tasks. The UI allows users to view task lists, check task details, submit new tasks, and monitor task execution status.

## Features

### Task List Page (`/tasks`)

The main task list page displays all tasks stored in the PostgreSQL `celery_taskmeta` table with the following features:

- **Real-time Updates**: Auto-refresh capability (every 5 seconds) to monitor task progress
- **Filtering**: Filter tasks by status (PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED)
- **Pagination**: Configurable rows per page (5, 10, 25, 50) with server-side pagination
- **Task Submission**: "New Task" button to create and submit tasks with parameters

#### Table Columns

The table displays the following columns from the database:

| Column | Description | Source Field |
|--------|-------------|--------------|
| Task ID | Unique task identifier | `task_id` |
| Task Name | Name of the task type | `name` |
| Status | Current task status | `status` |
| Queue | Queue the task was submitted to | `queue` |
| Worker | Worker that processed the task | `worker` |
| Completed At | Task completion timestamp | `date_done` |
| Retries | Number of retry attempts | `retries` |
| Result | Indicates if task has result/error | `has_result`/`has_error` |
| Actions | View details button | - |

### Task Detail Page (`/tasks/:taskId`)

Detailed view of individual tasks showing:

- **Basic Information**: Task ID, name, status with visual indicators
- **Timestamps**: Created, started, finished times with duration calculation
- **Execution Details**: Queue, worker hostname, retry count
- **Task Parameters**: Display of args and kwargs passed to the task
- **Progress Information**: Real-time progress updates (if available)
- **Results**: Task execution results in JSON format
- **Error Details**: Error messages and tracebacks for failed tasks

### Task Submission Dialog

Modal dialog for creating new tasks with:

- **Task Type Selection**: Dropdown of available task types
- **Dynamic Parameters**: Form fields based on selected task type
- **Priority Setting**: Slider to set task priority (0-10)
- **Parameter Validation**: Type-specific validation for task parameters

## Implementation Details

### Frontend Components

#### Tasks.tsx
Main task list component with:
- Material-UI table with sorting and pagination
- Status filtering dropdown
- Auto-refresh toggle
- Task creation dialog

#### TaskDetail.tsx
Task detail view component with:
- Structured display of all task metadata
- Real-time status updates
- JSON formatting for complex data

### Backend Integration

#### API Endpoints

All endpoints require authentication (Basic or Bearer token).

```
GET /tasks
  Query params: limit, offset, status
  Returns: List of tasks with pagination info

GET /tasks/{task_id}
  Returns: Detailed task information

GET /tasks/{task_id}/result
  Returns: Task execution result

POST /tasks/submit
  Body: { task_name, parameters, priority }
  Returns: { task_id, status, message }

DELETE /tasks/{task_id}/cancel
  Returns: Cancellation status
```

#### Database Queries

Tasks are queried directly from the PostgreSQL `celery_taskmeta` table:

```sql
SELECT task_id, status, result, date_done, traceback, 
       name, args, kwargs, worker, retries, queue
FROM celery_taskmeta
ORDER BY date_done DESC NULLS LAST
```

### Data Handling

#### Binary Data
The system handles PostgreSQL binary data (`bytea`) fields:
- Attempts UTF-8 decoding first
- Falls back to latin-1 for non-UTF-8 data
- Indicates binary data that cannot be decoded

#### Status Mapping
Celery statuses are mapped to user-friendly values:
- PENDING → queued
- STARTED → started
- SUCCESS → finished
- FAILURE → failed
- RETRY → queued
- REVOKED → cancelled

## Known Limitations

### Metadata Storage

Due to Celery's PostgreSQL backend design, certain fields may not be populated:

1. **Task Name (`name`)**: Only populated when workers execute the task
2. **Queue**: Only recorded when a worker picks up the task
3. **Worker**: Only set during actual task execution

This is because:
- The database backend is optimized for result storage, not full task tracking
- Metadata is only complete after worker processing
- Tasks in PENDING state have minimal information

### Workarounds

For complete task metadata, consider:
1. Using Celery Events for real-time monitoring
2. Implementing custom task base classes
3. Using Redis for metadata with PostgreSQL for results
4. Accepting the limitation as a trade-off for reliable result storage

## Configuration

### Environment Variables

The system uses existing database configuration:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
POSTGRES_DB=codeability
```

### Task Types

Currently supported task types:

```javascript
const taskTemplates = {
  example_long_running: {
    name: 'Long Running Task',
    description: 'Simulates a long-running operation',
    parameters: {
      duration: { type: 'number', default: 60, label: 'Duration (seconds)' },
      message: { type: 'string', default: 'Processing...', label: 'Status Message' },
    },
  },
  // Add more task types as needed
};
```

## Future Enhancements

1. **Task Cancellation**: Implement UI for cancelling running tasks
2. **Bulk Operations**: Select and operate on multiple tasks
3. **Advanced Filtering**: Filter by date range, worker, queue
4. **Task Templates**: Save and reuse common task configurations
5. **Metrics Dashboard**: Aggregate statistics on task performance
6. **WebSocket Updates**: Real-time updates without polling

## Security Considerations

- All API endpoints require authentication
- Task parameters are validated on submission
- Binary data is safely handled to prevent injection
- Result data is escaped when displayed

## Testing

To test the task management system:

1. Ensure Celery workers are running:
   ```bash
   docker-compose -f docker-compose-dev.yaml up -d
   ```

2. Submit a test task:
   ```bash
   curl -X POST "http://localhost:8000/tasks/submit" \
     -H "Authorization: Basic YWRtaW46YWRtaW4=" \
     -H "Content-Type: application/json" \
     -d '{
       "task_name": "example_long_running",
       "parameters": {"duration": 10, "message": "Test"},
       "priority": 5
     }'
   ```

3. View task list in UI: http://localhost:3000/tasks

4. Monitor task execution in real-time