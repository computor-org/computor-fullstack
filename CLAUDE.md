# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Computor is a full-stack university programming course management platform with:
- **Backend**: Python/FastAPI with PostgreSQL, Redis, and Prefect for workflow orchestration
- **Frontend**: React 19 with TypeScript (in early development)
- **Infrastructure**: Docker-based deployment with Traefik/Nginx

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
bash migrations_up.sh        # SQL migrations
bash alembic_up.sh          # Alembic migrations
bash seeder.sh              # Seed test data

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
- **model/**: SQLAlchemy ORM models for database entities
- **interface/**: Pydantic schemas for API request/response validation
- **flows/**: Prefect workflow definitions for async operations
- **generator/**: Code generation utilities for student repositories
- **cli/**: Command-line interface tools

### Key Concepts
1. **Hierarchical Organization**: Organizations → Course Categories → Courses
2. **GitLab Integration**: Deep integration for repository management and CI/CD
3. **Role-Based Access**: Students, Tutors, Lecturers with different permissions
4. **Automated Testing**: Framework for testing student submissions (Python/MATLAB)
5. **Task Management**: Uses Prefect for orchestrating complex workflows

### Database
- PostgreSQL 16 for main data storage
- Redis for caching and session management
- Migrations in `/db/migrations/` (V1.000-V1.018)

## Important Files
- `/docs/documentation.md`: Comprehensive system architecture
- `/docker/docker-compose.dev.yml`: Development environment setup
- `/src/ctutor_backend/config.py`: Configuration management
- `/defaults/`: Template structures for course content

## Testing
- Backend tests in `/src/ctutor_backend/api/tests.py`
- Frontend uses Jest/React Testing Library
- No specific test runner configuration found - use default pytest/jest settings

## Plugins

**Important**: Each subdirectory in `/plugins/` is its own Git repository. When working with plugins:
1. Navigate to the specific plugin directory (e.g., `cd plugins/computor-sso`)
2. Make changes and commit/push within that repository
3. **Always return to the project base folder afterwards** (`cd ../..` or absolute path)

Example:
```bash
cd plugins/computor-sso
git add .
git commit -m "Update SSO plugin"
git push
cd ../..  # Return to project base
```

## Notes
- The web UI is in early development stages
- Plugin system exists at `/plugins/` (see above for Git workflow)
- VSCode extension available in separate repository
- System designed for academic programming course management