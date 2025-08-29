# Enhanced Permission System Migration Plan

## Overview
This enhanced plan incorporates recommendations from both analyses, creating a comprehensive roadmap for migrating from the monolithic permission system to a modern, flexible authorization framework.

## Migration Phases

### Phase 0: Quick Win - Activate Existing System (Week 1)
**Goal**: Switch to the already-built modular system immediately

```python
# In api/permissions.py, replace the giant check_permissions function:
from ctutor_backend.permissions.core import check_permissions as new_check_permissions

def check_permissions(permissions: Principal, entity: Any, action: str, db: Session):
    return new_check_permissions(permissions, entity, action, db)
```

This gives immediate benefits:
- ✅ Cleaner code structure
- ✅ Better maintainability  
- ✅ Existing caching benefits
- ✅ No database changes needed

### Phase 1: Core Migration (Week 2)
Follow the original migration plan:
1. Enable environment variable switching
2. Test both systems in parallel
3. Gradual rollout through environments

### Phase 2: Database Enhancement (Week 3)
Add granular permission tables:

```python
# model/permission.py (new file)
from sqlalchemy import Column, String, UUID, Boolean, Enum, JSONB, ForeignKey, Index
from ctutor_backend.model.base import Base

class Permission(Base):
    __tablename__ = 'permission'
    
    id = Column(UUID, primary_key=True, default=uuid4)
    resource = Column(String(255), nullable=False)  # Entity tablename
    action = Column(String(50), nullable=False)      # CRUD action
    scope = Column(Enum('global', 'owned', 'related'), default='global')
    conditions = Column(JSONB)  # Additional conditions
    
    __table_args__ = (
        Index('ix_permission_resource_action', 'resource', 'action'),
    )

class RolePermission(Base):
    __tablename__ = 'role_permission'
    
    role_id = Column(ForeignKey('role.id'), primary_key=True)
    permission_id = Column(ForeignKey('permission.id'), primary_key=True)
    granted = Column(Boolean, default=True)
    conditions = Column(JSONB)  # Role-specific conditions
```

Migration:
```bash
alembic revision --autogenerate -m "Add permission and role_permission tables"
alembic upgrade head
```

### Phase 3: Policy-Based Permissions (Week 4)
Implement flexible policies:

```python
# permissions/policies.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class PermissionPolicy(ABC):
    """Base class for permission policies"""
    
    @abstractmethod
    def evaluate(self, principal: Principal, resource: Any, 
                action: str, context: dict) -> bool:
        pass

class OwnershipPolicy(PermissionPolicy):
    """Check if user owns the resource"""
    
    def evaluate(self, principal: Principal, resource: Any, 
                action: str, context: dict) -> bool:
        if hasattr(resource, 'user_id'):
            return str(resource.user_id) == principal.user_id
        if hasattr(resource, 'owner_id'):
            return str(resource.owner_id) == principal.user_id
        return False

class CourseRolePolicy(PermissionPolicy):
    """Check course-specific roles"""
    
    def __init__(self, required_role: str):
        self.required_role = required_role
    
    def evaluate(self, principal: Principal, resource: Any, 
                action: str, context: dict) -> bool:
        if hasattr(resource, 'course_id'):
            return principal.has_course_role(
                str(resource.course_id), 
                self.required_role
            )
        return False

class OrganizationPolicy(PermissionPolicy):
    """Check organization membership"""
    
    def evaluate(self, principal: Principal, resource: Any,
                action: str, context: dict) -> bool:
        if hasattr(resource, 'organization_id'):
            return principal.has_organization_access(
                str(resource.organization_id)
            )
        return False

class TimeBasedPolicy(PermissionPolicy):
    """Time-restricted access"""
    
    def __init__(self, start_hour: int = 8, end_hour: int = 18):
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def evaluate(self, principal: Principal, resource: Any,
                action: str, context: dict) -> bool:
        current_hour = datetime.now().hour
        return self.start_hour <= current_hour < self.end_hour

# Policy Engine
class PolicyEngine:
    def __init__(self):
        self.policies = {}
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        # Course content policies
        self.register_policy("course_content", "create", 
                           CourseRolePolicy("_lecturer"))
        self.register_policy("course_content", "update", 
                           CourseRolePolicy("_lecturer"))
        self.register_policy("course_content", "delete", 
                           CourseRolePolicy("_maintainer"))
        
        # User profile policies
        self.register_policy("profile", "update", OwnershipPolicy())
        self.register_policy("student_profile", "update", OwnershipPolicy())
        
        # Organization policies
        self.register_policy("organization", "update", 
                           OrganizationPolicy())
    
    def register_policy(self, resource: str, action: str, 
                       policy: PermissionPolicy):
        key = f"{resource}:{action}"
        if key not in self.policies:
            self.policies[key] = []
        self.policies[key].append(policy)
    
    def evaluate(self, principal: Principal, resource: Any, 
                action: str, context: dict = None) -> bool:
        resource_name = resource.__tablename__ if hasattr(resource, '__tablename__') else str(resource)
        key = f"{resource_name}:{action}"
        
        if key in self.policies:
            for policy in self.policies[key]:
                if policy.evaluate(principal, resource, action, context or {}):
                    return True
        return False

# Global policy engine instance
policy_engine = PolicyEngine()
```

