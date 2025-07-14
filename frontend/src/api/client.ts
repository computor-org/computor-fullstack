import { SSOAuthService } from '../services/ssoAuthService';
import { AuthService } from '../services/authService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Try SSO auth first
    const ssoToken = SSOAuthService.getStoredToken();
    if (ssoToken && ssoToken.accessToken) {
      headers['Authorization'] = `Bearer ${ssoToken.accessToken}`;
      return headers;
    }

    // Fall back to mock auth
    const mockAuth = AuthService.getStoredAuth();
    if (mockAuth && mockAuth.token && mockAuth.token.accessToken) {
      headers['Authorization'] = `Bearer ${mockAuth.token.accessToken}`;
      return headers;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      if (response.status === 401) {
        // Try to refresh token
        const ssoAuth = SSOAuthService.getStoredAuth();
        if (ssoAuth) {
          const refreshResult = await SSOAuthService.refreshToken();
          if (!refreshResult.success) {
            // Refresh failed, redirect to login
            window.location.href = '/';
          }
        }
      }

      const error = await response.text();
      throw new Error(error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const headers = options?.skipAuth ? {} : await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      method: 'GET',
      headers: {
        ...headers,
        ...options?.headers,
      },
    });

    return this.handleResponse<T>(response);
  }

  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    const headers = options?.skipAuth ? {} : await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      method: 'POST',
      headers: {
        ...headers,
        ...options?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    const headers = options?.skipAuth ? {} : await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      method: 'PUT',
      headers: {
        ...headers,
        ...options?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const headers = options?.skipAuth ? {} : await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      method: 'DELETE',
      headers: {
        ...headers,
        ...options?.headers,
      },
    });

    return this.handleResponse<T>(response);
  }
}

// Export a singleton instance
export const apiClient = new APIClient();

// Export the class for custom instances
export { APIClient };