import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../useAuth';
import { AuthService } from '../../services/authService';

// Mock AuthService
jest.mock('../../services/authService');
const mockAuthService = AuthService as jest.Mocked<typeof AuthService>;

// Test component to access auth context
function TestComponent() {
  const { state, login, logout, clearError } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {state.isLoading ? 'loading' : state.isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="user-email">{state.user?.email || 'no-user'}</div>
      <div data-testid="error">{state.error || 'no-error'}</div>
      <button
        data-testid="login-btn"
        onClick={() => login({ username: 'testuser', password: 'password' })}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
      <button data-testid="clear-error-btn" onClick={clearError}>
        Clear Error
      </button>
    </div>
  );
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );
}

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuthService.getStoredAuth.mockReturnValue(null);
  });

  it('should start with loading state and then set to not authenticated', async () => {
    renderWithAuth();

    // Initial state should eventually be not authenticated
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });

    expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
    expect(screen.getByTestId('error')).toHaveTextContent('no-error');
  });

  it('should handle successful login', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@test.com',
      givenName: 'Test',
      familyName: 'User',
      role: 'student' as const,
      permissions: ['test'],
    };

    const mockToken = {
      accessToken: 'token',
      refreshToken: 'refresh',
      expiresAt: Date.now() + 60000,
    };

    mockAuthService.login.mockResolvedValue({
      success: true,
      user: mockUser,
      token: mockToken,
    });

    renderWithAuth();

    // Wait for initial loading to complete
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });

    fireEvent.click(screen.getByTestId('login-btn'));

    // Should show loading during login
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('loading');
    });

    // Should show authenticated after successful login
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    expect(screen.getByTestId('user-email')).toHaveTextContent('test@test.com');
    expect(mockAuthService.login).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password',
    });
  });

  it('should handle failed login', async () => {
    mockAuthService.login.mockResolvedValue({
      success: false,
      error: 'Invalid credentials',
    });

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });

    fireEvent.click(screen.getByTestId('login-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials');
    });

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
  });

  it('should handle logout', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@test.com',
      givenName: 'Test',
      familyName: 'User',
      role: 'student' as const,
      permissions: ['test'],
    };

    const mockToken = {
      accessToken: 'token',
      refreshToken: 'refresh',
      expiresAt: Date.now() + 60000,
    };

    // Start with stored auth
    mockAuthService.getStoredAuth.mockReturnValue({
      user: mockUser,
      token: mockToken,
    });

    mockAuthService.refreshToken.mockResolvedValue({
      success: true,
      user: mockUser,
      token: mockToken,
    });

    mockAuthService.logout.mockResolvedValue();

    renderWithAuth();

    // Should be authenticated initially
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    fireEvent.click(screen.getByTestId('logout-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });

    expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
    expect(mockAuthService.logout).toHaveBeenCalled();
  });

  it('should clear error', async () => {
    mockAuthService.login.mockResolvedValue({
      success: false,
      error: 'Test error',
    });

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });

    fireEvent.click(screen.getByTestId('login-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Test error');
    });

    fireEvent.click(screen.getByTestId('clear-error-btn'));

    expect(screen.getByTestId('error')).toHaveTextContent('no-error');
  });

  it('should restore authentication from stored session', async () => {
    const mockUser = {
      id: '1',
      username: 'storeduser',
      email: 'stored@test.com',
      givenName: 'Stored',
      familyName: 'User',
      role: 'lecturer' as const,
      permissions: ['test'],
    };

    const mockToken = {
      accessToken: 'stored-token',
      refreshToken: 'stored-refresh',
      expiresAt: Date.now() + 60000,
    };

    mockAuthService.getStoredAuth.mockReturnValue({
      user: mockUser,
      token: mockToken,
    });

    mockAuthService.refreshToken.mockResolvedValue({
      success: true,
      user: mockUser,
      token: mockToken,
    });

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    expect(screen.getByTestId('user-email')).toHaveTextContent('stored@test.com');
    expect(mockAuthService.refreshToken).toHaveBeenCalled();
  });
});