### Phase 4: Attribute-Based Access Control (Week 5)
Add ABAC for complex scenarios:

```python
# permissions/abac.py
from typing import Any, Dict, List, Callable

class AttributeEvaluator:
    """Evaluate attribute-based expressions"""
    
    def __init__(self):
        self.evaluators = {
            'eq': self._eq,
            'neq': self._neq,
            'gt': self._gt,
            'gte': self._gte,
            'lt': self._lt,
            'lte': self._lte,
            'in': self._in,
            'contains': self._contains,
            'and': self._and,
            'or': self._or,
            'not': self._not
        }
    
    def evaluate(self, expression: dict, context: dict) -> bool:
        """
        Evaluate expressions like:
        {
            "and": [
                {"eq": ["$user.department", "$resource.department"]},
                {"in": ["$action", ["read", "list"]]},
                {"gte": ["$user.level", 3]}
            ]
        }
        """
        for op, args in expression.items():
            if op in self.evaluators:
                return self.evaluators[op](args, context)
        return False
    
    def _resolve(self, path: Any, context: dict) -> Any:
        """Resolve variable paths like $user.department"""
        if isinstance(path, str) and path.startswith("$"):
            parts = path[1:].split(".")
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
            return value
        return path
    
    def _eq(self, args: List, context: dict) -> bool:
        left = self._resolve(args[0], context)
        right = self._resolve(args[1], context)
        return left == right
    
    def _neq(self, args: List, context: dict) -> bool:
        return not self._eq(args, context)
    
    def _gt(self, args: List, context: dict) -> bool:
        left = self._resolve(args[0], context)
        right = self._resolve(args[1], context)
        return left > right
    
    def _gte(self, args: List, context: dict) -> bool:
        left = self._resolve(args[0], context)
        right = self._resolve(args[1], context)
        return left >= right
    
    def _lt(self, args: List, context: dict) -> bool:
        left = self._resolve(args[0], context)
        right = self._resolve(args[1], context)
        return left < right
    
    def _lte(self, args: List, context: dict) -> bool:
        left = self._resolve(args[0], context)
        right = self._resolve(args[1], context)
        return left <= right
    
    def _in(self, args: List, context: dict) -> bool:
        value = self._resolve(args[0], context)
        collection = self._resolve(args[1], context)
        return value in collection
    
    def _contains(self, args: List, context: dict) -> bool:
        collection = self._resolve(args[0], context)
        value = self._resolve(args[1], context)
        return value in collection
    
    def _and(self, args: List, context: dict) -> bool:
        return all(self.evaluate(expr, context) for expr in args)
    
    def _or(self, args: List, context: dict) -> bool:
        return any(self.evaluate(expr, context) for expr in args)
    
    def _not(self, args: List, context: dict) -> bool:
        return not self.evaluate(args[0], context)

# Global evaluator instance
attribute_evaluator = AttributeEvaluator()
```

### Phase 5: Enhanced Caching (Week 6)
Improve the caching strategy:

