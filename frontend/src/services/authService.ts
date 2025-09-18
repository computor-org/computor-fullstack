import { LoginCredentials, AuthResponse, AuthUser, AuthToken } from '../types/auth';

// Mock users database
const mockUsers: (AuthUser & { password: string })[] = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@university.edu',
    password: 'admin123',
    givenName: 'John',
    familyName: 'Admin',
    role: 'admin',
    permissions: [
      'view_students',
      'view_course_students',
      'create_assignments',
      'view_grades',
      'manage_course',
      'admin_access',
      'manage_users',
      'system_settings',
      'view_audit',
    ],
    courses: ['1', '2', '3'],
  },
  {
    id: '2',
    username: 'lecturer',
    email: 'lecturer@university.edu',
    password: 'lecturer123',
    givenName: 'Jane',
    familyName: 'Smith',
    role: 'lecturer',
    permissions: [
      'view_students',
      'view_course_students',
      'create_assignments',
      'view_grades',
      'manage_course',
    ],
    courses: ['1', '2'],
  },
  {
    id: '3',
    username: 'student',
    email: 'student@university.edu',
    password: 'student123',
    givenName: 'Bob',
    familyName: 'Johnson',
    role: 'student',
    permissions: ['view_assignments', 'submit_assignments'],
    courses: ['1'],
  },
];

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Generate mock JWT token
const generateToken = (user: AuthUser): AuthToken => {
  const now = Date.now();
  return {
    accessToken: `mock_token_${user.id}_${now}`,
    refreshToken: `mock_refresh_${user.id}_${now}`,
    expiresAt: now + (60 * 60 * 1000), // 1 hour from now
  };
};

export class AuthService {
  private static readonly TOKEN_KEY = 'auth_token';
  private static readonly USER_KEY = 'auth_user';

  static async login(credentials: LoginCredentials): Promise<AuthResponse> {
    await delay(800); // Simulate network delay

    // Find user by email
    const user = mockUsers.find(u => u.username === credentials.username || u.email === credentials.username);
    
    if (!user) {
      return {
        success: false,
        error: 'User not found',
      };
    }

    // Check password
    if (user.password !== credentials.password) {
      return {
        success: false,
        error: 'Invalid password',
      };
    }

    // Remove password from user object
    const { password, ...userWithoutPassword } = user;
    const token = generateToken(userWithoutPassword);

    // Store in localStorage (simulate server session)
    localStorage.setItem(this.TOKEN_KEY, JSON.stringify(token));
    localStorage.setItem(this.USER_KEY, JSON.stringify(userWithoutPassword));

    return {
      success: true,
      user: userWithoutPassword,
      token,
    };
  }

  static async logout(): Promise<void> {
    await delay(200);
    
    // Remove from localStorage
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  static async refreshToken(): Promise<AuthResponse> {
    await delay(300);

    const storedToken = localStorage.getItem(this.TOKEN_KEY);
    const storedUser = localStorage.getItem(this.USER_KEY);

    if (!storedToken || !storedUser) {
      return {
        success: false,
        error: 'No stored session',
      };
    }

    try {
      const token: AuthToken = JSON.parse(storedToken);
      const user: AuthUser = JSON.parse(storedUser);

      // Check if token is expired
      if (Date.now() > token.expiresAt) {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        return {
          success: false,
          error: 'Token expired',
        };
      }

      // Generate new token
      const newToken = generateToken(user);
      localStorage.setItem(this.TOKEN_KEY, JSON.stringify(newToken));

      return {
        success: true,
        user,
        token: newToken,
      };
    } catch (error) {
      return {
        success: false,
        error: 'Invalid stored session',
      };
    }
  }

  static getStoredAuth(): { user: AuthUser; token: AuthToken } | null {
    try {
      const storedToken = localStorage.getItem(this.TOKEN_KEY);
      const storedUser = localStorage.getItem(this.USER_KEY);

      if (!storedToken || !storedUser) {
        return null;
      }

      const token: AuthToken = JSON.parse(storedToken);
      
      // Check if we have SSO user data (temporary fix)
      let user: AuthUser;
      if (typeof storedUser === 'string' && storedUser.includes('isAuthenticated')) {
        // This is SSO data, create a mock user
        const ssoData = JSON.parse(storedUser);
        user = {
          id: ssoData.id || '1',
          username: 'admin',
          email: 'admin@university.edu',
          givenName: 'Admin',
          familyName: 'User',
          role: 'admin',
          permissions: [
            'view_students',
            'view_course_students',
            'create_assignments',
            'view_grades',
            'manage_course',
            'admin_access',
            'manage_users',
            'system_settings',
            'view_audit',
          ],
          courses: ['1', '2', '3'],
        };
      } else {
        user = JSON.parse(storedUser);
      }

      // Check if token is expired
      if (Date.now() > token.expiresAt) {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        return null;
      }

      return { user, token };
    } catch {
      return null;
    }
  }

  // Helper method to get demo credentials
  static getDemoCredentials() {
    return {
      admin: { username: 'admin', password: 'admin123' },
      lecturer: { username: 'lecturer', password: 'lecturer123' },
      student: { username: 'student', password: 'student123' },
    };
  }
}
