import { LoginCredentials, AuthResponse, AuthUser, AuthToken } from '../types/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export class BasicAuthService {
  private static readonly TOKEN_KEY = 'auth_token';
  private static readonly USER_KEY = 'auth_user';
  private static readonly AUTH_KEY = 'basic_auth';

  /**
   * Login with email/password using basic auth
   */
  static async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      // Create basic auth header
      const authString = btoa(`${credentials.email}:${credentials.password}`);
      
      // Try to authenticate by fetching user info
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Basic ${authString}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          return {
            success: false,
            error: 'Invalid email or password',
          };
        }
        throw new Error('Authentication failed');
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

      // Store basic auth credentials (in production, consider more secure storage)
      const authToken: AuthToken = {
        accessToken: authString, // Store basic auth string as token
        refreshToken: '', // No refresh token for basic auth
        expiresAt: Date.now() + (24 * 60 * 60 * 1000), // 24 hours
      };

      // Store authentication data
      localStorage.setItem(this.TOKEN_KEY, JSON.stringify(authToken));
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      localStorage.setItem(this.AUTH_KEY, 'true');

      return {
        success: true,
        user,
        token: authToken,
      };
    } catch (error) {
      console.error('Basic auth error:', error);
      return {
        success: false,
        error: 'Authentication failed. Please check your credentials.',
      };
    }
  }

  /**
   * Logout user
   */
  static async logout(): Promise<void> {
    // Clear local storage
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.AUTH_KEY);
  }

  /**
   * Get stored authentication data
   */
  static getStoredAuth(): { user: AuthUser; token: AuthToken } | null {
    try {
      const storedToken = localStorage.getItem(this.TOKEN_KEY);
      const storedUser = localStorage.getItem(this.USER_KEY);
      const isBasicAuth = localStorage.getItem(this.AUTH_KEY);

      if (!storedToken || !storedUser || !isBasicAuth) {
        return null;
      }

      const token: AuthToken = JSON.parse(storedToken);
      const user: AuthUser = JSON.parse(storedUser);

      // Check if token is expired
      if (Date.now() > token.expiresAt) {
        this.logout();
        return null;
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
      const isBasicAuth = localStorage.getItem(this.AUTH_KEY);
      return (storedToken && isBasicAuth) ? JSON.parse(storedToken) : null;
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
      const isBasicAuth = localStorage.getItem(this.AUTH_KEY);
      return (storedUser && isBasicAuth) ? JSON.parse(storedUser) : null;
    } catch {
      return null;
    }
  }

  /**
   * Check if using basic auth
   */
  static isBasicAuth(): boolean {
    return localStorage.getItem(this.AUTH_KEY) === 'true';
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
}