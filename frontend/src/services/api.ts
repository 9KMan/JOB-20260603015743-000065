const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;

    const authHeaders: Record<string, string> = {};
    const token = this.getToken();
    if (token) {
      authHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...headers,
      },
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(email: string, username: string, password: string, fullName?: string) {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: { email, username, password, full_name: fullName },
    });
  }

  async getMe() {
    return this.request('/api/v1/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // Chat endpoints
  async sendMessage(query: string, sessionId: string, topK: number = 5) {
    return this.request('/api/v1/chat/message', {
      method: 'POST',
      body: { query, session_id: sessionId, top_k: topK, stream: false },
    });
  }

  async getHistory(sessionId: string, limit: number = 50) {
    return this.request(`/api/v1/chat/history/${sessionId}?limit=${limit}`);
  }

  async clearHistory(sessionId: string) {
    return this.request(`/api/v1/chat/history/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Knowledge base endpoints
  async getKnowledgeItems(category?: string, search?: string) {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (search) params.append('search', search);
    const query = params.toString();
    return this.request(`/api/v1/knowledge-base/items${query ? `?${query}` : ''}`);
  }

  async createKnowledgeItem(title: string, content: string, category?: string, tags?: string[]) {
    return this.request('/api/v1/knowledge-base/items', {
      method: 'POST',
      body: { title, content, category, tags: tags || [] },
    });
  }
}

export const apiService = new ApiService();