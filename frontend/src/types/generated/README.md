# Generated TypeScript Interfaces

This directory contains auto-generated TypeScript interfaces from Python Pydantic models.

**DO NOT EDIT THESE FILES MANUALLY** - They will be overwritten on the next generation.

## Generation

To regenerate these interfaces, run:

```bash
cd src
python ctutor_backend/scripts/generate_typescript_interfaces.py
```

## Categories

- **auth.ts** - Authentication related interfaces (login, tokens, etc.)
- **users.ts** - User and account interfaces
- **courses.ts** - Course related interfaces
- **organizations.ts** - Organization interfaces
- **roles.ts** - Roles and permissions interfaces
- **sso.ts** - SSO provider interfaces
- **tasks.ts** - Task and job interfaces  
- **common.ts** - Common/shared interfaces

## Usage

Import the interfaces in your TypeScript code:

```typescript
import { User, Account } from '@/types/generated/users';
import { LoginRequest, AuthResponse } from '@/types/generated/auth';
```

Generated on: 2025-08-06T16:59:59.149955
