export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthToken {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export interface AuthUser {
  id: string;
  email: string;
  givenName: string;
  familyName: string;
  role: 'student' | 'tutor' | 'lecturer' | 'admin' | 'owner';
  permissions: string[];
  courses?: string[];
  avatar?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  token: AuthToken | null;
  isLoading: boolean;
  error: string | null;
}

export interface AuthResponse {
  success: boolean;
  user?: AuthUser;
  token?: AuthToken;
  error?: string;
}

export interface AuthContextType {
  state: AuthState;
  login: (credentials: LoginCredentials) => Promise<AuthResponse>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  clearError: () => void;
}