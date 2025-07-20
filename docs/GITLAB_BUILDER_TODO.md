# GitLab Builder TODO - Current Status & Next Steps

## 🔄 Current Status (Where We Left Off)

### ✅ What's Complete:
1. **GitLab Builder Core** - `gitlab_builder_new.py` implemented with:
   - Organization → CourseFamily → Course hierarchy creation
   - Enhanced GitLab properties storage (group_id, namespace_id, web_url)
   - Database integration with proper error handling
   - Idempotency support

2. **Bug Fixes Applied**:
   - ✅ Ltree path conversion for all database operations
   - ✅ Fixed queries to use `Ltree(path)` instead of string paths
   - ✅ Added `keep_base_url=True` to avoid GitLab warnings
   - ✅ Fixed `updated_at` manual assignment (database handles it)

### 🐛 Current Bug - Course Creation Failing:
```
❌ Parent course family missing GitLab group_id
```

**Last Test Results**:
- ✅ Organization created successfully (DB + GitLab)
- ✅ CourseFamily created successfully (DB + GitLab)
- ❌ Course creation failed - can't find parent GitLab group_id

## 🔍 Next Debugging Steps

### 1. Check Properties Storage
The issue appears to be that CourseFamily GitLab properties aren't being retrieved correctly.

**SQL to check**:
```sql
SELECT id, path, properties FROM organization WHERE path = 'real_test_org';
SELECT id, path, properties FROM course_family WHERE path = 'real_family';
```

### 2. Debug Points to Add
In `_create_course` method around line 520:
```python
# Debug: Check what's in the course_family properties
logger.debug(f"CourseFamily properties: {course_family.properties}")
logger.debug(f"CourseFamily GitLab config: {course_family.properties.get('gitlab', {})}")
```

### 3. Possible Issues
- Properties might not be committed/flushed properly
- JSONB field might need special handling
- The properties structure might be different than expected

## 📋 Complete TODO List

### Immediate Tasks:
1. **Fix Course Creation Bug** [HIGH]
   - Debug why parent GitLab group_id is missing
   - Ensure properties are properly saved and retrieved
   - Test full hierarchy creation

2. **Complete Testing** [HIGH]
   - Run `python test_gitlab_builder_real.py` successfully
   - Verify all 3 levels created (Org, Family, Course)
   - Test idempotency (run twice)

### Next Phase:
3. **Add Missing Features** [MEDIUM]
   - Create students group under course
   - Create submissions group under course
   - Create course projects (tests, student-template, reference)

4. **Implement Repositories** [MEDIUM]
   - CourseFamilyRepository (similar to OrganizationRepository)
   - CourseRepository with course-specific operations
   - Use repositories in gitlab_builder_new.py

5. **Integration** [MEDIUM]
   - Replace api_client.py calls with repository calls
   - Integrate GitService for repository operations
   - Add async support where needed

6. **Final Refactoring** [LOW]
   - Migrate original gitlab_builder.py to use new implementation
   - Remove old API client dependencies
   - Update all references

## 🛠️ Quick Commands

### Run Test:
```bash
python test_gitlab_builder_real.py
```

### Clean GitLab Groups:
```bash
python delete_test_gitlab_groups.py
```

### Check Logs:
Look for log output from `gitlab_builder_new.py` - it has detailed logging

## 💡 Key Files
- `/src/ctutor_backend/generator/gitlab_builder_new.py` - Main implementation
- `/test_gitlab_builder_real.py` - Real test with DB + GitLab
- `/GITLAB_PROPERTIES_UPDATE.md` - Enhanced properties design
- `/GITLAB_REFACTORING_PROGRESS.md` - Overall progress

## 🎯 Success Criteria
When we continue, success means:
1. Full hierarchy creates without errors
2. All GitLab metadata stored in database
3. Running test twice shows perfect idempotency
4. Can query by stored group_id instead of path

---
**Last worked on**: GitLab builder with database integration
**Current blocker**: CourseFamily GitLab properties not accessible for Course creation
**Next action**: Debug properties storage/retrieval