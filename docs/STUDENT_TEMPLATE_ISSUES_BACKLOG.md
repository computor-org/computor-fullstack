# Student Template Generation Issues - Backlog

## Issue Analysis from Error Logs

### ✅ Fixed Critical Issues

#### 1. Type Error: Ltree vs PosixPath ✅ RESOLVED
**Error**: `unsupported operand type(s) for /: 'PosixPath' and 'Ltree'`
**Location**: `temporal_student_template_v2.py:268`
**Root Cause**: Trying to use `/` operator between PosixPath and Ltree objects
**Fix**: Added `str()` conversion: `content_path_str = str(content.example.identifier)`
**Status**: Fixed in commit 8d88d05

#### 2. Content Processing Issues ✅ RESOLVED
**Problems**: 
- Only copied mediaFiles from content directory
- Incorrect studentTemplates processing
- Missing studentSubmissionFiles guarantees
**Fix**: Complete rewrite of content processing logic
**Status**: Fixed in latest commits

#### 3. Template File Resolution ✅ RESOLVED  
**Problem**: studentTemplates files not found due to path mismatches
**Fix**: Smart template resolution with filename matching and path preferences
**Status**: Fixed in latest commits

### 🟡 Remaining Issues (Still Need Investigation)

#### 1. MinIO Bucket Not Found
**Error**: `S3 operation failed; code: NoSuchBucket, message: The specified bucket does not exist, resource: /examples`
**Root Cause**: Bucket 'examples' doesn't exist in MinIO
**Impact**: Cannot download example files from storage
**Status**: Needs MinIO configuration review

#### 2. Git Authentication Failure
**Error**: `fatal: could not read Username for 'http://172.17.0.1:8084': No such device or address`
**Root Cause**: Git authentication not properly configured for HTTP URLs
**Impact**: Cannot push changes to GitLab repository
**Status**: Needs GitLab token/URL configuration review

### 🟡 Medium Priority Issues

#### 4. Branch Naming Inconsistency
**Error**: `fatal: The current branch master has no upstream branch`
**Root Cause**: Git creates 'master' branch but tries to push to 'main'
**Impact**: Push failures due to branch mismatch
**Solution**: Consistent branch naming

#### 5. Attribute Errors
**Error**: `'Ltree' object has no attribute 'split'` and `'str' object has no attribute 'path'`
**Root Cause**: Incorrect assumptions about object types
**Impact**: Workflow failures

### 🟢 Low Priority Issues

#### 6. Temporal Connection Issues
**Error**: Connection refused to Temporal server
**Root Cause**: Network configuration between containers
**Impact**: Worker cannot connect to Temporal server
**Note**: May be intermittent

## Detailed Analysis

### Issue 1: Type Compatibility (Line 268)
```python
# Current problematic code:
content_path_str = content.example.identifier # str(content.path)
target_path = Path(template_staging_path) / content_path_str
```

**Problem**: 
- `content.example.identifier` might be an Ltree object
- PosixPath `/` operator doesn't work with Ltree
- Need to convert to string first

### Issue 2: MinIO Configuration
**Current flow**:
1. `repository.source_url` used as bucket name
2. `version.storage_path` used as object prefix
3. Bucket 'examples' not found

**Questions**:
- Where should the bucket be created?
- What's the correct bucket naming convention?
- Is `source_url` the right field for bucket name?

### Issue 3: Git Authentication
**Current flow**:
1. GitLab token retrieved from organization properties
2. URL constructed with OAuth2 authentication
3. Push fails with authentication error

**Problems**:
- HTTP URL format may be incorrect
- Token may not have sufficient permissions
- Network connectivity to GitLab from container

## Action Plan

### Phase 1: Type Safety Fixes
- [ ] Fix Ltree/PosixPath type conversion
- [ ] Add proper type checks and conversions
- [ ] Test with various content path formats

### Phase 2: Storage Configuration
- [ ] Investigate MinIO bucket structure
- [ ] Verify example repository configuration
- [ ] Fix bucket naming and access

### Phase 3: Git Integration
- [ ] Fix OAuth2 authentication URL format
- [ ] Ensure consistent branch naming (main)
- [ ] Test GitLab connectivity from container

### Phase 4: Error Handling
- [ ] Add better error messages
- [ ] Implement graceful fallbacks
- [ ] Improve logging for debugging

## Code Locations to Review

1. **temporal_student_template_v2.py**:
   - Line 268: Type conversion issue
   - Line 90: Bucket name assignment
   - Line 180-185: OAuth2 URL construction
   - Line 340: Push operation

2. **Storage Service**:
   - MinIO bucket configuration
   - Object listing and downloading

3. **GitLab Builder**:
   - Token handling
   - Repository URL generation

## Test Cases Needed

1. **Type Conversion**:
   - Test with Ltree paths
   - Test with string paths
   - Test with None values

2. **Storage Integration**:
   - Test bucket existence
   - Test object listing
   - Test file downloads

3. **Git Operations**:
   - Test clone operations
   - Test push with authentication
   - Test branch operations

## Dependencies

- Need access to MinIO admin to check/create buckets
- Need GitLab token with proper permissions
- Need network connectivity between containers
- Need example data in MinIO for testing

## Success Criteria

- [ ] Template generation completes without type errors
- [ ] Example files successfully downloaded from MinIO
- [ ] Git repository successfully updated and pushed
- [ ] Proper error handling and logging
- [ ] All course contents processed successfully