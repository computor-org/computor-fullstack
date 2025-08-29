# New Permission System Architecture

## Overview

The new permission system is a complete refactor of the monolithic permission checking function into a modular, maintainable, and performant architecture. This document provides a detailed technical overview of the new system.

## Architecture Components

### 1. Core Modules

#### `permissions/principal.py`
**Purpose**: Enhanced Principal class with structured claims

**Key Components**:
- `Principal`: Main authorization context object
- `Claims`: Structured claim storage (general and dependent)
- `CourseRoleHierarchy`: Manages role inheritance (_student → _tutor → _lecturer → _maintainer)
- `build_claims()`: Constructs Claims from database tuples

**Features**:
- Type-safe claim management
- Course role hierarchy support
- Backward compatibility methods

#### `permissions/core.py`
**Purpose**: Main permission checking logic and registration

**Key Functions**:
- `check_permissions()`: Main entry point for permission checks
- `check_admin()`: Admin privilege verification
- `get_permitted_course_ids()`: Get accessible courses for a user
- `check_course_permissions()`: Course-specific permission checks
- `initialize_permission_handlers()`: Register all entity handlers

#### `permissions/handlers.py`
**Purpose**: Base handler interface and registry pattern

**Key Components**:
- `PermissionHandler`: Abstract base class for all handlers
- `PermissionRegistry`: Central registry for entity → handler mapping
- `permission_registry`: Global registry instance

**Pattern Benefits**:
- Open/Closed Principle compliance
- Easy to add new entities
- Consistent interface

#### `permissions/handlers_impl.py`
**Purpose**: Concrete permission handler implementations

**Handler Types**:

1. **UserPermissionHandler**
   - Handles User, Role, Group entities
   - Admin-only for write operations
   - Self-access for profile operations

2. **AccountPermissionHandler**
   - Manages Account entity permissions
   - Users can only access their own accounts

3. **ProfilePermissionHandler** 
   - Handles Profile, StudentProfile, Session
   - Self-access pattern

4. **CoursePermissionHandler**
   - Complex course access logic
   - Role-based filtering
   - Hierarchy support

5. **OrganizationPermissionHandler**
   - Organization visibility based on course membership
   - Read access for students in org courses

6. **CourseFamilyPermissionHandler**
   - Similar to organization handler
   - Filtered by course family membership

7. **CourseContentPermissionHandler**
   - Content access based on course role
   - Create/update for lecturers
   - Read for students

8. **CourseMemberPermissionHandler**
   - Member management permissions
   - Tutor+ for viewing
   - Maintainer for modifications

9. **ReadOnlyPermissionHandler**
   - For lookup tables (CourseRole, CourseContentKind)
   - Everyone can read, nobody can write

### 2. Supporting Modules

#### `permissions/auth.py`
**Purpose**: Refactored authentication with Principal creation

**Key Components**:
- `AuthenticationService`: Centralized auth logic
- `PrincipalBuilder`: Constructs Principal from credentials
- Support for Basic Auth, GitLab PAT, SSO tokens
- Caching of authenticated principals

#### `permissions/cache.py`
**Purpose**: Two-tier caching system for performance

**Cache Levels**:
1. **Permission Cache**: General permission results
2. **Course Permission Cache**: Course-specific permission results

**Features**:
- Redis-based distributed caching
- TTL-based expiration
- Cache key generation from principal + entity + action

#### `permissions/query_builders.py`
**Purpose**: Reusable query building components

**Builders**:
- `BasePermissionQueryBuilder`: Common query patterns
- `CoursePermissionQueryBuilder`: Course-specific queries
- `UserPermissionQueryBuilder`: User visibility queries

**Benefits**:
- DRY principle
- Optimized queries
- Consistent filtering

#### `permissions/integration.py`
**Purpose**: Bridge between old and new systems

**Features**:
- Environment variable control (`USE_NEW_PERMISSION_SYSTEM`)
- Adaptive functions that route to appropriate system
- Automatic Principal conversion
- Zero-downtime migration support

#### `permissions/migration.py`
**Purpose**: Migration utilities and helpers

**Components**:
- `PrincipalAdapter`: Converts between old/new Principal formats
- `MigrationHelper`: Unified interface during migration
- Comparison tools for validation
- Test helpers

## Data Flow

### Authentication Flow
```
Request → auth_type_switch() → Credentials
    ↓
AuthenticationService.authenticate()
    ↓
PrincipalBuilder.build()
    ↓
Principal (with claims)
    ↓
Cache (Redis)
```

