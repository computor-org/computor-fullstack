# Permission System Migration Checklist

## Pre-Migration Checklist

### Environment Setup
- [ ] Verify new permission system files are present in `src/ctutor_backend/permissions/`
- [ ] Confirm Redis is running and accessible
- [ ] Backup current production database
- [ ] Document current permission configurations

### Code Review
- [ ] Review all files in `src/ctutor_backend/permissions/`
- [ ] Verify handler coverage for all entities
- [ ] Check Principal adapter compatibility
- [ ] Review caching configuration

### Testing Infrastructure
- [ ] Create test database with production-like data
- [ ] Set up parallel testing environment
- [ ] Prepare load testing scripts
- [ ] Configure monitoring dashboards

## Phase 1: Development Environment

### Initial Setup
- [ ] Set `USE_NEW_PERMISSION_SYSTEM=false` in dev environment
- [ ] Deploy new permission system files
- [ ] Verify old system still works
- [ ] Enable detailed logging

### Compatibility Testing
- [ ] Run comparison tests between old and new systems
- [ ] Document any behavioral differences
- [ ] Verify Principal conversion works both ways
- [ ] Test with various authentication methods (Basic, GitLab, SSO)

### Enable New System
- [ ] Set `USE_NEW_PERMISSION_SYSTEM=true` 
- [ ] Run full test suite
- [ ] Monitor error logs
- [ ] Check cache hit rates

### API Endpoint Testing
- [ ] Test `/organizations` endpoints
- [ ] Test `/course-families` endpoints  
- [ ] Test `/courses` endpoints
- [ ] Test `/course-contents` endpoints
- [ ] Test `/users` endpoints
- [ ] Test `/course-members` endpoints
- [ ] Test authentication endpoints

### Performance Validation
- [ ] Measure response times with new system
- [ ] Compare with baseline metrics
- [ ] Verify cache is working (check Redis)
- [ ] Monitor database query counts

## Phase 2: Staging Environment

### Deployment
- [ ] Deploy code with new permission system
- [ ] Keep `USE_NEW_PERMISSION_SYSTEM=false` initially
- [ ] Verify deployment successful
- [ ] Check all services are running

### Gradual Enablement
- [ ] Enable for read-only endpoints first
- [ ] Monitor for 24 hours
- [ ] Enable for write endpoints
- [ ] Monitor for 24 hours

### Integration Testing
- [ ] Run full integration test suite
- [ ] Test Temporal workflows with permissions
- [ ] Test GitLab API integration
- [ ] Test MinIO operations
- [ ] Test with Keycloak SSO

### Load Testing
- [ ] Run load tests with new system
- [ ] Compare performance metrics
- [ ] Verify no memory leaks
- [ ] Check cache performance under load

## Phase 3: Production Migration

### Pre-Production Checks
- [ ] Review all test results
- [ ] Confirm rollback procedure
- [ ] Brief operations team
- [ ] Schedule maintenance window (if needed)

### Initial Deployment
- [ ] Deploy with `USE_NEW_PERMISSION_SYSTEM=false`
- [ ] Verify deployment successful
- [ ] Monitor for stability (1 hour)
- [ ] Check all health endpoints

### Canary Rollout
- [ ] Enable for 10% of traffic
- [ ] Monitor error rates (2 hours)
- [ ] Enable for 50% of traffic  
- [ ] Monitor error rates (2 hours)
- [ ] Enable for 100% of traffic

### Monitoring (First 48 Hours)
- [ ] Check error rates every hour
- [ ] Monitor performance metrics
- [ ] Review permission denial logs
- [ ] Check cache hit rates
- [ ] Monitor database load

### Validation
- [ ] Verify all user roles work correctly
- [ ] Test admin operations
- [ ] Test student access
- [ ] Test lecturer operations
- [ ] Test course maintainer functions

## Phase 4: Post-Migration

### Code Cleanup
- [ ] Update all imports to use new system directly
- [ ] Remove adaptive function usage
- [ ] Remove old permission system files
- [ ] Update documentation

### Final Steps
- [ ] Remove `USE_NEW_PERMISSION_SYSTEM` environment variable
- [ ] Remove migration helper code
- [ ] Archive old permission system code
- [ ] Update API documentation

### Documentation
- [ ] Update developer documentation
- [ ] Update deployment guides
- [ ] Document new handler creation process
- [ ] Create troubleshooting guide

## Rollback Procedures

### Immediate Rollback (< 5 minutes)
1. [ ] Set `USE_NEW_PERMISSION_SYSTEM=false`
2. [ ] Restart API services
3. [ ] Verify old system active
4. [ ] Check system stability

### Standard Rollback (< 30 minutes)
1. [ ] Deploy previous version
2. [ ] Clear Redis cache
3. [ ] Restart all services
4. [ ] Run health checks
5. [ ] Notify team

## Verification Tests

### Permission Checks
```python
# Run these tests after each phase
def verify_permissions():
    tests = [
        # Admin can do everything
        ("admin_user", "Organization", "create", True),
        ("admin_user", "Course", "delete", True),
        
        # Student access
        ("student_user", "CourseContent", "list", True),
        ("student_user", "CourseContent", "create", False),
        
        # Lecturer access
        ("lecturer_user", "CourseContent", "create", True),
        ("lecturer_user", "CourseMember", "delete", False),
        
        # Maintainer access
        ("maintainer_user", "Course", "update", True),
        ("maintainer_user", "Organization", "delete", False),
    ]
    
    for user, entity, action, expected in tests:
        result = check_permission(user, entity, action)
        assert result == expected
```

### Cache Validation
```bash
# Check Redis cache is working
redis-cli
> KEYS *permission*
> GET <cache_key>
> TTL <cache_key>
```

### Performance Metrics
```bash
# Monitor key metrics
curl http://localhost:8000/metrics | grep permission_check_duration
curl http://localhost:8000/metrics | grep cache_hit_rate
curl http://localhost:8000/metrics | grep db_query_count
```

## Contact Points

### Technical Leads
- Backend Team Lead: [Contact for permission system questions]
- DevOps Lead: [Contact for deployment issues]
- Security Lead: [Contact for security concerns]

### Escalation Path
1. Development team on-call
2. Backend team lead
3. Engineering manager
4. CTO (critical issues only)

## Success Criteria

### Functional
- [ ] All API endpoints working correctly
- [ ] No unauthorized access incidents
- [ ] All user types can perform expected actions
- [ ] Temporal workflows execute successfully

### Performance  
- [ ] Response times improved by >20%
- [ ] Cache hit rate >80%
- [ ] Database queries reduced by >30%
- [ ] No memory leaks detected

### Operational
- [ ] Zero unplanned downtime
- [ ] Smooth rollout without incidents
- [ ] Rollback procedure tested and documented
- [ ] Team trained on new system

## Sign-off

### Development Team
- [ ] Lead Developer: _________________ Date: _______
- [ ] QA Lead: _______________________ Date: _______

### Operations Team  
- [ ] DevOps Lead: ___________________ Date: _______
- [ ] System Admin: __________________ Date: _______

### Management
- [ ] Engineering Manager: ____________ Date: _______
- [ ] Product Owner: _________________ Date: _______

## Notes and Observations

[Document any issues, learnings, or improvements discovered during migration]

---

**Last Updated**: [Current Date]
**Version**: 1.0
**Status**: Ready for Migration