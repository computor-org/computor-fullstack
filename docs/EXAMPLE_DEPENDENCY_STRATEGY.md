# Example Dependency and Version Management Strategy

## Overview

This document describes how example dependencies are managed in the Computor platform, including version resolution strategies and future enhancements for version ranges.

## Current Implementation

### Dependency Declaration

Dependencies are declared in the example's `meta.yaml` file using the `testDependencies` field:

```yaml
title: "Matrix Operations"
description: "Example demonstrating matrix operations"
testDependencies:
  - "itpcp.pgph.mat.basic_functions"
  - "itpcp.pgph.mat.vector_operations"
```

### Dependency Storage

Dependencies are stored in the `example_dependency` table which tracks:
- `example_id`: The example that has dependencies
- `depends_id`: The example it depends on
- Created timestamp

### Current Behavior

1. **Simple Model**: Dependencies refer to the example level, not specific versions
2. **Latest Version**: When resolving dependencies, the system uses the latest version of the dependency
3. **Same Repository**: Dependencies must be within the same example repository
4. **Update on Upload**: Dependencies are updated each time a new version is uploaded

## Version Resolution Challenges

### Problem 1: Breaking Changes
When a dependency example gets a new version with breaking changes, dependent examples might break.

### Problem 2: Version Compatibility
Different examples might need different versions of the same dependency.

### Problem 3: Transitive Dependencies
Dependencies can have their own dependencies, creating a dependency tree.

## Proposed Version Management Strategy

### Phase 1: Version Pinning (Short-term)

Add version information to dependencies:

```yaml
testDependencies:
  - identifier: "itpcp.pgph.mat.basic_functions"
    version: "v1.0"  # Exact version
```

Database changes:
```sql
ALTER TABLE example_dependency ADD COLUMN version_constraint VARCHAR(64);
```

### Phase 2: Version Ranges (Medium-term)

Support semantic versioning ranges:

```yaml
testDependencies:
  - identifier: "itpcp.pgph.mat.basic_functions"
    version: "^1.0"  # Compatible with 1.x
  - identifier: "itpcp.pgph.mat.vector_operations"
    version: ">=2.0 <3.0"  # Range specification
```

Version range syntax:
- `^1.2.3` - Compatible with version (1.x.x)
- `~1.2.3` - Approximately equivalent (1.2.x)
- `>=1.0 <2.0` - Range specification
- `*` or not specified - Any version (current behavior)

### Phase 3: Dependency Resolution (Long-term)

Implement a dependency resolver that:
1. Builds a dependency graph
2. Resolves version conflicts
3. Ensures all constraints are satisfied
4. Provides clear error messages for conflicts

## Implementation Approach

### 1. Backward Compatibility

Maintain compatibility with existing `testDependencies` arrays:

```python
# Parse both old and new formats
if isinstance(dep, str):
    # Old format: just identifier
    dependency_id = dep
    version_constraint = "*"
elif isinstance(dep, dict):
    # New format: with version
    dependency_id = dep['identifier']
    version_constraint = dep.get('version', '*')
```

### 2. Version Resolution Algorithm

```python
def resolve_dependency_version(example_id: str, version_constraint: str) -> ExampleVersion:
    """Resolve which version of a dependency to use."""
    example = get_example_by_identifier(example_id)
    versions = get_example_versions(example)
    
    if version_constraint == "*":
        # Use latest version
        return max(versions, key=lambda v: v.version_number)
    
    # Parse semantic version constraint
    constraint = parse_version_constraint(version_constraint)
    
    # Find matching versions
    matching = [v for v in versions if constraint.matches(v.version_tag)]
    
    if not matching:
        raise VersionConflict(f"No version of {example_id} matches {version_constraint}")
    
    # Return highest matching version
    return max(matching, key=lambda v: v.version_number)
```

### 3. Deployment Considerations

When deploying examples with dependencies:

1. **Lock File Generation**: Create a lock file recording exact versions used
2. **Reproducible Builds**: Ensure same versions are used in student templates
3. **Conflict Detection**: Warn about potential conflicts before deployment

### 4. Migration Path

1. **Phase 1**: Update upload endpoint to parse version constraints
2. **Phase 2**: Add version resolution logic to template generation
3. **Phase 3**: Implement full dependency resolver
4. **Phase 4**: Add UI for dependency management

## Example Scenarios

### Scenario 1: Function Library Update

```yaml
# basic_functions v1.0
functions:
  - add(a, b)
  - multiply(a, b)

# basic_functions v2.0 (breaking change)
functions:
  - add(a, b, c=0)  # Added parameter
  - multiply(a, b)
```

Examples depending on v1.0 need to pin version or update code.

### Scenario 2: Shared Dependencies

```
Example A → basic_functions ^1.0
Example B → basic_functions ^2.0
Course uses both A and B → Conflict!
```

Resolution: Deploy separate versions or update Example A.

### Scenario 3: Diamond Dependency

```
Example A → B ^1.0, C ^1.0
Example B → D ^1.0
Example C → D ^2.0
```

Resolver must find compatible D version or report conflict.

## Benefits

1. **Stability**: Examples won't break when dependencies update
2. **Flexibility**: Can use different versions for different contexts
3. **Clarity**: Clear specification of requirements
4. **Safety**: Conflicts detected before deployment

## Future Enhancements

1. **Dependency Graph Visualization**: Show dependency relationships in UI
2. **Auto-update Tool**: Suggest safe dependency updates
3. **Version Compatibility Matrix**: Track which versions work together
4. **Dependency Bundling**: Package dependencies with examples for offline use

## Implementation Timeline

1. **Immediate**: Parse and store dependencies (completed)
2. **Q1 2025**: Add version constraints to database
3. **Q2 2025**: Implement basic version resolution
4. **Q3 2025**: Full dependency resolver with conflict detection
5. **Q4 2025**: UI tools for dependency management