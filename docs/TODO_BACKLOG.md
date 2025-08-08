# Computor Platform Development Backlog

This document tracks the current implementation status, pending tasks, and important references for continuing development of the Computor platform.

## 🎯 Current Status Summary

**Date**: 2025-08-08  
**Last Session Context**: Implemented tutor workspace with example download functionality via API, completed submission group refactoring, and enhanced student/tutor views in VSCode extension.

### ✅ Recently Completed (This Session)

1. **Performance & Scalability Improvements**
   - Multi-tier caching system with LRU, LFU, FIFO, and TTL eviction policies
   - Performance monitoring with P50, P95, P99 metrics
   - Virtual scrolling for large datasets
   - Request batching service for API optimization

2. **Submission Group Refactoring** 
   - Migrated to `CourseSubmissionGroupGrading` audit trail pattern
   - Repository URL tracking in JSONB properties
   - Fixed SQLAlchemy metadata reserved attribute issues
   - Updated student endpoints to use submission groups

3. **Student Workspace Implementation**
   - Course selection mechanism for focused workspace
   - Course content tree built from submission groups
   - Repository cloning and workspace organization

4. **Tutor Workspace Implementation** ⭐ **NEW**
   - Example download via API (`/examples/{id}/download`)
   - Hierarchical example management (courses → repositories → examples)
   - Dependency support for example downloads
   - Structured workspace organization
   - Bulk download capabilities

5. **VSCode Extension Enhancements**
   - StudentTreeDataProvider and StudentCommands
   - TutorTreeDataProvider and TutorCommands  
   - WorkspaceManager service
   - Enhanced ComputorApiService with caching and error recovery

## 📋 Pending Tasks (Priority Order)

### High Priority (Next Sprint)

1. **🧪 Test Coverage Implementation**
   - **Status**: Pending
   - **Scope**: Add comprehensive tests for new tutor/student functionality
   - **Files to test**:
     - `/home/theta/computor/computor-vsc-extension/src/ui/tree/tutor/TutorTreeDataProvider.ts`
     - `/home/theta/computor/computor-vsc-extension/src/commands/TutorCommands.ts`
     - `/home/theta/computor/computor-vsc-extension/src/services/WorkspaceManager.ts`
   - **Reference**: VSCode extension testing patterns in existing codebase

2. **👥 Course Member Management**
   - **Status**: Pending
   - **Scope**: Implement CRUD operations for course members
   - **API**: Extend existing `/course-members` endpoints
   - **UI**: Add member management to lecturer view
   - **Dependencies**: None

3. **🔧 WorkspaceManager Git Integration**
   - **Status**: Incomplete (stub implementation)
   - **Scope**: Replace filesystem stubs with actual Git operations
   - **Location**: `/home/theta/computor/computor-vsc-extension/src/services/WorkspaceManager.ts`
   - **Methods to implement**:
     - `cloneStudentRepository()` - actual git clone
     - `cloneTutorRepository()` - actual git clone with authentication
   - **Dependencies**: VS Code Git API or git command integration

### Medium Priority

4. **📚 Example Version Management**
   - **Status**: API exists, UI pending
   - **Scope**: Add version selection/download in tutor workspace
   - **API**: Use `/examples/download/{version_id}` endpoint
   - **Reference**: `/home/theta/computor/computor-fullstack/src/ctutor_backend/api/examples.py:572`

5. **🎛️ Student Assignment Workflow**
   - **Status**: Commands stubbed
   - **Location**: `/home/theta/computor/computor-vsc-extension/src/commands/StudentCommands.ts:134-177`
   - **Scope**: Implement `startAssignment` and `submitAssignment` workflows
   - **Dependencies**: GitLab API integration for submission repositories

6. **🔄 Repository Synchronization**
   - **Status**: Not started
   - **Scope**: Auto-sync repositories, conflict resolution
   - **Location**: WorkspaceManager service
   - **Features needed**:
     - Pull updates from remote
     - Handle merge conflicts
     - Team repository synchronization

### Low Priority (Future Enhancements)

7. **📊 Analytics & Monitoring**
   - Usage metrics for examples and workspaces
   - Performance dashboards
   - Student progress tracking

8. **🌐 Multi-Platform Support**
   - Windows Git integration testing
   - Cross-platform path handling improvements

9. **🔌 Extension APIs**
   - Public APIs for third-party integrations
   - Webhook support for external tools

## 📁 Important Documentation References

### Core Architecture
- **Main README**: `/home/theta/computor/computor-fullstack/CLAUDE.md`
- **VSCode Extension Guide**: `/home/theta/computor/computor-vsc-extension/CLAUDE.md`

### Implementation Details
- **Submission Group Refactoring**: `/home/theta/computor/computor-fullstack/docs/SUBMISSION_GROUP_REFACTORING.md`
  - Database schema changes
  - API endpoint updates
  - Migration guide
