export interface HttpClientRequestOptions extends Omit<RequestInit, 'body'> {
  body?: BodyInit | null | unknown;
  params?: Record<string, string | number | boolean | null | undefined>;
  skipAuth?: boolean;
}

export interface HttpClientConfig {
  baseUrl: string;
  defaultHeaders?: HeadersInit;
}

export interface AuthHeader {
  Authorization: string;
}

export type AuthProvider = () => Promise<AuthHeader | null> | AuthHeader | null;
export type UnauthorizedHandler = () => void;

export class ApiError<T = unknown> extends Error {
  status: number;
  statusText: string;
  data?: T;

  constructor(status: number, statusText: string, data?: T, message?: string) {
    super(message || getDefaultMessage(status, statusText, data));
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

const getDefaultMessage = <T,>(status: number, statusText: string, data?: T): string => {
  if (data && typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail?: string }).detail;
    if (detail) {
      return detail;
    }
  }
  return `Request failed with status ${status} ${statusText}`;
};

export class HttpClient {
  private authProvider: AuthProvider | null = null;
  private unauthorizedHandler: UnauthorizedHandler | null = null;
  private readonly baseUrl: string;
  private readonly defaultHeaders?: HeadersInit;

  constructor(config: HttpClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.defaultHeaders = config.defaultHeaders;
  }

  setAuthProvider(provider: AuthProvider | null) {
    this.authProvider = provider;
  }

  setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
    this.unauthorizedHandler = handler;
  }

  async request<T>(endpoint: string, options: HttpClientRequestOptions = {}): Promise<T> {
    const { data } = await this.executeRequest<T>(endpoint, options);
    return data;
  }

  async requestWithMeta<T>(
    endpoint: string,
    options: HttpClientRequestOptions = {}
  ): Promise<{ data: T; headers: Headers; status: number }> {
    const { data, response } = await this.executeRequest<T>(endpoint, options);
    return {
      data,
      headers: response.headers,
      status: response.status,
    };
  }

  private async executeRequest<T>(
    endpoint: string,
    options: HttpClientRequestOptions
  ): Promise<{ data: T; response: Response }> {
    const { params, skipAuth, headers: requestHeaders, body, ...fetchInit } = options;

    const url = this.buildUrl(endpoint, params);
    const headers = this.buildHeaders(requestHeaders);
    const normalizedBody = this.normalizeBody(body);

    if (!skipAuth && this.authProvider) {
      const authHeader = await this.authProvider();
      if (authHeader?.Authorization) {
        headers.set('Authorization', authHeader.Authorization);
      }
    }

    if (
      !headers.has('Content-Type') &&
      normalizedBody !== undefined &&
      !(normalizedBody instanceof FormData)
    ) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, {
      ...fetchInit,
      body: normalizedBody,
      headers,
    });

    if (response.status === 401 && this.unauthorizedHandler) {
      this.unauthorizedHandler();
    }

    if (response.status === 204) {
      return { data: {} as T, response };
    }

    let data: T | undefined;
    const contentType = response.headers.get('content-type');

    if (contentType && contentType.includes('application/json')) {
      data = (await response.json()) as T;
    } else {
      const text = await response.text();
      data = text ? (text as unknown as T) : undefined;
    }

    if (!response.ok) {
      throw new ApiError(response.status, response.statusText, data);
    }

    return { data: data as T, response };
  }

  get<T>(endpoint: string, options?: HttpClientRequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, body?: unknown, options?: HttpClientRequestOptions) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body,
    });
  }

  put<T>(endpoint: string, body?: unknown, options?: HttpClientRequestOptions) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body,
    });
  }

  patch<T>(endpoint: string, body?: unknown, options?: HttpClientRequestOptions) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body,
    });
  }

  delete<T>(endpoint: string, options?: HttpClientRequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
  
  getWithMeta<T>(endpoint: string, options?: HttpClientRequestOptions) {
    return this.requestWithMeta<T>(endpoint, { ...options, method: 'GET' });
  }

  private buildUrl(endpoint: string, params?: HttpClientRequestOptions['params']): string {
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = new URL(`${this.baseUrl}${normalizedEndpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (!isNil(value)) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return url.toString();
  }

  private buildHeaders(requestHeaders?: HeadersInit): Headers {
    const headers = new Headers(this.defaultHeaders);

    if (requestHeaders) {
      new Headers(requestHeaders).forEach((value, key) => {
        headers.set(key, value);
      });
    }

    return headers;
  }

  private normalizeBody(body: unknown): BodyInit | undefined {
    if (body === undefined || body === null) {
      return undefined;
    }

    if (body instanceof FormData || body instanceof Blob || body instanceof ArrayBuffer) {
      return body as BodyInit;
    }

    if (typeof body === 'string') {
      return body;
    }

    if (body instanceof URLSearchParams) {
      return body;
    }

    return JSON.stringify(body);
  }
}

const isNil = (value: unknown): value is null | undefined => value === null || value === undefined;

export const createHttpClient = (config: HttpClientConfig) => new HttpClient(config);
