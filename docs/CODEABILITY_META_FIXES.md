# CodeAbility Meta.yaml Fixes

## Issues Found

### 1. **CourseExecutionBackendConfig Missing Version**
- **Current**: Only has `slug` and `settings`
- **Required**: Add `version` field (string type)
- **Example**: `version: "r2024b"` or `version: "<eb_py_version>"`

### 2. **Course-Dependent Fields to Remove**
These fields belong to course configuration, not example metadata:
- `maxTestRuns` - Course/term specific
- `maxSubmissions` - Course/term specific  
- `maxGroupSize` - Course/term specific
- `contentTypes` - Examples are assigned to CourseContent, not courses directly

### 3. **LanguageEnum to String**
- **Current**: Enum with only `de` and `en`
- **Required**: String type to support any language
- **Reason**: More flexible for international courses

### 4. **Architecture Clarification**
- Examples are not directly linked to courses
- Examples are assigned to `CourseContent` (model)
- `CourseContent` has `CourseContentKind` (e.g., "assignment")
- Course-specific settings (maxRuns, etc.) belong to the course, not the example

## Fixed Structure

### Example-Level Meta (meta.yaml)
```yaml
slug: example.identifier
version: "1.0"
title: "Assignment Title"
description: "Assignment description"
language: "en"  # String, not enum
license: "MIT"
authors: [...]
properties:
  studentSubmissionFiles: [...]
  additionalFiles: [...]
  testFiles: [...]
  studentTemplates: [...]
  executionBackend:
    slug: "backend.identifier"
    version: "r2024b"  # NEW: version field
    settings: {...}
```

### Course-Level Settings (separate)
Course-dependent configurations belong in:
- Course model properties
- CourseContent properties
- CourseContentType configuration

## Implementation Plan

1. ✅ Add `version` field to `CourseExecutionBackendConfig`
2. ✅ Remove `maxTestRuns`, `maxSubmissions`, `maxGroupSize` from properties
3. ✅ Change `LanguageEnum` to `str` type
4. ✅ Remove `contentTypes` from course-level meta (if applicable)
5. ✅ Update validation and documentation