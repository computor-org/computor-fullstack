# TypeScript Interface Generation from Pydantic Models

## Overview

This project includes an automatic TypeScript interface generator that creates type-safe interfaces from Python Pydantic models. This ensures perfect type synchronization between the backend API and frontend React application.

## Features

- **Automatic Type Conversion**: Converts Python types to TypeScript equivalents
- **Pydantic Support**: Full support for Pydantic BaseModel classes
- **Field Descriptions**: Preserves field descriptions as JSDoc comments
- **Optional Fields**: Correctly handles optional fields with `?` notation
- **Complex Types**: Supports Lists, Dicts, Unions, and nested models
- **Category Organization**: Groups interfaces by domain (auth, users, courses, etc.)
- **CLI Integration**: Available as a CLI command with watch mode

## Usage

### Quick Start

Generate TypeScript interfaces:

```bash
# From project root
bash scripts/utilities/generate_types.sh

# Or using the CLI directly
cd src && ctutor generate-types
```

### CLI Options

```bash
# Generate with custom output directory
ctutor generate-types -o /path/to/output

# Watch mode - regenerate on Python file changes
ctutor generate-types --watch

# Clean output directory before generating
ctutor generate-types --clean
```

### Generated Files

The generator creates the following structure:

```
frontend/src/types/generated/
├── auth.ts          # Authentication interfaces
├── users.ts         # User and account interfaces
├── courses.ts       # Course-related interfaces
├── organizations.ts # Organization interfaces
├── roles.ts         # Roles and permissions
├── sso.ts          # SSO provider interfaces
├── tasks.ts        # Task and job interfaces
├── common.ts       # Shared/common interfaces
├── index.ts        # Barrel export file
└── README.md       # Documentation
```

## Type Mappings

| Python Type | TypeScript Type |
|------------|-----------------|
| `str` | `string` |
| `int` | `number` |
| `float` | `number` |
| `bool` | `boolean` |
| `datetime` | `string` (ISO format) |
| `UUID` | `string` |
| `List[T]` | `T[]` |
| `Dict[K, V]` | `Record<K, V>` |
| `Optional[T]` | `T \| null` |
| `Union[A, B]` | `A \| B` |
| `Any` | `any` |

## Example Usage in React

### Import Generated Types

```typescript
import { 
  UserRegistrationRequest, 
  UserRegistrationResponse 
} from '@/types/generated/users';

import { 
  TokenRefreshRequest, 
  TokenRefreshResponse 
} from '@/types/generated/auth';
```

### Use in Components

```typescript
const RegisterForm: React.FC = () => {
  const [formData, setFormData] = useState<UserRegistrationRequest>({
    username: '',
    email: '',
    password: '',
    given_name: '',
    family_name: '',
    provider: 'keycloak',
    send_verification_email: true,
  });

  const handleSubmit = async (data: UserRegistrationRequest) => {
    const response = await apiClient.post<UserRegistrationResponse>(
      '/auth/register',
      data
    );
    
    // TypeScript knows all the fields
    console.log(response.user_id);
    console.log(response.message);
  };
};
```

### Type-Safe API Calls

```typescript
// API client with generated types
class TypedAPIClient {
  async registerUser(
    data: UserRegistrationRequest
  ): Promise<UserRegistrationResponse> {
    return this.post('/auth/register', data);
  }

  async refreshToken(
    data: TokenRefreshRequest
  ): Promise<TokenRefreshResponse> {
    return this.post('/auth/refresh', data);
  }

  async getProviders(): Promise<ProviderInfo[]> {
    return this.get('/auth/providers');
  }
}
```

## Adding New Models

1. **Create Pydantic Model** in Python:

```python
# src/ctutor_backend/interface/example.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ExampleRequest(BaseModel):
    """Request for example endpoint."""
    name: str = Field(..., description="Name of the example")
    count: int = Field(1, ge=1, description="Number of items")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

2. **Run Generator**:

```bash
bash scripts/utilities/generate_types.sh
```

3. **Use in Frontend**:

```typescript
import { ExampleRequest } from '@/types/generated/common';

const example: ExampleRequest = {
  name: "Test",
  count: 5,
  tags: ["tag1", "tag2"],
  created_at: new Date().toISOString()
};
```

## Best Practices

### 1. Keep Models Simple

- Use clear, descriptive field names
- Add field descriptions for better documentation
- Avoid complex nested structures when possible

### 2. Use Enums

```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserCreate(BaseModel):
    role: UserRole = Field(..., description="User role")
```

Generated TypeScript:
```typescript
type UserRole = "admin" | "user" | "guest";

interface UserCreate {
  /** User role */
  role: UserRole;
}
```

### 3. Consistent Naming

- Use consistent naming conventions
- Model names should be descriptive
- Group related models in the same file

### 4. Version Control

- Generated files are included in version control
- Regenerate after model changes
- Review generated changes in PRs

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/types.yml
name: Generate TypeScript Types

on:
  push:
    paths:
      - 'src/ctutor_backend/interface/**'
      - 'src/ctutor_backend/api/**'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r src/requirements.txt
      
      - name: Generate types
        run: |
          bash scripts/utilities/generate_types.sh
      
      - name: Check for changes
        run: |
          git diff --exit-code frontend/src/types/generated/
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all Python dependencies are installed
   - Check that models inherit from `pydantic.BaseModel`

2. **Missing Types**
   - Verify the model is in a scanned directory
   - Check for syntax errors in Python files

3. **Type Conversion Issues**
   - Complex types may need manual adjustment
   - Check the type mapping table above

### Debug Mode

Run with verbose output:

```python
# In generate_typescript_interfaces.py
generator = TypeScriptGenerator()
generator.debug = True  # Add debug flag
```

## Future Enhancements

1. **Enum Support**: Better handling of Python enums
2. **Validation Rules**: Include Pydantic validation rules as JSDoc
3. **API Client Generation**: Generate typed API client methods
4. **GraphQL Support**: Generate GraphQL types
5. **Real-time Updates**: WebSocket support for live type updates

## Contributing

When adding new Pydantic models:

1. Place them in `src/ctutor_backend/interface/` or `src/ctutor_backend/api/`
2. Run `bash scripts/utilities/generate_types.sh`
3. Commit both Python models and generated TypeScript
4. Update frontend code to use new types

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [React TypeScript Guide](https://react-typescript-cheatsheet.netlify.app/)