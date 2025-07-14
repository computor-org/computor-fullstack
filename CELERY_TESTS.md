# Celery-Based Test Execution System

This document describes the new Celery-based test execution system that replaces Prefect flows for student testing and submission processing.

## Overview

The new system provides the same functionality as the original Prefect-based implementation but uses Celery tasks for better performance, reliability, and integration with the unified task executor framework.

## Key Components

### 1. API Endpoints

#### `/tests-celery` - Main test execution endpoint
- **Method**: POST
- **Purpose**: Submit student tests for execution using Celery tasks
- **Payload**: Same as original `/tests` endpoint (TestCreate)
- **Response**: TestRunResponse with task IDs

#### `/tests-celery/health` - Health check
- **Method**: GET  
- **Purpose**: Check Celery worker status and system health
- **Response**: Worker count, broker status, backend type

### 2. Celery Tasks

#### `student_testing` Task
- **Purpose**: Execute complete student testing workflow
- **Features**:
  - Repository cloning (student + reference)
  - Test execution in isolated environment
  - Result collection and scoring
  - Progress tracking with detailed stages
  - 30-minute timeout for complex tests

#### `submission_processing` Task  
- **Purpose**: Process student submissions
- **Features**:
  - Git operations and branch management
  - GitLab merge request creation
  - Submission validation
  - 10-minute timeout for submission processing

### 3. Execution Backend Configuration

To use the Celery-based system, update your execution backend configuration:

```yaml
# In your execution backend properties
type: "celery"  # Instead of "prefect"
properties:
  # Celery-specific configuration if needed
  # Falls back to Prefect if type is "prefect"
```

## Usage Examples

### 1. Submit a Test via API

```bash
# Submit test using Celery backend
curl -X POST http://localhost:8000/api/tests-celery \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "directory": "assignment1",
    "version_identifier": "abc123def",
    "submit": false
  }'
```

### 2. Check System Health

```bash
# Check Celery worker status
curl http://localhost:8000/api/tests-celery/health \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected response:
{
  "status": "healthy",
  "backend": "celery", 
  "workers": 1,
  "broker_status": "connected"
}
```

### 3. Monitor Task Progress

The system stores task progress in PostgreSQL (`celery_taskmeta` table):

```sql
-- Check recent test tasks
SELECT task_id, status, date_done, result 
FROM celery_taskmeta 
WHERE name = 'ctutor_backend.tasks.student_testing'
ORDER BY date_done DESC 
LIMIT 10;

-- Get specific task result
SELECT result 
FROM celery_taskmeta 
WHERE task_id = 'your-task-id';
```

## Task Workflow

### Student Testing Workflow

1. **Initialization** (10% progress)
   - Parse test job configuration
   - Setup temporary working directory

2. **Repository Cloning** (20% progress)
   - Clone student repository
   - Clone reference repository  
   - Checkout specific commits

3. **Environment Setup** (40% progress)
   - Prepare test environment
   - Install dependencies if needed

4. **Test Execution** (50-70% progress)
   - Run Python test scripts (if available)
   - Execute default comparison tests
   - Validate results

5. **Result Processing** (80% progress)
   - Calculate scores and grades
   - Generate detailed reports
   - Format final results

6. **Completion** (100% progress)
   - Store results in database
   - Update task status
   - Return formatted response

### Submission Processing Workflow

1. **Setup** (20% progress)
   - Parse submission configuration
   - Prepare Git operations

2. **Processing** (50-80% progress)
   - Execute submission workflow
   - Create Git branches
   - Handle merge requests

3. **Completion** (100% progress)
   - Update submission status
   - Store processing results

## Error Handling

The system provides comprehensive error handling:

- **Repository errors**: Failed cloning, missing commits
- **Test execution errors**: Script failures, timeouts
- **System errors**: Worker unavailability, database issues

All errors are captured with detailed messages and stored in task results.

## Performance Benefits

### Compared to Prefect

1. **Better Integration**: Uses the same Celery infrastructure as other system tasks
2. **Unified Monitoring**: Single Flower UI for all task types
3. **Persistent Storage**: PostgreSQL backend for reliable task history
4. **Simplified Deployment**: No separate Prefect server required
5. **Resource Efficiency**: Shared worker processes for all task types

### Monitoring

- **Flower UI**: http://localhost:5555 (development)
- **Database**: Direct SQL queries on `celery_taskmeta`
- **Health Endpoint**: Real-time worker status
- **Progress Tracking**: Detailed stage information

## Migration Guide

### From Prefect to Celery

1. **Update Execution Backend**:
   ```sql
   UPDATE execution_backends 
   SET type = 'celery' 
   WHERE type = 'prefect';
   ```

2. **Use New Endpoint**:
   - Change API calls from `/tests` to `/tests-celery`
   - Same request/response format

3. **Monitor Tasks**:
   - Use Flower UI instead of Prefect UI
   - Query PostgreSQL instead of Prefect database

### Gradual Migration

The system supports both backends simultaneously:
- Prefect tasks: Use `/tests` endpoint  
- Celery tasks: Use `/tests-celery` endpoint
- Backend type determined by execution_backend.type

## Development and Testing

### Running Tests

```bash
# Test the new Celery endpoint
python src/cli.py worker test-job --task=student_testing --wait

# Check worker status
python src/cli.py worker status
```

### Adding Custom Test Logic

Extend `StudentTestingTask._execute_tests()` method in `student_testing_advanced.py`:

```python
async def _execute_tests(self, student_path, reference_path, job_config, backend_properties):
    # Add your custom testing logic here
    # Return test results dictionary
    pass
```

## Configuration

### Environment Variables

The system uses the same configuration as the main Celery setup:

```bash
# Redis (message broker)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

# PostgreSQL (result backend)  
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=codeability
```

### Worker Configuration

Tasks run on the unified `celery-system-worker` with appropriate queue routing:

- **student_testing**: `high_priority` queue (priority 8)
- **submission_processing**: `default` queue (priority 6)

## Future Enhancements

1. **Advanced Test Runners**: Support for multiple programming languages
2. **Parallel Execution**: Run multiple test cases simultaneously  
3. **Resource Limits**: CPU/memory constraints for student code
4. **Custom Environments**: Docker containers for isolated execution
5. **Real-time Streaming**: Live test output streaming to frontend

## Troubleshooting

### Common Issues

1. **Worker Not Available**:
   - Check `celery-system-worker` is running
   - Verify Redis connection
   - Check worker logs

2. **Task Timeout**:
   - Increase timeout in task configuration
   - Check for infinite loops in student code
   - Monitor resource usage

3. **Repository Clone Failures**:
   - Verify GitLab token permissions
   - Check network connectivity
   - Validate repository URLs

### Debug Commands

```bash
# Check worker logs
docker logs computor-fullstack-celery-system-worker-1

# Test task submission
python src/cli.py worker test-job --task=student_testing

# Monitor task queue
curl http://localhost:8000/api/tasks/workers/status
```