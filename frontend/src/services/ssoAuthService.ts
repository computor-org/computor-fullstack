import { LoginCredentials, AuthResponse, AuthUser, AuthToken } from '../types/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface SSOCallbackParams {
  token?: string;
  refresh_token?: string;
  user_id?: string;
  error?: string;
}

export class SSOAuthService {
  private static readonly TOKEN_KEY = 'auth_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private static readonly USER_KEY = 'auth_user';

  /**
   * Initiate SSO login by redirecting to the provider
   */
  static initiateSSO(provider: string = 'keycloak') {
    // Save current location to return after auth
    sessionStorage.setItem('auth_redirect', window.location.pathname);
    
    // Build the frontend callback URL
    const frontendCallbackUrl = `${window.location.origin}/auth/success`;
    
    // Redirect to SSO login with redirect_uri parameter
    const params = new URLSearchParams({
      redirect_uri: frontendCallbackUrl
    });
    
    window.location.href = `${API_BASE_URL}/auth/${provider}/login?${params.toString()}`;
  }

  /**
   * Handle SSO callback - to be called when redirected back from SSO
   */
  static async handleSSOCallback(): Promise<AuthResponse> {
    // Parse URL parameters
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const refreshToken = params.get('refresh_token');
    const userId = params.get('user_id');
    const error = params.get('error');

    if (error) {
      return {
        success: false,
        error: `SSO Error: ${error}`,
      };
    }

    if (!token) {
      return {
        success: false,
        error: 'No authentication token received',
      };
    }

    try {
      // Fetch user info using the token
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user info');
      }

      const userInfo = await response.json();

      // Transform backend user data to frontend format
      const user: AuthUser = {
        id: userInfo.user.id,
        email: userInfo.user.email,
        givenName: userInfo.user.given_name,
        familyName: userInfo.user.family_name,
        role: this.mapRolesToFrontend(userInfo.roles),
        permissions: this.mapPermissions(userInfo.roles),
        courses: [], // TODO: Fetch from user's course enrollments
      };

      const authToken: AuthToken = {
        accessToken: token,
        refreshToken: refreshToken || '',
        expiresAt: Date.now() + (24 * 60 * 60 * 1000), // 24 hours
      };

      // Store authentication data
      localStorage.setItem(this.TOKEN_KEY, JSON.stringify(authToken));
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      if (refreshToken) {
        localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
      }

      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);

      return {
        success: true,
        user,
        token: authToken,
      };
    } catch (error) {
      console.error('SSO callback error:', error);
      return {
        success: false,
        error: 'Failed to complete authentication',
      };
    }
  }

  /**
   * Direct login (for testing or basic auth fallback)
   */
  static async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      // For SSO, we should redirect to SSO provider
      // This is kept for backwards compatibility or basic auth
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.text();
        return {
          success: false,
          error: error || 'Login failed',
        };
      }

      const data = await response.json();
      
      // Store and return auth data
      // ... similar to handleSSOCallback
      
      return {
        success: true,
        user: data.user,
        token: data.token,
      };
    } catch (error) {
      return {
        success: false,
        error: 'Network error',
      };
    }
  }

  /**
   * Logout user
   */
  static async logout(): Promise<void> {
    const token = this.getStoredToken();
    
    if (token) {
      try {
        // Notify backend about logout
        await fetch(`${API_BASE_URL}/auth/keycloak/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token.accessToken}`,
          },
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    // Clear local storage
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Refresh access token using refresh token
   */
  static async refreshToken(): Promise<AuthResponse> {
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    
    if (!refreshToken) {
      return {
        success: false,
        error: 'No refresh token available',
      };
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: refreshToken,
          provider: 'keycloak',
        }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      // Update stored tokens
      const storedUser = this.getStoredUser();
      if (!storedUser) {
        throw new Error('No user data found');
      }

      const newToken: AuthToken = {
        accessToken: data.access_token,
        refreshToken: data.refresh_token || refreshToken,
        expiresAt: Date.now() + (data.expires_in * 1000),
      };

      localStorage.setItem(this.TOKEN_KEY, JSON.stringify(newToken));
      if (data.refresh_token) {
        localStorage.setItem(this.REFRESH_TOKEN_KEY, data.refresh_token);
      }

      return {
        success: true,
        user: storedUser,
        token: newToken,
      };
    } catch (error) {
      console.error('Token refresh error:', error);
      return {
        success: false,
        error: 'Failed to refresh token',
      };
    }
  }

  /**
   * Get stored authentication data
   */
  static getStoredAuth(): { user: AuthUser; token: AuthToken } | null {
    try {
      const storedToken = localStorage.getItem(this.TOKEN_KEY);
      const storedUser = localStorage.getItem(this.USER_KEY);

      if (!storedToken || !storedUser) {
        return null;
      }

      const token: AuthToken = JSON.parse(storedToken);
      const user: AuthUser = JSON.parse(storedUser);

      // Check if token is expired
      if (Date.now() > token.expiresAt) {
        // Try to refresh before declaring expired
        return null; // Let the auth hook handle refresh
      }

      return { user, token };
    } catch {
      return null;
    }
  }

  /**
   * Get stored token only
   */
  static getStoredToken(): AuthToken | null {
    try {
      const storedToken = localStorage.getItem(this.TOKEN_KEY);
      return storedToken ? JSON.parse(storedToken) : null;
    } catch {
      return null;
    }
  }

  /**
   * Get stored user only
   */
  static getStoredUser(): AuthUser | null {
    try {
      const storedUser = localStorage.getItem(this.USER_KEY);
      return storedUser ? JSON.parse(storedUser) : null;
    } catch {
      return null;
    }
  }

  /**
   * Map backend roles to frontend role
   */
  private static mapRolesToFrontend(roles: string[]): 'admin' | 'lecturer' | 'student' {
    if (roles.includes('_admin')) return 'admin';
    if (roles.includes('_lecturer')) return 'lecturer';
    return 'student';
  }

  /**
   * Map roles to permissions
   */
  private static mapPermissions(roles: string[]): string[] {
    const permissions: string[] = [];

    if (roles.includes('_admin')) {
      permissions.push(
        'view_students',
        'view_course_students',
        'create_assignments',
        'view_grades',
        'manage_course',
        'admin_access',
        'manage_users',
        'system_settings',
        'view_audit'
      );
    }

    if (roles.includes('_lecturer')) {
      permissions.push(
        'view_students',
        'view_course_students',
        'create_assignments',
        'view_grades',
        'manage_course'
      );
    }

    if (roles.includes('_student')) {
      permissions.push(
        'view_assignments',
        'submit_assignments'
      );
    }

    return permissions;
  }

  /**
   * Check if current route is an SSO callback
   */
  static isSSOCallback(): boolean {
    const path = window.location.pathname;
    return path === '/auth/success' || path === '/auth/callback';
  }

  /**
   * Get SSO providers
   */
  static async getProviders(): Promise<Array<{ name: string; display_name: string }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/providers`);
      if (!response.ok) {
        throw new Error('Failed to fetch providers');
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch SSO providers:', error);
      return [];
    }
  }
}