import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, AuthContextType, LoginCredentials } from '../types/auth';
import { AuthService } from '../services/authService';
import { SSOAuthService } from '../services/ssoAuthService';

// Auth state reducer
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: any; token: any } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; payload: boolean };

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  isLoading: true, // Start with loading to check stored auth
  error: null,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        token: action.payload.token,
        isLoading: false,
        error: null,
      };
    case 'LOGIN_FAILURE':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
        error: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    default:
      return state;
  }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for stored authentication on app start
  useEffect(() => {
    const checkStoredAuth = async () => {
      // Check if we're on SSO callback page - don't check auth yet
      if (SSOAuthService.isSSOCallback()) {
        dispatch({ type: 'SET_LOADING', payload: false });
        return;
      }

      // First check for SSO auth
      const ssoAuth = SSOAuthService.getStoredAuth();
      if (ssoAuth) {
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: {
            user: ssoAuth.user,
            token: ssoAuth.token,
          },
        });
        return;
      }

      // Fall back to mock auth
      const storedAuth = AuthService.getStoredAuth();
      if (storedAuth) {
        // Try to refresh token to ensure it's still valid
        const refreshResult = await AuthService.refreshToken();
        
        if (refreshResult.success && refreshResult.user && refreshResult.token) {
          dispatch({
            type: 'LOGIN_SUCCESS',
            payload: {
              user: refreshResult.user,
              token: refreshResult.token,
            },
          });
        } else {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } else {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    checkStoredAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    dispatch({ type: 'LOGIN_START' });

    try {
      const result = await AuthService.login(credentials);

      if (result.success && result.user && result.token) {
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: {
            user: result.user,
            token: result.token,
          },
        });
        return result;
      } else {
        dispatch({
          type: 'LOGIN_FAILURE',
          payload: result.error || 'Login failed',
        });
        return result;
      }
    } catch (error) {
      const errorMessage = 'Network error occurred';
      dispatch({
        type: 'LOGIN_FAILURE',
        payload: errorMessage,
      });
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  const logout = async () => {
    try {
      // Check if we have SSO auth
      const ssoAuth = SSOAuthService.getStoredAuth();
      if (ssoAuth) {
        await SSOAuthService.logout();
      } else {
        await AuthService.logout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      // Check if we have SSO auth
      const ssoAuth = SSOAuthService.getStoredAuth();
      let result;
      
      if (ssoAuth) {
        result = await SSOAuthService.refreshToken();
      } else {
        result = await AuthService.refreshToken();
      }
      
      if (result.success && result.user && result.token) {
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: {
            user: result.user,
            token: result.token,
          },
        });
        return true;
      } else {
        dispatch({ type: 'LOGOUT' });
        return false;
      }
    } catch (error) {
      dispatch({ type: 'LOGOUT' });
      return false;
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    state,
    login,
    logout,
    refreshToken,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};