```python
# permissions/cache_enhanced.py
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class EnhancedPermissionCache:
    """Multi-tier caching with intelligent invalidation"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = {}  # In-memory L1 cache
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0
        }
    
    async def get_permissions(self, user_id: str) -> Optional[dict]:
        """Get permissions with L1/L2 cache"""
        cache_key = f"permissions:{user_id}"
        
        # L1 cache (in-memory)
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            if entry['expires'] > datetime.now():
                self.cache_stats['hits'] += 1
                return entry['data']
            else:
                del self.local_cache[cache_key]
        
        # L2 cache (Redis)
        data = await self.redis.get(cache_key)
        if data:
            permissions = json.loads(data)
            # Populate L1 cache
            self.local_cache[cache_key] = {
                'data': permissions,
                'expires': datetime.now() + timedelta(seconds=60)
            }
            self.cache_stats['hits'] += 1
            return permissions
        
        self.cache_stats['misses'] += 1
        return None
    
    async def set_permissions(self, user_id: str, permissions: dict, 
                            ttl: int = 300):
        """Set permissions in both cache tiers"""
        cache_key = f"permissions:{user_id}"
        
        # Set in Redis (L2)
        await self.redis.set(cache_key, json.dumps(permissions), ttl=ttl)
        
        # Set in local cache (L1)
        self.local_cache[cache_key] = {
            'data': permissions,
            'expires': datetime.now() + timedelta(seconds=min(ttl, 60))
        }
    
    async def invalidate_user(self, user_id: str):
        """Invalidate user permissions"""
        cache_key = f"permissions:{user_id}"
        
        # Clear L1
        if cache_key in self.local_cache:
            del self.local_cache[cache_key]
        
        # Clear L2
        await self.redis.delete(cache_key)
        self.cache_stats['invalidations'] += 1
    
    async def invalidate_course(self, course_id: str):
        """Invalidate all permissions for course members"""
        # Get course members
        pattern = f"course_members:{course_id}:*"
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=pattern, count=100
            )
            for key in keys:
                user_id = key.split(':')[-1]
                await self.invalidate_user(user_id)
            if cursor == 0:
                break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total if total > 0 else 0
        
        return {
            'hit_rate': f"{hit_rate:.2%}",
            'total_hits': self.cache_stats['hits'],
            'total_misses': self.cache_stats['misses'],
            'invalidations': self.cache_stats['invalidations'],
            'l1_size': len(self.local_cache)
        }

# Global cache instance
enhanced_cache = EnhancedPermissionCache(redis_client)
```

### Phase 6: Audit Logging (Week 7)
Add comprehensive audit logging:

```python
# model/audit.py
class PermissionAuditLog(Base):
    __tablename__ = 'permission_audit_log'
    
    id = Column(UUID, primary_key=True, default=uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(UUID, ForeignKey('user.id'), nullable=False)
    resource = Column(String(255), nullable=False)
    resource_id = Column(String(255))
    action = Column(String(50), nullable=False)
    granted = Column(Boolean, nullable=False)
    denial_reason = Column(String(500))
    context = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    __table_args__ = (
        Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_resource_timestamp', 'resource', 'timestamp'),
        Index('ix_audit_granted', 'granted'),
    )

# permissions/audit.py
import logging
from typing import Optional

class PermissionAuditor:
    """Audit permission checks for compliance and security"""
    
    def __init__(self, db: Session, logger: Optional[logging.Logger] = None):
        self.db = db
        self.logger = logger or logging.getLogger(__name__)
        self.buffer = []  # Batch writes
        self.buffer_size = 100
    
    def log_check(self, principal: Principal, resource: str, 
                  resource_id: Optional[str], action: str, 
                  granted: bool, denial_reason: Optional[str] = None,
                  request_context: Optional[dict] = None):
        """Log a permission check"""
        
        # Extract request info
        ip_address = None
        user_agent = None
        if request_context:
            ip_address = request_context.get('ip_address')
            user_agent = request_context.get('user_agent')
        
        entry = PermissionAuditLog(
            user_id=principal.user_id,
            resource=resource,
            resource_id=resource_id,
            action=action,
            granted=granted,
            denial_reason=denial_reason,
            context={'roles': principal.roles} if principal.roles else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Add to buffer
        self.buffer.append(entry)
        
        # Flush if buffer is full
        if len(self.buffer) >= self.buffer_size:
            self.flush()
        
        # Log important denials
        if not granted:
            self.logger.warning(
                f"Permission denied: user={principal.user_id}, "
                f"resource={resource}, action={action}, "
                f"reason={denial_reason}"
            )
    
    def flush(self):
        """Write buffered entries to database"""
        if self.buffer:
            self.db.bulk_save_objects(self.buffer)
            self.db.commit()
            self.buffer = []
    
    async def get_user_audit_trail(self, user_id: str, 
                                   days: int = 30) -> List[dict]:
        """Get audit trail for a user"""
        since = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(PermissionAuditLog).filter(
            PermissionAuditLog.user_id == user_id,
            PermissionAuditLog.timestamp >= since
        ).order_by(PermissionAuditLog.timestamp.desc()).all()
        
        return [
            {
                'timestamp': log.timestamp.isoformat(),
                'resource': log.resource,
                'action': log.action,
                'granted': log.granted,
                'denial_reason': log.denial_reason
            }
            for log in logs
        ]
    
    async def detect_anomalies(self, user_id: str) -> List[dict]:
        """Detect unusual permission patterns"""
        anomalies = []
        
        # Check for rapid denial rate
        recent_denials = self.db.query(PermissionAuditLog).filter(
            PermissionAuditLog.user_id == user_id,
            PermissionAuditLog.granted == False,
            PermissionAuditLog.timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ).count()
        
        if recent_denials > 10:
            anomalies.append({
                'type': 'rapid_denials',
                'severity': 'high',
                'message': f'{recent_denials} denials in last 5 minutes'
            })
        
        return anomalies

# Global auditor instance
permission_auditor = PermissionAuditor(db)
```

