# Development Guide

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and Yarn
- Docker and Docker Compose
- Git
- PostgreSQL client tools (optional)

### Initial Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd computor-fullstack
```

2. **Set up Python environment**
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
pip install -e src  # Install CLI tools
```

3. **Configure environment**
```bash
cp .env.example .env  # Edit with your settings
```

4. **Start Docker services**
```bash
docker-compose -f docker-compose-dev.yaml up -d
```

5. **Initialize database**
```bash
bash migrations.sh
bash initialize_system.sh
cd src && python seeder.py  # Optional: seed test data
```

6. **Start backend**
```bash
bash api.sh
# Or: python src/server.py
```

7. **Set up frontend**
```bash
cd frontend
yarn install
yarn start
```

## Development Workflow

### Backend Development

#### Adding a New Model

1. Create model in `src/ctutor_backend/model/`:
```python
# src/ctutor_backend/model/my_model.py
from sqlalchemy import Column, String, Integer
from .base import Base

class MyModel(Base):
    __tablename__ = "my_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
```

2. Create Pydantic DTO in `src/ctutor_backend/interface/`:
```python
# src/ctutor_backend/interface/my_model.py
from pydantic import BaseModel
from .base import EntityInterface

class MyModelDTO(BaseModel):
    id: int
    name: str

class MyModelInterface(EntityInterface[MyModelDTO]):
    pass
```

3. Create API endpoint in `src/ctutor_backend/api/`:
```python
# src/ctutor_backend/api/my_model.py
from fastapi import APIRouter, Depends
from ..interface.my_model import MyModelDTO
from ..database import get_db

router = APIRouter()

@router.get("/my-models")
async def list_my_models(db = Depends(get_db)):
    # Implementation
    pass
```

4. Register router in `src/ctutor_backend/server.py`:
```python
from .api.my_model import router as my_model_router
app.include_router(my_model_router, prefix="")
```

5. Generate migration:
```bash
alembic revision --autogenerate -m "Add MyModel"
alembic upgrade head
```

#### Adding a Temporal Workflow

1. Create workflow file in `src/ctutor_backend/tasks/`:
```python
# src/ctutor_backend/tasks/temporal_my_workflow.py
from temporalio import workflow, activity
from datetime import timedelta

@activity.defn
async def my_activity(param: str) -> str:
    # Activity implementation
    return f"Processed: {param}"

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, input_data: dict) -> str:
        result = await workflow.execute_activity(
            my_activity,
            input_data["param"],
            start_to_close_timeout=timedelta(minutes=5)
        )
        return result
```

2. Register workflow in worker:
```python
# src/ctutor_backend/tasks/temporal_worker.py
from .temporal_my_workflow import MyWorkflow, my_activity

workflows = [
    # ... existing workflows
    MyWorkflow
]

activities = [
    # ... existing activities  
    my_activity
]
```

3. Create API endpoint to trigger workflow:
```python
# src/ctutor_backend/api/tasks.py
from ..tasks.temporal_client import get_client

@router.post("/trigger-my-workflow")
async def trigger_workflow(data: dict):
    client = await get_client()
    result = await client.execute_workflow(
        MyWorkflow.run,
        data,
        id=f"my-workflow-{uuid4()}",
        task_queue="computor-tasks"
    )
    return {"workflow_id": result}
```

### Frontend Development

#### Adding a New Page

1. Create page component:
```tsx
// frontend/src/pages/MyPage.tsx
import React from 'react';
import { Box, Typography } from '@mui/material';

export const MyPage: React.FC = () => {
    return (
        <Box>
            <Typography variant="h4">My Page</Typography>
        </Box>
    );
};
```

2. Add route in App.tsx:
```tsx
import { MyPage } from './pages/MyPage';

// In routes
<Route path="/my-page" element={<MyPage />} />
```

3. Add to navigation:
```tsx
// frontend/src/utils/navigationConfig.ts
export const navigationItems = [
    // ... existing items
    {
        id: 'my-page',
        label: 'My Page',
        path: '/my-page',
        icon: MyIcon
    }
];
```

#### Using Generated TypeScript Types

1. Generate types from backend:
```bash
bash generate_types.sh
```

2. Use in components:
```tsx
import { UserDTO, CourseDTO } from '../types/generated';

interface Props {
    user: UserDTO;
    course: CourseDTO;
}
```

## Testing

### Backend Testing

#### Unit Tests
```python
# src/ctutor_backend/tests/test_my_feature.py
import pytest
from ..model.my_model import MyModel

def test_my_model_creation():
    model = MyModel(name="Test")
    assert model.name == "Test"
```

#### Integration Tests
```python
@pytest.mark.integration
async def test_api_endpoint(client):
    response = await client.get("/my-models")
    assert response.status_code == 200
```

#### Running Tests
```bash
# All tests
bash test.sh

# Specific test file
pytest src/ctutor_backend/tests/test_my_feature.py

# With coverage
pytest --cov=ctutor_backend src/ctutor_backend/tests/
```

### Frontend Testing

```tsx
// frontend/src/components/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { MyComponent } from '../MyComponent';

test('renders component', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
});
```