- **Student Workspace Design**: `/home/theta/computor/computor-vsc-extension/docs/STUDENT_WORKSPACE_DESIGN.md`
  - Directory structure
  - API integration patterns
  - Future tutor workspace plans (now implemented!)

### API Documentation
- **Examples API**: `/home/theta/computor/computor-fullstack/src/ctutor_backend/api/examples.py`
  - Key endpoints: `/examples/{id}/download`, `/examples/download/{version_id}`
  - Dependency support with `?with_dependencies=true`
- **Student API**: `/home/theta/computor/computor-fullstack/src/ctutor_backend/api/students.py`
  - Implemented: `/students/submission-groups` endpoint
- **Interface Definitions**: `/home/theta/computor/computor-fullstack/src/ctutor_backend/interface/`
  - `example.py` - Example and repository DTOs
  - `student_courses.py` - Student course interfaces

### Implementation Files (Key Components)

#### VSCode Extension
```
/home/theta/computor/computor-vsc-extension/
├── src/
│   ├── ui/tree/
│   │   ├── tutor/TutorTreeDataProvider.ts          # ✅ Implemented
│   │   └── student/StudentTreeDataProvider.ts      # ✅ Implemented  
│   ├── commands/
│   │   ├── TutorCommands.ts                       # ✅ Implemented
│   │   └── StudentCommands.ts                     # ⚠️ Partial (stubs)
│   ├── services/
│   │   ├── WorkspaceManager.ts                    # ⚠️ Needs Git integration
│   │   ├── ComputorApiService.ts                  # ✅ Enhanced
│   │   ├── CacheService.ts                        # ✅ Implemented
│   │   └── PerformanceMonitoringService.ts        # ✅ Implemented
│   └── extension.ts                               # ✅ Updated
├── package.json                                   # ✅ Updated with tutor commands
└── docs/STUDENT_WORKSPACE_DESIGN.md              # ✅ Current
```

#### Backend Services
```
/home/theta/computor/computor-fullstack/
├── src/ctutor_backend/
│   ├── api/
│   │   ├── examples.py                           # ✅ Complete API
│   │   └── students.py                           # ✅ Updated endpoints
│   ├── interface/
│   │   ├── example.py                            # ✅ Complete DTOs
│   │   └── student_courses.py                    # ✅ Updated interfaces
│   └── model/course.py                           # ✅ Refactored models
└── docs/
    ├── SUBMISSION_GROUP_REFACTORING.md           # ✅ Current
    └── TODO_BACKLOG.md                           # 📄 This file
```

## 🛠️ Development Context for Next Session

### When Resuming Development:

1. **Current Branch Status**:
   - `computor-fullstack`: `feature/example-course-content-tree` 
   - `computor-vsc-extension`: `feature/lecturer-view`

2. **Environment Setup**:
   ```bash
   # Backend
   cd /home/theta/computor/computor-fullstack
   source .venv/bin/activate
   bash api.sh  # Start API server
   
   # Frontend Extension Development
   cd /home/theta/computor/computor-vsc-extension
   npm install
   # Open in VS Code for debugging
   ```

3. **Key Integration Points**:
   - Student endpoints: `/students/courses`, `/students/submission-groups`
   - Example endpoints: `/examples`, `/examples/{id}/download`
   - Authentication: JWT token via ComputorAuthenticationProvider
   - Caching: Multi-tier cache in ComputorApiService

4. **Testing Strategy**:
   - Unit tests for WorkspaceManager methods
   - Integration tests for API service methods
   - E2E tests for tutor example download workflow
   - Student workspace cloning workflow tests

### Quick Start Commands for Testing:
```bash
# Test tutor workspace
# 1. Open VS Code
# 2. Sign in to Computor
# 3. Open Tutor View
# 4. Expand course → repository → example
# 5. Right-click example → "Download Example"

# Test student workspace  
# 1. Open Student View
# 2. Expand course → content item
# 3. Test repository cloning (needs Git integration)
```

## 🏗️ Architecture Decisions Made

1. **API-First Approach**: Tutor workspace uses existing `/examples/download` endpoints rather than direct repository cloning
2. **Hierarchical Organization**: Course → Repository → Example structure for tutors
3. **Submission Group Filtering**: Students only see content they have submission groups for
4. **Multi-Tier Caching**: Hot/Warm/Cold tiers based on access patterns
5. **Workspace Isolation**: Separate student and tutor workspace directories

## 🔄 Migration Notes

- **Database**: CourseSubmissionGroup refactoring migration already applied
- **API**: Backward compatible - existing endpoints still work
- **Frontend**: New views added, existing functionality unchanged
- **Configuration**: New workspace configuration in `~/.computor/workspace/`

---

**Next Priority**: Implement actual Git operations in WorkspaceManager and add comprehensive test coverage for the tutor/student workspace functionality.

**Context Preservation**: This session successfully delivered a complete tutor workspace with API-based example downloads, complementing the existing student workspace implementation. The foundation is now in place for a full-featured VS Code extension supporting both student and instructor workflows.