# Temporal Workflows Documentation

## Overview

Temporal.io provides the asynchronous task orchestration backbone for Computor, handling all long-running operations, GitLab integrations, and complex multi-step processes.

## Architecture

### Components

1. **Temporal Server** - Workflow state persistence and orchestration
2. **Worker Processes** - Execute workflow and activity code
3. **Client** - Submits workflows from API endpoints
4. **UI** - Monitoring and debugging interface (http://localhost:8088)

### File Structure
```
src/ctutor_backend/tasks/
├── temporal_base.py               # Base workflow classes
├── temporal_client.py             # Client configuration
├── temporal_worker.py             # Worker implementation
├── temporal_executor.py           # Task execution interface
├── temporal_hierarchy_management.py    # Organization/Course workflows
├── temporal_student_template_v2.py     # Student template generation
├── temporal_examples.py           # Example deployment workflows
├── temporal_student_testing.py    # Submission testing workflows
└── temporal_system.py            # System maintenance workflows
```

## Key Workflows

### 1. Hierarchy Management Workflow

**File**: `temporal_hierarchy_management.py`

**Purpose**: Creates and manages the GitLab group hierarchy for organizations, course families, and courses.

**Workflow Steps**:
1. Create organization GitLab group
2. Create course family subgroup
3. Create course subgroup
4. Create students subgroup
5. Initialize course repositories

**Activities**:
- `create_gitlab_group` - Creates GitLab groups
- `create_course_projects` - Creates assignment/reference repos
- `setup_students_group` - Configures student access

**Usage**:
```python
from temporal_hierarchy_management import HierarchyManagementWorkflow

# Triggered when creating a course through API
workflow_id = await temporal_client.execute_workflow(
    HierarchyManagementWorkflow.run,
    args={
        "organization_id": org_id,
        "course_family_id": family_id,
        "course_id": course_id
    },
    task_queue="computor-tasks"
)
```

### 2. Student Template Workflow

**File**: `temporal_student_template_v2.py`

**Purpose**: Generates and maintains student template repositories with course-specific content.

**Workflow Steps**:
1. Clone or create template repository
2. Generate directory structure
3. Add README and documentation
4. Create meta.yaml for CodeAbility
5. Push to GitLab
6. Configure CI/CD pipelines

**Key Features**:
- Flat directory structure for assignments
- Automatic meta.yaml generation
- GitLab CI integration
- Content versioning

**Usage**:
```python
from temporal_student_template_v2 import StudentTemplateWorkflow

workflow_id = await temporal_client.execute_workflow(
    StudentTemplateWorkflow.run,
    args={
        "course_id": course_id,
        "template_config": config
    },
    task_queue="computor-tasks"
)
```

### 3. Example Deployment Workflow

**File**: `temporal_examples.py`

**Purpose**: Deploys example solutions and reference implementations.

**Workflow Steps**:
1. Validate example content
2. Create/update repository
3. Deploy to appropriate branch
4. Update visibility settings
5. Notify instructors

**Activities**:
- `validate_example` - Content validation
- `deploy_to_repo` - Git operations
- `update_permissions` - Access control

### 4. Student Testing Workflow

**File**: `temporal_student_testing.py`

**Purpose**: Automated testing of student submissions.

**Workflow Steps**:
1. Clone student repository
2. Run test suites
3. Generate reports
4. Update grades
5. Send feedback

**Test Types**:
- Unit tests
- Integration tests
- Code quality checks
- Plagiarism detection

## Workflow Patterns

### Retry Policies

```python
retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=5
)
```

### Error Handling

```python
@activity.defn
async def risky_activity():
    try:
        # Activity logic
        pass
    except GitLabException as e:
        # Non-retryable error
        raise ApplicationError("GitLab unavailable", non_retryable=True)
    except Exception as e:
        # Retryable error
        raise ApplicationError(str(e))
```

### Long-Running Activities

```python
@activity.defn
async def long_running_task():
    for i in range(100):
        # Report progress
        activity.heartbeat({"progress": i})
        await process_item(i)
```

## Worker Management

### Starting Workers

```bash
# CLI command
ctutor worker start

# With specific queue
ctutor worker start --queues=computor-tasks,high-priority

# Direct Python
python -m ctutor_backend.tasks.temporal_worker
```

### Worker Configuration

```python
# temporal_worker.py
worker = Worker(
    client,
    task_queue="computor-tasks",
    workflows=[
        HierarchyManagementWorkflow,
        StudentTemplateWorkflow,
        ExampleDeploymentWorkflow,
        StudentTestingWorkflow
    ],
    activities=[
        create_gitlab_group,
        create_repository,
        run_tests,
        # ... more activities
    ]
)
```

### Scaling Workers

```yaml
# docker-compose-prod.yaml
temporal-worker:
  scale: 5  # Run 5 worker instances
  deploy:
    replicas: 5
```

## Monitoring

### Temporal UI

Access at http://localhost:8088

**Features**:
- Workflow history
- Activity timelines
- Error traces
- Retry attempts
- Query capabilities

### Workflow Queries

```python
@workflow.query
def get_status() -> str:
    return self.current_status

# Query from client
handle = client.get_workflow_handle(workflow_id)
status = await handle.query(WorkflowClass.get_status)
```

### Metrics

- Workflow completion rate
- Average execution time
- Retry frequency
- Error rates

## Best Practices

### 1. Idempotent Activities
```python
@activity.defn
async def create_group(name: str) -> str:
    # Check if already exists
    existing = await gitlab.get_group(name)
    if existing:
        return existing.id
    # Create if not exists
    return await gitlab.create_group(name)
```

### 2. Deterministic Workflows
```python
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self):
        # DON'T: Use random or time-based logic
        # if random.random() > 0.5:
        
        # DO: Use workflow-safe APIs
        await workflow.execute_activity(
            my_activity,
            start_to_close_timeout=timedelta(minutes=5)
        )
```

### 3. Activity Timeouts
```python
await workflow.execute_activity(
    quick_task,
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy=RetryPolicy(maximum_attempts=3)
)

await workflow.execute_activity(
    long_task,
    start_to_close_timeout=timedelta(hours=1),
    heartbeat_timeout=timedelta(minutes=1)
)
```

### 4. Workflow Versioning
```python
@workflow.defn
class VersionedWorkflow:
    @workflow.run
    async def run(self, version: int = 1):
        if version >= 2:
            # New behavior
            await self.new_logic()
        else:
            # Old behavior
            await self.old_logic()
```

## Testing Workflows

### Unit Tests
```python
async def test_workflow():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[MyWorkflow],
            activities=[my_activity]
        ):
            result = await env.client.execute_workflow(
                MyWorkflow.run,
                id="test-workflow",
                task_queue="test-queue"
            )
            assert result == expected
```

### Integration Tests
```python
# test_temporal_integration.py
async def test_gitlab_integration():
    # Start real Temporal server
    # Execute workflow
    # Verify GitLab state
    pass
```

## Troubleshooting

### Common Issues

1. **Worker not picking up tasks**
   - Check task queue names match
   - Verify Temporal server is running
   - Check worker logs for errors

2. **Workflow stuck**
   - Check Temporal UI for pending activities
   - Look for timeout configurations
   - Verify external services are accessible

3. **Non-determinism errors**
   - Don't use random values in workflows
   - Don't directly call external APIs
   - Use activities for all I/O operations

### Debug Commands

```bash
# Check worker status
ctutor worker status

# View workflow history
temporal workflow show --workflow-id=<id>

# List running workflows
temporal workflow list

# Terminate stuck workflow
temporal workflow terminate --workflow-id=<id>
```

## Configuration

### Environment Variables
```bash
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=computor-tasks
```

### Connection Settings
```python
# temporal_client.py
client = await Client.connect(
    f"{TEMPORAL_HOST}:{TEMPORAL_PORT}",
    namespace=TEMPORAL_NAMESPACE,
    data_converter=dataclasses.replace(
        temporalio.converter.default(),
        payload_codec=MyCodec()
    )
)
```