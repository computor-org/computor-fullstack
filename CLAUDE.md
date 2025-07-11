# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Computor is a full-stack university programming course management platform with:
- **Backend**: Python/FastAPI with PostgreSQL, Redis (aiocache 0.12.3), and Prefect for workflow orchestration
- **Frontend**: React 19 with TypeScript (in early development)
- **Infrastructure**: Docker-based deployment with Traefik/Nginx
- **Database**: Pure SQLAlchemy/Alembic approach with comprehensive model validation

## Development Commands

### Backend
```bash
# Setup environment
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt

# Start development services
bash startup_dev.sh          # All Docker services
bash startup_fastapi_dev.sh  # FastAPI only
bash startup_system_agent_dev.sh  # System agent

# Database operations
bash alembic_up.sh          # Alembic migrations (primary method)
bash seeder.sh              # Seed test data
alembic revision --autogenerate -m "description"  # Generate new migration
alembic upgrade head        # Apply all pending migrations

# Build and install CLI
pip install -e src
```

### Frontend
```bash
bash startup_frontend_dev.sh  # Start dev server
# Or directly:
cd frontend && npm start     # Development
cd frontend && npm build     # Production build
cd frontend && npm test      # Run tests
```

## Architecture

### Backend Structure (`/src/ctutor_backend/`)
- **api/**: FastAPI endpoints organized by resource (courses, users, submissions, etc.)
- **model/**: SQLAlchemy ORM models for database entities (single source of truth)
- **interface/**: Pydantic schemas for API request/response validation
- **flows/**: Prefect workflow definitions for async operations
- **generator/**: Code generation utilities for student repositories
- **cli/**: Command-line interface tools
- **utils/**: Shared utilities (color validation, etc.)
- **alembic/**: Database migrations using Alembic with SQLAlchemy models

### Key Concepts
1. **Hierarchical Organization**: Organizations → Course Families → Courses
2. **GitLab Integration**: Deep integration for repository management and CI/CD
3. **Role-Based Access**: Students, Tutors, Lecturers with different permissions
4. **Automated Testing**: Framework for testing student submissions (Python/MATLAB)
5. **Task Management**: Uses Prefect for orchestrating long running tasks and complex workflows

### Database
- **PostgreSQL 16** for main data storage with comprehensive schema
- **Redis** for caching and session management (using aiocache 0.12.3)
- **Migration Strategy**: Pure SQLAlchemy/Alembic approach (✅ **Completed**)
  - SQLAlchemy models are the single source of truth
  - All migrations generated from model changes using Alembic
  - Models organized in `/src/ctutor_backend/model/sqlalchemy_models/`
  - Comprehensive test coverage for model integration
- **Enhanced Features**:
  - Flexible color validation system (supports HTML/CSS colors)
  - Hierarchical paths using PostgreSQL ltree extension
  - UUID primary keys with proper relationships

## Important Files
- `/docs/documentation.md`: Comprehensive system architecture
- `/docker/docker-compose.dev.yml`: Development environment setup
- `/src/ctutor_backend/config.py`: Configuration management
- `/defaults/`: Template structures for course content
- `/src/ctutor_backend/alembic/`: Database migration files and configuration

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
- **Backend Tests**:
  - API tests in `/src/ctutor_backend/api/tests.py`
  - Model integration tests: `test_model_integration.py`
  - API endpoint tests: `test_api_endpoints.py`
  - Color validation tests: `test_color_refactoring.py`
- **Frontend**: Jest/React Testing Library
- **Test Commands**:
  ```bash
  python test_model_integration.py     # SQLAlchemy model tests
  python test_api_endpoints.py         # API integration tests
  python test_color_refactoring.py     # Color validation tests
  pytest                               # Run all pytest tests
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

## Notes
- The web UI is in early development stages
- Plugin system exists at `/plugins/` (see above for Git workflow)
- VSCode extension available in separate repository
- System designed for academic programming course management