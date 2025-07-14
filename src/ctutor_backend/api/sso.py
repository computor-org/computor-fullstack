"""
Generic SSO authentication API endpoints.
"""

import secrets
from typing import Dict, List, Optional
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ctutor_backend.database import get_db
from ctutor_backend.api.auth import get_current_permissions
from ctutor_backend.api.exceptions import UnauthorizedException, BadRequestException, NotFoundException
from ctutor_backend.interface.permissions import Principal
from ctutor_backend.model.auth import User, Account
from ctutor_backend.model.role import UserRole
from ctutor_backend.plugins import PluginMetadata, AuthStatus, UserInfo
from ctutor_backend.plugins.registry import get_plugin_registry
from ctutor_backend.redis_cache import get_redis_client
import json
import logging

logger = logging.getLogger(__name__)

sso_router = APIRouter(prefix="/auth")


class ProviderInfo(BaseModel):
    """Information about an authentication provider."""
    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    type: str = Field(..., description="Authentication type")
    enabled: bool = Field(..., description="Whether provider is enabled")
    login_url: Optional[str] = Field(None, description="Login URL if applicable")


class LoginRequest(BaseModel):
    """Login request for SSO."""
    provider: str = Field(..., description="Provider name")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI after login")


class CallbackRequest(BaseModel):
    """OAuth callback parameters."""
    code: str = Field(..., description="Authorization code")
    state: Optional[str] = Field(None, description="State parameter")


class SSOAuthResponse(BaseModel):
    """Response after successful SSO authentication."""
    user_id: str = Field(..., description="User ID")
    account_id: str = Field(..., description="Account ID")
    access_token: Optional[str] = Field(None, description="Access token if available")
    is_new_user: bool = Field(..., description="Whether this is a new user")


@sso_router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
    """
    List available authentication providers.
    
    Returns all enabled authentication providers with their metadata.
    """
    registry = get_plugin_registry()
    providers = []
    
    for plugin_name in registry.get_enabled_plugins():
        metadata = registry.get_plugin_metadata(plugin_name)
        if metadata:
            providers.append(ProviderInfo(
                name=plugin_name,
                display_name=metadata.provider_name,
                type=metadata.provider_type.value,
                enabled=True,
                login_url=f"/auth/{plugin_name}/login"
            ))
    
    return providers


