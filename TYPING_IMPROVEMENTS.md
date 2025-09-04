# Relationship Typing Improvements

## What Was Fixed

Replaced generic `Dict[str, Any]` types with proper Pydantic model types for relationships in the interface files.

## Changes Made

### 1. `src/ctutor_backend/interface/deployment.py`

**Before:**
```python
# Relationships (optionally loaded)
example_version: Optional[Dict[str, Any]] = None
course_content: Optional[Dict[str, Any]] = None
```

**After:**
```python
# Relationships (optionally loaded)
example_version: Optional['ExampleVersionGet'] = None
course_content: Optional['CourseContentGet'] = None
```

### 2. `src/ctutor_backend/interface/course_contents.py`

**Before:**
```python
# Optional deployment summary (populated when requested)
deployment: Optional[Dict[str, Any]] = Field(
    None,
    description="Deployment information if requested via include=deployment"
)
```

**After:**
```python
# Optional deployment summary (populated when requested)
deployment: Optional['CourseContentDeploymentGet'] = Field(
    None,
    description="Deployment information if requested via include=deployment"
)
```

## Benefits

1. **Type Safety**: IDEs can now provide proper autocomplete and type checking
2. **Better Documentation**: Developers can see exactly what fields are available
3. **Compile-time Checking**: Type checkers like mypy can catch errors early
4. **Improved Maintainability**: Changes to related models are automatically reflected

## Pattern Used

To avoid circular imports, we use:
1. `TYPE_CHECKING` import guard for type hints only
2. Forward references with string literals (`'ClassName'`)

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .other_module import OtherClass

class MyClass:
    # Use forward reference with quotes
    other: Optional['OtherClass'] = None
```

This ensures:
- Types are available for static analysis
- No circular import issues at runtime
- Clean, maintainable code