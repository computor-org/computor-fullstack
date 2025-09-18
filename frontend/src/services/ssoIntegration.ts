import { AuthUser, AuthToken } from '../types/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Helper to integrate SSO tokens with the existing auth system
 */
export class SSOIntegration {
  static async syncAuthData(): Promise<boolean> {
    try {
      // Check if we have SSO tokens
      const storedToken = localStorage.getItem('auth_token');
      if (!storedToken) return false;

      const token: AuthToken = JSON.parse(storedToken);
      
      // Fetch user info from API
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token.accessToken}`,
        },
      });

      if (!response.ok) {
        console.error('Failed to fetch user info:', response.status);
        return false;
      }

      const userInfo = await response.json();
      
      // Transform to frontend user format
      const user: AuthUser = {
        id: userInfo.user.id,
        username: userInfo.user.username || userInfo.user.email,
        email: userInfo.user.email,
        givenName: userInfo.user.given_name || 'User',
        familyName: userInfo.user.family_name || '',
        role: this.mapRole(userInfo.roles),
        permissions: this.mapPermissions(userInfo.roles),
        courses: [], // TODO: Fetch from API
      };

      // Store in the format expected by AuthService
      localStorage.setItem('auth_user', JSON.stringify(user));
      localStorage.setItem('auth_token', JSON.stringify(token));

      return true;
    } catch (error) {
      console.error('SSO sync error:', error);
      return false;
    }
  }

  private static mapRole(roles: string[]): 'admin' | 'lecturer' | 'student' {
    if (roles.includes('_admin')) return 'admin';
    if (roles.includes('_lecturer')) return 'lecturer';
    return 'student';
  }

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
    } else if (roles.includes('_lecturer')) {
      permissions.push(
        'view_students',
        'view_course_students',
        'create_assignments',
        'view_grades',
        'manage_course'
      );
    } else {
      permissions.push(
        'view_assignments',
        'submit_assignments'
      );
    }

    return permissions;
  }
}
