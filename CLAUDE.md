# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Computor is a full-stack university programming course management platform with:
- **Backend**: Python/FastAPI with PostgreSQL, Redis (aiocache 0.12.3), and Celery for task execution
- **Frontend**: React 19 + TypeScript with Material-UI, TanStack Table, Recharts, and modern tooling
- **Infrastructure**: Docker-based deployment with Traefik/Nginx and horizontal task worker scaling
- **Database**: Pure SQLAlchemy/Alembic approach with comprehensive model validation

## Development Commands

### Backend
```bash
# Setup environment
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt

# Start development services
bash startup.sh             # All Docker services (dev/prod)
bash api.sh                 # FastAPI only
bash system_agent.sh        # System agent

# Docker services (includes task workers)
docker-compose -f docker-compose-dev.yaml up -d     # Development with workers
docker-compose -f docker-compose-prod.yaml up -d    # Production with scaling

# Database operations
bash migrations.sh          # Alembic migrations
bash initialize_system.sh   # Initialize system data (roles, admin user)
cd src && python seeder.py  # Seed development test data
alembic revision --autogenerate -m "description"  # Generate new migration
alembic upgrade head        # Apply all pending migrations

# Build and install CLI
pip install -e src

# Celery Task Workers (requires Redis)
ctutor worker start              # Start Celery worker (all queues)
ctutor worker start --burst      # Process jobs and exit
ctutor worker start --queues=high_priority,default  # Specific queues
ctutor worker status             # Check worker and queue status

# Direct Celery commands
python -m celery -A ctutor_backend.tasks.celery_app worker --loglevel=info
python -m celery -A ctutor_backend.tasks.celery_app flower  # Start Flower UI

# Docker Celery testing and monitoring
./test_celery_docker.sh start   # Start Docker services including Flower
./test_celery_docker.sh ui      # Show Flower UI access information
./test_celery_docker.sh all     # Full test cycle with Docker
```

### Frontend
```bash
bash frontend.sh            # Start dev server
# Or directly:
cd frontend && npm start     # Development server
cd frontend && npm build     # Production build
cd frontend && npm test      # Run tests
cd frontend && npm install   # Install dependencies

# Frontend stack:
# - React 19 + TypeScript
# - Material-UI for UI components
# - TanStack Table for advanced data tables
# - Recharts for data visualization  
# - React Hook Form + Zod for forms
# - TanStack Query for API calls
# - Redux Toolkit for state management
```

## Architecture

