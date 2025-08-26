# CourseContent Hierarchy Improvement Proposal

## Executive Summary

The current CourseContent hierarchy system is well-designed but has several areas for improvement. This proposal outlines specific enhancements to improve clarity, enforce constraints, and simplify management while maintaining the system's flexibility.

## Current Architecture Assessment

### ✅ What Works Well

1. **ltree Integration**: Efficient hierarchical queries and path-based organization
2. **Flexible Abstraction**: Three-layer system allows fine-grained customization
3. **Course Isolation**: Content types can be customized per course
4. **Example Templates**: Reusable content initialization patterns
5. **Submission Integration**: Built-in testing and submission workflows

### ❌ Problem Areas

1. **Missing Constraints**: Tree structure rules not enforced at database level
2. **Unclear Relationships**: Example → CourseContent initialization not tracked
3. **Complex Management**: Three layers require complex operations for simple tasks
4. **Validation Gaps**: Path generation and validation rules unclear
5. **Documentation Deficit**: Relationships and workflows poorly documented

## Proposed Improvements

### 1. Database Constraint Enhancement

#### A. Tree Structure Validation

Add database constraints to enforce CourseContentKind rules:

```sql
-- Trigger to validate tree structure rules
CREATE OR REPLACE FUNCTION validate_course_content_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if parent allows descendants (if we have a parent)
    IF nlevel(NEW.path) > 1 THEN
        IF NOT EXISTS (
            SELECT 1 FROM course_content cc
            JOIN course_content_type cct ON cc.course_content_type_id = cct.id
            JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
            WHERE cc.course_id = NEW.course_id 
            AND cc.path = subltree(NEW.path, 0, nlevel(NEW.path) - 1)
            AND cck.has_descendants = true
        ) THEN
            RAISE EXCEPTION 'Parent content type does not allow descendants';
        END IF;
    END IF;
    
    -- Check if this content type allows ascendants (if we have a parent)
    IF nlevel(NEW.path) > 1 THEN
        SELECT has_ascendants INTO has_asc
        FROM course_content_kind cck
        JOIN course_content_type cct ON cck.id = cct.course_content_kind_id
        WHERE cct.id = NEW.course_content_type_id;
        
        IF NOT has_asc THEN
            RAISE EXCEPTION 'Content type % does not allow ascendants', 
                           (SELECT cck.id FROM course_content_kind cck 
                            JOIN course_content_type cct ON cck.id = cct.course_content_kind_id
                            WHERE cct.id = NEW.course_content_type_id);
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_course_content_hierarchy_trigger
    BEFORE INSERT OR UPDATE ON course_content
    FOR EACH ROW EXECUTE FUNCTION validate_course_content_hierarchy();
```

#### B. Path Validation

Add constraints for proper ltree path formatting:

```sql
ALTER TABLE course_content ADD CONSTRAINT course_content_path_format
CHECK (path ~ '^[a-z0-9_]+(\.[a-z0-9_]+)*$');

-- Ensure paths are unique within course
-- (Already exists but worth emphasizing)
-- UNIQUE(course_id, path)
```

### 2. Example-CourseContent Relationship Tracking

Add explicit tracking of which examples were used to initialize content:

```sql
-- Add column to track example initialization
ALTER TABLE course_content 
ADD COLUMN initialized_from_example_id UUID REFERENCES example(id);

-- Add index for performance
CREATE INDEX idx_course_content_example ON course_content(initialized_from_example_id);

-- Add metadata to track initialization details
ALTER TABLE course_content 
ADD COLUMN initialization_metadata JSONB;
```

Benefits:
- Track which examples are being used
- Enable example usage analytics
- Support content updates when examples change
- Maintain audit trail for content origins

### 3. Simplified Management Interface

Create views and functions to simplify common operations:

#### A. Unified Content View

```sql
CREATE VIEW course_content_full AS
SELECT 
    cc.id,
    cc.course_id,
    cc.title,
    cc.description,
    cc.path,
    cc.position,
    cc.max_group_size,
    cc.submittable,
    cc.archived_at,
    -- Content type information
    cct.slug as content_type_slug,
    cct.title as content_type_title,
    cct.color as content_type_color,
    -- Content kind information  
    cck.id as content_kind,
    cck.has_ascendants,
    cck.has_descendants,
    cck.submittable as kind_submittable,
    -- Example information
    e.title as example_title,
    e.directory as example_directory,
    er.name as example_repository_name,
    -- Hierarchy helpers
    nlevel(cc.path) as depth_level,
    subltree(cc.path, 0, nlevel(cc.path) - 1) as parent_path
FROM course_content cc
JOIN course_content_type cct ON cc.course_content_type_id = cct.id
JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
LEFT JOIN example e ON cc.initialized_from_example_id = e.id
LEFT JOIN example_repository er ON e.example_repository_id = er.id;
```

