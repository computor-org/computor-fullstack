# CourseContent Hierarchy System Analysis

## Overview

The CourseContent system in Computor implements a sophisticated hierarchical content management structure using PostgreSQL's **ltree** extension. This system manages educational content within courses through multiple layers of abstraction and relationships.

## Core Components

### 1. CourseContentKind (Content Type Template)

**Purpose**: Defines the fundamental characteristics of content types that can exist in the system.

```sql
CREATE TABLE course_content_kind (
    id               VARCHAR(255) PRIMARY KEY,    -- String ID for builtin types (e.g., 'assignment', 'unit', 'folder')
    title            VARCHAR(255),               -- Display name
    description      TEXT,                       -- Detailed description
    has_ascendants   BOOLEAN NOT NULL,           -- Can have parent nodes in tree
    has_descendants  BOOLEAN NOT NULL,           -- Can have child nodes in tree
    submittable      BOOLEAN NOT NULL            -- Can accept student submissions
);
```

**Key Properties**:
- `has_ascendants`: Controls whether this kind can be nested under other content
- `has_descendants`: Controls whether this kind can contain other content
- `submittable`: Determines if students can submit work for this content type

**Typical CourseContentKind entries**:
- `assignment` (submittable=true, has_ascendants=true, has_descendants=false)
- `unit` (submittable=false, has_ascendants=false, has_descendants=true)  
- `folder` (submittable=false, has_ascendants=true, has_descendants=true)
- `quiz` (submittable=true, has_ascendants=true, has_descendants=false)

### 2. CourseContentType (Course-Specific Configuration)

**Purpose**: Course-specific customization of CourseContentKind templates.

```sql
CREATE TABLE course_content_type (
    id                      UUID PRIMARY KEY,
    course_id               UUID NOT NULL REFERENCES course(id),
    course_content_kind_id  VARCHAR(255) NOT NULL REFERENCES course_content_kind(id),
    title                   VARCHAR(255),           -- Course-specific title override
    description             TEXT,                   -- Course-specific description
    slug                    VARCHAR(255) NOT NULL,  -- URL-friendly identifier
    color                   VARCHAR(255),           -- Visual customization
    -- Standard metadata fields...
    UNIQUE(slug, course_id, course_content_kind_id)
);
```

**Key Features**:
- **Course-specific customization**: Same CourseContentKind can have different titles/colors per course
- **Slug-based identification**: URL-friendly identifiers for API endpoints
- **Visual customization**: Each course can style content types differently

**Example**: A course might have:
- CourseContentKind "assignment" → CourseContentType "Mandatory Assignment" (red color)
- CourseContentKind "assignment" → CourseContentType "Extra Credit" (green color)

### 3. CourseContent (Actual Content Hierarchy)

**Purpose**: The actual hierarchical content structure using ltree paths.

```sql
CREATE TABLE course_content (
    id                      UUID PRIMARY KEY,
    course_id               UUID NOT NULL REFERENCES course(id),
    course_content_type_id  UUID NOT NULL REFERENCES course_content_type(id),
    title                   VARCHAR(255),
    description             TEXT,
    path                    LTREE NOT NULL,         -- Hierarchical path (e.g., 'week1.assignment1')
    position                FLOAT NOT NULL,         -- Ordering within same level
    version_identifier      VARCHAR(2048) NOT NULL, -- Content version/hash
    max_group_size          INTEGER NOT NULL,       -- Submission group constraints
    max_test_runs           INTEGER,                -- Testing limitations
    max_submissions         INTEGER,                -- Submission limitations
    execution_backend_id    UUID REFERENCES execution_backend(id), -- Testing system
    archived_at             TIMESTAMP,              -- Soft deletion
    -- Standard metadata fields...
    UNIQUE(course_id, path)
);
```

**Key Features**:
- **ltree paths**: Enable efficient hierarchical queries (ancestors, descendants, siblings)
- **Flexible positioning**: Float-based ordering allows insertion between existing items
- **Version tracking**: Content can be versioned for change detection
- **Testing integration**: Links to execution backends for automated testing
- **Submission constraints**: Controls group sizes and submission limits

### 4. Example System Integration

**Purpose**: Pre-built content templates that can initialize CourseContent.

```sql
CREATE TABLE example_repository (
    id              UUID PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    source_url      TEXT NOT NULL UNIQUE,       -- Git repository URL
    visibility      VARCHAR(20) DEFAULT 'private', -- public/private/restricted
    organization_id UUID REFERENCES organization(id),
    -- Metadata fields...
);

CREATE TABLE example (
    id                      UUID PRIMARY KEY,
    example_repository_id   UUID NOT NULL REFERENCES example_repository(id),
    directory               VARCHAR(255) NOT NULL,  -- Directory name in repo
    title                   VARCHAR(255) NOT NULL,
    subject                 VARCHAR(50),            -- Programming language
    category                VARCHAR(100),           -- Grouping category
    tags                    TEXT[],                 -- Search tags
    version_identifier      VARCHAR(64),            -- Content hash
    is_active               BOOLEAN DEFAULT true,
    UNIQUE(example_repository_id, directory)
);
```