### Backend Structure (`/src/ctutor_backend/`)
- **api/**: FastAPI endpoints organized by resource (courses, users, submissions, etc.)
- **model/**: SQLAlchemy ORM models for database entities (single source of truth)
- **interface/**: Pydantic schemas for API request/response validation (DTOs with EntityInterface pattern)
- **flows/**: Prefect workflow definitions for async operations
- **generator/**: Code generation utilities for student repositories
- **cli/**: Command-line interface tools
- **utils/**: Shared utilities (color validation, etc.)
- **alembic/**: Database migrations using Alembic with SQLAlchemy models
- **tests/**: Test files for comprehensive testing coverage
- **scripts/**: Development and maintenance utility scripts

### Frontend Structure (`/frontend/`)
- **src/components/**: Reusable UI components (tables, forms, sidebar, navigation)
  - Advanced data tables with TanStack Table (filtering, sorting, pagination)
  - Professional form components with React Hook Form + Zod validation
  - Configurable sidebar system with context-aware navigation
- **src/pages/**: Main application pages and views (Dashboard, Students, Courses)
- **src/hooks/**: Custom React hooks for data fetching and logic
- **src/store/**: Redux store configuration and slices (state management)
- **src/api/**: API client and TanStack Query configuration (future FastAPI integration)
- **src/types/**: TypeScript type definitions for entities and interfaces
- **src/utils/**: Frontend utility functions, helpers, and mock data
- **src/styles/**: Material-UI theme configuration and global styles

### Frontend Features (✅ **Implemented**)
- **Dashboard**: Metrics cards and data visualization with Recharts
- **Students Management**: Advanced CRUD operations with professional table interface
- **Courses Overview**: Card-based layout with enrollment progress indicators  
- **Navigation System**: Top navigation bar with active state management
- **Form Validation**: Real-time validation with TypeScript integration
- **Responsive Design**: Professional UI/UX with Material-UI components
- **Hot Reload Development**: Modern development environment with proper TypeScript configuration

### Next: Configurable Sidebar System (🚧 **In Progress**)
- **GitLab-style Sidebar**: Collapsible navigation with hierarchical menu structure
- **Context-Aware Navigation**: Dynamic sidebar content based on selected course/context
- **Permission-Based Menus**: Role-specific menu visibility (Admin/Lecturer/Student)
- **Submenu Support**: Nested navigation with expandable sections
- **State Management**: Persistent sidebar state and configuration

### Key Concepts
1. **Hierarchical Organization**: Organizations → Course Families → Courses
2. **GitLab Integration**: Deep integration for repository management and CI/CD
3. **Role-Based Access**: Students, Tutors, Lecturers with different permissions
4. **Automated Testing**: Framework for testing student submissions (Python/MATLAB)
5. **Task Management**: Uses Prefect for orchestrating long running tasks and complex workflows

### Database
- **PostgreSQL 16** for main data storage with comprehensive schema
- **Redis** for caching and session management (using aiocache 0.12.3)
- **Hybrid Task Storage**: Redis for message broker + PostgreSQL for task results (production-grade persistence)
- **Redis Configuration**: Clean environment variable approach with `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- **Migration Strategy**: Pure SQLAlchemy/Alembic approach (✅ **Completed**)
  - SQLAlchemy models are the single source of truth
  - All migrations generated from model changes using Alembic
  - Models organized in `/src/ctutor_backend/model/sqlalchemy_models/`
  - Comprehensive test coverage for model integration
- **Enhanced Features**:
  - Flexible color validation system (supports HTML/CSS colors)
  - Hierarchical paths using PostgreSQL ltree extension
  - UUID primary keys with proper relationships

### ✅ Celery Task Executor Framework (Completed)
Comprehensive Celery-based system for handling long-running operations:
- **Priority Queues**: High, default, and low priority task processing with Celery
- **Horizontal Scaling**: Multiple Celery worker instances with Docker Compose
- **FastAPI Integration**: RESTful endpoints for task submission, monitoring, and worker status
- **CLI Tools**: Worker management commands (`ctutor worker start/status`) with Celery backend
- **Flower UI**: Web-based monitoring and diagnostics interface with automatic configuration
- **Docker Integration**: Complete Docker Compose setup with Redis broker and Celery workers
- **Hybrid Architecture**: Redis message broker + PostgreSQL result backend for optimal performance and persistence
- **Clean Configuration**: Structured environment variables for both Redis and PostgreSQL
- **Simplified Setup**: Environment variables with fallback defaults, no separate config files needed

### ✅ Keycloak SSO Integration (Completed)
Full Single Sign-On implementation with Keycloak identity provider:
- **OpenID Connect Authentication**: Complete OIDC flow with authorization code grant
- **User Registration**: API endpoint for creating users in both Keycloak and local database
- **Admin User Sync**: Automatic provisioning of admin user in Keycloak during system initialization
- **Plugin Architecture**: Extensible authentication plugin system supporting multiple providers
- **Account Linking**: Seamless linking between local user accounts and Keycloak identities
- **Docker Integration**: Keycloak service with PostgreSQL backend in docker-compose
- **Realm Configuration**: Pre-configured realm with demo users and client settings
- **Frontend Integration**: Complete React frontend SSO authentication flow
- **Key Features**:
  - JWT token verification with JWKS
  - Session management with Redis
  - Bearer token authentication for API access
  - Token refresh mechanism
  - Role-based access control ready
  - Email verification support
  - Password management through Keycloak
  - Automatic token inclusion in API requests
  - Debug tools for troubleshooting SSO issues
- **Default Users**:
  - Admin: `admin`/`admin` (synced from environment variables)
  - Demo users: `demo_user` and `demo_admin` (password: `password`)

## Important Files
- `/docs/documentation.md`: Comprehensive system architecture
- `/docs/PRODUCTION_MIGRATION_GUIDE.md`: Database migration guide
- `/docs/TASK_EXECUTOR.md`: Task executor framework guide
- `/docs/DOCKER_TASK_WORKERS.md`: Docker task worker configuration
- `/docs/SSO_FRONTEND_INTEGRATION.md`: SSO frontend integration guide
- `/docker-compose-dev.yaml`: Development environment with Celery workers and Flower UI
- `/docker-compose-prod.yaml`: Production environment with Celery scaling
- `/src/ctutor_backend/tasks/`: Celery task executor framework implementation
- `/src/ctutor_backend/tasks/celery_app.py`: Celery application configuration and setup
- `/test_celery_docker.sh`: Helper script for Docker Celery testing and monitoring
- `/src/ctutor_backend/config.py`: Configuration management
- `/defaults/`: Template structures for course content
- `/src/ctutor_backend/alembic/`: Database migration files and configuration
- `/src/ctutor_backend/tests/`: Test files for comprehensive testing (including Docker integration)
- `/src/ctutor_backend/scripts/`: Development and maintenance scripts

## Development Principles

### Test-Driven Development (TDD)
We follow a strict TDD approach:
1. Write the test first
2. Run the test and see it fail
3. Write minimal code to make the test pass
4. Refactor while keeping tests green

### Core Principles
- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **KISS**: Keep It Simple, Stupid - avoid unnecessary complexity
- **YAGNI**: You Aren't Gonna Need It - don't add functionality until it's needed
- **SRP**: Single Responsibility Principle - each class/function should have one reason to change

### Code Style
- **Use speaking names**: Variables, functions, and classes should clearly express their purpose
- **Let code speak for itself**: Write code as well-written prose that needs no explanation
- **Avoid redundant comments**: Don't comment what the code already says
- **Comment only when required for clarity**: Complex algorithms, workarounds, or non-obvious decisions
- **Document sparingly**: Function headers and classes only when purpose is not obvious, mainly for public APIs
- **Code ordering**: High-level and public API elements appear at the top, lower-level helper functions below
- **Follow PEP standards**: Strictly adhere to current PEP 8 and other applicable Python Enhancement Proposals

Example of good code:
```python
def calculate_student_final_grade(assignments: List[Assignment], exam_score: float) -> float:
    assignment_average = sum(a.score for a in assignments) / len(assignments)
    return assignment_average * 0.4 + exam_score * 0.6
```

## Testing
- **Backend Tests** (in `/src/ctutor_backend/tests/`):
  - Model tests: `test_models.py` - SQLAlchemy model imports and relationships
  - API tests: `test_api.py` - API module imports and basic functionality
  - API endpoint tests: `test_api_endpoints.py` - Comprehensive API endpoint testing with authentication and caching
  - DTO validation tests: `test_dto_validation.py`, `test_dto_properties.py`, `test_dto_edge_cases.py` - Pydantic validation testing
  - Redis caching tests: `test_redis_caching.py` - Cache functionality and performance testing
  - Color validation tests: `test_color_validation.py` - Color system validation
  - Pytest configuration: `conftest.py` - Test fixtures and database setup
- **Frontend**: Jest/React Testing Library
- **Test Runner**: `bash test.sh` - Comprehensive test runner with options
- **Test Commands**:
  ```bash
  # From project root
  bash test.sh                 # Run all tests
  bash test.sh --unit          # Run only unit tests
  bash test.sh --integration   # Run only integration tests
  bash test.sh --file test_models  # Run specific test file
  bash test.sh -v              # Run with verbose output
  
  # From src directory (if pytest installed)
  pytest                       # Run all tests
  pytest -m unit              # Run unit tests only
  pytest -m integration       # Run integration tests only
  pytest -k "color"           # Run tests matching "color"
  ```

## Plugins

**Important**: Each subdirectory in `/plugins/` is its own Git repository. When working with plugins:
1. Navigate to the specific plugin directory (e.g., `cd plugins/computor-sso`)
2. Make changes and commit/push within that repository

Example:
```bash
cd plugins/computor-sso
git add .
git commit -m "Update SSO plugin"
git push
```

## Recent Enhancements

### ✅ Task Queue Migration: RQ → Celery (Completed)
Successfully migrated the task execution framework from Redis Queue (RQ) to Celery:
- **Enhanced Scalability**: Celery provides better horizontal scaling and worker management
- **Production Ready**: More robust task queue system with better error handling and retries
- **Monitoring & Diagnostics**: Integrated Flower UI for real-time task and worker monitoring
- **Docker Integration**: Complete Docker Compose setup with Celery workers and Flower
- **Comprehensive Testing**: 29 tests including unit tests and Docker integration tests
- **Backwards Compatibility**: Maintained existing CLI and API interfaces
- **Key Benefits**: Better reliability, monitoring, scaling, and production deployment support

### ✅ Database Refactoring (Completed)
Successfully migrated from PostgreSQL migration files to pure SQLAlchemy/Alembic approach:
- **Achieved**: Single source of truth using SQLAlchemy models
- **Benefits**: Better maintainability, ORM benefits, automatic migration generation
- **Current State**: All models refactored, comprehensive test coverage, all imports resolved
- **Best Practice**: Future database changes should be made in SQLAlchemy models only

### ✅ Color System Enhancement (Completed)
Upgraded color handling from rigid ENUMs to flexible validation:
- **Enhanced**: Support for HTML/CSS colors (hex, rgb, hsl, named colors)
- **Validation**: Comprehensive color validation with clear error messages
- **Compatibility**: Maintains backward compatibility with existing data
- **Usage Examples**:
  ```python
  # All of these are now valid color formats:
  color = "#FF5733"              # Hex
  color = "rgb(255, 87, 51)"     # RGB
  color = "hsl(9, 100%, 60%)"    # HSL
  color = "tomato"               # Named color
  color = "emerald"              # Tailwind color
  ```

### ✅ API DTO Refactoring (Completed)
Complete Pydantic v1 to v2 migration with enhanced API infrastructure:
- **Pydantic Migration**: All `@validator` patterns migrated to `@field_validator` with proper decorators
- **Enhanced Validation**: Added `model_validator` for cross-field validation and comprehensive error handling
- **BaseEntityList Architecture**: Clean inheritance hierarchy for consistent datetime handling across all DTOs
- **Redis Caching System**: Full implementation with appropriate TTL values (60s-600s) and proper JSON serialization
- **API Testing Suite**: Comprehensive endpoint testing with 14 test cases covering authentication, caching, and validation
- **Missing Routes Fixed**: Added groups, profiles, sessions endpoints that were missing from API registration
- **Datetime Serialization**: Fixed JSON serialization issues for proper API responses
- **Interface Coverage**: All core entities (Users, Accounts, Organizations, Roles) and course-dependent entities refactored
- **Current State**: All 148 tests passing, all API endpoints functional, Redis caching operational

## Notes
- The web UI is in early development stages
- Plugin system exists at `/plugins/` (see above for Git workflow)
- VSCode extension available in separate repository
- System designed for academic programming course management