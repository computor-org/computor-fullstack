# Permission System Migration Plan

## Executive Summary

This document outlines a comprehensive plan to migrate from the current monolithic permission system (`ctutor_backend.api.permissions`) to the new modular permission system (`ctutor_backend.permissions.*`). The migration is designed to be gradual, safe, and reversible with minimal disruption to the production system.

## Current State Analysis

### Existing System (`ctutor_backend.api.permissions`)
- **Location**: `src/ctutor_backend/api/permissions.py`
- **Characteristics**:
  - Single 500+ line file with one massive `check_permissions()` function
  - Hard-coded entity-specific logic in a giant if-elif chain
  - Tight coupling between permission logic and database queries
  - Difficult to maintain, test, and extend
  - No caching strategy
  - Mixed concerns (authentication, authorization, query building)

### New System (`ctutor_backend.permissions.*`)
- **Location**: `src/ctutor_backend/permissions/`
- **Characteristics**:
  - Modular architecture with separated concerns
  - Registry pattern for entity-specific handlers
  - Two-tier caching (permissions and course permissions)
  - Clean separation of authentication and authorization
  - Testable, maintainable components
  - Built-in migration support with adapter pattern

## Migration Strategy

### Phase 1: Preparation (Week 1)
1. **Enable Dual System Support**
   - The new system already includes `integration.py` for running both systems
   - Environment variable `USE_NEW_PERMISSION_SYSTEM` controls which system is active
   - Adapter classes convert between old and new Principal formats

2. **Comprehensive Testing**
   - Create test suite that validates both systems produce identical results
   - Run parallel testing in development environment
   - Document any behavioral differences

3. **Performance Baseline**
   - Measure current system performance
   - Compare with new system performance
   - Ensure new caching improves response times

### Phase 2: Gradual Rollout (Weeks 2-3)
1. **Development Environment**
   - Enable new system in development (`USE_NEW_PERMISSION_SYSTEM=true`)
   - Monitor logs and performance
   - Fix any issues that arise

2. **Staging Environment**
   - Deploy with new system enabled
   - Run comprehensive integration tests
   - Validate with real-world scenarios

3. **Production Canary**
   - Enable for specific endpoints or user groups
   - Monitor error rates and performance
   - Gradually increase coverage

### Phase 3: Full Migration (Week 4)
1. **Production Deployment**
   - Enable new system globally
   - Keep old system available for quick rollback
   - Monitor closely for first 48 hours

2. **Code Cleanup**
   - Update all imports to use new system directly
   - Remove adapter usage where not needed
   - Update documentation

### Phase 4: Cleanup (Week 5)
1. **Remove Old System**
   - Delete `api/permissions.py`
   - Remove migration helpers
   - Clean up integration module
   - Update all remaining references

## Implementation Steps

### Step 1: Update Import Statements
Replace imports throughout the codebase:

```python
# OLD
from ctutor_backend.api.permissions import check_permissions
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.interface.permissions import Principal

# NEW (using integration module during migration)
from ctutor_backend.permissions.integration import (
    adaptive_check_permissions as check_permissions,
    get_current_permissions,
    Principal
)
```

### Step 2: Update API Endpoints
Update each API file to use the adaptive functions:

1. **crud.py**:
   - Already uses `check_permissions()` - will work with adaptive version
   - No code changes needed, just import update

2. **course_contents.py**:
   - Uses `check_course_permissions()` 
   - Update to use adaptive version from integration module

3. **organizations.py**:
   - Uses `check_permissions()`
   - Update import to use adaptive version

4. **auth.py**:
   - Core authentication file
   - Update to use new `AuthenticationService` and `PrincipalBuilder`
   - Keep backward compatibility during migration

### Step 3: Enable Environment-Based Switching
Add to deployment configuration:

```bash
# Development
export USE_NEW_PERMISSION_SYSTEM=false  # Start with old system

# Staging (after testing)
export USE_NEW_PERMISSION_SYSTEM=true

# Production (gradual rollout)
export USE_NEW_PERMISSION_SYSTEM=false  # Then switch to true
```

### Step 4: Testing Strategy

1. **Unit Tests**:
   ```python
   # Test both systems produce same results
   from ctutor_backend.permissions.migration import MigrationHelper
   
   def test_permission_compatibility():
       result = MigrationHelper.compare_systems(
           principal, entity, action, db
       )
       assert result.matches == True
   ```

2. **Integration Tests**:
   - Run full API test suite with both systems
   - Compare response codes, data, and performance

3. **Load Testing**:
   - Verify caching improves performance
   - Ensure no memory leaks or resource issues

## Risk Mitigation

### Rollback Plan
1. **Immediate Rollback**:
   - Set `USE_NEW_PERMISSION_SYSTEM=false`
   - System automatically uses old implementation
   - No code changes required

2. **Gradual Rollback**:
   - Use adaptive functions to handle mixed scenarios
   - Can run both systems in parallel

### Monitoring
1. **Metrics to Track**:
   - Permission check latency
   - Cache hit rates
   - Error rates by endpoint
   - Database query counts

2. **Alerting**:
   - Set up alerts for increased error rates
   - Monitor performance degradation
   - Track unusual permission denials

## Benefits After Migration

1. **Maintainability**:
   - New entities require only a handler class
   - Clear separation of concerns
   - Self-documenting code structure

2. **Performance**:
   - Two-tier caching reduces database queries
   - Optimized query builders
   - Redis-based caching for distributed systems

3. **Testability**:
   - Each handler can be tested independently
   - Mock-friendly architecture
   - Clear test boundaries

4. **Extensibility**:
   - Easy to add new permission rules
   - Plugin-style handler registration
   - Support for custom authorization logic

## Timeline

| Week | Phase | Activities | Milestone |
|------|-------|------------|-----------|
| 1 | Preparation | Testing, validation, documentation | Test suite complete |
| 2 | Dev Rollout | Enable in development, fix issues | Dev environment stable |
| 3 | Staging | Deploy to staging, integration tests | Staging validated |
| 4 | Production | Gradual production rollout | System fully migrated |
| 5 | Cleanup | Remove old code, finalize docs | Migration complete |

## Success Criteria

1. **Functional**:
   - All endpoints work identically to old system
   - No unauthorized access or permission errors
   - All tests pass

2. **Performance**:
   - Response times improved by 20%+ due to caching
   - Database query reduction of 30%+
   - Memory usage stable

3. **Operational**:
   - Zero downtime during migration
   - Quick rollback capability maintained
   - Clear audit trail of changes

## Conclusion

This migration plan provides a safe, gradual path from the monolithic permission system to the new modular architecture. The dual-system support and adapter pattern ensure we can migrate without disruption while maintaining the ability to rollback instantly if issues arise.