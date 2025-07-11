# Database Refactoring Plan: PostgreSQL to SQLAlchemy-Only

## Overview
This document outlines the migration from mixed PostgreSQL migration files + SQLAlchemy models to a pure SQLAlchemy-only approach using Alembic for migrations.

## Current State Analysis

### PostgreSQL Migrations (db/migrations/)
- **V1.000**: Extensions and utility functions (uuid-ossp, ltree, pgcrypto, etc.)
- **V1.001**: Interface tables (abstract table structures)
- **V1.002**: Authentication tables (user, profile, student_profile, account, session)
- **V1.003**: Organizations
- **V1.004**: Course families
- **V1.005**: Courses
- **V1.006**: Course groups
- **V1.007**: Course roles
- **V1.008**: Course members
- **V1.009**: Execution backends
- **V1.010**: Course execution backends
- **V1.011**: Course content kinds
- **V1.012**: Course content types
- **V1.013**: Course contents
- **V1.014**: Course submission groups
- **V1.015**: Course submission group members
- **V1.016**: Results
- **V1.017**: User roles
- **V1.018**: Messages

### SQLAlchemy Models (models.py)
- Contains most core entities but missing some tables
- Some models have relationship issues
- Missing trigger implementations
- Missing some constraints and indexes

### Alembic Migrations
- Only 4 migrations, mainly incremental changes
- Uses mix of SQLAlchemy models and raw SQL
- Not configured to use models metadata

## Issues Identified

### 1. Missing Tables in SQLAlchemy Models
- `interfaces.*` tables (abstract interfaces)
- `group` table (referenced in relationships)
- `role` table (referenced in relationships)
- Proper trigger implementations
- Some utility functions

### 2. Model Inconsistencies
- Inheritance structure from PostgreSQL not properly represented
- Missing check constraints
- Incomplete indexes
- Some foreign key relationships need fixing

### 3. Configuration Issues
- Alembic `env.py` not configured to use models metadata
- Missing proper database URL configuration
- No autogenerate support

## Migration Strategy

### Phase 1: Prepare SQLAlchemy Models
1. **Add missing tables to models.py**:
   - `Group` table (already exists but needs verification)
   - `Role` table (already exists but needs verification)
   - Interface tables (if needed for inheritance)

2. **Fix model relationships**:
   - Ensure all foreign keys are properly defined
   - Fix relationship back-references
   - Add missing constraints

3. **Add database functions and triggers**:
   - PostgreSQL functions as migration scripts
   - Trigger implementations

### Phase 2: Configure Alembic
1. **Update alembic/env.py**:
   - Import models metadata
   - Configure autogenerate
   - Set up proper database connection

2. **Generate initial migration**:
   - Create baseline migration from current schema
   - Ensure all tables, indexes, and constraints are captured

### Phase 3: Testing and Validation
1. **Test migration process**:
   - Run migrations on test database
   - Verify schema matches expected structure
   - Test data integrity

2. **Update documentation**:
   - Remove references to PostgreSQL migrations
   - Update development setup instructions

## Missing Tables for Future Implementation

Based on analysis, the following tables are referenced but not fully implemented:

1. **Message-related tables** (V1.018 partially implemented)
   - Full message system schema
   - Message threading/replies
   - Message attachments

2. **Advanced role/permission tables**
   - Role inheritance
   - Permission granularity
   - Context-specific permissions

3. **Audit/logging tables**
   - Change tracking
   - User activity logs
   - System event logs

4. **File/asset management**
   - File storage metadata
   - Asset versioning
   - Upload tracking

5. **Notification system**
   - Notification preferences
   - Delivery tracking
   - Notification templates

6. **Advanced course features**
   - Course templates
   - Course copying/cloning
   - Course analytics

## Implementation Steps

### Step 1: Fix Current Models
```python
# Add missing check constraints
# Fix relationship definitions
# Add proper indexes
# Implement proper inheritance
```

### Step 2: Configure Alembic
```python
# Update env.py to use models metadata
# Set up autogenerate
# Configure database connection
```

### Step 3: Generate Migration
```bash
# Create initial migration from models
alembic revision --autogenerate -m "Initial SQLAlchemy migration"
```

### Step 4: Test Migration
```bash
# Test on clean database
# Verify schema correctness
# Test data migration if needed
```

## Benefits of This Approach

1. **Single source of truth**: All schema in SQLAlchemy models
2. **Better maintainability**: Model changes automatically generate migrations
3. **Improved development experience**: ORM benefits, IDE support
4. **Consistency**: Unified approach across the application
5. **Version control**: Better tracking of schema changes

## Risks and Mitigation

1. **Data loss risk**: 
   - Mitigation: Thorough testing on copies of production data
   - Backup strategy before migration

2. **Schema mismatch**: 
   - Mitigation: Careful comparison of generated vs. existing schema
   - Manual verification of constraints and indexes

3. **Performance impact**: 
   - Mitigation: Review generated migrations for efficiency
   - Test with realistic data volumes

## Timeline

- **Phase 1**: Model updates and fixes (2-3 days)
- **Phase 2**: Alembic configuration (1 day)
- **Phase 3**: Testing and validation (2-3 days)
- **Total**: 5-7 days

## Next Steps

1. Start with fixing the most critical model issues
2. Add missing tables and constraints
3. Configure Alembic for autogenerate
4. Generate and test initial migration
5. Update documentation and development processes