### Authorization Flow
```
Principal + Entity + Action → check_permissions()
    ↓
PermissionRegistry.get_handler(entity)
    ↓
Handler.check_permissions()
    ↓
Query Builder (if needed)
    ↓
Filtered SQLAlchemy Query
    ↓
Cache Result
```

## Key Design Patterns

### 1. Registry Pattern
- Central registry maps entities to handlers
- Easy registration of new entities
- Consistent interface across all entities

### 2. Strategy Pattern
- Different handler strategies for different entity types
- Handlers encapsulate entity-specific logic
- Easy to swap or modify strategies

### 3. Builder Pattern
- PrincipalBuilder constructs complex Principal objects
- QueryBuilders construct optimized database queries

### 4. Adapter Pattern
- PrincipalAdapter converts between old/new formats
- Enables gradual migration

### 5. Cache-Aside Pattern
- Check cache before expensive operations
- Update cache after operations
- TTL-based invalidation

## Performance Optimizations

### 1. Caching Strategy
- **L1 Cache**: Permission results (5-10 min TTL)
- **L2 Cache**: Course permissions (5-10 min TTL)
- **Principal Cache**: Authenticated principals (10 min TTL)

### 2. Query Optimization
- Reusable query builders prevent duplication
- Optimized joins and subqueries
- Index-aware query construction

### 3. Lazy Evaluation
- Queries returned, not executed immediately
- Allows further filtering by calling code
- Reduces unnecessary database hits

## Extension Points

### Adding New Entities

1. Create handler class:
```python
class MyEntityHandler(PermissionHandler):
    def check_permissions(self, principal, action, db):
        # Custom logic here
        pass
```

2. Register handler:
```python
permission_registry.register(MyEntity, MyEntityHandler(MyEntity))
```

3. Done! The system automatically handles the new entity.

### Adding New Permission Types

1. Extend Claims class:
```python
class ExtendedClaims(Claims):
    custom_permissions: Dict[str, Set[str]]
```

2. Update PrincipalBuilder:
```python
def build_custom_claims(self, user_id, db):
    # Custom claim building logic
    pass
```

### Custom Caching Strategies

1. Implement cache interface:
```python
class CustomCache(BaseCache):
    async def get(self, key):
        # Custom retrieval
    
    async def set(self, key, value, ttl):
        # Custom storage
```

2. Configure in cache.py:
```python
cache_backend = CustomCache()
```

## Security Considerations

### 1. Principle of Least Privilege
- Default deny for all operations
- Explicit grants required
- Role hierarchy enforces minimum access

### 2. Defense in Depth
- Multiple authorization checks
- Query-level filtering
- Result validation

### 3. Cache Security
- Hashed cache keys prevent information leakage
- TTL prevents stale permissions
- User-specific cache invalidation

### 4. Audit Trail
- All permission checks logged
- Failed attempts tracked
- Performance metrics collected

## Testing Strategy

### 1. Unit Tests
- Each handler tested independently
- Mock database and principals
- Verify query construction

### 2. Integration Tests
- Full flow from auth to query
- Real database interactions
- Cache behavior validation

### 3. Performance Tests
- Load testing with/without cache
- Query optimization validation
- Memory usage profiling

### 4. Security Tests
- Privilege escalation attempts
- Cache poisoning prevention
- SQL injection prevention

## Migration Compatibility

### Backward Compatibility
- Adapter pattern for Principal conversion
- Same interface signatures maintained
- Drop-in replacement possible

### Forward Compatibility
- Extensible architecture
- Version-aware handlers possible
- Gradual feature addition

## Monitoring and Observability

### Metrics to Track
- Permission check latency (p50, p95, p99)
- Cache hit/miss rates
- Handler execution times
- Database query counts
- Failed authorization attempts

### Logging
- Structured logging with context
- Debug mode for detailed traces
- Error aggregation for patterns

### Health Checks
- Registry initialization status
- Cache connectivity
- Database connection pool status

## Best Practices

### 1. Handler Development
- Keep handlers focused and simple
- Reuse query builders
- Always return queries, not results
- Handle None cases explicitly

### 2. Claim Management
- Use structured claims, not strings
- Validate claim formats
- Document claim semantics

### 3. Caching
- Always set appropriate TTLs
- Invalidate on permission changes
- Monitor cache memory usage

### 4. Testing
- Test both positive and negative cases
- Include edge cases (admin, no permissions)
- Verify cache behavior

## Conclusion

The new permission system provides a robust, scalable, and maintainable foundation for authorization in the Computor platform. Its modular architecture, comprehensive caching, and clear separation of concerns make it easy to understand, extend, and optimize.