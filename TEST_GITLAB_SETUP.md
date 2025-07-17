# GitLab Integration Test Setup

## Environment Variables

To run the GitLab integration tests, you need to set the following environment variables:

```bash
export TEST_GITLAB_URL=http://localhost:8084
export TEST_GITLAB_TOKEN=your-gitlab-token-here
export TEST_GITLAB_GROUP_ID=2
```

## Running Tests

### Test GitLab Builder
```bash
python test_gitlab_builder_real.py
```

### Delete Test Groups
```bash
python delete_test_gitlab_groups.py
```

## Important Notes

1. **GitLab Token**: The GitLab access token should never be hardcoded in the source files. Always use environment variables.

2. **Ltree Paths**: PostgreSQL ltree paths only support letters, numbers, and underscores. Use underscores instead of hyphens in paths.

3. **Database Connection**: The scripts will use the standard database environment variables (POSTGRES_HOST, POSTGRES_USER, etc.) with sensible defaults.

## Example .env File

Copy `.env.dev` and set your actual GitLab token:

```bash
cp .env.dev .env
# Edit .env and set TEST_GITLAB_TOKEN
```