Run tests:
```bash
cd frontend
yarn test
```

## Database Operations

### Migrations

```bash
# Generate new migration
cd src
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one revision
alembic downgrade -1

# View migration history
alembic history
```

### Direct Database Access

```bash
# Connect to database
docker exec -it computor-postgres psql -U computor -d computor

# Backup database
docker exec computor-postgres pg_dump -U computor computor > backup.sql

# Restore database
docker exec -i computor-postgres psql -U computor computor < backup.sql
```

## Docker Operations

### Service Management

```bash
# Start all services
docker-compose -f docker-compose-dev.yaml up -d

# Stop all services
docker-compose -f docker-compose-dev.yaml down

# View logs
docker-compose -f docker-compose-dev.yaml logs -f [service-name]

# Restart specific service
docker-compose -f docker-compose-dev.yaml restart temporal-worker
```

### Building Images

```bash
# Build API image
docker build -f docker/api/Dockerfile -t computor-api .

# Build frontend image
docker build -f docker/frontend/Dockerfile -t computor-frontend ./frontend
```

## GitLab Integration

### Testing GitLab Operations

```bash
# Test authentication
python scripts/debug/debug_gitlab_auth.py

# Test group creation
python scripts/testing/test_complete_gitlab_setup.py

# View GitLab structure
python scripts/testing/show_gitlab_structure.py
```

### Manual GitLab Operations

```python
# scripts/manual_gitlab_operation.py
from ctutor_backend.generator.gitlab_builder import GitLabBuilder

builder = GitLabBuilder(token="your-token")
group = builder.create_group("test-group")
```

## Debugging

### Backend Debugging

#### Using VS Code
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "server:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            "cwd": "${workspaceFolder}/src",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
```

#### Using pdb
```python
import pdb

def my_function():
    pdb.set_trace()  # Debugger will stop here
    # ... rest of code
```

### Frontend Debugging

- Use React Developer Tools browser extension
- Add debugger statements:
```tsx
function MyComponent() {
    debugger;  // Browser will pause here
    return <div>Content</div>;
}
```

### Temporal Debugging

1. Access Temporal UI: http://localhost:8088
2. Search for workflow by ID
3. View execution history
4. Check activity failures and retries

## Performance Optimization

### Backend

1. **Database Queries**
   - Use eager loading for relationships
   - Add appropriate indexes
   - Use query optimization

2. **Caching**
   - Implement Redis caching for frequently accessed data
   - Use appropriate TTL values

3. **Async Operations**
   - Use Temporal for long-running tasks
   - Implement pagination for large datasets

### Frontend

1. **Code Splitting**
   - Use React.lazy for route-based splitting
   - Implement dynamic imports

2. **Memoization**
   - Use React.memo for expensive components
   - Implement useMemo and useCallback

3. **API Optimization**
   - Implement request debouncing
   - Use React Query for caching

## Security Best Practices

### Backend

1. **Input Validation**
   - Always validate with Pydantic DTOs
   - Sanitize user inputs
   - Use parameterized queries

2. **Authentication**
   - Verify JWT tokens on all protected endpoints
   - Implement rate limiting
   - Use HTTPS in production

3. **Secrets Management**
   - Never commit secrets to Git
   - Use environment variables
   - Rotate tokens regularly

### Frontend

1. **XSS Prevention**
   - Sanitize user-generated content
   - Use Content Security Policy headers
   - Avoid dangerouslySetInnerHTML

2. **Authentication**
   - Store tokens in httpOnly cookies when possible
   - Implement token refresh
   - Clear tokens on logout

## Deployment

### Production Checklist

- [ ] Update environment variables
- [ ] Run database migrations
- [ ] Build frontend production bundle
- [ ] Configure SSL certificates
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test rollback procedure
- [ ] Update documentation

### Deployment Commands

```bash
# Build and deploy
docker-compose -f docker-compose-prod.yaml build
docker-compose -f docker-compose-prod.yaml up -d

# Scale workers
docker-compose -f docker-compose-prod.yaml scale temporal-worker=5

# Monitor logs
docker-compose -f docker-compose-prod.yaml logs -f
```

## Troubleshooting Guide

### Common Issues

#### Temporal Worker Not Starting
```bash
# Check Temporal server status
docker-compose -f docker-compose-dev.yaml ps temporal

# View worker logs
docker-compose -f docker-compose-dev.yaml logs temporal-worker

# Test connection
ctutor worker status
```

#### Database Connection Errors
```bash
# Check PostgreSQL status
docker-compose -f docker-compose-dev.yaml ps postgres

# Test connection
docker exec -it computor-postgres psql -U computor -c "SELECT 1"
```

#### Frontend Build Errors
```bash
# Clear cache
rm -rf frontend/node_modules frontend/yarn.lock
cd frontend && yarn install

# Check for type errors
yarn tsc --noEmit
```

## Contributing

### Code Style

- Python: Follow PEP 8
- TypeScript: Use Prettier and ESLint
- Commit messages: Use conventional commits

### Pull Request Process

1. Create feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit PR with clear description
6. Address review feedback

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No secrets in code
- [ ] Performance impact considered
- [ ] Security implications reviewed