## Relationship Analysis

### Current Architecture Flow

```
CourseContentKind (Template)
      ↓ (customized per course)
CourseContentType (Course-specific configuration)  
      ↓ (instantiated as content)
CourseContent (Actual hierarchy using ltree)
      ↓ (can be initialized from)
Example (Pre-built templates)
```

### Key Relationships

1. **CourseContentKind → CourseContentType** (1:N)
   - One kind can have multiple course-specific types
   - Enables "Mandatory Assignment" vs "Extra Credit Assignment"

2. **CourseContentType → CourseContent** (1:N)
   - One type can be used for multiple content items
   - Provides consistent styling and behavior

3. **Example → CourseContent** (Initialization relationship)
   - Examples can be used to initialize new CourseContent
   - Provides templates for common assignment patterns

## Current Implementation Assessment

### ✅ Strengths

1. **Flexible Hierarchy**: ltree enables efficient tree operations
2. **Multi-level Abstraction**: Clean separation between templates and instances
3. **Course Customization**: Same content kinds can look different per course
4. **Template System**: Examples provide reusable content patterns
5. **Submission Integration**: Built-in support for testing and submissions
6. **Version Tracking**: Content can be versioned for change detection

### ⚠️ Areas of Concern

1. **Complexity**: Three-layer abstraction (Kind → Type → Content) may be over-engineered
2. **Missing Direct Relationships**: No direct CourseContent → Example relationship in schema
3. **Initialization Logic**: How Examples initialize CourseContent is unclear
4. **Path Management**: ltree path generation and validation rules unclear
5. **Type Enforcement**: How has_ascendants/has_descendants are enforced is unclear

## Architecture Questions

### 1. Is the Three-Layer Abstraction Necessary?

**Current**: CourseContentKind → CourseContentType → CourseContent

**Alternative**: Could be simplified to CourseContentTemplate → CourseContent

**Analysis**: The current system allows fine-grained control but adds complexity. The middle layer (CourseContentType) primarily provides course-specific styling and naming.

### 2. Example Integration Clarity

**Current**: Examples exist independently, relationship to CourseContent unclear

**Missing**: How are Examples used to initialize CourseContent? Is there tracking of which Example was used?

### 3. Tree Constraint Enforcement

**Current**: has_ascendants/has_descendants flags exist but enforcement unclear

**Missing**: Database constraints or application logic to enforce tree structure rules

## Recommendations for Improvement

### 1. Simplify or Clarify Architecture

**Option A - Simplify**: Merge CourseContentKind and CourseContentType
```sql
CREATE TABLE course_content_template (
    id UUID PRIMARY KEY,
    course_id UUID REFERENCES course(id),
    kind VARCHAR(255) NOT NULL,  -- 'assignment', 'unit', etc.
    title VARCHAR(255),
    has_ascendants BOOLEAN,
    has_descendants BOOLEAN,
    submittable BOOLEAN,
    color VARCHAR(255)
);
```

**Option B - Clarify**: Keep current architecture but add documentation and constraints

### 2. Explicit Example-Content Relationship

Add tracking of example usage:
```sql
ALTER TABLE course_content 
ADD COLUMN initialized_from_example_id UUID REFERENCES example(id);
```

### 3. Tree Structure Validation

Add database constraints or triggers to enforce:
- has_ascendants: parent must allow descendants
- has_descendants: children must allow ascendants
- Path validation based on content type rules

### 4. Enhanced Path Management

Define clear rules for:
- Path generation algorithms
- Path uniqueness within courses
- Path restructuring when content moves

### 5. Documentation and Examples

Create comprehensive documentation covering:
- Content type design patterns
- ltree path conventions
- Example repository management
- Migration strategies for content restructuring

## Conclusion

The current CourseContent hierarchy system is sophisticated and flexible, but suffers from complexity and unclear integration points. The three-layer abstraction provides powerful customization capabilities but may be over-engineered for typical use cases.

**Recommendation**: Maintain the current architecture but focus on:
1. Clear documentation of all relationships
2. Database constraints to enforce tree rules
3. Explicit Example-CourseContent initialization tracking
4. Simplified management interfaces for common operations

The system's foundation is solid, but operational clarity and constraint enforcement need improvement.