#### B. Content Management Functions

```sql
-- Function to create content with proper validation
CREATE OR REPLACE FUNCTION create_course_content(
    p_course_id UUID,
    p_content_type_slug VARCHAR,
    p_title VARCHAR,
    p_parent_path LTREE DEFAULT NULL,
    p_position FLOAT DEFAULT NULL,
    p_example_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_content_type_id UUID;
    v_new_path LTREE;
    v_new_position FLOAT;
    v_content_id UUID;
BEGIN
    -- Get content type ID
    SELECT id INTO v_content_type_id
    FROM course_content_type 
    WHERE course_id = p_course_id AND slug = p_content_type_slug;
    
    IF v_content_type_id IS NULL THEN
        RAISE EXCEPTION 'Content type % not found for course %', p_content_type_slug, p_course_id;
    END IF;
    
    -- Generate path
    IF p_parent_path IS NULL THEN
        v_new_path = text2ltree(lower(regexp_replace(p_title, '[^a-zA-Z0-9]', '_', 'g')));
    ELSE
        v_new_path = p_parent_path || text2ltree(lower(regexp_replace(p_title, '[^a-zA-Z0-9]', '_', 'g')));
    END IF;
    
    -- Generate position if not provided
    IF p_position IS NULL THEN
        SELECT COALESCE(MAX(position), 0) + 10 INTO v_new_position
        FROM course_content 
        WHERE course_id = p_course_id 
        AND (p_parent_path IS NULL OR path ~ (p_parent_path::text || '.*{1}')::lquery);
    ELSE
        v_new_position = p_position;
    END IF;
    
    -- Insert content
    INSERT INTO course_content (
        course_id, course_content_type_id, title, path, position,
        initialized_from_example_id, max_group_size, version_identifier
    ) VALUES (
        p_course_id, v_content_type_id, p_title, v_new_path, v_new_position,
        p_example_id, 1, 'initial'
    ) RETURNING id INTO v_content_id;
    
    RETURN v_content_id;
END;
$$ LANGUAGE plpgsql;
```

### 4. Enhanced Path Management

#### A. Path Utilities

```sql
-- Function to move content and update all descendants
CREATE OR REPLACE FUNCTION move_course_content(
    p_content_id UUID,
    p_new_parent_path LTREE,
    p_new_position FLOAT DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    v_old_path LTREE;
    v_new_path LTREE;
    v_new_position FLOAT;
BEGIN
    -- Get current path
    SELECT path INTO v_old_path FROM course_content WHERE id = p_content_id;
    
    -- Generate new path
    v_new_path = p_new_parent_path || subltree(v_old_path, nlevel(v_old_path) - 1, nlevel(v_old_path));
    
    -- Handle position
    IF p_new_position IS NULL THEN
        SELECT COALESCE(MAX(position), 0) + 10 INTO v_new_position
        FROM course_content 
        WHERE path ~ (p_new_parent_path::text || '.*{1}')::lquery;
    ELSE
        v_new_position = p_new_position;
    END IF;
    
    -- Update this content and all descendants
    UPDATE course_content 
    SET path = v_new_path || subltree(path, nlevel(v_old_path), nlevel(path)),
        position = CASE WHEN id = p_content_id THEN v_new_position ELSE position END
    WHERE path <@ v_old_path;
END;
$$ LANGUAGE plpgsql;
```

### 5. Built-in Content Types

Create standard CourseContentKind entries with clear purposes:

```sql
-- Standard content kinds
INSERT INTO course_content_kind (id, title, description, has_ascendants, has_descendants, submittable) VALUES
('unit', 'Unit', 'A thematic unit containing related content', false, true, false),
('folder', 'Folder', 'A folder for organizing content', true, true, false),
('assignment', 'Assignment', 'A submittable assignment', true, false, true),
('quiz', 'Quiz', 'An interactive quiz', true, false, true),
('reading', 'Reading', 'Reading material or resources', true, false, false),
('lecture', 'Lecture', 'Lecture notes or materials', true, false, false);
```

### 6. API Enhancements

#### A. Simplified Content Creation API