### Phase 7: Permission Decorators (Week 8)
Simplify endpoint protection:

```python
# api/decorators.py
from functools import wraps
from typing import Optional, List, Callable
from fastapi import HTTPException, status

def require_permission(
    resource: Optional[str] = None,
    action: Optional[str] = None,
    use_entity_class: bool = False,
    policies: Optional[List[PermissionPolicy]] = None
):
    """
    Decorator to check permissions before executing endpoint.
    
    Args:
        resource: Resource name (if None, extracted from entity)
        action: Action to check (if None, inferred from method)
        use_entity_class: Extract resource from entity class
        policies: Additional policies to evaluate
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract principal
            principal = kwargs.get('permissions')
            if not principal:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Determine resource name
            resource_name = resource
            if use_entity_class and 'entity' in func.__annotations__:
                entity_class = func.__annotations__['entity']
                resource_name = entity_class.__tablename__
            elif not resource_name:
                # Try to infer from endpoint name
                resource_name = func.__name__.split('_')[-1]
            
            # Determine action
            action_name = action
            if not action_name:
                # Infer from HTTP method
                method_map = {
                    'GET': 'get',
                    'POST': 'create',
                    'PUT': 'update',
                    'PATCH': 'update',
                    'DELETE': 'delete'
                }
                method = kwargs.get('request', {}).method
                action_name = method_map.get(method, 'get')
            
            # Check basic permission
            if not principal.permitted(resource_name, action_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No permission for {action_name} on {resource_name}"
                )
            
            # Evaluate additional policies
            if policies:
                db = kwargs.get('db')
                entity_id = kwargs.get('id') or kwargs.get(f'{resource_name}_id')
                
                # Load entity if needed
                entity = None
                if entity_id and db:
                    entity_class = func.__annotations__.get('entity')
                    if entity_class:
                        entity = db.query(entity_class).filter(
                            entity_class.id == entity_id
                        ).first()
                
                # Check policies
                context = {
                    'user': principal,
                    'resource': entity,
                    'action': action_name,
                    'request': kwargs.get('request')
                }
                
                for policy in policies:
                    if not policy.evaluate(principal, entity, action_name, context):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Policy check failed for {action_name} on {resource_name}"
                        )
            
            # Execute function
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Specialized decorators
def admin_only(func):
    """Require admin privileges"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        principal = kwargs.get('permissions')
        if not principal or not principal.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return await func(*args, **kwargs)
    return wrapper

def owner_only(resource_field: str = 'user_id'):
    """Require resource ownership"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            principal = kwargs.get('permissions')
            entity = kwargs.get('entity')
            
            if not entity or not hasattr(entity, resource_field):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Resource not found"
                )
            
            if str(getattr(entity, resource_field)) != principal.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't own this resource"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def course_role(minimum_role: str):
    """Require specific course role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            principal = kwargs.get('permissions')
            course_id = kwargs.get('course_id')
            
            if not course_id:
                # Try to extract from entity
                entity = kwargs.get('entity')
                if entity and hasattr(entity, 'course_id'):
                    course_id = str(entity.course_id)
            
            if not course_id or not principal.has_course_role(course_id, minimum_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {minimum_role} role in course"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

Usage examples:

```python
# Basic permission check
@router.get("/users/{user_id}")
@require_permission(resource="user", action="get")
async def get_user(user_id: str, permissions: Principal = Depends(get_current_permissions)):
    # Permission already checked
    return await fetch_user(user_id)

# Admin only endpoint
@router.delete("/organizations/{org_id}")
@admin_only
async def delete_organization(org_id: str, permissions: Principal = Depends(get_current_permissions)):
    # Only admins can reach here
    return await remove_organization(org_id)

# Owner only access
@router.put("/profiles/{profile_id}")
@owner_only(resource_field='user_id')
async def update_profile(profile_id: str, entity: Profile, permissions: Principal = Depends(get_current_permissions)):
    # Only profile owner can update
    return await save_profile(entity)

# Course role requirement
@router.post("/courses/{course_id}/content")
@course_role("_lecturer")
async def create_content(course_id: str, content: CourseContent, permissions: Principal = Depends(get_current_permissions)):
    # Only lecturers and above can create content
    return await save_content(content)

