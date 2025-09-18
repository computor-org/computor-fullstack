/**
 * Auto-generated client for SsoClient.
 * Endpoint: /auth
 */

import type { ProviderInfo, TokenRefreshRequest, TokenRefreshResponse, UserRegistrationRequest, UserRegistrationResponse } from 'types/generated';
import { APIClient, apiClient } from 'api/client';
import { BaseEndpointClient } from './baseClient';

export class SsoClient extends BaseEndpointClient {
  constructor(client: APIClient = apiClient) {
    super(client, '/auth');
  }

  /**
   * List Providers
   * List available authentication providers.
   * Returns all enabled authentication providers with their metadata.
   */
  async listProvidersAuthProvidersGet(): Promise<ProviderInfo[]> {
    return this.client.get<ProviderInfo[]>(this.buildPath('providers'));
  }

  /**
   * Initiate Login
   * Initiate SSO login for a specific provider.
   * Redirects the user to the provider's login page.
   */
  async initiateLoginAuthProviderLoginGet({ provider, redirectUri }: { provider: string; redirectUri?: string | null }): Promise<void> {
    const queryParams: Record<string, unknown> = {
      redirect_uri: redirectUri,
    };
    return this.client.get<void>(this.buildPath(provider, 'login'), { params: queryParams });
  }

  /**
   * Handle Callback
   * Handle OAuth callback from provider.
   * Exchanges the authorization code for tokens and creates/updates user account.
   */
  async handleCallbackAuthProviderCallbackGet({ provider, code, state }: { provider: string; code: string; state?: string | null }): Promise<void> {
    const queryParams: Record<string, unknown> = {
      code,
      state,
    };
    return this.client.get<void>(this.buildPath(provider, 'callback'), { params: queryParams });
  }

  /**
   * Sso Success
   * Default success page after SSO authentication.
   */
  async ssoSuccessAuthSuccessGet(): Promise<void> {
    return this.client.get<void>(this.buildPath('success'));
  }

  /**
   * Get Current User Info
   * Get current authenticated user information.
   * This endpoint can be used to test SSO authentication and retrieve
   * the current user's details and roles.
   */
  async getCurrentUserInfoAuthMeGet(): Promise<void> {
    return this.client.get<void>(this.buildPath('me'));
  }

  /**
   * Logout
   * Logout from a specific provider.
   * Revokes tokens and performs provider-specific logout if supported.
   */
  async logoutAuthProviderLogoutPost({ provider }: { provider: string }): Promise<void> {
    return this.client.post<void>(this.buildPath(provider, 'logout'));
  }

  /**
   * List All Plugins
   * List all available plugins (admin only).
   * Shows both enabled and disabled plugins with full metadata.
   */
  async listAllPluginsAuthAdminPluginsGet(): Promise<void> {
    return this.client.get<void>(this.buildPath('admin', 'plugins'));
  }

  /**
   * Enable Plugin
   * Enable a plugin (admin only).
   */
  async enablePluginAuthAdminPluginsPluginNameEnablePost({ pluginName }: { pluginName: string }): Promise<void> {
    return this.client.post<void>(this.buildPath('admin', 'plugins', pluginName, 'enable'));
  }

  /**
   * Disable Plugin
   * Disable a plugin (admin only).
   */
  async disablePluginAuthAdminPluginsPluginNameDisablePost({ pluginName }: { pluginName: string }): Promise<void> {
    return this.client.post<void>(this.buildPath('admin', 'plugins', pluginName, 'disable'));
  }

  /**
   * Reload Plugins
   * Reload all plugins (admin only).
   */
  async reloadPluginsAuthAdminPluginsReloadPost(): Promise<void> {
    return this.client.post<void>(this.buildPath('admin', 'plugins', 'reload'));
  }

  /**
   * Register User
   * Register a new user with SSO provider.
   * Creates user in both the authentication provider and local database.
   */
  async registerUserAuthRegisterPost({ body }: { body: UserRegistrationRequest }): Promise<UserRegistrationResponse> {
    return this.client.post<UserRegistrationResponse>(this.buildPath('register'), body);
  }

  /**
   * Refresh Token
   * Refresh SSO access token using refresh token.
   * This endpoint allows users to refresh their session token using
   * the refresh token obtained during initial authentication.
   */
  async refreshTokenAuthRefreshPost({ body }: { body: TokenRefreshRequest }): Promise<TokenRefreshResponse> {
    return this.client.post<TokenRefreshResponse>(this.buildPath('refresh'), body);
  }
}
