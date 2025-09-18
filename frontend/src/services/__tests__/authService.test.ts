import { AuthService } from '../authService';
import { LoginCredentials } from '../../types/auth';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      const credentials: LoginCredentials = {
        username: 'admin',
        password: 'admin123',
      };

      const result = await AuthService.login(credentials);

      expect(result.success).toBe(true);
      expect(result.user).toBeDefined();
      expect(result.user?.username).toBe(credentials.username);
      expect(result.user?.role).toBe('admin');
      expect(result.token).toBeDefined();
      expect(localStorageMock.setItem).toHaveBeenCalledTimes(2);
    });

    it('should fail login with invalid username', async () => {
      const credentials: LoginCredentials = {
        username: 'nonexistent',
        password: 'admin123',
      };

      const result = await AuthService.login(credentials);

      expect(result.success).toBe(false);
      expect(result.error).toBe('User not found');
      expect(result.user).toBeUndefined();
      expect(result.token).toBeUndefined();
    });

    it('should fail login with invalid password', async () => {
      const credentials: LoginCredentials = {
        username: 'admin',
        password: 'wrongpassword',
      };

      const result = await AuthService.login(credentials);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid password');
      expect(result.user).toBeUndefined();
      expect(result.token).toBeUndefined();
    });

    it('should return different users based on role', async () => {
      const adminLogin = await AuthService.login({
        username: 'admin',
        password: 'admin123',
      });

      const studentLogin = await AuthService.login({
        username: 'student',
        password: 'student123',
      });

      expect(adminLogin.user?.role).toBe('admin');
      expect(studentLogin.user?.role).toBe('student');
      expect(adminLogin.user?.permissions).toContain('admin_access');
      expect(studentLogin.user?.permissions).not.toContain('admin_access');
    });
  });

  describe('logout', () => {
    it('should remove tokens from localStorage', async () => {
      await AuthService.logout();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_user');
    });
  });

  describe('refreshToken', () => {
    it('should successfully refresh valid token', async () => {
      const mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@university.edu',
        givenName: 'John',
        familyName: 'Admin',
        role: 'admin' as const,
        permissions: ['admin_access'],
      };
      
      const mockToken = {
        accessToken: 'mock_token',
        refreshToken: 'mock_refresh',
        expiresAt: Date.now() + 60000, // 1 minute from now
      };

      localStorageMock.getItem
        .mockReturnValueOnce(JSON.stringify(mockToken))
        .mockReturnValueOnce(JSON.stringify(mockUser));

      const result = await AuthService.refreshToken();

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(result.token).toBeDefined();
    });

    it('should fail refresh with expired token', async () => {
      const mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@university.edu',
        givenName: 'John',
        familyName: 'Admin',
        role: 'admin' as const,
        permissions: ['admin_access'],
      };
      
      const mockToken = {
        accessToken: 'mock_token',
        refreshToken: 'mock_refresh',
        expiresAt: Date.now() - 60000, // 1 minute ago (expired)
      };

      localStorageMock.getItem
        .mockReturnValueOnce(JSON.stringify(mockToken))
        .mockReturnValueOnce(JSON.stringify(mockUser));

      const result = await AuthService.refreshToken();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Token expired');
      expect(localStorageMock.removeItem).toHaveBeenCalledTimes(2);
    });

    it('should fail refresh with no stored session', async () => {
      const result = await AuthService.refreshToken();

      expect(result.success).toBe(false);
      expect(result.error).toBe('No stored session');
    });
  });

  describe('getStoredAuth', () => {
    it('should return stored auth when valid', () => {
      const mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@university.edu',
        givenName: 'John',
        familyName: 'Admin',
        role: 'admin' as const,
        permissions: ['admin_access'],
      };
      
      const mockToken = {
        accessToken: 'mock_token',
        refreshToken: 'mock_refresh',
        expiresAt: Date.now() + 60000, // Valid token
      };

      localStorageMock.getItem
        .mockReturnValueOnce(JSON.stringify(mockToken))
        .mockReturnValueOnce(JSON.stringify(mockUser));

      const result = AuthService.getStoredAuth();

      expect(result).toEqual({
        user: mockUser,
        token: mockToken,
      });
    });

    it('should return null when token is expired', () => {
      const mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@university.edu',
        givenName: 'John',
        familyName: 'Admin',
        role: 'admin' as const,
        permissions: ['admin_access'],
      };
      
      const mockToken = {
        accessToken: 'mock_token',
        refreshToken: 'mock_refresh',
        expiresAt: Date.now() - 60000, // Expired token
      };

      localStorageMock.getItem
        .mockReturnValueOnce(JSON.stringify(mockToken))
        .mockReturnValueOnce(JSON.stringify(mockUser));

      const result = AuthService.getStoredAuth();

      expect(result).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledTimes(2);
    });

    it('should return null when no stored data', () => {
      const result = AuthService.getStoredAuth();

      expect(result).toBeNull();
    });
  });

  describe('getDemoCredentials', () => {
    it('should return demo credentials for all roles', () => {
      const credentials = AuthService.getDemoCredentials();

      expect(credentials.admin).toEqual({
        username: 'admin',
        password: 'admin123',
      });
      expect(credentials.lecturer).toEqual({
        username: 'lecturer',
        password: 'lecturer123',
      });
      expect(credentials.student).toEqual({
        username: 'student',
        password: 'student123',
      });
    });
  });
});
