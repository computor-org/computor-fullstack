# SSO Frontend Integration

## Overview

The SSO (Single Sign-On) integration allows users to authenticate using Keycloak instead of the mock authentication system. This provides enterprise-grade authentication with support for multiple identity providers.

## Architecture

### Frontend Components

1. **SSOAuthService** (`/frontend/src/services/ssoAuthService.ts`)
   - Handles SSO authentication flow
   - Manages token storage and refresh
   - Provides API for SSO operations

2. **SSOLoginModal** (`/frontend/src/components/SSOLoginModal.tsx`)
   - Replaces the mock login modal
   - Provides "Login with Keycloak" option
   - Handles SSO initiation

3. **SSOCallback** (`/frontend/src/components/SSOCallback.tsx`)
   - Processes SSO redirect from Keycloak
   - Fetches user data from API
   - Stores authentication tokens

4. **SSOIntegration** (`/frontend/src/services/ssoIntegration.ts`)
   - Syncs SSO tokens with frontend auth system
   - Transforms backend user data to frontend format

5. **API Client** (`/frontend/src/api/client.ts`)
   - Automatically includes Bearer token in API requests
   - Handles token refresh on 401 errors
   - Supports both SSO and mock authentication

### Backend Endpoints

1. **`GET /auth/keycloak/login`**
   - Initiates SSO flow
   - Redirects to Keycloak login page

2. **`GET /auth/keycloak/callback`**
   - Handles OAuth callback
   - Creates/updates user account
   - Generates API session token

3. **`GET /auth/me`**
   - Returns current user information
   - Requires Bearer token authentication

4. **`POST /auth/refresh`**
   - Refreshes access token
   - Uses refresh token from initial auth

## Authentication Flow

1. User clicks "Sign In" → "Login with Keycloak"
2. Frontend redirects to `/auth/keycloak/login?redirect_uri=http://localhost:3000/auth/success`
3. Backend redirects to Keycloak login page
4. User authenticates with Keycloak
5. Keycloak redirects to backend callback
6. Backend processes auth and redirects to frontend with tokens
7. Frontend `/auth/success` page:
   - Extracts tokens from URL
   - Stores in localStorage
   - Fetches user data from `/auth/me`
   - Redirects to dashboard

## Token Storage

Tokens are stored in localStorage:

```javascript
// auth_token
{
  "accessToken": "sso_session_token",
  "refreshToken": "keycloak_refresh_token",
  "expiresAt": 1234567890000
}

// auth_user
{
  "id": "user_uuid",
  "email": "user@example.com",
  "givenName": "John",
  "familyName": "Doe",
  "role": "admin",
  "permissions": ["..."],
  "courses": []
}
```

## API Authentication

All API requests automatically include the Bearer token:

```javascript
Authorization: Bearer <sso_session_token>
```

## Debugging

### Debug Page

Access `/debug/sso` in the frontend to see:
- Current auth state
- Stored tokens
- Test API calls
- Quick actions

### Common Issues

1. **Stuck on /auth/success**
   - Check browser console for errors
   - Verify tokens in URL parameters
   - Check if API is reachable

2. **"Enable JavaScript" error**
   - React app failed to load
   - Check for JavaScript errors
   - Verify build is successful

3. **401 Unauthorized on API calls**
   - Token may be expired
   - Token format may be incorrect
   - Check Bearer token in request headers

4. **User data not loading**
   - `/auth/me` endpoint may be failing
   - Check user exists in database
   - Verify roles are properly assigned

### Testing

1. Start all services:
   ```bash
   bash startup.sh      # Backend + Keycloak
   bash frontend.sh     # Frontend
   ```

2. Access http://localhost:3000

3. Click "Sign In" → "Login with Keycloak"

4. Use admin/admin credentials

5. Verify successful login and dashboard access

## Configuration

### Environment Variables

Frontend (`.env`):
```
REACT_APP_API_URL=http://localhost:8000
```

Backend (`.env`):
```
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=computor
KEYCLOAK_CLIENT_ID=computor-api
KEYCLOAK_CLIENT_SECRET=your-secret
```

### CORS Settings

Backend must allow frontend origin:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Future Enhancements

1. **Role Mapping**
   - Map Keycloak groups to Computor roles
   - Sync permissions from Keycloak claims

2. **Auto-refresh**
   - Implement token refresh before expiration
   - Handle refresh token rotation

3. **Logout**
   - Implement proper SSO logout
   - Clear Keycloak session

4. **Multiple Providers**
   - Support GitLab SSO
   - Support SAML providers

5. **User Profile Sync**
   - Sync profile updates from Keycloak
   - Handle email verification status