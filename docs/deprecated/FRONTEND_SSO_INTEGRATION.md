# Frontend SSO Integration Guide

## Overview

This guide explains how to integrate the SSO authentication system with the React frontend application.

## Architecture

### Components

1. **SSOAuthService** (`services/ssoAuthService.ts`)
   - Handles SSO authentication flow
   - Manages tokens in localStorage
   - Provides token refresh functionality
   - Interfaces with backend SSO endpoints

2. **SSOCallback** (`components/SSOCallback.tsx`)
   - Handles redirect from SSO provider
   - Processes authentication tokens
   - Updates auth context

3. **SSOLoginModal** (`components/SSOLoginModal.tsx`)
   - Shows available SSO providers
   - Initiates SSO login flow
   - Fallback to basic auth if needed

4. **APIClient** (`services/apiClient.ts`)
   - Automatically includes Bearer tokens in requests
   - Handles token refresh on 401 responses
   - Provides typed API methods

## Implementation Steps

### 1. Update Environment Variables

Create `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

### 2. Replace Mock Auth Service

Update `useAuth.tsx` to use the SSO service:

```typescript
// In useAuth.tsx, replace imports
import { SSOAuthService as AuthService } from '../services/ssoAuthService';
```

### 3. Update Login Modal

Replace the existing LoginModal with SSOLoginModal in App.tsx:

```typescript
import SSOLoginModal from './components/SSOLoginModal';

// In the component
<SSOLoginModal open={loginModalOpen} onClose={() => setLoginModalOpen(false)} />
```

### 4. Handle SSO Redirects

The app already includes routes for SSO callbacks:
- `/auth/success` - Default success redirect
- `/auth/callback` - Alternative callback path

## Authentication Flow

### Login Flow

1. User clicks "Login with Keycloak"
2. Browser redirects to Keycloak login page
3. User enters credentials
4. Keycloak redirects back with tokens
5. SSOCallback component processes tokens
6. User is logged in and redirected to original page

### Token Management

```typescript
// Tokens are automatically included in API calls
const courses = await apiClient.get('/courses');

// Manual token access if needed
const token = SSOAuthService.getStoredToken();
```

### Token Refresh

The API client automatically refreshes tokens:

1. API call returns 401
2. Client attempts token refresh
3. If successful, retries the API call
4. If refresh fails, redirects to login

## Usage Examples

### Making Authenticated API Calls

```typescript
import { apiClient } from '../services/apiClient';

// GET request
const courses = await apiClient.get<Course[]>('/courses');

// POST request
const newCourse = await apiClient.post('/courses', {
  name: 'Advanced Programming',
  code: 'CS401'
});

// With error handling
try {
  const data = await apiClient.get('/protected-endpoint');
} catch (error) {
  console.error('API Error:', error);
}
```

### Using the Courses Hook

```typescript
import { useCourses } from '../hooks/useCourses';

function CoursesComponent() {
  const { courses, loading, error, refetch } = useCourses();

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <div>
      {courses.map(course => (
        <CourseCard key={course.id} course={course} />
      ))}
    </div>
  );
}
```

### Checking Authentication Status

```typescript
import { useAuth } from '../hooks/useAuth';

function ProtectedComponent() {
  const { state: authState } = useAuth();

  if (!authState.isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <div>Protected content for {authState.user?.email}</div>;
}
```

## Security Considerations

### Token Storage

- Access tokens stored in localStorage
- Refresh tokens stored separately
- Tokens cleared on logout

### CORS Configuration

Ensure your backend allows frontend origin:

```python
# In FastAPI backend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Secure Token Handling

- Tokens are only sent over HTTPS in production
- Refresh tokens are used to minimize access token exposure
- Automatic token refresh prevents unnecessary re-authentication

## Development Tips

### Testing SSO Locally

1. Start all backend services:
   ```bash
   docker-compose -f docker-compose-dev.yaml up -d
   bash api.sh
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm start
   ```

3. Access the app at `http://localhost:3000`

### Debugging

Enable debug logging:

```typescript
// In ssoAuthService.ts
console.log('SSO Debug:', {
  token: SSOAuthService.getStoredToken(),
  user: SSOAuthService.getStoredUser(),
});
```

### Mock SSO for Development

To bypass SSO during development:

```typescript
// In useAuth.tsx
const USE_MOCK_AUTH = process.env.REACT_APP_USE_MOCK_AUTH === 'true';
const AuthService = USE_MOCK_AUTH 
  ? MockAuthService 
  : SSOAuthService;
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check backend CORS configuration
   - Ensure frontend URL is allowed

2. **Token Expired**
   - Check token TTL in backend
   - Verify refresh token logic

3. **Redirect Loop**
   - Clear localStorage
   - Check callback URL configuration

4. **404 on API Calls**
   - Verify API_BASE_URL in .env
   - Check endpoint paths

### Support

For issues with:
- Frontend integration: Check browser console
- Backend SSO: Check API logs
- Keycloak: Check Keycloak admin console