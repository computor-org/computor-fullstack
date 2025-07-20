# DEPRECATED - Backup Service

This backup service is deprecated and no longer maintained.

## Reasons for Deprecation
- The backup functionality should be handled by external backup solutions
- Database backups are better managed through PostgreSQL's native tools
- File system backups should use dedicated backup solutions

## Migration Path
Consider using:
- PostgreSQL's `pg_dump` for database backups
- Cloud provider backup solutions for cloud deployments
- Dedicated backup tools like Restic, Borg, or Duplicity for file backups

## Status
- Not included in docker-compose files
- Code kept for reference only
- Will be removed in a future release