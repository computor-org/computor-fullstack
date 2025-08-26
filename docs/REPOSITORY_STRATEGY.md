# Repository Strategy for Multi-Role Access

## Overview

This document describes the repository structure and access strategy for supporting different user roles (Students, Lecturers, Tutors) in the Computor course management platform.

## Current Challenge

The platform needs to support different workflows for different user roles:
- **Students**: Work on assignments by forking template repositories
- **Lecturers**: Modify and improve examples when issues are found
- **Tutors (Study Assistants)**: Help students and grade submissions with access to reference solutions

## Proposed Repository Structure

### GitLab Group Hierarchy
```
Organization Group
├── Course Family Subgroup  
│   └── Course Subgroup
│       ├── Students Subgroup
│       │   ├── student1-assignment-repo (fork of student-template)
│       │   └── student2-assignment-repo (fork of student-template)
│       ├── Tutors Subgroup
│       │   ├── tutor1-workspace Repository (individual workspace)
│       │   └── tutor2-workspace Repository (individual workspace)
│       ├── student-template Repository (processed version for students)
│       └── assignments Repository (full example with solutions)
```

## Repository Types & Content

### 1. assignments Repository (Reference Repository)
**Purpose**: Full example content for lecturers and reference for tutors

**Content**:
- Complete, unmodified example content
- All solution files included
- Complete meta.yaml with all metadata
- Test files and grading scripts
- Original directory structure preserved
- All media files and resources

**Access**:
- **Lecturers**: Read/Write (can modify and improve examples)
- **Tutors**: Read-only (access to reference solutions)
- **Students**: No access

### 2. student-template Repository
**Purpose**: Student-facing template for assignment work

**Content**:
- Processed/converted version from assignments repository
- Solution files removed or stubbed out
- meta.yaml simplified/removed
- Only student-facing files (README, templates, media)
- Starter code templates where applicable

**Access**:
- **Students**: Fork/Read (students fork this for their work)
- **Tutors**: Read-only (can see what students start with)
- **Lecturers**: Read/Write (can make direct modifications if needed)

### 3. tutor-workspace Repositories
**Purpose**: Individual workspace for tutors to test and grade student submissions

**Content**:
- Initially empty
- Tutors manually copy student submissions here (via VSCode extension)
- Workspace for testing student code
- Isolated environment for grading and feedback

**Access**:
- **Individual Tutor**: Read/Write (own workspace)
- **Lecturers**: Read-only (can review tutor work)
- **Other Tutors**: No access
- **Students**: No access

### 4. Student Assignment Repositories
**Purpose**: Individual student work on assignments

**Content**:
- Forked from student-template
- Student's work and submissions
- Modified templates and solutions

**Access**:
- **Individual Student**: Read/Write (own repository)
- **Tutors**: Read-only (for grading and assistance)
- **Lecturers**: Read-only (oversight and grading)

## Workflows

### 1. Example Version Management

#### Initial Deployment
1. Example selected for course content
2. Temporal workflow generates:
   - **assignments repository**: Full example copy
   - **student-template repository**: Processed student version

#### Example Updates
- **Manual Process**: Lecturer chooses to update from new example version
- **OR**: Lecturer changes example version in course content settings
- Temporal workflow regenerates both repositories with new content

#### Lecturer Improvements
1. Lecturer modifies content in assignments repository
2. Lecturer creates new example version via API upload
3. Uploads modified content from assignments repository
4. Can choose to update course content to use new version

### 2. Student Workflow
1. Student receives access to student-template repository
2. Student forks student-template → personal assignment repository
3. Student works on assignment in their fork
4. Student submits via GitLab or platform interface

### 3. Tutor Workflow
1. Tutor has read access to assignments repository (reference solutions)
2. Tutor has read access to student assignment repositories
3. **VSCode Extension** handles:
   - Copying student submissions to tutor-workspace
   - Local testing and grading tools
   - Comparison with reference solutions
4. Tutor provides feedback through platform or GitLab

### 4. Lecturer Workflow
1. Lecturer has full access to assignments repository
2. Can modify examples directly for course-specific improvements
3. Can upload new versions back to example library
4. Oversees both student and tutor work
5. **VSCode Extension** provides:
   - Direct editing of examples
   - Integration with example library

## Implementation Requirements

### 1. GitLab Group Structure Updates
- Add **Tutors Subgroup** creation in hierarchy management
- Create individual **tutor-workspace repositories** for each tutor
- Set up appropriate permissions for all repository types

### 2. Temporal Workflow Modifications

#### `temporal_hierarchy_management.py`
- Add Tutors subgroup creation alongside Students subgroup
- Create tutor-workspace repositories for each tutor in the course

#### `temporal_student_template_v2.py`
- **Parallel processing**: Generate both repositories simultaneously
- **assignments repository**: Copy full, unmodified example content
- **student-template repository**: Current processed/converted version
- Maintain consistency between both repositories

### 3. Permission Management
```yaml
Repository Permissions:
  assignments:
    - Lecturers: Maintainer (read/write)
    - Tutors: Reporter (read-only)
    - Students: No access
  
  student-template:
    - Students: Reporter (read/fork)
    - Tutors: Reporter (read-only)
    - Lecturers: Maintainer (read/write)
  
  tutor-workspace:
    - Individual Tutor: Maintainer (read/write)
    - Lecturers: Reporter (read-only)
    - Other Tutors: No access
    - Students: No access
  
  student-assignment:
    - Individual Student: Maintainer (read/write)
    - Tutors: Reporter (read-only)
    - Lecturers: Reporter (read-only)
```

### 4. API Enhancements
- Endpoints for tutor workspace management
- Example version update workflows
- Repository synchronization status

## Integration with VSCode Extension

While the VSCode extension is separate from this backend strategy, the repository structure supports:

### For Lecturers
- Direct access to assignments repository for example editing
- Integration with example library for version uploads
- Access to all student and tutor repositories for oversight

### For Tutors
- Access to reference solutions (assignments repository)
- Tools to copy student work to tutor-workspace
- Local testing and grading environment
- Comparison tools between student work and reference

### For Students
- Access to student-template for initial assignment setup
- Standard Git workflows for assignment submission
- Integration with platform for submission tracking

## Benefits

1. **Clear Separation**: Each role has appropriate access levels
2. **Isolated Workspaces**: Tutors can test student code safely
3. **Reference Access**: Tutors have access to complete solutions
4. **Lecturer Control**: Full example editing and version management
5. **Scalable**: Individual workspaces prevent conflicts
6. **VSCode Integration**: Repository structure supports extension workflows

## Migration from Current System

1. **Phase 1**: Implement Tutors subgroup creation
2. **Phase 2**: Add assignments repository generation (parallel to student-template)
3. **Phase 3**: Create tutor-workspace repositories
4. **Phase 4**: Update permissions and access controls
5. **Phase 5**: Test and validate with VSCode extension

## Future Considerations

- **Automated Testing**: Integration of student code testing in tutor workspaces
- **Plagiarism Detection**: Cross-repository analysis capabilities
- **Bulk Operations**: Managing multiple student repositories efficiently
- **Archive Strategy**: Handling completed courses and old versions