# Student Template Directory Structure

This document defines how example assignments are organized in the student-template repository.

## Overview

The student-template repository uses a **flat directory structure** based on example identifiers, not the hierarchical CourseContent paths. This provides a cleaner, more maintainable structure for students.

## Current vs. Required Behavior

### ❌ Current Behavior (Tree Structure)
```
student-template/
├── week_1/
│   └── aufgabe_1/
│       ├── main.py
│       └── README.md
├── week_2/
│   └── aufgabe_2/
│       ├── solution.py
│       └── meta.yaml
└── final_project/
    └── implementation/
        └── ...
```

### ✅ Required Behavior (Flat Structure)
```
student-template/
├── python-basics-hello-world/     # Example identifier as directory
│   ├── main.py
│   └── README.md
├── python-loops-fibonacci/        # Example identifier as directory
│   ├── solution.py
│   └── meta.yaml
├── advanced-algorithms-sorting/   # Example identifier as directory
│   └── ...
└── README.md
```

## Implementation Requirements

### CourseContent Properties Enhancement

The `CourseContentProperties` model in `src/ctutor_backend/interface/course_contents.py` must be extended to store directory mapping information:

```python
class CourseContentProperties(BaseModel):
    gitlab: Optional[GitLabConfig] = None
    
    # Example deployment properties
    directory: Optional[str] = None  # Target directory name in student-template
    example_identifier: Optional[str] = None  # Example identifier from Example Library
    deployment_config: Optional[dict] = None  # Additional deployment configuration
    
    model_config = ConfigDict(extra='allow')
```

### Directory Resolution Logic

The student template generation workflow should determine directory names using this hierarchy:

1. **`properties.directory`** - Explicit directory override
2. **Example identifier** - From the Example Library (`example.identifier`)
3. **Fallback** - Sanitized version of `course_content.title`

### Example Directory Mapping

| CourseContent Path | Example Identifier | Directory Name | Source |
|-------------------|-------------------|----------------|---------|
| `week_1.aufgabe_1` | `python-hello-world` | `python-hello-world` | Example identifier |
| `week_2.loops` | `fibonacci-sequence` | `fibonacci-sequence` | Example identifier |
| `final.project` | `web-scraper-advanced` | `web-scraper-advanced` | Example identifier |
| `custom.assignment` | `null` | `custom_assignment` | Fallback from title |

## Workflow Changes Required

### Current Workflow Logic
```python
# ❌ Creates tree structure from course content path
content_path_str = str(content.path)
target_path = Path(template_staging_path) / content_path_str.replace('.', '/')
```

### Required Workflow Logic
```python
# ✅ Uses flat structure with example identifier
directory_name = get_student_template_directory_name(content, example)
target_path = Path(template_staging_path) / directory_name

def get_student_template_directory_name(content: CourseContent, example: Example) -> str:
    """Determine directory name for student template."""
    
    # 1. Check for explicit directory override
    if (content.properties and 
        content.properties.get('directory')):
        return content.properties['directory']
    
    # 2. Use example identifier
    if example and example.identifier:
        return example.identifier
    
    # 3. Fallback to sanitized content title
    if content.title:
        return sanitize_directory_name(content.title)
    
    # 4. Ultimate fallback
    return f"assignment_{content.id[:8]}"

def sanitize_directory_name(name: str) -> str:
    """Convert title to valid directory name."""
    import re
    # Replace spaces and special chars with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '-', name.lower())
    # Remove multiple consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing hyphens
    return sanitized.strip('-')
```

## Benefits of Flat Structure

### ✅ Advantages
- **Simpler Navigation** - Students don't need to navigate nested directories
- **Clear Naming** - Directory names directly reflect assignment content
- **Better Organization** - Each assignment is self-contained
- **IDE Friendly** - Easier to work with in development environments
- **Version Control** - Cleaner git history and conflict resolution

### ❌ Previous Issues with Tree Structure  
- **Deep Nesting** - Complex paths like `week_1/aufgabe_1/sub_task/`
- **Path Dependencies** - Changes to course structure affect directory paths
- **Navigation Complexity** - Students get lost in hierarchical structure
- **Inconsistent Naming** - Technical path names vs. human-readable content

## Database Schema Considerations

### CourseContent.properties JSON Structure
```json
{
  "gitlab": {
    "url": "...",
    "token": "..."
  },
  "directory": "python-basic-calculator",
  "example_identifier": "python-basic-calculator", 
  "deployment_config": {
    "include_tests": false,
    "student_files_only": true
  }
}
```

### Example Assignment Workflow
1. **Course Content Created** - Points to example via `example_id`
2. **Directory Determined** - Using hierarchy: properties.directory → example.identifier → fallback
3. **Template Generated** - Files placed in flat directory structure
4. **Student Repository** - Clean, navigable structure for students

## Migration Strategy

### For Existing Courses
1. **Audit Current Structure** - Identify all course contents with examples
2. **Map Directories** - Determine appropriate directory names for each assignment
3. **Update Properties** - Populate `CourseContentProperties.directory` fields
4. **Regenerate Templates** - Run student template generation with new structure
5. **Communicate Changes** - Notify instructors and students of new structure

### For New Courses
- **Automatic Directory Assignment** - Use example identifiers by default
- **Override Capability** - Allow instructors to specify custom directory names
- **Validation** - Ensure directory names are unique within a course

## File Organization Within Directories

Each assignment directory should contain:
- **Assignment files** - Based on `meta.yaml` configuration
- **README.md** - Assignment description and instructions  
- **meta.yaml** - Assignment metadata (student-safe version)
- **Template files** - Starter code and resources
- **No test files** - Tests remain in instructor repositories

## Validation Rules

### Directory Name Requirements
- **Unique per course** - No duplicate directory names
- **Valid filesystem names** - No invalid characters
- **Reasonable length** - Max 50 characters recommended
- **Descriptive** - Should indicate assignment content

### Conflict Resolution
If directory names conflict:
1. **Explicit properties.directory** takes precedence
2. **Add suffix** - Append `-2`, `-3`, etc.
3. **Log warnings** - Alert administrators to conflicts
4. **Maintain mapping** - Track original vs. resolved names

## Implementation Timeline

1. **Phase 1** - Update CourseContentProperties model
2. **Phase 2** - Implement directory resolution logic
3. **Phase 3** - Update student template workflow
4. **Phase 4** - Add validation and conflict resolution
5. **Phase 5** - Migration tools for existing courses
6. **Phase 6** - Documentation and training materials

## Testing Strategy

- **Unit tests** - Directory name resolution logic
- **Integration tests** - Full workflow with various scenarios
- **Edge cases** - Conflict resolution, missing data, invalid names
- **Migration tests** - Existing course conversion accuracy
- **User acceptance** - Instructor and student feedback on usability