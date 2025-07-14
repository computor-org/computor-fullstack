# SSO Plugins Implementation Plan

## Overview

This document outlines the implementation plan for Single Sign-On (SSO) authentication plugins for the Computor platform. The goal is to add support for Keycloak and GitLab.com authentication alongside the existing GitLab self-hosted authentication.

## Current Authentication Architecture

### Existing Components
1. **Account Model** (`src/ctutor_backend/model/auth.py`)
   - Supports multiple authentication providers via `provider` and `type` fields
   - Current implementation: GitLab authentication (self-hosted)
   - Fields: `provider`, `type`, `provider_account_id`, `user_id`

2. **Authentication Flow**
   - Basic auth with username/password (stored users)
   - GitLab token authentication via `/signup/gitlab` endpoint
   - Token validation and user creation/linking

3. **Plugin Directory Structure**
   - Location: `/plugins/`
   - Important: Each subdirectory is its own Git repository
   - Currently empty (only .gitkeep file)

## Proposed Plugin Architecture

### 1. Plugin Interface
Create a base authentication plugin interface that all SSO plugins must implement:

```python
class AuthenticationPlugin(ABC):
    """Base class for authentication plugins."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique name for this provider (e.g., 'keycloak', 'gitlab_com')."""
        pass
    
    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Type of authentication (e.g., 'oauth2', 'saml', 'oidc')."""
        pass
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """Authenticate user with given credentials."""
        pass
    
    @abstractmethod
    async def get_user_info(self, token: str) -> UserInfo:
        """Retrieve user information from provider."""
        pass
    
    @abstractmethod
    def get_login_url(self, redirect_uri: str) -> str:
        """Generate login URL for OAuth flows."""
        pass
    
    @abstractmethod
    async def handle_callback(self, code: str, state: str) -> AuthResult:
        """Handle OAuth callback."""
        pass
```

### 2. Plugin Directory Structure
```
/plugins/
├── computor-sso-keycloak/      # Keycloak plugin (separate git repo)
│   ├── .git/
│   ├── README.md
│   ├── setup.py
│   ├── requirements.txt
│   └── src/
│       ├── __init__.py
│       ├── keycloak_plugin.py
│       └── config.py
│
└── computor-sso-gitlab/        # GitLab.com plugin (separate git repo)
    ├── .git/
    ├── README.md
    ├── setup.py
    ├── requirements.txt
    └── src/
        ├── __init__.py
        ├── gitlab_plugin.py
        └── config.py
```

## Implementation Plan

### Phase 1: Core Plugin Infrastructure
1. **Create Plugin Loading System**
   - Dynamic plugin discovery and loading
   - Plugin registration mechanism
   - Configuration management for plugins

2. **Update Authentication API**
   - Create generic SSO endpoints
   - Add plugin-based authentication routing
   - Maintain backward compatibility

3. **Database Considerations**
   - No schema changes needed (Account model already supports multiple providers)
   - Add provider configuration table if needed

### Phase 2: Keycloak Plugin
1. **Docker Service Setup**
   ```yaml
   # docker-compose-dev.yaml addition
   keycloak:
     image: quay.io/keycloak/keycloak:latest
     environment:
       KEYCLOAK_ADMIN: admin
       KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
       KC_DB: postgres
       KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
       KC_DB_USERNAME: ${POSTGRES_USER}
       KC_DB_PASSWORD: ${POSTGRES_PASSWORD}
     ports:
       - "8180:8080"
     command: start-dev
   ```

2. **Plugin Implementation**
   - OIDC/OAuth2 flow support
   - User attribute mapping
   - Role/group synchronization
   - Token validation and refresh

3. **Configuration**
   ```yaml
   # Example configuration
   keycloak:
     realm: computor
     client_id: computor-backend
     client_secret: ${KEYCLOAK_CLIENT_SECRET}
     server_url: http://localhost:8180
     redirect_uri: http://localhost:8000/auth/keycloak/callback
   ```

### Phase 3: GitLab.com Plugin
1. **OAuth Application Setup**
   - Register OAuth application on GitLab.com
   - Configure scopes: `read_user`, `api`

2. **Plugin Implementation**
   - OAuth2 flow for GitLab.com
   - User information retrieval
   - Group/project membership sync

3. **Configuration**
   ```yaml
   gitlab_com:
     client_id: ${GITLAB_COM_CLIENT_ID}
     client_secret: ${GITLAB_COM_CLIENT_SECRET}
     redirect_uri: http://localhost:8000/auth/gitlab-com/callback
     scopes: ["read_user", "api"]
   ```

## API Endpoints

### New Endpoints
1. **Generic SSO Endpoints**
   - `GET /auth/providers` - List available SSO providers
   - `GET /auth/{provider}/login` - Initiate SSO login
   - `GET /auth/{provider}/callback` - Handle OAuth callback
   - `POST /auth/{provider}/logout` - Provider-specific logout

2. **Plugin Management** (Admin only)
   - `GET /admin/plugins` - List installed plugins
   - `POST /admin/plugins/reload` - Reload plugins
   - `GET /admin/plugins/{plugin}/status` - Plugin health check

## Security Considerations

1. **Token Storage**
   - Store provider tokens encrypted in database
   - Implement token refresh mechanisms
   - Set appropriate token expiration

2. **CSRF Protection**
   - Use state parameter in OAuth flows
   - Validate redirect URIs

3. **User Linking**
   - Secure account linking process
   - Email verification for account merging
   - Prevent account takeover

## Testing Strategy

1. **Unit Tests**
   - Mock provider responses
   - Test authentication flows
   - Validate user mapping

2. **Integration Tests**
   - Docker-based test environments
   - Real provider testing (test realms/apps)

3. **Security Tests**
   - Token validation
   - CSRF attack prevention
   - Session management

## Migration Path

1. **Existing Users**
   - Allow linking existing accounts to SSO providers
   - Maintain backward compatibility with current auth

2. **Configuration Migration**
   - Document environment variable changes
   - Provide migration scripts if needed

## Environment Variables

### Keycloak
```bash
KEYCLOAK_ENABLED=true
KEYCLOAK_SERVER_URL=http://localhost:8180
KEYCLOAK_REALM=computor
KEYCLOAK_CLIENT_ID=computor-backend
KEYCLOAK_CLIENT_SECRET=your-secret
KEYCLOAK_ADMIN_PASSWORD=admin
```

### GitLab.com
```bash
GITLAB_COM_ENABLED=true
GITLAB_COM_CLIENT_ID=your-client-id
GITLAB_COM_CLIENT_SECRET=your-client-secret
GITLAB_COM_REDIRECT_URI=http://localhost:8000/auth/gitlab-com/callback
```

## Benefits

1. **Centralized Authentication**
   - Single sign-on across services
   - Reduced password fatigue
   - Better security through centralized management

2. **Enterprise Features**
   - Support for LDAP/AD via Keycloak
   - Multi-factor authentication
   - Advanced access policies

3. **Flexibility**
   - Easy to add new providers
   - Plugin-based architecture
   - Provider-specific customizations

## Next Steps

1. Create GitHub issue for tracking
2. Implement core plugin infrastructure
3. Develop Keycloak plugin
4. Develop GitLab.com plugin
5. Update documentation
6. Create deployment guides

## Notes

- The plugin system is designed to be extensible for future providers (Google, Microsoft, GitHub, etc.)
- Each plugin is a separate Git repository to allow independent versioning
- Plugins should be installable via pip for easy deployment
- Consider creating a plugin template repository for faster development