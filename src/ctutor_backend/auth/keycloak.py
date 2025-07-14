"""
Keycloak authentication provider implementation.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from jose import jwt, JWTError

from ctutor_backend.plugins.base import (
    AuthenticationPlugin,
    AuthResult,
    UserInfo,
    PluginConfig,
    PluginMetadata,
    AuthStatus,
    AuthenticationType
)

logger = logging.getLogger(__name__)


class KeycloakConfig(PluginConfig):
    """Keycloak-specific configuration."""
    server_url: str = os.environ.get("KEYCLOAK_SERVER_URL", "http://localhost:8180")
    realm: str = os.environ.get("KEYCLOAK_REALM", "master")
    client_id: str = os.environ.get("KEYCLOAK_CLIENT_ID", "computor-backend")
    client_secret: str = os.environ.get("KEYCLOAK_CLIENT_SECRET", "")
    scopes: list = ["openid", "profile", "email"]
    verify_ssl: bool = True


class KeycloakAuthPlugin(AuthenticationPlugin):
    """
    Keycloak authentication provider using OpenID Connect.
    """
    
    def __init__(self, config: Optional[KeycloakConfig] = None):
        """Initialize Keycloak plugin with configuration."""
        if config is None:
            config = KeycloakConfig()
        super().__init__(config)
        self.config: KeycloakConfig = config
        self._oidc_config = None
        self._jwks = None
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="keycloak",
            version="1.0.0",
            description="Keycloak authentication provider using OpenID Connect",
            author="Computor Team",
            provider_name="Keycloak",
            provider_type=AuthenticationType.OIDC,
            requires=["httpx", "python-jose"],
            homepage="https://www.keycloak.org/"
        )
    
    async def initialize(self) -> None:
        """Initialize the plugin and fetch OIDC configuration."""
        await super().initialize()
        
        # Fetch OpenID configuration
        try:
            await self._fetch_oidc_config()
            await self._fetch_jwks()
            logger.info("Keycloak plugin initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak plugin: {e}")
            raise
    
    async def _fetch_oidc_config(self) -> None:
        """Fetch OpenID Connect configuration from Keycloak."""
        well_known_url = f"{self.config.server_url}/realms/{self.config.realm}/.well-known/openid-configuration"
        
        async with httpx.AsyncClient(verify=self.config.verify_ssl) as client:
            response = await client.get(well_known_url)
            response.raise_for_status()
            self._oidc_config = response.json()
    
    async def _fetch_jwks(self) -> None:
        """Fetch JSON Web Key Set from Keycloak."""
        if not self._oidc_config:
            await self._fetch_oidc_config()
        
        jwks_uri = self._oidc_config.get("jwks_uri")
        if not jwks_uri:
            raise ValueError("JWKS URI not found in OIDC configuration")
        
        async with httpx.AsyncClient(verify=self.config.verify_ssl) as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            self._jwks = response.json()
    
    def get_login_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Keycloak login URL."""
        if not self._oidc_config:
            raise RuntimeError("Plugin not initialized. Call initialize() first.")
        
        auth_endpoint = self._oidc_config.get("authorization_endpoint")
        if not auth_endpoint:
            raise ValueError("Authorization endpoint not found in OIDC configuration")
        
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "redirect_uri": redirect_uri
        }
        
        if state:
            params["state"] = state
        
        # Build URL with query parameters
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{auth_endpoint}?{query_string}"
    
    async def handle_callback(self, code: str, state: Optional[str] = None) -> AuthResult:
        """
        Handle OAuth callback from Keycloak.
        
        Exchange authorization code for tokens and get user info.
        """
        try:
            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(code)
            
            # Parse ID token to get user info
            id_token = tokens.get("id_token")
            if not id_token:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    error_message="No ID token received from Keycloak"
                )
            
            # Decode and verify ID token
            claims = await self._verify_and_decode_token(id_token)
            
            # Extract user info from claims
            user_info = UserInfo(
                provider_id=claims.get("sub", ""),
                email=claims.get("email"),
                username=claims.get("preferred_username", claims.get("email", "").split("@")[0]),
                given_name=claims.get("given_name"),
                family_name=claims.get("family_name"),
                full_name=claims.get("name"),
                picture=claims.get("picture"),
                groups=claims.get("groups", []),
                attributes={
                    "email_verified": claims.get("email_verified", False),
                    "realm_access": claims.get("realm_access", {}),
                    "resource_access": claims.get("resource_access", {})
                }
            )
            
            # Calculate token expiration
            expires_at = None
            if "exp" in claims:
                expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
            
            return AuthResult(
                status=AuthStatus.SUCCESS,
                user_info=user_info,
                access_token=tokens.get("access_token"),
                refresh_token=tokens.get("refresh_token"),
                expires_at=expires_at,
                session_data={
                    "token_type": tokens.get("token_type", "Bearer"),
                    "expires_in": tokens.get("expires_in"),
                    "scope": tokens.get("scope", "")
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to handle Keycloak callback: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                error_message=str(e)
            )
    
    async def _exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        if not self._oidc_config:
            raise RuntimeError("Plugin not initialized")
        
        token_endpoint = self._oidc_config.get("token_endpoint")
        if not token_endpoint:
            raise ValueError("Token endpoint not found in OIDC configuration")
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret
        }
        
        async with httpx.AsyncClient(verify=self.config.verify_ssl) as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return response.json()
    
    async def _verify_and_decode_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token using Keycloak's JWKS."""
        if not self._jwks:
            await self._fetch_jwks()
        
        # Get the key ID from token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise JWTError("No key ID found in token header")
        
        # Find the matching key in JWKS
        key = None
        for jwk in self._jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        
        if not key:
            raise JWTError(f"No matching key found for kid: {kid}")
        
        # Verify and decode the token
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.config.client_id,
                issuer=f"{self.config.server_url}/realms/{self.config.realm}"
            )
            return claims
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """
        Direct authentication with username/password (Resource Owner Password Credentials).
        
        Note: This flow should be avoided in production. Use authorization code flow instead.
        """
        if not self._oidc_config:
            raise RuntimeError("Plugin not initialized")
        
        token_endpoint = self._oidc_config.get("token_endpoint")
        if not token_endpoint:
            raise ValueError("Token endpoint not found in OIDC configuration")
        
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            return AuthResult(
                status=AuthStatus.FAILED,
                error_message="Username and password required"
            )
        
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": " ".join(self.config.scopes)
        }
        
        try:
            async with httpx.AsyncClient(verify=self.config.verify_ssl) as client:
                response = await client.post(
                    token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 401:
                    return AuthResult(
                        status=AuthStatus.FAILED,
                        error_message="Invalid username or password"
                    )
                
                response.raise_for_status()
                tokens = response.json()
                
                # Handle the tokens like in callback
                return await self.handle_callback("", "")  # Reuse token processing logic
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Authentication failed: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                error_message=f"Authentication failed: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResult(
                status=AuthStatus.ERROR,
                error_message=str(e)
            )
    
    async def get_user_info(self, access_token: str) -> UserInfo:
        """Get user information using access token."""
        if not self._oidc_config:
            raise RuntimeError("Plugin not initialized")
        
        userinfo_endpoint = self._oidc_config.get("userinfo_endpoint")
        if not userinfo_endpoint:
            raise ValueError("UserInfo endpoint not found in OIDC configuration")
        
        async with httpx.AsyncClient(verify=self.config.verify_ssl) as client:
            response = await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            claims = response.json()
        
        return UserInfo(
            provider_id=claims.get("sub", ""),
            email=claims.get("email"),
            username=claims.get("preferred_username", claims.get("email", "").split("@")[0]),
            given_name=claims.get("given_name"),
            family_name=claims.get("family_name"),
            full_name=claims.get("name"),
            picture=claims.get("picture"),
            groups=claims.get("groups", []),
            attributes={
                "email_verified": claims.get("email_verified", False),
                "realm_access": claims.get("realm_access", {}),
                "resource_access": claims.get("resource_access", {})
            }
        )
    
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh access token using refresh token."""
        if not self._oidc_config:
            raise RuntimeError("Plugin not initialized")
        
        token_endpoint = self._oidc_config.get("token_endpoint")
        if not token_endpoint:
            raise ValueError("Token endpoint not found in OIDC configuration")
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret
        }
        
        try:
            async with httpx.AsyncClient(verify=self.config.verify_ssl) as client:
                response = await client.post(
                    token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                tokens = response.json()
                
                # Process the new tokens
                return await self.handle_callback("", "")  # Reuse token processing logic
                
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                error_message=f"Token refresh failed: {str(e)}"
            )
    
    async def logout(self, access_token: str) -> bool:
        """Logout user from Keycloak."""
        if not self._oidc_config:
            return False
        
        end_session_endpoint = self._oidc_config.get("end_session_endpoint")
        if not end_session_endpoint:
            # If no end session endpoint, just return success
            return True
        
        try:
            async with httpx.AsyncClient(verify=self.config.verify_ssl) as client:
                response = await client.post(
                    end_session_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                return response.status_code < 400
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False