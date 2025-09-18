import { createHttpClient, ApiError as HttpError, HttpClientRequestOptions } from '../lib/api/httpClient';
import { SSOAuthService } from './ssoAuthService';
import { BasicAuthService } from './basicAuthService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface RequestOptions extends HttpClientRequestOptions {}

const httpClient = createHttpClient({
  baseUrl: API_BASE_URL,
});

const resolveAuthHeader = () => {
  if (BasicAuthService.isBasicAuth()) {
    const basicToken = BasicAuthService.getStoredToken();
    if (basicToken) {
      return { Authorization: `Basic ${basicToken.accessToken}` };
    }
  }

  const token = SSOAuthService.getStoredToken();
  if (token) {
    return { Authorization: `Bearer ${token.accessToken}` };
  }

  return null;
};

httpClient.setAuthProvider(resolveAuthHeader);

class APIClient {
  private static instance: APIClient;

  static getInstance(): APIClient {
    if (!APIClient.instance) {
      APIClient.instance = new APIClient();
    }

    return APIClient.instance;
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    try {
      return await httpClient.request<T>(endpoint, options);
    } catch (error) {
      if (options.skipAuth) {
        throw error;
      }

      if (error instanceof HttpError && error.status === 401) {
        const refreshResult = await SSOAuthService.refreshToken();

        if (refreshResult.success && refreshResult.token) {
          return httpClient.request<T>(endpoint, options);
        }

        await BasicAuthService.logout();
        await SSOAuthService.logout();
        window.location.href = '/login';
      }

      throw error;
    }
  }

  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async getWithMeta<T>(
    endpoint: string,
    options?: RequestOptions
  ): Promise<{ data: T; headers: Headers; status: number }> {
    try {
      return await httpClient.getWithMeta<T>(endpoint, options);
    } catch (error) {
      if (options?.skipAuth) {
        throw error;
      }

      if (error instanceof HttpError && error.status === 401) {
        const refreshResult = await SSOAuthService.refreshToken();

        if (refreshResult.success && refreshResult.token) {
          return httpClient.getWithMeta<T>(endpoint, options);
        }

        await BasicAuthService.logout();
        await SSOAuthService.logout();
        window.location.href = '/login';
      }

      throw error;
    }
  }

  async post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data,
    });
  }

  async put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data,
    });
  }

  async patch<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data,
    });
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  async deleteTask(taskId: string): Promise<{ task_id: string; status: string; message: string }> {
    return this.delete<{ task_id: string; status: string; message: string }>(`/tasks/${taskId}`);
  }

  async listUsers(params?: {
    limit?: number;
    offset?: number;
    search?: string;
    user_type?: string;
    archived?: boolean;
  }): Promise<any[]> {
    return this.get('/users', { params });
  }

  async getUserById(userId: string): Promise<any> {
    return this.get(`/users/${userId}`);
  }

  async getCurrentUser(): Promise<any> {
    return this.get('/user');
  }

  async createUser(userData: {
    given_name?: string;
    family_name?: string;
    email?: string;
    username?: string;
    user_type?: 'user' | 'token';
    properties?: any;
  }): Promise<any> {
    return this.post('/users', userData);
  }

  async updateUser(
    userId: string,
    userData: {
      given_name?: string;
      family_name?: string;
      email?: string;
      username?: string;
      number?: string;
      properties?: any;
    }
  ): Promise<any> {
    return this.patch(`/users/${userId}`, userData);
  }

  async deleteUser(userId: string): Promise<void> {
    await this.delete(`/users/${userId}`);
  }
}

export const apiClient = APIClient.getInstance();

export { HttpError as ApiError };