# Complex policy-based check
@router.patch("/courses/{course_id}/members/{member_id}")
@require_permission(
    resource="course_member",
    action="update",
    policies=[
        CourseRolePolicy("_maintainer"),
        TimeBasedPolicy(start_hour=8, end_hour=18)
    ]
)
async def update_member(course_id: str, member_id: str, permissions: Principal = Depends(get_current_permissions)):
    # Must be maintainer AND during business hours
    return await modify_member(member_id)
```

## Implementation Timeline

| Week | Phase | Key Deliverables |
|------|-------|-----------------|
| 1 | Quick Win | Switch to modular system |
| 2 | Core Migration | Environment switching, parallel testing |
| 3 | Database | Permission tables, migration scripts |
| 4 | Policies | Policy engine, default policies |
| 5 | ABAC | Attribute evaluator, complex rules |
| 6 | Caching | Multi-tier cache, invalidation |
| 7 | Audit | Logging, anomaly detection |
| 8 | Decorators | Endpoint protection, cleanup |

## Testing Strategy

```python
# tests/test_enhanced_permissions.py
import pytest
from unittest.mock import Mock, AsyncMock

class TestPermissionSystem:
    
    @pytest.fixture
    def test_context(self):
        return {
            'db': Mock(),
            'redis': AsyncMock(),
            'principal': Mock(user_id='test_user', is_admin=False)
        }
    
    async def test_policy_evaluation(self, test_context):
        """Test policy-based permissions"""
        policy = OwnershipPolicy()
        resource = Mock(user_id='test_user')
        
        assert policy.evaluate(
            test_context['principal'],
            resource,
            'update',
            {}
        ) == True
    
    async def test_abac_expressions(self, test_context):
        """Test attribute-based expressions"""
        evaluator = AttributeEvaluator()
        
        expression = {
            "and": [
                {"eq": ["$user.id", "test_user"]},
                {"in": ["$action", ["read", "update"]]}
            ]
        }
        
        context = {
            'user': {'id': 'test_user'},
            'action': 'read'
        }
        
        assert evaluator.evaluate(expression, context) == True
    
    async def test_cache_performance(self, test_context):
        """Test cache hit rates"""
        cache = EnhancedPermissionCache(test_context['redis'])
        
        # First call - miss
        result = await cache.get_permissions('user1')
        assert result is None
        
        # Set in cache
        await cache.set_permissions('user1', {'test': 'data'})
        
        # Second call - hit
        result = await cache.get_permissions('user1')
        assert result == {'test': 'data'}
        
        stats = cache.get_stats()
        assert stats['hit_rate'] == '50.00%'
    
    async def test_audit_logging(self, test_context):
        """Test audit trail creation"""
        auditor = PermissionAuditor(test_context['db'])
        
        auditor.log_check(
            test_context['principal'],
            'course',
            'course_123',
            'update',
            False,
            'Insufficient role'
        )
        
        assert len(auditor.buffer) == 1
        assert auditor.buffer[0].granted == False
    
    @pytest.mark.parametrize("decorator,expected", [
        (admin_only, False),
        (owner_only(), True),
        (course_role("_lecturer"), True),
    ])
    async def test_decorators(self, decorator, expected):
        """Test permission decorators"""
        @decorator
        async def test_endpoint(permissions=None):
            return "success"
        
        # Test based on expected result
        # Implementation depends on mock setup
        pass
```

## Benefits Over Original Plan

1. **Immediate Value**: Quick win in Week 1 by activating existing system
2. **Granular Control**: Database-backed permissions for fine-grained access
3. **Flexible Policies**: Dynamic policy evaluation for complex rules
4. **ABAC Support**: Attribute-based decisions beyond simple RBAC
5. **Better Caching**: Multi-tier with intelligent invalidation
6. **Compliance Ready**: Full audit logging with anomaly detection
7. **Developer Experience**: Clean decorators for endpoint protection
8. **Comprehensive Testing**: More thorough test coverage

## Risk Mitigation

1. **Gradual Enhancement**: Each phase builds on the previous
2. **Backward Compatibility**: Old system remains available throughout
3. **Feature Flags**: Enable/disable features independently
4. **Monitoring**: Comprehensive metrics at each phase
5. **Rollback Points**: Clear rollback strategy for each phase

## Conclusion

This enhanced plan combines the best of both analyses:
- My original migration strategy for safe deployment
- The other Claude's advanced features for long-term flexibility

The result is a comprehensive, modern permission system that can grow with your needs while maintaining backward compatibility during migration.