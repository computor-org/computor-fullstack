import { SSOAuthService } from '../services/ssoAuthService';
import { AuthService } from '../services/authService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  params?: Record<string, unknown>;
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

  private async handleResponse<T>(response: Response, method?: string): Promise<T> {
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

    if (response.status === 204 || (method && method.toUpperCase() === 'HEAD')) {
      return {} as T;
    }

    const text = await response.text();
    if (!text) {
      return {} as T;
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        return JSON.parse(text) as T;
      } catch (error) {
        console.warn('Failed to parse JSON response', error);
      }
    }

    return text as unknown as T;
  }

  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...(options ?? {}), method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...(options ?? {}), method: 'POST', data });
  }

  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...(options ?? {}), method: 'PUT', data });
  }

  async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...(options ?? {}), method: 'PATCH', data });
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...(options ?? {}), method: 'DELETE' });
  }

  async request<T>(
    endpoint: string,
    options: RequestOptions & { method: string; data?: any }
  ): Promise<T> {
    const {
      method,
      data,
      skipAuth,
      params,
      headers: customHeaders,
      body: rawBody,
      ...restOptions
    } = options;

    const headers = skipAuth ? {} : await this.getAuthHeaders();
    const url = this.buildUrl(endpoint, params);

    let body: BodyInit | undefined = rawBody as BodyInit | undefined;
    if (data !== undefined) {
      body = data instanceof FormData ? data : JSON.stringify(data);
    }

    const methodUpper = method.toUpperCase();

    const response = await fetch(url, {
      ...restOptions,
      method: methodUpper,
      headers: {
        ...headers,
        ...(customHeaders ?? {}),
      },
      body: ['GET', 'HEAD'].includes(methodUpper) ? undefined : body,
    });

    return this.handleResponse<T>(response, methodUpper);
  }

  private buildUrl(endpoint: string, params?: Record<string, unknown>): string {
    if (!params || Object.keys(params).length === 0) {
      return `${this.baseURL}${endpoint}`;
    }

    const searchParams = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null) {
        continue;
      }

      if (Array.isArray(value)) {
        value
          .filter((item) => item !== undefined && item !== null)
          .forEach((item) => searchParams.append(key, String(item)));
      } else if (value instanceof Date) {
        searchParams.append(key, value.toISOString());
      } else if (typeof value === 'object') {
        searchParams.append(key, JSON.stringify(value));
      } else {
        searchParams.append(key, String(value));
      }
    }

    const query = searchParams.toString();
    if (!query) {
      return `${this.baseURL}${endpoint}`;
    }

    return `${this.baseURL}${endpoint}?${query}`;
  }
}

// Export a singleton instance
export const apiClient = new APIClient();

// Export the class for custom instances
export { APIClient };
