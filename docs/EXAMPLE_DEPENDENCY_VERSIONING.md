# Example Dependency Versioning System

**Status:** ✅ Implemented  
**Date:** August 5, 2025  
**Version:** 1.0.0

## Overview

This document describes the complete example dependency versioning system implemented for the Computor platform. The system allows examples to declare dependencies on other examples with flexible version constraints, supporting both backward-compatible string formats and structured version constraints.

## Architecture

### Database Schema

#### ExampleDependency Table
```sql
CREATE TABLE example_dependency (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    example_id UUID NOT NULL REFERENCES example(id) ON DELETE CASCADE,
    depends_id UUID NOT NULL REFERENCES example(id) ON DELETE CASCADE,
    version_constraint VARCHAR(100) NULL,  -- New field
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE(example_id, depends_id)
);
```

**Key Fields:**
- `version_constraint`: Optional version constraint string (e.g., `>=1.2.0`, `^2.1.0`)
- `NULL` value means "latest version" (backward compatible)

### Meta.yaml Integration

#### Flexible TestDependency Format
The system supports both legacy string format and new structured format:

```yaml
# Legacy format (backward compatible)
testDependencies:
  - "physics.math.vectors"        # = latest version
  - "common.utilities"            # = latest version

# New structured format
testDependencies:
  - slug: "physics.math.vectors"
    version: ">=1.2.0"            # Minimum version
  - slug: "physics.constants"
    version: "1.0.0"              # Exact version
  - slug: "common.utilities"
    version: "^2.1.0"             # Compatible version range

# Mixed format (both in same file)
testDependencies:
  - "physics.utils.helpers"       # String = latest
  - slug: "advanced.algorithms"   # Structured with constraint
    version: "~2.3.0"
```

#### TestDependency Pydantic Model
```python
class TestDependency(BaseModel):
    slug: str = Field(..., description="Hierarchical slug of dependency")
    version: Optional[str] = Field(None, description="Version constraint")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        # Ensures hierarchical format (e.g., 'domain.subdomain.name')
        parts = v.split('.')
        if len(parts) < 2:
            raise ValueError("Slug must be hierarchical")
        return v
```

## Version Resolution Strategy

### Database-Level Ordering Approach

Instead of parsing arbitrary version tag strings, the system uses the existing `version_number` field for proper ordering:

#### Key Concept:
- **version_tag**: Human-readable string (`"v1.0"`, `"spring-2024"`, `"latest"`, `"beta-3"`)
- **version_number**: Integer defining chronological order (1, 2, 3, 4...)
- **Constraints reference tag names, ordering uses numbers**

#### Resolution Process:
```python
# Step 1: Find target version by version_tag
target_version = find_exact_version("spring-2024", versions)
target_number = target_version.version_number  # e.g., 3

# Step 2: Apply constraint using version_number
if constraint == ">=spring-2024":
    candidates = [v for v in versions if v.version_number >= 3]
    return min(candidates, key=lambda v: v.version_number)  # Oldest match
```

#### Example Database State:
```
version_tag     | version_number | Constraint Result
"alpha-1"      | 1              | 
"beta-2"       | 2              | 
"spring-2024"  | 3              | >=spring-2024 → returns this
"summer-2024"  | 4              | >spring-2024  → returns this
"v1.0"         | 5              | <=v1.0        → returns this (newest ≤)
"v1.1"         | 6              |
```

### Supported Constraint Operators

| Operator | Description | Example | Behavior |
|----------|-------------|---------|----------|
| `>=1.2.0` | Minimum version | Returns oldest version with number ≥ target |
| `<=2.0.0` | Maximum version | Returns newest version with number ≤ target |
| `>1.0.0` | Greater than | Returns oldest version with number > target |
| `<3.0.0` | Less than | Returns newest version with number < target |
| `^2.1.0` | Compatible range | SemVer-aware major version compatibility |
| `~1.3.0` | Patch compatible | SemVer-aware minor.patch compatibility |
| `==1.0.0` | Exact match | Returns exact version_tag match |
| `1.0.0` | Exact (no operator) | Returns exact version_tag match |
| (none) | Latest version | Returns highest version_number |

### Advanced Operators (^ and ~)

For SemVer-compatible tags, the system attempts semantic parsing:
```python
# ^2.1.0 with SemVer tags
try:
    target_major = parse_version("2.1.0").major  # 2
    # Find versions with same major (2.x.x) and >= version_number
except:
    # Fallback to >= constraint for non-SemVer tags
```

## Services and Components

### 1. VersionResolver Service
**File:** `src/ctutor_backend/services/version_resolver.py`

**Purpose:** Resolves version constraints to specific ExampleVersion objects

**Key Methods:**
- `resolve_constraint(slug, constraint)` - Main resolution entry point
- `_find_version_with_number_constraint()` - Database-level ordering logic
- `_find_compatible_version()` - ^ operator support
- `_find_patch_compatible_version()` - ~ operator support

### 2. DependencySyncService  
**File:** `src/ctutor_backend/services/dependency_sync.py`

**Purpose:** Syncs testDependencies from meta.yaml to database records

