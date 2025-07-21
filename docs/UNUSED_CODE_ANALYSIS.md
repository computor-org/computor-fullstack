# Unused Code Analysis Report

This document provides a comprehensive analysis of unused, obsolete, and potentially removable code in the Computor codebase as of the `cleanup/prefect-and-unused-code` branch.

## Executive Summary

The codebase is generally well-maintained, but there are several areas where cleanup would improve maintainability:
- **Prefect legacy code**: Remnants from the migration to Celery
- **Unused database models**: 4 models appear to be unused
- **Commented code blocks**: Large sections of commented-out code
- **Unused configuration variables**: 11+ environment variables are defined but never used
- **TODO/FIXME comments**: 26 instances indicating incomplete work

## 1. Prefect Legacy Code

### Files with Prefect References
- `/src/ctutor_backend/api/tests.py` - Contains `prefect_test_job()` function and imports
- `/src/ctutor_backend/api/tests_celery.py` - References Prefect as fallback option
- `/src/ctutor_backend/scripts/initialize_system_data.py` - Creates `prefect_builtin` execution backend
- `/src/ctutor_backend/scripts/fake_data_seeder.py` - Preserves `prefect_builtin` backend
- `/docs/documentation.md` - References Prefect for task orchestration
- `/CLAUDE.md` - Mentions non-existent `flows/` directory for Prefect workflows

### Recommendations
1. Remove `prefect_test_job()` function from `tests.py`
2. Remove Prefect fallback from `tests_celery.py`
3. Update documentation to reflect Celery-only architecture
4. Consider removing `prefect_builtin` execution backend

## 2. Unused Database Models

### Completely Unused Models
1. **Message** and **MessageRead** - No interfaces, no API endpoints
2. **Example** and **ExampleRepository** - No interfaces, no API endpoints

### Partially Integrated Models
1. **StudentProfile** - Has interface but no CRUD routes registered
2. **CourseContentKind** - Has interface but no routes registered

### Recommendations
- Remove Message/MessageRead models if messaging feature is not planned
- Remove Example/ExampleRepository models or complete implementation
- Register routes for StudentProfile and CourseContentKind if needed

## 3. Commented-Out Code Blocks

### Large Commented Sections
- `/src/ctutor_backend/client/crud_client.py` (lines 146-186) - Entire `filter()` method
- `/src/ctutor_backend/api/tests.py` - Old Prefect flow run code
- `/src/ctutor_backend/api/system.py` (lines 309-323) - Prefect client code
- `/src/ctutor_backend/model/exports.py` (lines 145-161) - Status chooser function
- `/src/ctutor_backend/interface/deployments.py` - GitHubConfig class

### Recommendations
- Remove commented code that's been replaced by new implementations
- Complete or remove the unfinished `filter()` method in crud_client.py

## 4. Unused Utility Functions

### Functions in `/api/utils.py` with No External Usage
- `get_course_content_id_from_url_and_directory`
- `getattrtuple`
- `hasattrtuple`

### Recommendations
- Review and remove if confirmed obsolete
- Document if intended for future use

## 5. Unused Configuration Variables

### Environment Variables Never Used in Code
- `API_ROOT_PATH`
- `KEYCLOAK_DB_PASSWORD` (only in docker-compose)
- `MINIO_DEFAULT_BUCKETS` (only in docker-compose)
- `MINIO_ROOT_PASSWORD` (only in docker-compose)
- `MINIO_ROOT_USER` (only in docker-compose)
- `REACT_APP_BACKEND_URL` (frontend only)
- `SYSTEM_DEPLOYMENT_PATH` (only in docker/scripts)
- `SYSTEM_GIT_EMAIL` (only as docker build arg)
- `SYSTEM_GIT_NAME` (only as docker build arg)

### Unused in storage_config.py
- `MAX_STORAGE_PER_USER`
- `MAX_STORAGE_PER_COURSE`
- `STORAGE_PATH_PATTERNS`

### Recommendations
- Remove truly unused variables
- Document docker-only variables clearly
- Fix the DOCKER_SOCKET_PATH typo

## 6. TODO/FIXME Comments

### Statistics
- **26 total occurrences** across the codebase
- Key areas: GitLab integration, error handling, refactoring needs

### High Priority TODOs
- Multiple "TODO: proper error handling" comments
- "TODO: REFACTORING" in several files
- GitLab-related TODOs for course integration

### Recommendations
- Create issues for each TODO item
- Prioritize error handling TODOs
- Remove completed TODOs

## 7. API Endpoints

### Duplicate Implementations
- `/tests` (RQ-based) vs `/tests-celery` (Celery-based)
- Both are registered but represent the old vs new implementation

### Commented Router
- `services_router` is commented out in server.py

### Recommendations
- Remove the old `/tests` endpoint after confirming all clients use `/tests-celery`
- Remove or implement the services_router

## 8. Misnamed Files

- `/src/ctutor_backend/api/messages.py` - Contains GitLab merge request functions, not message-related code

## Action Items

### High Priority
1. Complete Prefect removal from codebase
2. Remove or implement unused database models
3. Clean up large commented code blocks
4. Fix configuration variable typos

### Medium Priority
1. Review and remove unused utility functions
2. Address TODO/FIXME comments
3. Remove duplicate test endpoints
4. Update documentation to reflect current architecture

### Low Priority
1. Clean up unused environment variables
2. Rename misnamed files
3. Document docker-only configuration variables

## Conclusion

The codebase shows signs of a successful migration from Prefect to Celery, but cleanup of legacy code would improve maintainability. The unused database models suggest some features were planned but not implemented. Overall, the code is well-structured, and these cleanup items are typical technical debt from an evolving system.