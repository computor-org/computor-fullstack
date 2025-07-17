# Scripts Directory

This directory contains various utility scripts organized by purpose:

## 📁 Directory Structure

### `/debug/`
Debug tools and troubleshooting scripts:
- `debug_gitlab_auth.py` - Test GitLab authentication and API connectivity

### `/testing/`
Testing and validation scripts:
- `test_celery_docker.sh` - Docker Celery testing and monitoring helper
- `test_sso_frontend.sh` - SSO frontend integration testing
- `delete_test_gitlab_groups.py` - Clean up GitLab test groups

### `/utilities/`
General utility scripts for development:
- `generate_types.sh` - Generate TypeScript interfaces from Pydantic models
- `initialize_system.sh` - Initialize system data (roles, admin user)
- `migrations.sh` - Alembic database migrations

## 🚀 Usage

All scripts should be run from the project root directory:

```bash
# Generate TypeScript types
bash scripts/utilities/generate_types.sh

# Run database migrations
bash scripts/utilities/migrations.sh

# Test GitLab authentication
python scripts/debug/debug_gitlab_auth.py

# Start Docker Celery testing
bash scripts/testing/test_celery_docker.sh start
```

## 📝 Notes

- Scripts maintain their original functionality after reorganization
- All documentation has been updated to reflect new paths
- Scripts are organized by purpose for better maintainability