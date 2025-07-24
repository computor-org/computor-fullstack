# Temporal Quick Start Guide

## 🚀 Quick Start (Development Mode)

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

#### Option A: Using curl (no auth required in dev mode)
```bash
# Submit a 30-second test task
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "example_long_running",
    "parameters": {"duration": 30, "message": "Hello Temporal!"},
    "priority": 0
  }'
```

#### Option B: Using the test script
```bash
python scripts/test_temporal_tasks.py
```

### 5. Monitor in Temporal UI
- Go to http://localhost:8088
- Click on "Workflows" to see your running task
- Click on the workflow ID to see execution details

## 📊 Available Example Tasks

1. **example_long_running** - Simulates long-running work
   ```json
   {
     "task_name": "example_long_running",
     "parameters": {
       "duration": 60,
       "message": "Processing..."
     }
   }
   ```

2. **example_data_processing** - Simulates data processing
   ```json
   {
     "task_name": "example_data_processing", 
     "parameters": {
       "data_size": 1000,
       "processing_type": "transform"
     }
   }
   ```

3. **example_error_handling** - Demonstrates error handling
   ```json
   {
     "task_name": "example_error_handling",
     "parameters": {
       "should_fail": true,
       "fail_at_step": 2
     }
   }
   ```

## 🔍 Monitoring Tasks

### Via API
```bash
# Get task status
curl http://localhost:8000/tasks/{task_id}

# Get task result  
curl http://localhost:8000/tasks/{task_id}/result

# List all task types
curl http://localhost:8000/tasks/types
```

### Via Temporal UI
1. **Workflows Tab**: See all workflows with status
2. **Click on Workflow**: View execution timeline, inputs, outputs
3. **Workers Tab**: See connected workers
4. **Search**: Find workflows by ID or type

## 🎯 Priority Queues

Tasks are routed based on priority:
- **High Priority (>5)**: `computor-high-priority` queue
- **Normal Priority (0-5)**: `computor-tasks` queue  
- **Low Priority (<0)**: `computor-low-priority` queue

Example high-priority task:
```bash
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "example_long_running",
    "parameters": {"duration": 10},
    "priority": 10
  }'
```

## 🛑 Stopping Services

```bash
# Stop all Temporal services including worker
docker-compose -f docker-compose-dev.yaml down temporal-worker temporal temporal-postgres temporal-ui

# Or stop individual services
docker-compose -f docker-compose-dev.yaml stop temporal-worker
```

## 💡 Tips

1. Worker logs show real-time activity
2. Temporal UI auto-refreshes every 15 seconds
3. Failed workflows show error details in UI
4. Workflows persist even if worker restarts

## 🔗 Useful URLs

- **API**: http://localhost:8000/docs
- **Temporal UI**: http://localhost:8088
- **Full Documentation**: See `docs/TEMPORAL_TASK_USAGE.md`