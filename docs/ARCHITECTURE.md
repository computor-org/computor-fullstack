# System Architecture

## Overview

Computor is a full-stack university programming course management platform designed with a clean separation between backend services, frontend application, and asynchronous task processing.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend (React)                        │
│                    TypeScript + Material-UI                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │   API Layer │◄─┤   Interface  │◄─┤    Model Layer      │    │
│  │  (Endpoints)│  │   (Pydantic) │  │   (SQLAlchemy)      │    │
│  └─────────────┘  └──────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │                │                      │
         ▼                ▼                      ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐
│   PostgreSQL │  │     Redis    │  │      MinIO         │
│   (Database) │  │   (Cache)    │  │  (Object Storage)  │
└──────────────┘  └──────────────┘  └─────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Temporal Workflows                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  GitLab Integration (Groups, Repos, Content Generation)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Model Layer (`/src/ctutor_backend/model/`)

The foundation of the application's data structure:

- **Technology**: SQLAlchemy ORM
- **Purpose**: Single source of truth for database schema
- **Key Models**:
  - `Organization` - Top-level educational institutions
  - `CourseFamilies` - Groups of related courses
  - `Courses` - Individual course instances
  - `Users`, `Accounts`, `Roles` - Authentication and authorization
  - `CourseContent` - Course materials and assignments

**Design Principles**:
- Models define the database structure directly
- Alembic migrations are auto-generated from model changes
- No manual SQL migrations

### 2. Interface Layer (`/src/ctutor_backend/interface/`)

Data transfer and validation layer:

- **Technology**: Pydantic v2
- **Purpose**: Request/response validation and serialization
- **Key Components**:
  - DTOs for each model entity
  - `EntityInterface` base classes for consistent patterns
  - Validation decorators for business rules
  - TypeScript interface generation support

**Design Principles**:
- Strict type validation at API boundaries
- Automatic documentation generation
- Clear separation from ORM models

### 3. API Layer (`/src/ctutor_backend/api/`)

RESTful endpoint implementation:

- **Technology**: FastAPI
- **Purpose**: HTTP interface for all operations
- **Organization**: One file per resource type
- **Key Features**:
  - Automatic OpenAPI documentation
  - JWT authentication with Keycloak
  - Permission-based access control
  - Dependency injection for database sessions

**Design Principles**:
- Resource-oriented design
- Consistent URL patterns
- Stateless operations

### 4. Temporal Tasks (`/src/ctutor_backend/tasks/`)

Asynchronous workflow orchestration:

- **Technology**: Temporal.io
- **Purpose**: Long-running and complex operations
- **Key Workflows**:
  - **GitLab Integration**: Group and repository creation
  - **Content Generation**: Student templates, assignments
  - **Testing**: Automated submission evaluation

**Workflow Components**:
- `temporal_hierarchy_management.py` - Organization/Course hierarchy
- `temporal_student_template_v2.py` - Template repository generation
- `temporal_examples.py` - Example deployment
- `temporal_student_testing.py` - Submission testing

## Data Flow

### 1. Standard Request Flow
```
Client Request → API Endpoint → Interface Validation → 
Business Logic → Model Operations → Database → Response
```

### 2. Async Task Flow
```
API Request → Temporal Client → Workflow Queue → 
Worker Process → GitLab API → Status Updates → Complete
```

### 3. Authentication Flow
```
Client → Keycloak → JWT Token → API Validation → 
Permission Check → Resource Access
```

## Service Architecture

### Core Services

1. **FastAPI Application** (`server.py`)
   - HTTP server
   - Route registration
   - Middleware configuration
   - CORS setup

2. **Database Service** (`database.py`)
   - Connection pooling
   - Session management
   - Transaction handling

3. **Temporal Worker** (`temporal_worker.py`)
   - Workflow execution
   - Activity implementation
   - Queue management

### External Integrations

1. **GitLab API**
   - Group management
   - Repository creation
   - Member management
   - CI/CD pipeline triggers

2. **Keycloak SSO**
   - User authentication
   - Token validation
   - Role management

3. **MinIO Storage**
   - File uploads
   - Assignment submissions
   - Course materials

## Deployment Architecture

### Development Environment
```yaml
Services:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Temporal Server (port 7233)
- Temporal UI (port 8088)
- Keycloak (port 8080)
- FastAPI (port 8000)
- Frontend (port 3000)
```

### Production Environment
- Horizontal scaling for Temporal workers
- Load balancing for API servers
- Database replication
- Redis clustering
- MinIO distributed mode

## Security Architecture

### Authentication
- Keycloak OpenID Connect
- JWT tokens
- Session management in Redis

### Authorization
- Role-based access control (RBAC)
- Permission decorators on endpoints
- Course-level permissions

### Data Security
- Encrypted database connections
- Secure file storage in MinIO
- API rate limiting
- Input validation at all boundaries

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Multiple Temporal workers
- Database read replicas

### Async Processing
- Temporal for long-running tasks
- Queue-based task distribution
- Automatic retry and recovery

### Caching Strategy
- Redis for session data
- API response caching (planned)
- Database query optimization

## Technology Decisions

### Why Temporal over Celery?
- Better workflow orchestration
- Built-in state persistence
- Visual workflow monitoring
- Automatic failure recovery

### Why SQLAlchemy + Pydantic?
- Clear separation of concerns
- Type safety throughout
- Automatic TypeScript generation
- Better validation capabilities

### Why MinIO?
- S3-compatible API
- Self-hosted option
- Cost-effective storage
- Easy backup and replication