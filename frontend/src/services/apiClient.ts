import { SSOAuthService } from './ssoAuthService';
import { BasicAuthService } from './basicAuthService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

class APIClient {
  private static instance: APIClient;

  private constructor() {}

  static getInstance(): APIClient {
    if (!APIClient.instance) {
      APIClient.instance = new APIClient();
    }
    return APIClient.instance;
  }

  /**
   * Make an authenticated API request
   */
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { skipAuth = false, ...fetchOptions } = options;

    // Prepare headers
    const headers = new Headers(fetchOptions.headers);

    // Add authentication header if not skipped
    if (!skipAuth) {
      // Check for basic auth first
      if (BasicAuthService.isBasicAuth()) {
        const basicToken = BasicAuthService.getStoredToken();
        if (basicToken) {
          headers.set('Authorization', `Basic ${basicToken.accessToken}`);
        }
      } else {
        // Use SSO/Bearer token
        const token = SSOAuthService.getStoredToken();
        if (token) {
          headers.set('Authorization', `Bearer ${token.accessToken}`);
        }
      }
    }

    // Set content type if not already set
    if (!headers.has('Content-Type') && fetchOptions.body) {
      headers.set('Content-Type', 'application/json');
    }

    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
      });

      // Handle 401 Unauthorized - try to refresh token
      if (response.status === 401 && !skipAuth) {
        const refreshResult = await SSOAuthService.refreshToken();
        
        if (refreshResult.success && refreshResult.token) {
          // Retry with new token
          headers.set('Authorization', `Bearer ${refreshResult.token.accessToken}`);
          const retryResponse = await fetch(url, {
            ...fetchOptions,
            headers,
          });

          if (!retryResponse.ok) {
            throw new Error(`API Error: ${retryResponse.status} ${retryResponse.statusText}`);
          }

          return await retryResponse.json();
        } else {
          // Refresh failed, redirect to login
          window.location.href = '/login';
          throw new Error('Authentication required');
        }
      }

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(errorBody || `API Error: ${response.status} ${response.statusText}`);
      }

      // Return JSON response
      return await response.json();
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
  }

  /**
   * Delete a task from the database
   */
  async deleteTask(taskId: string): Promise<{ task_id: string; status: string; message: string }> {
    return this.delete<{ task_id: string; status: string; message: string }>(`/tasks/${taskId}`);
  }
}

// Export singleton instance
export const apiClient = APIClient.getInstance();

// Export types for API responses
export interface APIResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface APIError {
  message: string;
  status: number;
  details?: any;
}