**Key Methods:**
- `sync_dependencies_from_meta()` - Main sync logic
- `_parse_test_dependencies()` - Handles mixed string/object format
- `_is_valid_version_constraint()` - Basic constraint validation

### 3. API Integration

#### Upload Endpoint Enhancement
The example upload endpoint automatically syncs dependencies:
```python
# Parse testDependencies from meta.yaml
test_dependencies = meta_data.get('testDependencies', [])

# Sync to database with version constraints
dependency_sync = DependencySyncService(db)
dependency_sync.sync_dependencies_from_meta(
    example=example,
    test_dependencies=test_dependencies,  
    repository_id=repository.id
)
```

#### Download Endpoint Enhancement
The download endpoint uses version constraints:
```python
# Get dependencies with constraints
dependencies = get_all_dependencies_with_constraints(example.id)
version_resolver = VersionResolver(db)

for dep_example_id, version_constraint in dependencies:
    # Resolve constraint to specific version
    dep_version = version_resolver.resolve_constraint(
        str(dep_example.identifier),
        version_constraint  # Uses database-level ordering
    )
```

#### New CRUD Endpoints
```http
GET    /examples/{id}/dependencies           # List dependencies with constraints
POST   /examples/{id}/dependencies           # Create dependency with constraint  
DELETE /examples/{id}/dependencies/{dep_id}  # Remove dependency
```

## Complete Pipeline

```
📝 meta.yaml → ⚙️ Upload API → 🗄️ Database → 📥 Download API → 📦 ZIP
```

**Detailed Flow:**
1. **Upload**: Parse `testDependencies` from meta.yaml (both formats)
2. **Validation**: Ensure all dependency slugs exist in same repository
3. **Sync**: Create `ExampleDependency` records with version constraints
4. **Download**: Resolve constraints using database ordering
5. **Package**: Include resolved dependencies in flat ZIP structure

## Frontend Integration

### Download Dialog Enhancement
**File:** `frontend/src/components/ExamplesTable.tsx`

**Features:**
- Conditional dialog only when example has dependencies
- User choice to include/exclude dependencies via checkbox
- Flat directory structure using identifier names
- Clear messaging about dependency inclusion

**Download Structure:**
```
example-main-identifier/
├── main.py
├── meta.yaml
└── test.yaml
dependency-1-identifier/
├── helper.py
├── meta.yaml
└── test.yaml
dependency-2-identifier/
├── utils.py
└── meta.yaml
```

## Benefits and Advantages

### ✅ Flexibility
- **Any Version Tag Format**: Supports `"v1.0"`, `"spring-2024"`, `"latest"`, `"beta-3"`
- **Mixed Formats**: String and structured dependencies in same file
- **Arbitrary Constraints**: Database ordering works with any naming scheme

### ✅ Reliability  
- **Predictable Ordering**: Database `version_number` controls sequence
- **No Parse Failures**: No dependency on version string parsing
- **Backward Compatible**: Existing exact matches continue working

### ✅ Performance
- **Database Queries**: Efficient constraint resolution using indexes
- **No String Parsing**: Runtime resolution uses integer comparisons
- **Caching Ready**: Results can be easily cached

### ✅ User Experience
- **Intuitive Constraints**: Natural version references in meta.yaml
- **Clear Error Messages**: Helpful validation during upload
- **Conditional Downloads**: Smart frontend dependency inclusion

## Migration and Compatibility

### Database Migration
The `version_constraint` field was added to the initial schema migration, ensuring:
- **No Migration Conflicts**: Clean linear migration history  
- **Fresh Installs**: New databases have complete schema from start
- **Existing Data**: NULL constraints mean "latest version" (backward compatible)

### Legacy Support
- **String Format**: Existing `testDependencies: ["slug1", "slug2"]` continue working
- **Null Constraints**: Empty version constraints default to latest version
- **API Compatibility**: All existing endpoints remain functional

## Future Enhancements

### Potential Improvements
1. **Version Validation**: Stricter constraint format validation during upload
2. **Dependency Graphs**: Visual representation of dependency trees  
3. **Circular Detection**: Enhanced circular dependency detection
4. **Version Suggestions**: UI hints for available versions during constraint definition
5. **Bulk Operations**: API endpoints for batch dependency management

### Configuration Options
```yaml
# Future repository-level configuration
versionScheme: "semantic"  # semantic, date, custom
constraintValidation: "strict"  # strict, permissive
circularDependencyPolicy: "error"  # error, warning, allow
```

## Conclusion

The Example Dependency Versioning System provides a robust, flexible, and user-friendly approach to managing dependencies between examples. By leveraging database-level ordering instead of string parsing, the system supports arbitrary version naming schemes while maintaining predictable behavior and excellent performance.

The system successfully balances:
- **Developer Experience**: Natural constraint syntax in meta.yaml
- **System Reliability**: Database-driven ordering and validation  
- **Backward Compatibility**: Existing workflows remain unchanged
- **Future Flexibility**: Extensible design for additional features

This implementation establishes a solid foundation for complex dependency management in educational programming environments.