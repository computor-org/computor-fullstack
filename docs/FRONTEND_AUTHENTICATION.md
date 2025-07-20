# Frontend Authentication System

## Overview

The Computor frontend includes a comprehensive authentication system supporting both SSO (Single Sign-On) and Basic authentication methods, with login/logout functionality, session persistence, and role-based access control.

## Features

### 🔐 **User Authentication**
- Dual authentication support: SSO (Keycloak) and Basic Auth
- Email/password login system
- Session persistence with localStorage
- Automatic token refresh for SSO tokens
- Secure logout functionality
- Authentication method switching

### 👤 **User Roles & Permissions**
- **Admin**: Full system access including user management
- **Lecturer**: Course management and student oversight
- **Student**: Assignment submission and course materials

### 🎨 **UI Components**
- SSO login modal with authentication method selection
- Basic authentication form with email/password
- Professional login modal with form validation
- User avatar menu with context switching
- Loading states and error handling
- Auto-redirect after successful authentication

## Demo Accounts

### Basic Authentication
| Role | Username/Email | Password |
|------|----------------|----------|
| Admin | `admin` or `admin@computor.com` | `admin` |

### SSO Authentication (Keycloak)
| Role | Username | Password |
|------|----------|----------|
| Demo User | `demo_user` | `password` |
| Demo Admin | `demo_admin` | `password` |

## Technical Implementation

### Architecture
```
hooks/useAuth.tsx          - React Context for auth state management
services/ssoAuthService.ts - SSO authentication service (Keycloak)
services/basicAuthService.ts - Basic authentication service
services/apiClient.ts      - Unified API client with auth support
components/SSOLoginModal.tsx - SSO login with method selection
components/SSOCallback.tsx - SSO redirect handler
types/auth.ts             - TypeScript type definitions
```

### Authentication Flow

#### SSO Flow (Keycloak)
1. **Initial Load**: Check localStorage for existing SSO token
2. **Login**: Redirect to Keycloak login page
3. **Callback**: Handle redirect with authorization code
4. **Token Exchange**: Exchange code for access/refresh tokens
5. **Token Refresh**: Automatically refresh expired tokens
6. **Logout**: Clear session and redirect to login

#### Basic Auth Flow
1. **Initial Load**: Check localStorage for Basic auth token
2. **Login**: Send credentials to /auth/me endpoint
3. **Validation**: Verify credentials and store encoded token
4. **Logout**: Clear session from localStorage

### State Management
- Uses React Context + useReducer for state management
- Persistent session storage with automatic restoration
- Loading states for smooth UX transitions
- Error handling with user-friendly messages

### API Integration
The authentication system integrates with the backend API:
- `apiClient` automatically includes authentication headers
- Supports both `Bearer` (SSO) and `Basic` authentication
- Handles 401 responses with automatic token refresh (SSO)
- Seamless switching between authentication methods

## Integration with Sidebar

The authentication system seamlessly integrates with the configurable sidebar:
- Context switching based on user permissions
- Role-specific menu visibility
- Dynamic navigation based on user access level
- Automatic sidebar updates when user changes

## Current Implementation Status

✅ **Fully Integrated with FastAPI Backend**:
- SSO authentication via Keycloak integration
- Basic authentication with email/password
- Token refresh mechanism for SSO
- Proper error handling for authentication failures
- Secure token storage in localStorage
- Automatic auth header injection in API calls

## Usage Example

```tsx
import { useAuth } from './hooks/useAuth';

function MyComponent() {
  const { state, login, logout } = useAuth();

  if (state.isLoading) return <Loading />;
  if (!state.isAuthenticated) return <LoginForm />;
  
  return (
    <div>
      Welcome, {state.user?.givenName}!
      <button onClick={logout}>Sign Out</button>
    </div>
  );
}
```

## Security Features

- Password validation with proper error messages
- Token expiration handling
- Automatic session cleanup on logout
- Role-based permission checking
- Secure credential storage simulation