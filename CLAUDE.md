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
bash startup.sh             # All Docker services (dev/prod)
bash api.sh                 # FastAPI only
bash system_agent.sh        # System agent

# Database operations
bash migrations.sh          # Alembic migrations
bash initialize_system.sh   # Initialize system data (roles, admin user)
cd src && python seeder.py  # Seed development test data
alembic revision --autogenerate -m "description"  # Generate new migration
alembic upgrade head        # Apply all pending migrations

# Build and install CLI
pip install -e src
```

### Frontend
```bash
bash frontend.sh            # Start dev server
# Or directly:
cd frontend && npm start     # Development
cd frontend && npm build     # Production build
cd frontend && npm test      # Run tests
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
- `/docs/PRODUCTION_MIGRATION_GUIDE.md`: Database migration guide
- `/docker/docker-compose.dev.yml`: Development environment setup
- `/src/ctutor_backend/config.py`: Configuration management
- `/defaults/`: Template structures for course content
- `/src/ctutor_backend/alembic/`: Database migration files and configuration
- `/src/ctutor_backend/tests/`: Test files for comprehensive testing
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