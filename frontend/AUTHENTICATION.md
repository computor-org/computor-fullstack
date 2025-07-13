# Authentication System

## Overview

The Computor frontend includes a complete authentication system with login/logout functionality, session persistence, and role-based access control.

## Features

### 🔐 **User Authentication**
- Email/password login system
- Session persistence with localStorage
- Automatic token refresh
- Secure logout functionality

### 👤 **User Roles & Permissions**
- **Admin**: Full system access including user management
- **Lecturer**: Course management and student oversight
- **Student**: Assignment submission and course materials

### 🎨 **UI Components**
- Professional login modal with form validation
- Demo account chips for easy testing
- User avatar menu with context switching
- Loading states and error handling

## Demo Accounts

For testing purposes, use these credentials:

| Role | Email | Password |
|------|--------|----------|
| Admin | `admin@university.edu` | `admin123` |
| Lecturer | `lecturer@university.edu` | `lecturer123` |
| Student | `student@university.edu` | `student123` |

## Technical Implementation

### Architecture
```
hooks/useAuth.tsx     - React Context for auth state management
services/authService.ts - Mock authentication service (simulates FastAPI)
components/LoginModal.tsx - Login form component
types/auth.ts         - TypeScript type definitions
```

### Authentication Flow
1. **Initial Load**: Check localStorage for existing session
2. **Login**: Validate credentials and store session
3. **Token Refresh**: Automatically refresh expired tokens
4. **Logout**: Clear session and redirect to login

### State Management
- Uses React Context + useReducer for state management
- Persistent session storage with automatic restoration
- Loading states for smooth UX transitions
- Error handling with user-friendly messages

### Testing
- Comprehensive unit tests for AuthService
- React Testing Library tests for useAuth hook
- Mock localStorage for isolated testing
- 18 test cases covering all authentication scenarios

## Integration with Sidebar

The authentication system seamlessly integrates with the configurable sidebar:
- Context switching based on user permissions
- Role-specific menu visibility
- Dynamic navigation based on user access level
- Automatic sidebar updates when user changes

## Future FastAPI Integration

The current mock service can be easily replaced with real FastAPI endpoints:
- Replace `AuthService.login()` with API calls
- Update token refresh logic for real JWT handling  
- Add proper error handling for network issues
- Implement secure token storage mechanisms

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