```python
# API endpoint for creating content from examples
@router.post("/courses/{course_id}/content/from-example")
async def create_content_from_example(
    course_id: UUID,
    request: CreateContentFromExampleRequest,
    db: Session = Depends(get_db)
):
    """Create course content initialized from an example."""
    
    # Validate example exists and is accessible
    example = db.query(Example).filter(Example.id == request.example_id).first()
    if not example:
        raise HTTPException(404, "Example not found")
    
    # Create content type if it doesn't exist
    content_type = ensure_content_type(
        db, course_id, request.content_kind, request.content_type_title
    )
    
    # Create content using management function
    content_id = db.execute(
        text("SELECT create_course_content(:course_id, :slug, :title, :parent_path, :position, :example_id)"),
        {
            "course_id": course_id,
            "slug": content_type.slug,
            "title": request.title,
            "parent_path": request.parent_path,
            "position": request.position,
            "example_id": request.example_id
        }
    ).scalar()
    
    return {"content_id": content_id}
```

### 7. Monitoring and Analytics

Add views for content usage analytics:

```sql
-- Content type usage statistics
CREATE VIEW content_type_usage_stats AS
SELECT 
    c.id as course_id,
    c.title as course_title,
    cct.slug as content_type_slug,
    cct.title as content_type_title,
    cck.id as content_kind,
    COUNT(cc.id) as content_count,
    COUNT(CASE WHEN cc.archived_at IS NULL THEN 1 END) as active_content_count,
    COUNT(cc.initialized_from_example_id) as initialized_from_example_count
FROM course c
JOIN course_content_type cct ON c.id = cct.course_id
JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
LEFT JOIN course_content cc ON cct.id = cc.course_content_type_id
GROUP BY c.id, c.title, cct.id, cct.slug, cct.title, cck.id;

-- Example usage statistics
CREATE VIEW example_usage_stats AS
SELECT 
    e.id as example_id,
    e.title as example_title,
    e.directory,
    er.name as repository_name,
    COUNT(cc.id) as usage_count,
    COUNT(DISTINCT cc.course_id) as courses_using,
    MAX(cc.created_at) as last_used_at
FROM example e
JOIN example_repository er ON e.example_repository_id = er.id
LEFT JOIN course_content cc ON e.id = cc.initialized_from_example_id
GROUP BY e.id, e.title, e.directory, er.name;
```

## Implementation Plan

### Phase 1: Database Constraints (Week 1)
1. Add tree structure validation triggers
2. Add path format constraints
3. Add example tracking columns
4. Test constraint enforcement

### Phase 2: Management Functions (Week 2)
1. Create content management functions
2. Create unified views
3. Add path manipulation utilities
4. Test with sample data

### Phase 3: API Enhancements (Week 3)
1. Update content creation endpoints
2. Add example-based initialization
3. Add content moving/restructuring APIs
4. Update frontend interfaces

### Phase 4: Analytics and Monitoring (Week 4)
1. Create usage analytics views
2. Add content health monitoring
3. Create management dashboards
4. Document best practices

## Migration Strategy

### 1. Backward Compatibility
- All existing data remains valid
- New constraints only affect new content
- Existing APIs continue to work

### 2. Data Migration
```sql
-- Add new columns with defaults
ALTER TABLE course_content 
ADD COLUMN initialized_from_example_id UUID REFERENCES example(id),
ADD COLUMN initialization_metadata JSONB DEFAULT '{}';

-- Migrate existing constraints
-- (Run validation and fix any inconsistencies)
```

### 3. Gradual Rollout
1. Deploy database changes
2. Update backend APIs
3. Update frontend interfaces
4. Enable new features progressively

## Expected Benefits

### For Developers
- **Clearer relationships**: Explicit example tracking
- **Better constraints**: Database-level validation
- **Simpler APIs**: Higher-level management functions
- **Better debugging**: Clear hierarchy rules and validation

### For Course Creators
- **Easier content creation**: Template-based initialization
- **Better organization**: Clear hierarchy rules
- **Content reuse**: Track and reuse successful patterns
- **Error prevention**: Validation prevents invalid structures

### For System Administrators
- **Usage analytics**: Understand content patterns
- **System health**: Monitor constraint violations
- **Performance optimization**: Better indexing and queries
- **Migration support**: Tools for content restructuring

## Conclusion

These improvements address the main pain points in the current CourseContent hierarchy while maintaining its flexibility and power. The enhancements focus on:

1. **Constraint enforcement**: Database-level validation prevents invalid structures
2. **Relationship clarity**: Explicit tracking of example usage and initialization
3. **Management simplification**: Higher-level functions for common operations
4. **Analytics support**: Understanding usage patterns and system health

The proposed changes are backward-compatible and can be implemented incrementally, allowing for gradual adoption and testing.