@sso_router.get("/{provider}/login")
async def initiate_login(
    provider: str,
    redirect_uri: Optional[str] = Query(None, description="Redirect URI after authentication"),
    request: Request = None
):
    """
    Initiate SSO login for a specific provider.
    
    Redirects the user to the provider's login page.
    """
    registry = get_plugin_registry()
    
    # Check if provider exists and is enabled
    if provider not in registry.get_enabled_plugins():
        raise NotFoundException(f"Authentication provider not found or not enabled: {provider}")
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in Redis with 10 minute expiration
    redis_client = await get_redis_client()
    state_data = {
        "provider": provider,
        "redirect_uri": redirect_uri or str(request.url_for("sso_success")),
        "timestamp": str(request.headers.get("date", ""))
    }
    await redis_client.setex(
        f"sso_state:{state}",
        600,  # 10 minutes
        json.dumps(state_data)
    )
    
    # Get callback URL
    callback_url = str(request.url_for("handle_callback", provider=provider))
    
    try:
        # Get login URL from provider
        login_url = registry.get_login_url(provider, callback_url, state)
        
        # Redirect to provider login
        return RedirectResponse(url=login_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Failed to initiate login for {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate login")


@sso_router.get("/{provider}/callback", name="handle_callback")
async def handle_callback(
    provider: str,
    code: str = Query(..., description="Authorization code"),
    state: Optional[str] = Query(None, description="State parameter"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from provider.
    
    Exchanges the authorization code for tokens and creates/updates user account.
    """
    registry = get_plugin_registry()
    redis_client = await get_redis_client()
    
    # Validate state parameter
    if state:
        state_key = f"sso_state:{state}"
        state_data_raw = await redis_client.get(state_key)
        
        if not state_data_raw:
            raise BadRequestException("Invalid or expired state parameter")
        
        state_data = json.loads(state_data_raw)
        
        # Delete state to prevent replay attacks
        await redis_client.delete(state_key)
        
        # Validate provider matches
        if state_data["provider"] != provider:
            raise BadRequestException("Provider mismatch in state parameter")
    
    try:
        # Handle callback with provider
        auth_result = await registry.handle_callback(provider, code, state)
        
        if auth_result.status != AuthStatus.SUCCESS:
            raise UnauthorizedException(f"Authentication failed: {auth_result.error_message}")
        
        # Get user info
        user_info = auth_result.user_info
        if not user_info:
            raise BadRequestException("No user information received from provider")
        
        # Find or create user account
        account = db.query(Account).filter(
            Account.provider == provider,
            Account.type == registry.get_plugin_metadata(provider).provider_type.value,
            Account.provider_account_id == user_info.provider_id
        ).first()
        
        is_new_user = False
        
        if account:
            # Existing account - get user
            user = account.user
            
            # Update account properties with latest info
            account.properties = {
                "email": user_info.email,
                "username": user_info.username,
                "picture": user_info.picture,
                "groups": user_info.groups,
                "attributes": user_info.attributes,
                "last_login": str(auth_result.expires_at) if auth_result.expires_at else None
            }
            
        else:
            # New account - create user
            is_new_user = True
            
            # Create new user
            user = User(
                given_name=user_info.given_name or "",
                family_name=user_info.family_name or "",
                username=user_info.username or user_info.email or f"{provider}_{user_info.provider_id}",
                email=user_info.email
            )
            db.add(user)
            db.flush()
            
            # Create account
            account = Account(
                provider=provider,
                type=registry.get_plugin_metadata(provider).provider_type.value,
                provider_account_id=user_info.provider_id,
                user_id=user.id,
                properties={
                    "email": user_info.email,
                    "username": user_info.username,
                    "picture": user_info.picture,
                    "groups": user_info.groups,
                    "attributes": user_info.attributes,
                    "last_login": str(auth_result.expires_at) if auth_result.expires_at else None
                }
            )
            db.add(account)
            
            # Add default user role
            user_role = UserRole(
                user_id=user.id,
                role_id="_user"
            )
            db.add(user_role)
        
        db.commit()
        
        # Store tokens in Redis if available
        if auth_result.access_token:
            token_key = f"sso_token:{provider}:{user.id}"
            token_data = {
                "access_token": auth_result.access_token,
                "refresh_token": auth_result.refresh_token,
                "expires_at": str(auth_result.expires_at) if auth_result.expires_at else None
            }
            
            # Store with appropriate expiration
            expiration = 3600  # Default 1 hour
            if auth_result.expires_at:
                # Calculate seconds until expiration
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                delta = auth_result.expires_at - now
                expiration = max(int(delta.total_seconds()), 60)  # At least 1 minute
            
            await redis_client.setex(
                token_key,
                expiration,
                json.dumps(token_data)
            )
        
        # Get redirect URI from state or use default
        redirect_uri = "/"
        if state and "redirect_uri" in state_data:
            redirect_uri = state_data["redirect_uri"]
        
        # Create response with user info
        response_data = SSOAuthResponse(
            user_id=str(user.id),
            account_id=str(account.id),
            access_token=auth_result.access_token,
            is_new_user=is_new_user
        )
        
        # Redirect with encoded response
        params = {
            "user_id": response_data.user_id,
            "account_id": response_data.account_id,
            "is_new_user": str(response_data.is_new_user).lower()
        }
        
        if "?" in redirect_uri:
            redirect_url = f"{redirect_uri}&{urlencode(params)}"
        else:
            redirect_url = f"{redirect_uri}?{urlencode(params)}"
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Failed to handle callback for {provider}: {e}")
        
        # Redirect to error page
        error_params = {"error": str(e), "provider": provider}
        error_url = f"/?{urlencode(error_params)}"
        return RedirectResponse(url=error_url, status_code=302)


@sso_router.get("/success", name="sso_success")
async def sso_success():
    """Default success page after SSO authentication."""
    return {"message": "Authentication successful", "status": "success"}


@sso_router.post("/{provider}/logout")
async def logout(
    provider: str,
    principal: Principal = Depends(get_current_permissions),
    db: Session = Depends(get_db)
):
    """
    Logout from a specific provider.
    
    Revokes tokens and performs provider-specific logout if supported.
    """
    registry = get_plugin_registry()
    redis_client = await get_redis_client()
    
    # Check if provider exists and is enabled
    if provider not in registry.get_enabled_plugins():
        raise NotFoundException(f"Authentication provider not found or not enabled: {provider}")
    
    # Get stored tokens
    token_key = f"sso_token:{provider}:{principal.user_id}"
    token_data_raw = await redis_client.get(token_key)
    
    if token_data_raw:
        token_data = json.loads(token_data_raw)
        access_token = token_data.get("access_token")
        
        if access_token:
            try:
                # Perform provider logout
                plugin = registry.get_plugin(provider)
                if plugin:
                    await plugin.logout(access_token)
            except Exception as e:
                logger.error(f"Failed to logout from {provider}: {e}")
        
        # Delete stored tokens
        await redis_client.delete(token_key)
    
    return {"message": "Logout successful", "provider": provider}


@sso_router.get("/admin/plugins", dependencies=[Depends(get_current_permissions)])
async def list_all_plugins(principal: Principal = Depends(get_current_permissions)):
    """
    List all available plugins (admin only).
    
    Shows both enabled and disabled plugins with full metadata.
    """
    # Check admin permission
    if "_admin" not in principal.roles:
        raise UnauthorizedException("Admin access required")
    
    registry = get_plugin_registry()
    
    plugins = {}
    
    # Get all discovered plugins
    discovered = registry.loader.discover_plugins()
    
    for plugin_name in discovered:
        metadata = registry.get_plugin_metadata(plugin_name)
        if metadata:
            plugins[plugin_name] = {
                "metadata": metadata.model_dump(),
                "enabled": plugin_name in registry.get_enabled_plugins(),
                "loaded": plugin_name in registry.get_loaded_plugins()
            }
    
    return plugins


@sso_router.post("/admin/plugins/{plugin_name}/enable", dependencies=[Depends(get_current_permissions)])
async def enable_plugin(
    plugin_name: str,
    principal: Principal = Depends(get_current_permissions)
):
    """Enable a plugin (admin only)."""
    # Check admin permission
    if "_admin" not in principal.roles:
        raise UnauthorizedException("Admin access required")
    
    registry = get_plugin_registry()
    
    # Enable plugin
    registry.enable_plugin(plugin_name)
    
    # Try to load it
    try:
        await registry.load_plugin(plugin_name)
        return {"message": f"Plugin {plugin_name} enabled and loaded"}
    except Exception as e:
        return {"message": f"Plugin {plugin_name} enabled but failed to load: {e}"}


@sso_router.post("/admin/plugins/{plugin_name}/disable", dependencies=[Depends(get_current_permissions)])
async def disable_plugin(
    plugin_name: str,
    principal: Principal = Depends(get_current_permissions)
):
    """Disable a plugin (admin only)."""
    # Check admin permission
    if "_admin" not in principal.roles:
        raise UnauthorizedException("Admin access required")
    
    registry = get_plugin_registry()
    
    # Unload if loaded
    await registry.unload_plugin(plugin_name)
    
    # Disable plugin
    registry.disable_plugin(plugin_name)
    
    return {"message": f"Plugin {plugin_name} disabled"}


@sso_router.post("/admin/plugins/reload", dependencies=[Depends(get_current_permissions)])
async def reload_plugins(principal: Principal = Depends(get_current_permissions)):
    """Reload all plugins (admin only)."""
    # Check admin permission
    if "_admin" not in principal.roles:
        raise UnauthorizedException("Admin access required")
    
    registry = get_plugin_registry()
    await registry.reload_all()
    
    return {
        "message": "Plugins reloaded",
        "loaded": registry.get_loaded_plugins()
    }